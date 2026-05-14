# FindMate ML Service

AI-powered matching service for lost and found items. This microservice handles all machine learning operations for the FindMate application.

## 🎯 Features

- **Hybrid Matching Algorithm**
  - Category compatibility with related-category fallbacks
  - Description similarity using word TF-IDF, character TF-IDF, token overlap, and fuzzy matching
  - Item-name similarity for short reports
  - Attribute matching for color, brand, and model tokens
  - Location proximity with campus aliases and fuzzy matching
  - Date proximity with decay function

- **Intelligent Scoring**
  - Configurable confidence threshold
  - Configurable top-k result limit
  - Candidate prefiltering for faster ranking
  - Related category matching
  - Color/brand contradiction penalties
  - Exponential date decay
  - Campus-specific location groups

- **Production Ready**
  - Secure API key authentication
  - MongoDB integration
  - Comprehensive logging
  - Error handling

## 📂 Project Structure

```
FindMate-ML-Service/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── Procfile                    # Deployment configuration
├── .env.example               # Environment variables template
├── middleware/
│   └── auth.py                # API key authentication
├── services/
│   ├── matcher.py             # Core matching logic
│   └── db_service.py          # MongoDB operations
├── utils/
│   ├── text_similarity.py     # TF-IDF text matching
│   ├── location_matcher.py    # Fuzzy location matching
│   └── date_scorer.py         # Date proximity calculation
└── config/
    └── (future configuration files)
```

## 🚀 Quick Start

### Local Development

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run Service**
   ```bash
   python app.py
   ```

Service runs at: `http://localhost:5000`

## 🔧 Configuration

### Environment Variables

```env
# Flask Configuration
FLASK_ENV=production
PORT=5000

# MongoDB (same as main app)
MONGODB_URI=mongodb+srv://...

# API Security (must match main app)
ML_SERVICE_API_KEY=your-secure-key

# ML Settings
ML_MATCHING_THRESHOLD=0.65
ML_MAX_MATCHES=10
ML_PREFILTER_THRESHOLD=0.35
```

### Matching Weights

Configured in `services/matcher.py`:

```python
WEIGHTS = {
    'category': 0.18,
    'description': 0.28,
    'name': 0.13,
    'attributes': 0.14,
    'location': 0.16,
    'date': 0.11
}
```

## 📡 API Endpoints

### Health Check
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "FindMate ML Service",
  "version": "2.0.0",
  "algorithm": "hybrid-tfidf-fuzzy-attribute-ranker"
}
```

### Match Lost to Found
```
POST /match/lost-to-found
Headers: X-API-Key: your-api-key
Content-Type: application/json
```

Request:
```json
{
  "itemId": "507f1f77bcf86cd799439011",
  "itemName": "iPhone 13",
  "category": "electronics",
  "description": "Blue iPhone 13 with black case",
  "location": "Library",
  "date": "2024-02-15",
  "color": "blue",
  "brand": "Apple"
}
```

Response:
```json
{
  "matches": [
    {
      "matchedItemId": "507f1f77bcf86cd799439012",
      "confidenceScore": 0.892,
      "factors": {
        "categoryMatch": 1.0,
        "descriptionSimilarity": 0.85,
        "locationProximity": 1.0,
        "dateProximity": 0.97,
        "itemNameSimilarity": 0.91,
        "attributeMatch": 1.0,
        "colorMatch": 1.0,
        "brandMatch": 1.0,
        "modelTokenMatch": 1.0,
        "tokenOverlap": 0.82
      }
    }
  ],
  "count": 1
}
```

### Match Found to Lost
```
POST /match/found-to-lost
Headers: X-API-Key: your-api-key
Content-Type: application/json
```

Same request/response format as above.

## 🧪 Testing

### Test API with curl

```bash
# Health check
curl http://localhost:5000/health

# Test matching
curl -X POST http://localhost:5000/match/lost-to-found \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "itemId": "test123",
    "itemName": "Blue backpack",
    "category": "bags",
    "description": "Nike blue backpack with laptop compartment",
    "location": "Library",
    "date": "2024-02-15"
  }'
```

### Test with Python

```python
import requests

url = "http://localhost:5000/match/lost-to-found"
headers = {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
}
data = {
    "itemId": "test123",
    "itemName": "Blue backpack",
    "category": "bags",
    "description": "Nike blue backpack",
    "location": "Library",
    "date": "2024-02-15"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

## 🚀 Deployment

### Deploy to Render

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial ML service"
   git push origin main
   ```

2. **Create Render Web Service**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your repository
   - Configure:
     - **Name:** findmate-ml-service
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`

3. **Add Environment Variables**
   - `MONGODB_URI`
   - `ML_SERVICE_API_KEY`
   - `ML_MATCHING_THRESHOLD`
   - `FLASK_ENV=production`

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment
   - Copy service URL

5. **Update Main Application**
   Update main app's `.env`:
   ```env
   ML_ENABLED=true
   ML_SERVICE_URL=https://findmate-ml-service.onrender.com
   ML_SERVICE_API_KEY=your-matching-api-key
   ```

### Deploy to Heroku

```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create findmate-ml-service

# Add Python buildpack
heroku buildpacks:set heroku/python

# Set environment variables
heroku config:set MONGODB_URI="your-mongodb-uri"
heroku config:set ML_SERVICE_API_KEY="your-api-key"
heroku config:set ML_MATCHING_THRESHOLD=0.65
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main

# Check logs
heroku logs --tail
```

## 🔐 Security

- **API Key Authentication:** All endpoints require valid API key
- **CORS Enabled:** Configure allowed origins in production
- **Environment Variables:** Never commit `.env` file
- **Data Sanitization:** Input validation on all endpoints

## 📊 Matching Algorithm

### Overall Confidence Score

```
score = (category * 0.18) +
        (description * 0.28) +
        (item_name * 0.13) +
        (attributes * 0.14) +
        (location * 0.16) +
        (date * 0.11)
```

### Category Matching
- Exact match: 1.0
- Related categories: 0.6
- Generic ('other'): 0.3
- No match: 0.0

### Description Similarity
- Word TF-IDF and character TF-IDF
- Token overlap for short reports
- Fuzzy similarity for typos
- Normalizes common aliases such as mobile/phone/iPhone, rucksack/backpack, and spectacles/glasses

### Attribute Matching
- Extracts colors, common brands, and model-like tokens
- Rewards exact attribute agreement
- Penalizes known color or brand contradictions

### Location Proximity
- Exact match: 1.0
- Same group (e.g., both departments): 0.7
- Fuzzy string matching for partial matches
- Campus-specific location grouping

### Date Proximity
- Exponential decay function
- Same day: 1.0
- 1 day apart: ~0.97
- 7 days apart: ~0.77
- 30+ days apart: 0.0

## 🐛 Troubleshooting

### Service won't start
- Check MongoDB connection string
- Verify all dependencies installed
- Check Python version (3.8+)

### No matches found
- Lower `ML_MATCHING_THRESHOLD` (try 0.50)
- Check database has active items
- Verify item data is complete

### Authentication errors
- Ensure API key matches in both services
- Check `X-API-Key` header is present
- Verify environment variables loaded

## 📈 Performance

- Response time: < 500ms for typical queries
- Concurrent requests: Supports multiple workers
- Database queries: Indexed for fast retrieval
- Memory usage: ~200MB per worker

## 🔄 Future Enhancements

- [ ] Image similarity using CNN
- [ ] Advanced NLP with spaCy
- [ ] Real-time matching with WebSockets
- [ ] Batch processing for existing items
- [ ] Model training from admin feedback
- [ ] A/B testing for algorithm tuning

## 📞 Support

Issues or questions? Check the main FindMate documentation.

---

**Version:** 2.0.0  
**Status:** Production Ready
