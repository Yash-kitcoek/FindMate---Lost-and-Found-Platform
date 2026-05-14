"""
FindMate ML Service - Main Application
AI-powered matching service for lost and found items
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

from services.matcher import ItemMatcher
from middleware.auth import require_api_key

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize matcher service
matcher = ItemMatcher()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'FindMate ML Service',
        'version': '2.0.0',
        'algorithm': 'hybrid-tfidf-fuzzy-attribute-ranker'
    }), 200

@app.route('/match/lost-to-found', methods=['POST'])
@require_api_key
def match_lost_to_found():
    """
    Match a lost item against existing found items
    
    Request Body:
    {
        "itemId": "string",
        "itemName": "string",
        "category": "string",
        "description": "string",
        "location": "string",
        "date": "ISO date string",
        "color": "string" (optional),
        "brand": "string" (optional)
    }
    
    Response:
    {
        "matches": [
            {
                "matchedItemId": "string",
                "confidenceScore": float (0-1),
                "factors": {
                    "categoryMatch": float,
                    "descriptionSimilarity": float,
                    "locationProximity": float,
                    "dateProximity": float
                }
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['itemId', 'itemName', 'category', 'description', 'location', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        logger.info(f"Matching lost item: {data['itemId']}")
        
        # Find matches
        matches = matcher.find_matches_for_lost_item(data)
        
        logger.info(f"Found {len(matches)} matches for lost item: {data['itemId']}")
        
        return jsonify({
            'matches': matches,
            'count': len(matches)
        }), 200
        
    except Exception as e:
        logger.error(f"Error matching lost item: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/match/found-to-lost', methods=['POST'])
@require_api_key
def match_found_to_lost():
    """
    Match a found item against existing lost items
    
    Request Body: Same as /match/lost-to-found
    Response: Same as /match/lost-to-found
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['itemId', 'itemName', 'category', 'description', 'location', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        logger.info(f"Matching found item: {data['itemId']}")
        
        # Find matches
        matches = matcher.find_matches_for_found_item(data)
        
        logger.info(f"Found {len(matches)} matches for found item: {data['itemId']}")
        
        return jsonify({
            'matches': matches,
            'count': len(matches)
        }), 200
        
    except Exception as e:
        logger.error(f"Error matching found item: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting FindMate ML Service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
