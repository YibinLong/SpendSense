# 🚀 SpendSense Deployment Checklist (100% FREE)

Use this checklist to deploy SpendSense step-by-step. Check off each item as you complete it.

**No credit card needed! Both platforms have generous free tiers.**

---

## Pre-Deployment (Already Done ✅)

- [x] Created `frontend/vercel.json` configuration  
- [x] Updated CORS in `spendsense/app/main.py`
- [x] Verified `.gitignore` excludes `.env` files

---

## Part A: Deploy Backend to Render (FREE Tier)

- [ ] **Step 1**: Commit and push code to GitHub
  ```bash
  git add .
  git commit -m "Add deployment configurations"
  git push origin main
  ```

- [ ] **Step 2**: Sign up/login to [render.com](https://render.com) (no credit card!)

- [ ] **Step 3**: Create new **Web Service** (NOT Blueprint)
  - Click "New +" → "Web Service"
  - Connect GitHub repository

- [ ] **Step 4**: Fill in configuration:
  - [ ] Name: `spendsense-backend`
  - [ ] Runtime: **Python 3**
  - [ ] Build Command: `pip install -r requirements.txt`
  - [ ] Start Command: `uvicorn spendsense.app.main:app --host 0.0.0.0 --port $PORT`
  - [ ] Instance Type: **Free** ⭐

- [ ] **Step 5**: Add Environment Variables (one by one):
  - [ ] `APP_ENV` = `prod`
  - [ ] `SEED` = `42`
  - [ ] `DATABASE_URL` = `sqlite:///./data/spendsense.db`
  - [ ] `DATA_DIR` = `./data`
  - [ ] `PARQUET_DIR` = `./data/parquet`
  - [ ] `LOG_LEVEL` = `WARNING`
  - [ ] `DEBUG` = `false`
  - [ ] `JWT_SECRET_KEY` = `[32+ random characters - create your own!]`
  - [ ] `JWT_ALGORITHM` = `HS256`
  - [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` = `1440`
  - [ ] `FRONTEND_PORT` = `5173`

- [ ] **Step 6**: Click "Create Web Service" and wait (5-10 minutes)

- [ ] **Step 7**: Copy backend URL
  - Format: `https://spendsense-backend-xxxx.onrender.com`
  - Write it here: ___________________________________

- [ ] **Step 8**: Test backend health
  ```bash
  curl https://YOUR-BACKEND-URL/health
  ```
  Should return: `{"status":"healthy","app":"SpendSense","environment":"prod"}`

- [ ] **Step 9**: Initialize database
  - Go to Render dashboard → Your service → "Shell" tab
  - Run: `python -m scripts.reset_and_populate`
  - Wait for completion

---

## Part B: Deploy Frontend to Vercel (FREE Tier)

- [ ] **Step 10**: Create `frontend/.env.production` locally
  ```bash
  # Add this content:
  VITE_API_BASE=https://YOUR-BACKEND-URL-FROM-STEP-7
  ```
  **Do NOT commit this file!**

- [ ] **Step 11**: Sign up/login to [vercel.com](https://vercel.com) (no credit card!)

- [ ] **Step 12**: Import project
  - Click "Add New..." → "Project"
  - Select GitHub repository
  - Click "Import"

- [ ] **Step 13**: Configure project settings:
  - [ ] Framework Preset: **Vite** (auto-detected)
  - [ ] Root Directory: Click "Edit" → Set to `frontend` → Click "Continue"
  - [ ] Build Command: `npm run build` (auto-filled)
  - [ ] Output Directory: `dist` (auto-filled)

- [ ] **Step 14**: Add environment variable
  - Expand "Environment Variables" section
  - Name: `VITE_API_BASE`
  - Value: `https://YOUR-BACKEND-URL-FROM-STEP-7`
  - Environment: Check all (Production, Preview, Development)

- [ ] **Step 15**: Click "Deploy" and wait (2-5 minutes)

- [ ] **Step 16**: Copy frontend URL
  - Format: `https://spendsense-xxxx.vercel.app`
  - Write it here: ___________________________________

---

## Post-Deployment Testing

- [ ] **Step 17**: Test the application
  - [ ] Visit your Vercel URL
  - [ ] Open browser DevTools (F12) → Console
  - [ ] Try logging in with: `user_001@example.com` / `password123`
  - [ ] Check for errors in console

- [ ] **Step 18**: Verify everything works
  - [ ] Login page loads
  - [ ] Can log in successfully
  - [ ] Dashboard shows data
  - [ ] No CORS errors in console
  - [ ] No network errors

---

## Optional: Update CORS (only if needed)

- [ ] **Step 19**: If your Vercel URL is NOT `https://spendsense.vercel.app`:
  - [ ] Open `spendsense/app/main.py`
  - [ ] Find line 85: `"https://spendsense.vercel.app"`
  - [ ] Replace with your ACTUAL Vercel URL
  - [ ] Commit and push:
    ```bash
    git add spendsense/app/main.py
    git commit -m "Update CORS with production URL"
    git push origin main
    ```
  - [ ] Wait for Render to auto-redeploy (~3 minutes)

---

## 📋 URLs Reference

After deployment, fill in your URLs:

| Service | URL | Status |
|---------|-----|--------|
| Backend API | https://________________________ | [ ] Working |
| Frontend App | https://________________________ | [ ] Working |
| Backend Health | https://________________________/health | [ ] Returns healthy |
| Backend Docs | https://________________________/docs | [ ] Accessible |

---

## 🎉 Success Criteria

Your deployment is successful when:

1. ✅ Backend health check returns `{"status":"healthy","app":"SpendSense","environment":"prod"}`
2. ✅ Frontend loads without errors
3. ✅ You can log in with test credentials
4. ✅ Dashboard displays user data
5. ✅ No CORS or network errors in browser console

---

## ⚠️ Common Issues

If something doesn't work:

| Issue | Fix | Done? |
|-------|-----|-------|
| CORS error | Update backend CORS with your Vercel URL (Step 19) | [ ] |
| Can't login | Database empty - rerun Step 9 | [ ] |
| Network error | Check `VITE_API_BASE` in Vercel dashboard | [ ] |
| 500 errors | Check Render logs in dashboard | [ ] |
| Slow backend | Cold start (normal on free tier after 15 min idle) | [ ] |

---

## 🎯 Free Tier Reminders

**Render Free Tier:**
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ Database resets when service spins down
- ⚠️ First request after spin-down takes 30-60 seconds
- ✅ 750 hours/month (plenty for demos)

**Vercel Free Tier:**
- ✅ No limitations for this use case
- ✅ Fast, global CDN
- ✅ Auto-deploys from GitHub

---

## 📚 Full Documentation

For detailed explanations, see `DEPLOYMENT_GUIDE.md`

---

## 🔑 Test Credentials

After deployment, use these to log in:

- **Regular User**: `user_001@example.com` / `password123`
- **Operator**: `operator@spendsense.com` / `operator123`

(Created by `scripts/reset_and_populate.py` in Step 9)
