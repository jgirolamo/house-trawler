# 🚀 Quick Deploy to Render - Step by Step

Since you're already logged into Render, follow these steps:

## Step 1: Prepare Your Code (if not on GitHub)

If your code isn't on GitHub yet:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Property Trawler"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy on Render

1. **Click "New +"** button (top right corner)
2. **Select "Web Service"**
3. **Connect Repository:**
   - If you see "Connect account", click it and authorize GitHub
   - Select your repository from the list
4. **Configure:**
   - **Name**: `property-trawler` (or any name you like)
   - **Region**: Choose closest to you
   - **Branch**: `main` (or `master`)
   - **Root Directory**: Leave blank
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
5. **Environment Variables** (click "Advanced"):
   - `FLASK_ENV` = `production`
   - `FLASK_DEBUG` = `False`
   - (PORT is set automatically by Render)
6. **Click "Create Web Service"**
7. **Wait 2-5 minutes** for build to complete
8. **Your app will be live!** 🎉

## Your App URL

Once deployed, your app will be at:
`https://property-trawler.onrender.com`

(Replace `property-trawler` with whatever name you chose)

## Troubleshooting

If build fails:
- Check the build logs in Render dashboard
- Make sure `requirements.txt` has all dependencies
- Verify `app.py` exists and is correct

If app doesn't start:
- Check start command is `python app.py`
- Verify PORT environment variable is being used (it is in app.py)

## Next Steps After Deployment

1. Test your app URL
2. Run a scrape: The scraper will need to run separately or you can add a button to trigger it
3. Share your URL with others!

---

**Note**: On free tier, app may take 30-60 seconds to wake up after inactivity.

