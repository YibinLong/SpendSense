# Fix Summary: Recommendation Caching by Time Window

## Issue Description
The `get_recommendations` endpoint had a critical caching bug where recommendations generated for one time window (e.g., 30 days) would be returned when requesting a different time window (e.g., 180 days). This happened because:

1. The `Recommendation` model didn't store which `window_days` was used to generate each recommendation
2. The cache lookup only filtered by `user_id`, not by `window_days`

## Example of the Bug
```python
# User requests 30-day recommendations
GET /recommendations/user_123?window=30
# Generates recommendations based on 30-day signals and stores them

# Later, user requests 180-day recommendations  
GET /recommendations/user_123?window=180
# BUG: Returns the cached 30-day recommendations instead of generating new 180-day ones!
```

## Root Cause
Looking at the original code in `routes_recommendations.py` (lines 92-100):

```python
# Check if recommendations already exist
if not regenerate:
    existing_recs = db.query(Recommendation).filter(
        Recommendation.user_id == user_id,
        # MISSING: Recommendation.window_days == window,
    ).all()
```

The query only filtered by `user_id`, so any cached recommendations were returned regardless of which time window was requested.

## Fix Applied

### 1. Added `window_days` field to `Recommendation` model
**File:** `spendsense/app/db/models.py`

Added a new column to track which time window was used:
```python
class Recommendation(Base):
    # ... other fields ...
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
```

**Why this fixes it:** Now each recommendation stores which time window (30 or 180 days) was used to generate it.

### 2. Updated cache lookup to filter by BOTH user_id AND window_days
**File:** `spendsense/app/api/routes_recommendations.py`

Changed the query to include `window_days` filter:
```python
# Check if recommendations already exist for this user AND window
if not regenerate:
    existing_recs = db.query(Recommendation).filter(
        Recommendation.user_id == user_id,
        Recommendation.window_days == window,  # NEW: Filter by window too!
    ).all()
```

**Why this fixes it:** Now the cache only returns recommendations that were generated for the requested time window.

### 3. Engine stores window_days when creating recommendations
**File:** `spendsense/app/recommend/engine.py`

Updated both education and offer creation to include `window_days`:
```python
rec = Recommendation(
    user_id=user_id,
    persona_id=persona_id,
    window_days=window_days,  # NEW: Store the time window
    item_type="education",
    # ... other fields ...
)
```

**Why this fixes it:** Ensures every new recommendation records which time window it was generated for.

### 4. Updated Pydantic schema to include window_days
**File:** `spendsense/app/schemas/recommendation.py`

Added field to API response model:
```python
class RecommendationItem(BaseModel):
    # ... other fields ...
    window_days: int = Field(
        default=30,
        description="Time window in days (30 or 180) used to generate this recommendation"
    )
```

**Why this fixes it:** Now API responses include the time window information, making it transparent to users.

## Database Migration

Since the `Recommendation` table already exists in some databases, a migration script was created:

**File:** `scripts/migrate_add_window_days.py`

This script:
- Checks if `window_days` column exists
- Adds it if missing (with default value of 30)
- Safe to run multiple times (idempotent)

**Usage:**
```bash
python -m scripts.migrate_add_window_days
```

For new databases, just run `init_db()` and the column will be created automatically.

## Testing

The fix preserves existing test behavior because:
1. Tests use `generate_recommendations()` which now includes `window_days`
2. Tests don't directly create `Recommendation` objects
3. The default value (30) matches typical test scenarios

Existing tests in `test_recommendations_flow.py` will continue to pass.

## Verification

After applying the fix, test the scenario:

```bash
# 1. Generate 30-day recommendations
curl "http://localhost:8000/recommendations/user_123?window=30"
# Should return recommendations based on 30-day signals
# Response includes "window_days": 30

# 2. Generate 180-day recommendations  
curl "http://localhost:8000/recommendations/user_123?window=180"
# Should return DIFFERENT recommendations based on 180-day signals
# Response includes "window_days": 180

# 3. Request 30-day again (without regenerate)
curl "http://localhost:8000/recommendations/user_123?window=30"
# Should return cached 30-day recommendations (not the 180-day ones)
```

## Impact

- **Fixed:** Users now get correct recommendations for their requested time window
- **Breaking Change:** Minimal - just adds a new field to the database and API response
- **Migration:** Required for existing databases (see migration script)

## Files Changed

1. `spendsense/app/db/models.py` - Added `window_days` field to `Recommendation` model
2. `spendsense/app/api/routes_recommendations.py` - Updated cache lookup query
3. `spendsense/app/recommend/engine.py` - Store `window_days` when creating recommendations
4. `spendsense/app/schemas/recommendation.py` - Added `window_days` to API response schema
5. `scripts/migrate_add_window_days.py` - Migration script for existing databases
