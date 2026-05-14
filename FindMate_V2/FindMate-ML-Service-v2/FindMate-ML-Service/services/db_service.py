"""
Database Service for MongoDB Operations
"""

from datetime import datetime, timedelta
import os
import logging

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for interacting with MongoDB"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.lost_items = None
        self.found_items = None
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            if not mongodb_uri:
                raise Exception("MONGODB_URI not set in environment")

            if not MongoClient:
                raise Exception("pymongo is not installed. Run: pip install -r requirements.txt")
            
            self.client = MongoClient(mongodb_uri)
            self.db = self.client.get_database()
            self.lost_items = self.db.lostitems
            self.found_items = self.db.founditems
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def get_active_lost_items(self, exclude_id=None):
        """
        Get all active lost items (not already matched)
        
        Args:
            exclude_id: Optional item ID to exclude from results
            
        Returns:
            List of lost item documents
        """
        try:
            query = {
                'status': {'$nin': ['reunited', 'resolved', 'closed']},
                'mlMatchStatus': {'$ne': 'verified_match'}
            }
            
            if exclude_id:
                query['_id'] = {'$ne': exclude_id}
            
            items = list(self.lost_items.find(query))
            logger.info(f"Retrieved {len(items)} active lost items")
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving lost items: {str(e)}")
            return []
    
    def get_active_found_items(self, exclude_id=None):
        """
        Get all active found items (not already matched)
        
        Args:
            exclude_id: Optional item ID to exclude from results
            
        Returns:
            List of found item documents
        """
        try:
            query = {
                'status': {'$nin': ['claimed', 'resolved', 'closed']},
                'mlMatchStatus': {'$ne': 'verified_match'}
            }
            
            if exclude_id:
                query['_id'] = {'$ne': exclude_id}
            
            items = list(self.found_items.find(query))
            logger.info(f"Retrieved {len(items)} active found items")
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving found items: {str(e)}")
            return []
    
    def get_recent_items(self, collection, days=30):
        """
        Get items from the last N days
        
        Args:
            collection: 'lost' or 'found'
            days: Number of days to look back
            
        Returns:
            List of item documents
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if collection == 'lost':
                items = list(self.lost_items.find({
                    'lostDate': {'$gte': cutoff_date},
                    'status': {'$in': ['lost', 'active']}
                }))
            else:
                items = list(self.found_items.find({
                    'foundDate': {'$gte': cutoff_date},
                    'status': {'$in': ['found', 'pending']}
                }))
            
            logger.info(f"Retrieved {len(items)} recent {collection} items")
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving recent items: {str(e)}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
