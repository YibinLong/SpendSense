# 🎯 What YOU Need to Do - Quick Summary

I've done all the code setup for you! Here's what **you** need to do manually on the Render and Vercel websites.

---

## ✅ What I Already Did

1. ✅ Created `render.yaml` - tells Render how to deploy your backend
2. ✅ Created `frontend/vercel.json` - tells Vercel how to deploy your frontend
3. ✅ Updated `spendsense/app/main.py` - added CORS for Vercel domains
4. ✅ Created deployment guides and checklists

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

### TASK 2: Deploy Backend on Render.com (10 minutes)

1. Go to **[render.com](https://render.com)** → Sign up/Login
2. Click **"New +"** button → Select **"Blueprint"**
3. **Connect GitHub** (if not already connected)
4. Find your **SpendSense** repository
5. Render detects `render.yaml` automatically
6. Click **"Apply"** or **"Create Resources"**
7. ⏰ Wait 5-10 minutes for deployment

**Result**: You'll get a URL like `https://spendsense-backend-xxxx.onrender.com`

**COPY THIS URL** - you need it for Task 4!

---

### TASK 3: Initialize the Database (2 minutes)

1. In Render dashboard, click your **spendsense-backend** service
2. Click **"Shell"** tab (left sidebar)
3. Wait for terminal to connect
4. Type this command:
   ```bash
   python reset_and_populate.py
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
3. Save the file (DO NOT commit it)

**Why**: Tells your frontend where to find the backend API.

---

### TASK 5: Deploy Frontend on Vercel.com (5 minutes)

1. Go to **[vercel.com](https://vercel.com)** → Sign up/Login
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. **IMPORTANT**: Click "Edit" and set **Root Directory** to: `frontend`
5. Framework should auto-detect as **"Vite"** ✅
6. Expand **"Environment Variables"** section
7. Add ONE variable:
   - **Key**: `VITE_API_BASE`
   - **Value**: `https://spendsense-backend-xxxx.onrender.com` (from Task 2)
   - **Environments**: Check all boxes
8. Click **"Deploy"**
9. ⏰ Wait 2-5 minutes

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
   - Try logging in
   - Check for errors

**If you see CORS errors**: Your Vercel URL might not match what I set. Proceed to Task 7.

---

### TASK 7: Update CORS (ONLY if needed - 2 minutes)

**Skip this if everything works!**

If your Vercel URL is NOT `https://spendsense.vercel.app`:

1. Open `spendsense/app/main.py`
2. Find line 85: `"https://spendsense.vercel.app"`
3. Replace with your ACTUAL Vercel URL
4. Save, commit, push:
   ```bash
   git add spendsense/app/main.py
   git commit -m "Update CORS with production URL"
   git push origin main
   ```
5. Render auto-redeploys in ~3 minutes

---

## 🎉 Done!

**Total time**: ~20-25 minutes

Your app will be live at:
- **Backend**: `https://your-backend.onrender.com`
- **Frontend**: `https://spendsense.vercel.app`

---

## 📚 Need More Help?

- **Step-by-step guide**: Open `DEPLOYMENT_GUIDE.md`
- **Checklist format**: Open `DEPLOYMENT_CHECKLIST.md`
- **Troubleshooting**: See bottom of `DEPLOYMENT_GUIDE.md`

---

## ⚠️ Important Notes

1. **Free Tier Limitations**:
   - Render: Database resets after 15 min inactivity
   - Render: First request after inactivity takes 30-60 seconds (cold start)
   
2. **Environment Variables**:
   - `.env.production` should NOT be committed (already in .gitignore)
   - Set `VITE_API_BASE` in Vercel dashboard instead

3. **Database**:
   - You created it in Task 3 with sample data
   - On free tier, it resets when backend spins down
   - For production, upgrade to paid plan or use PostgreSQL

