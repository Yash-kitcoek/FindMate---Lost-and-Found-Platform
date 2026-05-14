# FindMate - ML-Enhanced Lost & Found System

A full-stack lost and found web application with **AI-powered matching** built with Node.js, Express, MongoDB, and EJS. Features intelligent item matching using machine learning to automatically connect lost and found items.

## 🆕 What's New in ML-Enhanced Version

### ✨ New Features

1. **AI-Powered Matching**
   - Automatic matching between lost and found items
   - Confidence scoring based on multiple factors
   - Smart algorithms considering category, description, location, and date

2. **Admin ML Dashboard**
   - Review pending ML matches
   - Side-by-side item comparison
   - Verify or reject matches
   - Initiate contact between users

3. **Enhanced Item Tracking**
   - Match status tracking for all items
   - Confidence scores for verified matches
   - Complete audit trail of admin actions

4. **Automated Notifications**
   - Email alerts for high-confidence matches
   - User contact initiation emails
   - Admin notification system

## 🚀 Quick Start

```bash
cd FindMate-ML-Enhanced
npm install
cp .env.example .env
# Edit .env with your configuration
npm run dev
```

Access at: `http://localhost:3000`

## 📋 Key Features

- ✅ User authentication with email verification
- ✅ Report lost items (public)
- ✅ Report found items (admin-only)
- ✅ **⭐ AI-powered item matching**
- ✅ **⭐ Admin match review dashboard**
- ✅ Photo uploads via Cloudinary
- ✅ Email notifications
- ✅ Mobile-responsive design

## 🔧 ML Service Status

Currently: **ML Service Disabled** (`ML_ENABLED=false`)

The application works perfectly without ML:
- Manual admin matching available
- All features functional
- No ML service required

To enable ML matching later:
1. Deploy ML service (separate Python/Flask app)
2. Set `ML_ENABLED=true` in `.env`
3. Configure `ML_SERVICE_URL` and `ML_SERVICE_API_KEY`

## 📂 Project Structure

```
FindMate-ML-Enhanced/
├── models/          # MongoDB schemas (ML-enhanced)
├── services/        # ⭐ NEW: ML & notification services
├── routes/          # Express routes + admin ML routes
├── views/           # EJS templates + admin ML views
├── public/          # Static assets
└── config/          # Cloudinary configuration
```

## 📊 Tech Stack

- **Backend:** Node.js, Express.js
- **Database:** MongoDB
- **Auth:** Passport.js
- **Email:** Nodemailer
- **Storage:** Cloudinary
- **Frontend:** EJS, Tailwind CSS
- **ML:** Python/Flask (separate service, optional)

## 🔐 Admin Access

- Login: `/admin-login`
- Dashboard: `/admin-dashboard`
- ML Matches: `/admin/matches`

## 📧 Environment Variables

See `.env.example` for all required configuration.

Key variables:
- `DATABASE_URL` - MongoDB connection string
- `SESSION_SECRET` - Session encryption key
- `CLOUDINARY_*` - Image upload credentials
- `EMAIL_*` - SMTP configuration
- `ML_ENABLED` - Enable/disable ML matching
- `ML_SERVICE_URL` - ML service endpoint

## 🧪 Testing ML Features

### With ML Disabled (Current)
1. Create lost & found items
2. Use admin dashboard for manual matching
3. Works without ML service

### With ML Enabled (Future)
1. Items automatically matched on submission
2. Admin reviews matches at `/admin/matches`
3. High-confidence alerts sent to admin
4. Verify and contact users via dashboard

## 📦 Deployment

Ready to deploy to:
- Render
- Heroku
- Railway
- Vercel

Set all environment variables in your hosting platform.

## 🛣️ Roadmap

- ✅ ML matching integration
- ✅ Admin review workflow
- 🔄 Image similarity matching
- 🔄 SMS notifications
- 🔄 Mobile app
- 🔄 Advanced analytics

## 📄 License

MIT License

---

**Version:** 2.0.0-ML-Enhanced  
**Status:** Production Ready (ML Optional)
