# 🚀 AI Company Research Agent - Deployment Guide

## 🌍 Live Demo
🔗 https://company-account-planner-ai.onrender.com  
(If inactive for a while, Render will display "Waking Up..." — please wait a moment!)

---

## 📦 Deployment Instructions (Render)

### ✔ Prerequisites
- GitHub account with the project pushed
- Render account (Free): https://render.com
- API Keys required:
  - `GEMINI_API_KEY`
  - `TAVILY_API_KEY` 

---

### 🛠 Step 1 — Deploy Backend (FastAPI)

1️⃣ Go to Render  
2️⃣ Click **New + → Web Service**  
3️⃣ Connect your GitHub repository  
4️⃣ Configure settings:

| Setting | Value |
|--------|------|
| Name | ai-company-research-backend |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn server:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |

5️⃣ Add Environment Variables:

GEMINI_API_KEY = YOUR_KEY
TAVILY_API_KEY = YOUR_KEY 



Click **Deploy Web Service** 🎉

---

### 🎨 Step 2 — Deploy Frontend (React UI)

1️⃣ Click **New + → Static Site**  
2️⃣ Select the same GitHub repo  
3️⃣ Configure:

| Setting | Value |
|--------|------|
| Build Command | `npm install && npm run build` |
| Publish directory | `frontend/dist` |
| Instance | Free |

4️⃣ Update backend URL in:

📌 `frontend/src/App.jsx`
```js
const API_URL = "https://company-account-planner-ai.onrender.com//api/chat";
```

Then push changes:
```
git add .
git commit -m "Updated API URL for Render"
git push
```

Render will automatically rebuild 🔁

## 🧪 Local Development

## Backend:
```
pip install -r requirements.txt
uvicorn server:app --reload
```

## Frontend:
```
cd frontend
npm install
npm run dev
```

Open 👉 http://localhost:5173

## 🎥 Demo Video

📌 Uploaded to Google Drive
🔗 [https://drive.google.com/file/d/1io0Krqgh1MM0QlENgNqqd7iw5xChC70W/view?usp=sharing](https://drive.google.com/file/d/1io0Krqgh1MM0QlENgNqqd7iw5xChC70W/view?usp=sharing)

## 📧 Contact

Valli Viswa Varshini M
📩 Email: valliviswavarshini@gmail.com

GitHub: https://github.com/Valli-Viswa-Varshini
