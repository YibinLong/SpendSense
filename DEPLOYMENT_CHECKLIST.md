# 🚀 SpendSense Deployment Checklist

Use this checklist to deploy SpendSense step-by-step. Check off each item as you complete it.

---

## Pre-Deployment (Already Done ✅)

- [x] Created `render.yaml` configuration
- [x] Created `frontend/vercel.json` configuration  
- [x] Updated CORS in `spendsense/app/main.py`
- [x] Verified `.gitignore` excludes `.env` files

---

## Part A: Deploy Backend to Render

- [ ] **Step 1**: Commit and push code to GitHub
  ```bash
  git add .
  git commit -m "Add deployment configurations"
  git push origin main
  ```

- [ ] **Step 2**: Sign up/login to [render.com](https://render.com)

- [ ] **Step 3**: Create new Blueprint
  - Click "New +" → "Blueprint"
  - Connect GitHub repository
  - Click "Apply" to deploy

- [ ] **Step 4**: Wait for deployment (5-10 minutes)

- [ ] **Step 5**: Copy backend URL
  - Format: `https://spendsense-backend-xxxx.onrender.com`
  - Write it here: ___________________________________

- [ ] **Step 6**: Test backend health
  ```bash
  curl https://YOUR-BACKEND-URL/health
  ```
  Should return: `{"status":"healthy","app":"SpendSense","environment":"prod"}`

- [ ] **Step 7**: Initialize database
  - Go to Render dashboard → Your service → "Shell" tab
  - Run: `python reset_and_populate.py`
  - Wait for completion

---

## Part B: Deploy Frontend to Vercel

- [ ] **Step 8**: Create `frontend/.env.production` locally
  ```bash
  # Add this content:
  VITE_API_BASE=https://YOUR-BACKEND-URL-FROM-STEP-5
  ```

- [ ] **Step 9**: Sign up/login to [vercel.com](https://vercel.com)

- [ ] **Step 10**: Import project
  - Click "Add New..." → "Project"
  - Select GitHub repository
  - Set Root Directory to: `frontend`
  - Framework should auto-detect as "Vite"

- [ ] **Step 11**: Add environment variable
  - Name: `VITE_API_BASE`
  - Value: `https://YOUR-BACKEND-URL-FROM-STEP-5`
  - Check all environments

- [ ] **Step 12**: Click "Deploy" and wait (2-5 minutes)

- [ ] **Step 13**: Copy frontend URL
  - Format: `https://spendsense.vercel.app`
  - Write it here: ___________________________________

---

## Post-Deployment

- [ ] **Step 14**: Update CORS if needed (only if your Vercel URL is different)
  - Edit `spendsense/app/main.py` line 85
  - Replace with your actual Vercel URL
  - Commit and push (Render auto-redeploys)

- [ ] **Step 15**: Test the application
  - Visit your Vercel URL
  - Open browser DevTools (F12) → Console
  - Try logging in
  - Check for errors

- [ ] **Step 16**: Verify everything works
  - [ ] Login page loads
  - [ ] Can log in successfully
  - [ ] Dashboard shows data
  - [ ] No CORS errors in console
  - [ ] No network errors

---

## 📋 URLs Reference

After deployment, fill in your URLs:

| Service | URL | Notes |
|---------|-----|-------|
| Backend | https://________________________ | Render backend API |
| Frontend | https://________________________ | Vercel frontend app |
| Backend Health | https://________________________/health | Test endpoint |
| Backend Docs | https://________________________/docs | API documentation |

---

## 🎉 Success Criteria

Your deployment is successful when:

1. ✅ Backend health check returns `{"status":"healthy"}`
2. ✅ Frontend loads without errors
3. ✅ You can log in with test credentials
4. ✅ Dashboard displays user data
5. ✅ No CORS or network errors in browser console

---

## ⚠️ Common Issues

If something doesn't work:

| Issue | Fix |
|-------|-----|
| CORS error | Update backend CORS with Vercel URL (Step 14) |
| Can't login | Database empty - rerun Step 7 |
| Network error | Check `VITE_API_BASE` in Vercel dashboard |
| 500 errors | Check Render logs in dashboard |

---

## 📚 Full Documentation

For detailed explanations, see `DEPLOYMENT_GUIDE.md`

