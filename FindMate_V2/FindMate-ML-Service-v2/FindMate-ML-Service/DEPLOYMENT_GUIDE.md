# 🚀 ML Service Deployment Guide

Complete guide to deploy FindMate ML Service to production.

## 📋 Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account (same database as main app)
- Render or Heroku account for deployment
- Git installed

## 🎯 Deployment Options

### Option 1: Deploy to Render (Recommended)

#### Step 1: Prepare Repository

```bash
cd FindMate-ML-Service

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial ML service deployment"

# Push to GitHub
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

#### Step 2: Create Render Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure service:
   - **Name:** `findmate-ml-service`
   - **Environment:** `Python 3`
   - **Region:** Choose closest to your users
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** Leave empty (uses Procfile)

#### Step 3: Add Environment Variables

In Render dashboard, add these environment variables:

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/findmate
ML_SERVICE_API_KEY=your-secure-random-api-key-here
ML_MATCHING_THRESHOLD=0.65
FLASK_ENV=production
```

**IMPORTANT:** The `ML_SERVICE_API_KEY` must match exactly with the key in your main FindMate application!

#### Step 4: Deploy

Click **"Create Web Service"**

Render will:
- Install dependencies
- Start the service
- Provide you with a URL like: `https://findmate-ml-service.onrender.com`

#### Step 5: Test Deployment

```bash
# Test health check
curl https://findmate-ml-service.onrender.com/health

# Should return:
# {"status": "healthy", "service": "FindMate ML Service", "version": "1.0.0"}
```

#### Step 6: Update Main Application

Update your main FindMate application's `.env`:

```env
ML_ENABLED=true
ML_SERVICE_URL=https://findmate-ml-service.onrender.com
ML_SERVICE_API_KEY=your-matching-api-key
```

Restart your main application.

---

### Option 2: Deploy to Heroku

#### Step 1: Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

#### Step 2: Login and Create App

```bash
heroku login
heroku create findmate-ml-service
```

#### Step 3: Add Python Buildpack

```bash
heroku buildpacks:set heroku/python
```

#### Step 4: Set Environment Variables

```bash
heroku config:set MONGODB_URI="your-mongodb-uri"
heroku config:set ML_SERVICE_API_KEY="your-api-key"
heroku config:set ML_MATCHING_THRESHOLD=0.65
heroku config:set FLASK_ENV=production
```

#### Step 5: Deploy

```bash
git push heroku main
```

#### Step 6: Check Status

```bash
# View logs
heroku logs --tail

# Open in browser
heroku open
```

#### Step 7: Test

```bash
heroku run python test_service.py
```

---

### Option 3: Deploy to Railway

#### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
```

#### Step 2: Login and Deploy

```bash
railway login
railway init
railway up
```

#### Step 3: Add Environment Variables

In Railway dashboard:
- Go to your project
- Click "Variables"
- Add all required environment variables

---

## 🧪 Testing Deployed Service

### Test with curl

```bash
# Replace with your actual service URL and API key
SERVICE_URL="https://findmate-ml-service.onrender.com"
API_KEY="your-api-key"

# Health check
curl $SERVICE_URL/health

# Test matching
curl -X POST $SERVICE_URL/match/lost-to-found \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "itemId": "test123",
    "itemName": "Blue iPhone",
    "category": "electronics",
    "description": "Blue iPhone 13 with case",
    "location": "Library",
    "date": "2024-02-15"
  }'
```

### Test with Python Script

Run the included test script:

```bash
# Install requests library
pip install requests python-dotenv

# Create .env file
echo "ML_SERVICE_URL=https://findmate-ml-service.onrender.com" > .env
echo "ML_SERVICE_API_KEY=your-api-key" >> .env

# Run tests
python test_service.py
```

Expected output:
```
✅ PASS - Health Check
✅ PASS - Match Lost to Found
✅ PASS - Match Found to Lost
✅ PASS - Invalid API Key
✅ PASS - Missing Required Fields

5/5 tests passed

🎉 All tests passed! Service is working correctly.
```

---

## 🔧 Post-Deployment Configuration

### 1. Update Main Application

In your main FindMate app, update `.env`:

```env
ML_ENABLED=true
ML_SERVICE_URL=https://your-ml-service-url.com
ML_SERVICE_API_KEY=your-matching-api-key
```

### 2. Restart Main Application

```bash
# If on Render
# Go to dashboard → Click "Manual Deploy" → "Deploy latest commit"

# If on Heroku
heroku restart -a findmate

# If local
npm restart
```

### 3. Verify Integration

1. Login to main app as user
2. Report a lost item
3. Check console logs: Should see `[ML] Searching matches for...`
4. Login as admin
5. Go to `/admin/matches`
6. Should see empty state (no matches yet) or actual matches if items match

---

## 📊 Monitoring

### Check Service Health

```bash
# Render
# Dashboard → Service → Logs

# Heroku
heroku logs --tail -a findmate-ml-service

# Check status
curl https://your-service-url/health
```

### Monitor Performance

**Render:**
- Dashboard → Metrics
- View CPU, Memory, Request rate

**Heroku:**
```bash
heroku ps -a findmate-ml-service
heroku logs --tail -a findmate-ml-service
```

---

## 🐛 Troubleshooting

### Service Won't Start

**Check logs:**
```bash
# Render: Dashboard → Logs
# Heroku: heroku logs --tail
```

**Common issues:**
- Missing environment variables
- Invalid MongoDB connection string
- Python version mismatch

### Database Connection Errors

```
Error: Failed to connect to MongoDB
```

**Solution:**
1. Verify `MONGODB_URI` is correct
2. Check MongoDB Atlas whitelist (add `0.0.0.0/0` for testing)
3. Ensure database user has read permissions

### API Key Authentication Fails

```
{"error": "Invalid API key"}
```

**Solution:**
1. Verify `ML_SERVICE_API_KEY` matches in both services
2. Check for typos or extra spaces
3. Ensure `.env` is loaded correctly

### No Matches Found

**Solution:**
1. Check MongoDB has active items
2. Lower threshold: `ML_MATCHING_THRESHOLD=0.50`
3. Verify item data is complete
4. Check logs for matching process

### Timeout Errors

**Solution:**
1. Increase worker timeout in Procfile:
   ```
   web: gunicorn app:app --timeout 300
   ```
2. Add more workers if needed:
   ```
   web: gunicorn app:app --workers 4
   ```

---

## 🔐 Security Checklist

- [ ] Strong API key (32+ characters, random)
- [ ] API key matches between services
- [ ] MongoDB connection string secured
- [ ] CORS configured for production
- [ ] Environment variables not in code
- [ ] `.env` in `.gitignore`
- [ ] HTTPS enabled (automatic on Render/Heroku)

---

## 📈 Performance Optimization

### Scaling on Render

1. Go to Dashboard → Service
2. Click "Settings"
3. Under "Instance Type", upgrade if needed
4. Enable Auto-scaling (paid plans)

### Scaling on Heroku

```bash
# Scale dynos
heroku ps:scale web=2 -a findmate-ml-service

# Upgrade dyno type
heroku ps:resize web=standard-1x
```

---

## 🔄 Updates and Maintenance

### Deploy Updates

```bash
# Make changes
git add .
git commit -m "Update matching algorithm"
git push origin main

# Render: Auto-deploys on push
# Heroku: git push heroku main
```

### Rollback if Needed

**Render:**
- Dashboard → Deploys → Click on previous deploy → "Redeploy"

**Heroku:**
```bash
heroku rollback -a findmate-ml-service
```

---

## ✅ Deployment Checklist

Before going live:

- [ ] Service deployed and accessible
- [ ] Health check returns 200
- [ ] Test script passes all tests
- [ ] MongoDB connection working
- [ ] API key authentication working
- [ ] Main app configured with service URL
- [ ] Main app restarted
- [ ] Test end-to-end: Report item → Check admin matches
- [ ] Monitor logs for errors
- [ ] Set up monitoring/alerts

---

## 🎉 Success!

Your ML service is now deployed and ready to match items!

**What happens now:**
1. Users report lost/found items
2. ML service automatically matches them
3. Admin receives notifications
4. Admin reviews matches at `/admin/matches`
5. Admin verifies and connects users

---

## 📞 Need Help?

- Check service logs first
- Review this guide
- Test with `test_service.py`
- Verify environment variables
- Check MongoDB Atlas dashboard

**Common URLs:**
- Service: `https://your-service.onrender.com`
- Health: `https://your-service.onrender.com/health`
- Logs: Render/Heroku Dashboard
