# AI Company Research Agent - Deployment Guide

## 🌐 Live Demo
[Add your deployed URL here after deployment]

## 📦 Deployment Instructions (Render)

### Prerequisites
- GitHub account
- Render account (free): https://render.com
- API Keys: Gemini, Tavily

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to https://render.com and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `ai-research-agent`
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`

5. Add Environment Variables:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `TAVILY_API_KEY`: Your Tavily API key

6. Click **"Create Web Service"**

### Step 3: Update Frontend API URL

After deployment, update `frontend/src/App.jsx`:
```javascript
// Change this line (around line 42):
const response = await fetch('http://localhost:8000/api/chat', {

// To your Render URL:
const response = await fetch('https://YOUR-APP-NAME.onrender.com/api/chat', {
```

Then push the update:
```bash
git add .
git commit -m "Update API URL"
git push
```

Render will auto-redeploy!

---

## 🏃‍♂️ Local Development

See main README.md for local setup instructions.

## 🎥 Demo Video
[Add YouTube/Loom link here]

## 📧 Contact
[Your email/GitHub]
