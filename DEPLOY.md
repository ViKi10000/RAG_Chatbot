# Deploying RAG Chatbot to Render

## Quick Deploy (One-Click)

1. Push your repo to GitHub
2. Go to https://render.com → Dashboard → New → Web Service
3. Connect your GitHub repository
4. **Use the `render.yaml` file** (Render will auto-detect it)
5. Render will deploy both backend and frontend automatically

---

## Manual Deploy (Two Services)

### Backend Service

1. Create a new **Web Service** on Render
2. Choose **Python** as the runtime
3. Fill in:
   - **Name:** `rag-chatbot-backend`
   - **Runtime:** Python 3.11
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   - `GROQ_API_KEY` = your Groq API key
5. Click **Deploy**
6. Copy the backend URL (e.g., `https://rag-chatbot-backend.onrender.com`)

### Frontend Service

1. Create a new **Web Service** on Render
2. Choose **Node** as the runtime
3. Fill in:
   - **Name:** `rag-chatbot-frontend`
   - **Runtime:** Node 18+
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Start Command:** `npm run preview -- --host 0.0.0.0`
4. Add environment variables:
   - `VITE_API_URL` = paste the backend URL from step 1 (e.g., `https://rag-chatbot-backend.onrender.com`)
5. Click **Deploy**

---

## Verification

- **Frontend:** https://rag-chatbot-frontend.onrender.com
- **Backend API Docs:** https://rag-chatbot-backend.onrender.com/docs
- **Health Check:** https://rag-chatbot-backend.onrender.com/health

---

## Environment Variables

Both `.env.example` files are in the repo. Fill them in locally before pushing to GitHub.

- **Backend:** `.env` with `GROQ_API_KEY`
- **Frontend:** `.env` with `VITE_API_URL` (only used if different from default)

---

## Troubleshooting

### Frontend shows 404 or blank page

- Ensure `VITE_API_URL` env var is set correctly in Render frontend service
- Check browser console for API fetch errors
- Verify backend is running and accessible

### Backend fails to start

- Check that `GROQ_API_KEY` is set in Render backend service
- Ensure Python version is 3.11+ (`pythonVersion: 3.11` in render.yaml)
- View logs in Render dashboard → Service → Logs tab

### Slow cold start

- Render free tier has cold starts — backend may take 30–60s to spin up
- Use paid tier for faster response times

---

## Local Test Before Deploy

```powershell
# Backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend
npm run build
npm run preview -- --host 127.0.0.1 --port 3000
```

---

Done — your RAG Chatbot is now deployment-ready!
