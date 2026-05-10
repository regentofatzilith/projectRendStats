# UW PermaCalc - Render.com Deployment Guide

## Step-by-Step Deployment to Render.com

### 1. Prepare Files

You need these files in a folder or GitHub repo:
- `perma_calc_new.py` (already updated with server object)
- `render_requirements.txt` (created - rename to `requirements.txt`)

### 2. Create GitHub Repository (Recommended)

**Option A: Using GitHub**
1. Go to https://github.com and create a new repository
2. Name it: `uw-permacalc` (or any name you prefer)
3. Make it Public or Private (both work with Render)
4. Upload these files:
   - Copy `pages/perma_calc_new.py` to root as `perma_calc_new.py`
   - Rename `render_requirements.txt` to `requirements.txt`
5. Commit the files

**Option B: Without GitHub**
You can upload files directly to Render (less convenient for updates).

### 3. Deploy on Render.com

1. **Login to Render**
   - Go to https://render.com
   - Sign in with your account

2. **Create New Web Service**
   - Click "New +" button
   - Select "Web Service"

3. **Connect Repository**
   - If using GitHub: Click "Connect account" and select your repo
   - If not using GitHub: Choose "Public Git repository" and enter URL, OR use "Deploy from folder" (less common)

4. **Configure Service**
   Fill in these settings:
   
   **Name:** `uw-permacalc` (or your choice - this becomes part of URL)
   
   **Region:** Choose closest to you
   
   **Branch:** `main` (or `master`)
   
   **Root Directory:** Leave blank (unless file is in subdirectory)
   
   **Runtime:** `Python 3`
   
   **Build Command:**
   ```
   pip install -r requirements.txt
   ```
   
   **Start Command:**
   ```
   gunicorn perma_calc_new:server
   ```
   
   **Instance Type:** `Free` (select Free tier)

5. **Environment Variables** (Optional)
   - None required for this app
   - You can add `PYTHON_VERSION=3.11` if you want to specify version

6. **Deploy**
   - Click "Create Web Service"
   - Render will start building (takes 2-5 minutes first time)
   - Watch the logs for any errors

### 4. Access Your App

Once deployed, you'll get a URL like:
```
https://uw-permacalc.onrender.com
```

Share this URL with anyone - they just click and use!

### 5. Important Notes

**Free Tier Limitations:**
- App "spins down" after 15 minutes of inactivity
- First visit after spin-down takes 30-60 seconds to wake up
- 750 hours/month free (plenty for personal use)
- Automatic HTTPS included

**Updating Your App:**
- With GitHub: Just push changes to repo, Render auto-deploys
- Without GitHub: Redeploy manually from Render dashboard

### Troubleshooting

**Build Fails:**
- Check that `requirements.txt` exists in root directory
- Verify file is named exactly `requirements.txt`
- Check logs for specific error

**App Won't Start:**
- Verify Start Command: `gunicorn perma_calc_new:server`
- Check that filename is `perma_calc_new.py` (no `pages/` prefix)
- Look at deployment logs for errors

**App Shows 502 Error:**
- App is still building, wait a minute
- Or app crashed - check logs

### Files Checklist

```
your-repo/
├── perma_calc_new.py          ← Must be in root directory
└── requirements.txt           ← Must be named exactly this
```

### Example Repository Structure

If using GitHub, your repo should look like:
```
https://github.com/yourusername/uw-permacalc/
├── perma_calc_new.py
├── requirements.txt
└── README.md (optional)
```

---

## Quick Start Commands

If you already have files ready:

1. **Create repo and upload files**
2. **On Render.com:**
   - New Web Service
   - Connect GitHub repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn perma_calc_new:server`
   - Click Deploy

Done! Your app will be live in 3-5 minutes.

---

## Alternative: Quick Manual Upload

If you want to avoid GitHub:

1. Create a new folder on your computer
2. Copy `perma_calc_new.py` to the folder
3. Rename `render_requirements.txt` to `requirements.txt`
4. Zip the folder
5. On Render, use "Deploy from folder" option
6. Upload the zip file

Note: Manual updates require re-uploading each time.
