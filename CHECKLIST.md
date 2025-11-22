# 📋 Deployment Checklist

## Before Deployment

- [x] Code is working locally
- [x] README.md is complete
- [x] requirements.txt is updated
- [x] .gitignore is configured
- [x] .env.example is created
- [ ] Demo video is recorded (10 min max)
- [ ] GitHub repository is created
- [ ] Repository is public

## Deployment Steps

### 1. Push to GitHub
```bash
cd "c:/Users/Valli/OneDrive/Desktop/EightFold AI"
git init
git add .
git commit -m "Initial commit: AI Company Research Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Deploy on Render
1. Go to https://render.com
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Select your repository
5. Configure:
   - Name: `ai-research-agent`
   - Environment: `Python 3`
   - Build Command: `./build.sh`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables:
   - `GEMINI_API_KEY`
   - `TAVILY_API_KEY`
7. Click "Create Web Service"
8. Wait for deployment (~5-10 minutes)

### 3. Update Frontend API URL
After deployment, edit `frontend/src/App.jsx`:
- Line 42: Change `http://localhost:8000` to your Render URL
- Commit and push

### 4. Test Deployed App
- Open your Render URL
- Test voice input
- Test research functionality
- Check sources display

### 5. Submit
1. Record demo video (show all 4 user personas)
2. Upload video to YouTube/Loom
3. Fill out submission form: https://forms.gle/EjyVS4cSXMt5ojE49
   - GitHub repo link
   - Demo video link
   - Deployed URL (Render)

## Deadline
**24th Nov 2025 - 02:00 pm**

## Notes
- Make sure repository is PUBLIC
- Include README with setup instructions
- Demo video should be max 10 minutes
- Show architecture and design decisions in video
