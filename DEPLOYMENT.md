# 🚀 ChatBot Deployment Guide

Complete guide to deploy your ChatBot to various cloud platforms.

## 📋 Prerequisites

1. **GitHub Account** - Your code is already on GitHub
2. **Groq API Key** - Get yours at [console.groq.com](https://console.groq.com)
3. **Platform Account** - Choose one: Vercel, Heroku, Railway, Render, or PythonAnywhere

---

## 🟢 Option 1: Deploy to Vercel (Recommended - FREE)

**Best for:** Quick deployment, automatic HTTPS, global CDN

### Steps:

1. **Go to [vercel.com](https://vercel.com)**
2. **Sign in with GitHub**
3. **Click "Add New Project"**
4. **Import your repository:** `vc74/Chatbot`
5. **Configure Environment Variables:**
   - Click "Environment Variables"
   - Add: `GROQ_API_KEY` = `your_groq_api_key_here`
   - Add: `SECRET_KEY` = `your-secret-key-here`
   - Add: `DATABASE_URL` = `chatbot.db`
6. **Click "Deploy"**
7. **Wait 2-3 minutes** - Your app will be live!

### Your URL will be:
- `https://chatbot-[random].vercel.app`
- You can add a custom domain later

### Note:
- Vercel uses serverless functions
- Database will be ephemeral (resets on deployment)
- For persistent database, use external service like:
  - Supabase (free PostgreSQL)
  - MongoDB Atlas (free MongoDB)
  - PlanetScale (free MySQL)

---

## 🟣 Option 2: Deploy to Heroku (FREE Tier Available)

**Best for:** Traditional hosting, persistent database

### Steps:

1. **Install Heroku CLI:**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku:**
   ```bash
   heroku login
   ```

3. **Create Heroku App:**
   ```bash
   heroku create your-chatbot-name
   ```

4. **Set Environment Variables:**
   ```bash
   heroku config:set GROQ_API_KEY=your_groq_api_key_here
   heroku config:set SECRET_KEY=your-secret-key-here
   heroku config:set DATABASE_URL=chatbot.db
   ```

5. **Deploy:**
   ```bash
   git push heroku main
   ```

6. **Open your app:**
   ```bash
   heroku open
   ```

### Your URL will be:
- `https://your-chatbot-name.herokuapp.com`

---

## 🔵 Option 3: Deploy to Railway (FREE)

**Best for:** Easy setup, persistent storage

### Steps:

1. **Go to [railway.app](https://railway.app)**
2. **Sign in with GitHub**
3. **Click "New Project"**
4. **Choose "Deploy from GitHub repo"**
5. **Select your repository: `vc74/Chatbot`**
6. **Add Environment Variables:**
   - `GROQ_API_KEY` = `your_groq_api_key_here`
   - `SECRET_KEY` = `your-secret-key`
   - `PORT` = `8080` (Railway default)
7. **Click "Deploy"**

### Your URL will be:
- Automatically generated
- Can add custom domain

---

## 🟠 Option 4: Deploy to Render (FREE)

**Best for:** Full control, persistent database

### Steps:

1. **Go to [render.com](https://render.com)**
2. **Sign in with GitHub**
3. **Click "New +"** → **"Web Service"**
4. **Connect your repository: `vc74/Chatbot`**
5. **Configure:**
   - **Name:** your-chatbot
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn server:app`
6. **Add Environment Variables:**
   - `GROQ_API_KEY` = `your_groq_api_key_here`
   - `SECRET_KEY` = `your-secret-key`
7. **Click "Create Web Service"**

### Your URL will be:
- `https://your-chatbot.onrender.com`

---

## 🔴 Option 5: Deploy to PythonAnywhere (FREE)

**Best for:** Python-specific hosting, persistent files

### Steps:

1. **Go to [pythonanywhere.com](https://www.pythonanywhere.com)**
2. **Create free account**
3. **Go to "Web" tab**
4. **Click "Add a new web app"**
5. **Choose "Flask"**
6. **Upload your code:**
   - Use Git: `git clone https://github.com/vc74/Chatbot.git`
7. **Configure WSGI file:**
   - Point to your `wsgi.py` file
8. **Set environment variables in WSGI file:**
   ```python
   import os
   os.environ['GROQ_API_KEY'] = 'your_groq_api_key_here'
   ```
9. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
10. **Reload web app**

### Your URL will be:
- `https://yourusername.pythonanywhere.com`

---

## 📊 Comparison Table

| Platform | Free Tier | Database | Custom Domain | Difficulty |
|----------|-----------|----------|---------------|------------|
| **Vercel** | ✅ Yes | Ephemeral | ✅ Yes | ⭐ Easy |
| **Heroku** | ✅ Yes | Persistent | ✅ Yes | ⭐⭐ Medium |
| **Railway** | ✅ Yes | Persistent | ✅ Yes | ⭐ Easy |
| **Render** | ✅ Yes | Persistent | ✅ Yes | ⭐⭐ Medium |
| **PythonAnywhere** | ✅ Yes | Persistent | ❌ No (paid) | ⭐⭐⭐ Hard |

---

## 🔐 Environment Variables

All platforms need these variables:

```env
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your-secret-key-change-this
DATABASE_URL=chatbot.db
DEBUG=False
PORT=8080
```

**⚠️ IMPORTANT:** Never commit `.env` file to GitHub!

---

## 🗄️ Database Options for Production

### Option 1: Supabase (Recommended for Vercel)
1. Go to [supabase.com](https://supabase.com)
2. Create free project
3. Get PostgreSQL connection string
4. Update `DATABASE_URL` environment variable

### Option 2: MongoDB Atlas
1. Go to [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Create free cluster
3. Get connection string
4. Update code to use MongoDB instead of SQLite

### Option 3: PlanetScale (MySQL)
1. Go to [planetscale.com](https://planetscale.com)
2. Create free database
3. Get connection string
4. Update database configuration

---

## 🚨 Common Issues & Solutions

### Issue 1: "Module not found"
**Solution:** Ensure all dependencies are in `requirements.txt`

### Issue 2: "GROQ_API_KEY not found"
**Solution:** Double-check environment variables are set correctly

### Issue 3: "Database locked" or "Permission denied"
**Solution:** 
- Use external database (Supabase, MongoDB Atlas)
- Or ensure write permissions in deployment

### Issue 4: "Port already in use"
**Solution:** Platform assigns port automatically, use `PORT` env variable

### Issue 5: "Cold start / Slow first request"
**Solution:** This is normal for free tiers, add a health check endpoint

---

## ✅ Post-Deployment Checklist

- [ ] Test homepage loads: `https://your-app.com`
- [ ] Test chat works: `https://your-app.com/chat`
- [ ] Test authentication: `https://your-app.com/auth`
- [ ] Test voice features (may need HTTPS)
- [ ] Check logs for errors
- [ ] Verify environment variables are set
- [ ] Test on mobile devices
- [ ] Set up custom domain (optional)
- [ ] Enable automatic deployments from GitHub
- [ ] Monitor usage and performance

---

## 🎯 Recommended: Quick Deploy to Vercel

**Fastest method (5 minutes):**

1. Visit: https://vercel.com/new
2. Import: `vc74/Chatbot`
3. Add env var: `GROQ_API_KEY`
4. Click Deploy
5. Done! ✅

---

## 📞 Support

If deployment fails:
1. Check deployment logs
2. Verify all environment variables
3. Ensure `requirements.txt` is complete
4. Test locally first: `python server.py`
5. Check platform status pages

---

## 🌐 After Deployment

Your ChatBot will be accessible at:
- Homepage: `https://your-app.com/`
- Chat: `https://your-app.com/chat`
- Auth: `https://your-app.com/auth`
- Analytics: `https://your-app.com/analytics`

**Share your deployed app URL and start chatting!** 🚀
