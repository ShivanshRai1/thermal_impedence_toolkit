# Deployment Guide - Thermal Impedance Toolkit

## Option 1: Vercel (Recommended - Free & Easy)

### Prerequisites
- GitHub account (free)
- Vercel account (free) - sign up at https://vercel.com

### Step 1: Push Code to GitHub

1. **Create a new repository on GitHub:**
   - Go to https://github.com/new
   - Name it: `thermal-impedance-toolkit`
   - Make it Public or Private
   - Click "Create repository"

2. **Push your code:**
   ```powershell
   cd "c:\Users\Dragon Byte\Downloads\thermal_impedance_toolkit_v9"
   
   # Initialize git (if not already)
   git init
   
   # Add all files
   git add .
   
   # Commit
   git commit -m "Initial commit - React + Flask thermal toolkit"
   
   # Add GitHub remote (replace YOUR_USERNAME)
   git remote add origin https://github.com/YOUR_USERNAME/thermal-impedance-toolkit.git
   
   # Push to GitHub
   git push -u origin main
   ```

### Step 2: Deploy Backend (Flask)

1. **Go to Vercel Dashboard:**
   - Visit https://vercel.com/dashboard
   - Click "Add New" → "Project"

2. **Import your GitHub repository**

3. **Configure Backend:**
   - Root Directory: `./` (leave as root)
   - Framework Preset: `Other`
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
   
4. **Add Environment Variables:**
   - No environment variables needed for basic setup

5. **Click "Deploy"**

6. **Copy the backend URL:**
   - After deployment, you'll get a URL like: `https://thermal-impedance-toolkit.vercel.app`
   - **Save this URL!**

### Step 3: Deploy Frontend (React)

1. **Update frontend environment variable:**
   ```powershell
   cd frontend
   ```
   
   Edit `.env.production` and replace with your backend URL:
   ```
   VITE_API_URL=https://YOUR-BACKEND-URL.vercel.app
   ```

2. **Go to Vercel Dashboard again:**
   - Click "Add New" → "Project"
   - Import the **same** GitHub repository

3. **Configure Frontend:**
   - Root Directory: `frontend`
   - Framework Preset: `Vite`
   - Build Command: `npm run build`
   - Output Directory: `dist`

4. **Click "Deploy"**

5. **Get your frontend URL:**
   - You'll get a URL like: `https://thermal-impedance-frontend.vercel.app`
   - **This is the link you send to your colleague!**

---

## Option 2: Netlify (Alternative - Also Free)

### Backend: Use Railway or Render

**Railway (Easier for Python):**
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect Flask and deploy
6. Copy the generated URL

**Frontend: Netlify**
1. Go to https://netlify.com
2. Sign up and click "Add new site" → "Import from Git"
3. Select your repository
4. Base directory: `frontend`
5. Build command: `npm run build`
6. Publish directory: `frontend/dist`
7. Add environment variable: `VITE_API_URL` = your Railway backend URL
8. Deploy!

---

## Option 3: Single Platform - Render (Simplest for Beginners)

1. **Go to https://render.com** (free tier available)
2. **Sign up with GitHub**

### Deploy Backend:
1. Click "New" → "Web Service"
2. Connect your GitHub repo
3. Settings:
   - Name: `thermal-toolkit-backend`
   - Root Directory: `.`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Add `gunicorn` to your requirements.txt first:
   ```powershell
   cd "c:\Users\Dragon Byte\Downloads\thermal_impedance_toolkit_v9"
   echo "gunicorn" >> requirements.txt
   git add requirements.txt
   git commit -m "Add gunicorn"
   git push
   ```
5. Click "Create Web Service"
6. **Copy the URL** (e.g., `https://thermal-toolkit-backend.onrender.com`)

### Deploy Frontend:
1. Click "New" → "Static Site"
2. Connect your GitHub repo
3. Settings:
   - Name: `thermal-toolkit-frontend`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Publish Directory: `frontend/dist`
4. Environment Variables:
   - Key: `VITE_API_URL`
   - Value: `https://thermal-toolkit-backend.onrender.com` (your backend URL)
5. Click "Create Static Site"
6. **Copy the frontend URL** - send this to your colleague!

---

## Quick Deployment Comparison

| Platform | Difficulty | Cost | Speed | Best For |
|----------|-----------|------|-------|----------|
| **Vercel** | Easy | Free | Fast | React apps |
| **Netlify + Railway** | Medium | Free | Fast | Split frontend/backend |
| **Render** | Easiest | Free* | Slower | All-in-one solution |

*Free tier has cold starts (15-30 second delay on first load)

---

## After Deployment

### Send to Your Colleague:

**Email/Message Template:**
```
Hi,

I've deployed the Thermal Impedance Toolkit web app. You can access it here:

🔗 https://your-frontend-url.vercel.app

How to use:
1. Upload your CSV file (must have columns: tp, Zth)
2. Click "Fit Foster" to generate the RC model
3. Switch tabs to convert to Cauer or predict sibling packages

The app runs entirely in the browser - no installation needed!

Let me know if you have any issues.
```

---

## Troubleshooting

### Backend deployment fails
- Check that `requirements.txt` includes all dependencies
- For Render, make sure `gunicorn` is in requirements.txt
- Check build logs in the platform dashboard

### Frontend can't reach backend
- Verify `.env.production` has the correct backend URL
- Check CORS settings in Flask (already configured with flask-cors)
- Open browser console (F12) to see error messages

### "Module not found" errors
- Make sure `package.json` includes all dependencies
- Try rebuilding: clear cache and redeploy

---

## Recommendation

**For you (beginner):** Use **Render** - it's the simplest all-in-one solution.

**Steps:**
1. Create GitHub repo and push code
2. Deploy backend on Render (Web Service)
3. Deploy frontend on Render (Static Site)
4. Send the frontend URL to your colleague

Total time: ~15 minutes

Need help with any specific step?
