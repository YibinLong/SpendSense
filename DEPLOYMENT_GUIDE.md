# SpendSense Deployment Guide

This guide walks you through deploying SpendSense to production using **Render** (backend) and **Vercel** (frontend).

## ✅ What I've Already Done For You

I've created the following files and configurations:

1. **`render.yaml`** - Configuration file for Render backend deployment
2. **`frontend/vercel.json`** - Configuration file for Vercel frontend deployment  
3. **`frontend/.env.production`** - Production environment variables (you'll need to create this manually since it's gitignored)
4. **Updated `spendsense/app/main.py`** - Added CORS settings for Vercel domains

---

## 🚀 Deployment Steps

### PART A: Deploy Backend to Render

#### Step 1: Push Your Code to GitHub

Make sure all changes are committed and pushed to GitHub:

```bash
git add .
git commit -m "Add deployment configurations for Render and Vercel"
git push origin main
```

**Why**: Both Render and Vercel deploy directly from your GitHub repository.

---

#### Step 2: Create Render Account & Deploy

1. Go to [render.com](https://render.com) and **sign up** or **log in**
2. Click **"New +"** button in the top right
3. Select **"Blueprint"**
4. Click **"Connect GitHub"** (if not already connected)
5. Find and select your **SpendSense** repository
6. Render will automatically detect the `render.yaml` file
7. Click **"Apply"** or **"Create Resources"**
8. Wait 5-10 minutes for deployment to complete

**Why we use Blueprint**: The `render.yaml` file I created tells Render exactly how to build and run your FastAPI backend, including all environment variables.

---

#### Step 3: Copy Your Backend URL

After deployment completes:

1. Click on your **spendsense-backend** service
2. At the top, you'll see a URL like: `https://spendsense-backend-xxxx.onrender.com`
3. **Copy this URL** - you'll need it for the frontend

**Test it**: Visit `https://your-backend-url.onrender.com/health` - you should see:
```json
{"status":"healthy","app":"SpendSense","environment":"prod"}
```

---

#### Step 4: Initialize the Database

Your backend is running but has an empty database. Let's populate it:

1. In Render dashboard, go to your **spendsense-backend** service
2. Click the **"Shell"** tab on the left
3. Wait for the shell to connect
4. Run this command:
   ```bash
   python reset_and_populate.py
   ```
5. Wait for it to complete (creates users, transactions, etc.)

**Why this is needed**: Your SQLite database starts empty. This script creates sample users and transactions for testing.

**Important Note**: Render's free tier has **ephemeral storage** - the database will reset after 15 minutes of inactivity. For a real production app, you'd want to upgrade to a paid plan or use PostgreSQL.

---

### PART B: Deploy Frontend to Vercel

#### Step 5: Create Production Environment File

Since `.env.production` is gitignored, you need to create it manually:

1. Create `frontend/.env.production` with this content:
   ```bash
   VITE_API_BASE=https://your-backend-url.onrender.com
   ```
2. **Replace `your-backend-url.onrender.com`** with the actual URL from Step 3
3. **Do NOT commit this file** - it's already in `.gitignore`

**Why this is needed**: In development, your frontend calls `http://127.0.0.1:8000`. In production, it needs to call your deployed backend on Render.

---

#### Step 6: Deploy to Vercel

**Option A: Using Vercel Dashboard (Easiest)**

1. Go to [vercel.com](https://vercel.com) and **sign up** or **log in**
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. **IMPORTANT**: Click **"Edit"** next to "Root Directory"
5. Set Root Directory to: **`frontend`**
6. Framework Preset should auto-detect as **"Vite"**
7. Click **"Environment Variables"** section
8. Add one variable:
   - **Name**: `VITE_API_BASE`
   - **Value**: `https://your-backend-url.onrender.com` (from Step 3)
   - **Environments**: Check all (Production, Preview, Development)
9. Click **"Deploy"**
10. Wait 2-5 minutes for deployment

**Option B: Using Vercel CLI**

```bash
# Install Vercel CLI globally
npm install -g vercel

# Navigate to frontend directory
cd frontend

# Login to Vercel
vercel login

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Y
# - Which scope? (choose your account)
# - Link to existing project? N
# - Project name? spendsense
# - Directory? ./ (already in frontend)
# - Override settings? N

# After first deployment, deploy to production:
vercel --prod
```

---

#### Step 7: Copy Your Frontend URL

After deployment:

1. Vercel will show you a URL like: `https://spendsense.vercel.app`
2. **Copy this URL**

**Why**: We need to update the backend CORS settings with your actual Vercel URL.

---

#### Step 8: Update Backend CORS (If Needed)

If your Vercel URL is NOT `https://spendsense.vercel.app`, you need to update the backend:

1. Open `spendsense/app/main.py`
2. Find line 85 where it says `"https://spendsense.vercel.app"`
3. Replace with your actual Vercel URL
4. Commit and push:
   ```bash
   git add spendsense/app/main.py
   git commit -m "Update CORS with production Vercel URL"
   git push origin main
   ```
5. Render will automatically redeploy (takes 2-3 minutes)

**Why**: CORS (Cross-Origin Resource Sharing) security prevents unauthorized websites from calling your API. We need to explicitly allow your Vercel domain.

---

## 🧪 Testing Your Deployment

1. **Test Backend Health**:
   ```bash
   curl https://your-backend-url.onrender.com/health
   ```
   Expected response: `{"status":"healthy","app":"SpendSense","environment":"prod"}`

2. **Test Frontend**:
   - Visit your Vercel URL: `https://spendsense.vercel.app`
   - You should see the login page
   - Try logging in with a test user (credentials from seeded database)

3. **Check for Issues**:
   - Open browser DevTools (F12) → Console tab
   - Look for any red errors
   - Common issues:
     - **CORS errors**: Backend CORS needs updating
     - **Network errors**: Check if backend URL is correct in Vercel env vars
     - **401/403 errors**: Database might be empty (rerun Step 4)

---

## 🔐 Environment Variables Summary

### Backend (Render)

These are automatically set from `render.yaml`:

| Variable | Value | Notes |
|----------|-------|-------|
| `APP_ENV` | `prod` | Sets production mode |
| `SEED` | `42` | Random seed for data generation |
| `DATABASE_URL` | `sqlite:///./data/spendsense.db` | SQLite database path |
| `DATA_DIR` | `./data` | Data storage directory |
| `PARQUET_DIR` | `./data/parquet` | Parquet files directory |
| `LOG_LEVEL` | `WARNING` | Reduces log verbosity |
| `DEBUG` | `false` | Disables debug mode |
| `JWT_SECRET_KEY` | *Auto-generated* | Secure random key for JWT tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 24 hour token expiry |

### Frontend (Vercel)

Set this manually in Vercel dashboard:

| Variable | Value | Notes |
|----------|-------|-------|
| `VITE_API_BASE` | `https://your-backend-url.onrender.com` | Backend API URL |

---

## ⚠️ Important Limitations & Notes

### 1. **Render Free Tier - Ephemeral Storage**
- Database **resets** when service spins down (after 15 min inactivity)
- First request after spin-down takes 30-60 seconds ("cold start")
- **Solution for production**: 
  - Upgrade to paid plan ($7/month) with persistent disk
  - OR switch to PostgreSQL database (Render offers free PostgreSQL)

### 2. **CORS Configuration**
- Wildcard `https://*.vercel.app` allows ALL Vercel preview deployments
- For production, you might want to restrict to specific domain only
- If you get CORS errors, check that your Vercel URL is in the backend's CORS list

### 3. **Environment Variables**
- **NEVER** commit `.env` files to git (they contain secrets)
- `.env.production` should be created locally for testing
- In production, Vercel/Render use their own environment variable systems
- Changes to Vercel env vars require redeployment

### 4. **Database Initialization**
- You need to manually run `reset_and_populate.py` after backend deployment
- This creates test users and sample data
- For production, you'd want a proper database migration strategy

---

## 🎯 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| **Can't login** | Database might be empty - run Step 4 again |
| **CORS errors** | Update backend CORS with your Vercel URL (Step 8) |
| **Backend returns 500** | Check Render logs in dashboard |
| **Frontend shows "Network Error"** | Verify `VITE_API_BASE` is set correctly in Vercel |
| **Backend is slow** | Cold start after inactivity (free tier limitation) |

---

## 📊 Monitoring Your Deployment

### Render Dashboard
- **Logs**: Click "Logs" tab to see backend errors
- **Metrics**: See CPU, memory usage
- **Shell**: Access terminal for debugging

### Vercel Dashboard
- **Deployments**: See all deployment history
- **Functions**: Monitor serverless function performance (not used in this app)
- **Analytics**: Track page views (requires upgrade)

---

## 🔄 Making Updates

### Backend Updates
1. Make changes to Python code
2. Commit and push to GitHub
3. Render auto-deploys (takes 2-5 minutes)

### Frontend Updates
1. Make changes to React code
2. Commit and push to GitHub  
3. Vercel auto-deploys (takes 1-2 minutes)

### Environment Variable Changes
- **Render**: Update in dashboard → Manual redeploy needed
- **Vercel**: Update in dashboard → Automatic redeploy

---

## 🎉 You're Done!

Your SpendSense app should now be live:
- **Backend API**: `https://your-backend.onrender.com`
- **Frontend App**: `https://spendsense.vercel.app`

Questions? Check the troubleshooting section or review the Render/Vercel docs.

