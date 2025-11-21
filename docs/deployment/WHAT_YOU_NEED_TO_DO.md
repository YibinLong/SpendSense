# 🎯 What YOU Need to Do - Quick Summary (100% FREE)

I've done all the code setup for you! Here's what **you** need to do manually on the Render and Vercel websites.

**All steps use FREE tiers - no credit card required!**

---

## ✅ What I Already Did

1. ✅ Created `frontend/vercel.json` - tells Vercel how to deploy your frontend
2. ✅ Updated `spendsense/app/main.py` - added CORS for Vercel domains
3. ✅ Created deployment guides and checklists

---

## 🚀 Your Tasks (In Order)

### TASK 1: Push to GitHub (1 minute)

```bash
cd /Users/yibin/Documents/WORKZONE/VSCODE/GAUNTLET_AI/4_Week/SpendSense
git add .
git commit -m "Add deployment configurations for Render and Vercel"
git push origin main
```

**Why**: Both platforms deploy from your GitHub repo.

---

### TASK 2: Deploy Backend on Render.com (10 minutes) - FREE

1. Go to **[render.com](https://render.com)** → Sign up/Login (no credit card needed)
2. Click **"New +"** button → Select **"Web Service"** (NOT Blueprint)
3. Click **"Connect GitHub"** (if not already connected)
4. Find and select your **SpendSense** repository
5. Configure the Web Service:

   **Fill in these fields:**
   
   | Field | Value |
   |-------|-------|
   | **Name** | `spendsense-backend` (or anything you want) |
   | **Region** | Choose closest to you (Oregon, Ohio, Frankfurt, Singapore) |
   | **Branch** | `main` |
   | **Root Directory** | Leave empty (entire repo) |
   | **Runtime** | **Python 3** |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn spendsense.app.main:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | **Free** ⭐ |

6. Scroll down to **"Environment Variables"** section
7. Click **"Add Environment Variable"** and add these **ONE BY ONE**:

   ```
   APP_ENV = prod
   SEED = 42
   DATABASE_URL = sqlite:///./data/spendsense.db
   DATA_DIR = ./data
   PARQUET_DIR = ./data/parquet
   LOG_LEVEL = WARNING
   DEBUG = false
   JWT_SECRET_KEY = your-super-secret-key-minimum-32-characters-long-please-change-this
   JWT_ALGORITHM = HS256
   ACCESS_TOKEN_EXPIRE_MINUTES = 1440
   FRONTEND_PORT = 5173
   ```

   **Important for JWT_SECRET_KEY**: Replace with any random string of at least 32 characters. Example:
   ```
   JWT_SECRET_KEY = 8a3f9b2e7c1d4a5e6f8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2
   ```

8. Click **"Create Web Service"** at the bottom
9. ⏰ Wait 5-10 minutes for deployment (watch the logs)

**Result**: You'll get a URL like `https://spendsense-backend-xxxx.onrender.com`

**COPY THIS URL** - you need it for Task 4!

---

### TASK 3: Initialize the Database (2 minutes)

1. In Render dashboard, click your **spendsense-backend** service
2. Click **"Shell"** tab (left sidebar)
3. Wait for terminal to connect (may take 30 seconds)
4. Type this command:
   ```bash
   python -m scripts.reset_and_populate
   ```
5. Press Enter and wait for it to finish

**Why**: Creates test users and sample data in the database.

---

### TASK 4: Create Environment File (1 minute)

Since `.env.production` is blocked from git, create it manually:

1. Create file: `frontend/.env.production`
2. Add this ONE line (replace with your actual URL from Task 2):
   ```
   VITE_API_BASE=https://spendsense-backend-xxxx.onrender.com
   ```
3. Save the file (DO NOT commit it - it's in .gitignore)

**Why**: Tells your frontend where to find the backend API.

---

### TASK 5: Deploy Frontend on Vercel.com (5 minutes) - FREE

1. Go to **[vercel.com](https://vercel.com)** → Sign up/Login (no credit card needed)
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Find your **SpendSense** repository and click **"Import"**
5. **IMPORTANT**: Configure these settings:

   | Field | Value |
   |-------|-------|
   | **Framework Preset** | Vite (should auto-detect) |
   | **Root Directory** | Click "Edit" → Set to `frontend` → Click "Continue" |
   | **Build Command** | `npm run build` (auto-filled) |
   | **Output Directory** | `dist` (auto-filled) |
   | **Install Command** | `npm install` (auto-filled) |

6. Expand **"Environment Variables"** section
7. Add ONE variable:
   - **Name**: `VITE_API_BASE`
   - **Value**: `https://spendsense-backend-xxxx.onrender.com` (from Task 2)
   - **Environment**: Select all (Production, Preview, Development)
8. Click **"Deploy"**
9. ⏰ Wait 2-5 minutes (watch the build logs)

**Result**: You'll get a URL like `https://spendsense.vercel.app`

---

### TASK 6: Test Everything (2 minutes)

1. **Test Backend**:
   ```bash
   curl https://your-backend-url.onrender.com/health
   ```
   Should see: `{"status":"healthy","app":"SpendSense","environment":"prod"}`

2. **Test Frontend**:
   - Visit your Vercel URL in browser
   - Press F12 to open DevTools → Console tab
   - Try logging in with these test credentials:
     - Email: `user_001@example.com`
     - Password: `password123`
   - Check for errors in console

**If you see CORS errors**: Your Vercel URL might not match what I set. Proceed to Task 7.

---

### TASK 7: Update CORS (ONLY if needed - 2 minutes)

**Skip this if everything works!**

If your Vercel URL is NOT `https://spendsense.vercel.app`:

1. Open `spendsense/app/main.py`
2. Find line 85: `"https://spendsense.vercel.app"`
3. Replace with your ACTUAL Vercel URL from Task 5
4. Save, commit, push:
   ```bash
   git add spendsense/app/main.py
   git commit -m "Update CORS with production URL"
   git push origin main
   ```
5. Render auto-redeploys in ~3 minutes (watch in Render dashboard)

---

## 🎉 Done!

**Total time**: ~20-25 minutes

Your app will be live at:
- **Backend**: `https://your-backend.onrender.com`
- **Frontend**: `https://spendsense.vercel.app`

Both are 100% FREE (no credit card required)!

---

## 📚 Need More Help?

- **Step-by-step guide**: Open `DEPLOYMENT_GUIDE.md`
- **Checklist format**: Open `DEPLOYMENT_CHECKLIST.md`
- **Troubleshooting**: See bottom of `DEPLOYMENT_GUIDE.md`

---

## ⚠️ Important Notes About FREE Tier

1. **Render Free Tier**:
   - ✅ 750 hours/month of runtime (plenty for demos)
   - ⚠️ Database resets after 15 min of inactivity
   - ⚠️ First request after inactivity takes 30-60 seconds (cold start)
   - ⚠️ Spins down after 15 minutes with no traffic
   
2. **Vercel Free Tier**:
   - ✅ Unlimited deployments
   - ✅ No cold starts
   - ✅ Global CDN
   - ✅ Perfect for this use case!

3. **Environment Variables**:
   - `.env.production` should NOT be committed (already in .gitignore)
   - Set `VITE_API_BASE` in Vercel dashboard (not in code)
   - Set all backend vars in Render dashboard (not in code)

4. **Database**:
   - You created it in Task 3 with sample data
   - On free tier, it **resets when backend spins down** (no traffic for 15 min)
   - To keep it running: Visit your backend URL every 10 minutes OR upgrade to paid

---

## 🔑 Test User Credentials

After deployment, log in with these users (created by `scripts/reset_and_populate.py`):

- **User 1**: `user_001@example.com` / `password123`
- **User 2**: `user_002@example.com` / `password123`
- **User 3**: `user_003@example.com` / `password123`
- **Operator**: `operator@spendsense.com` / `operator123`

All passwords are the same: `password123`
