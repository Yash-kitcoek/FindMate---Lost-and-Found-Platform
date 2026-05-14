"""
Item Matcher Service - Core ML Matching Logic
"""

from services.db_service import DatabaseService
from utils.text_similarity import TextSimilarity
from utils.location_matcher import LocationMatcher
from utils.date_scorer import DateScorer
import logging
import os

logger = logging.getLogger(__name__)

class ItemMatcher:
    """Main service for matching lost and found items"""
    
    # Category matching rules
    CATEGORY_EXACT_MATCH = 1.0
    CATEGORY_RELATED_MATCH = 0.6
    CATEGORY_GENERIC_MATCH = 0.3
    
    # Related categories (can be extended)
    RELATED_CATEGORIES = {
        'electronics': ['accessories', 'documents'],
        'accessories': ['electronics', 'jewelry', 'bags'],
        'clothing': ['bags', 'accessories'],
        'bags': ['clothing', 'accessories', 'documents'],
        'documents': ['bags', 'electronics'],
        'jewelry': ['accessories'],
        'books': ['documents'],
        'stationery': ['books', 'documents']
    }
    
    # Matching weights. These favor direct item evidence over broad category labels.
    WEIGHTS = {
        'category': 0.10,
        'description': 0.34,
        'name': 0.18,
        'attributes': 0.16,
        'location': 0.12,
        'date': 0.10
    }
    
    def __init__(self):
        """Initialize matcher with all utility services"""
        self.db = DatabaseService()
        self.text_similarity = TextSimilarity()
        self.location_matcher = LocationMatcher()
        self.date_scorer = DateScorer(max_days=int(os.getenv('ML_DATE_MAX_DAYS', 180)))
        
        # Matching configuration
        self.min_confidence = float(os.getenv('ML_MATCHING_THRESHOLD', 0.65))
        self.max_matches = int(os.getenv('ML_MAX_MATCHES', 10))
        self.prefilter_threshold = float(os.getenv('ML_PREFILTER_THRESHOLD', 0.35))
        
        logger.info(
            "ItemMatcher initialized "
            f"(min_confidence={self.min_confidence}, max_matches={self.max_matches})"
        )
    
    def calculate_category_score(self, category1, category2):
        """
        Calculate category match score
        
        Args:
            category1: First category
            category2: Second category
            
        Returns:
            Score (0-1)
        """
        try:
            if not category1 or not category2:
                return 0.0
            
            cat1 = category1.lower()
            cat2 = category2.lower()
            
            # Exact match
            if cat1 == cat2:
                return self.CATEGORY_EXACT_MATCH
            
            # Check if related
            related1 = self.RELATED_CATEGORIES.get(cat1, [])
            related2 = self.RELATED_CATEGORIES.get(cat2, [])
            
            if cat2 in related1 or cat1 in related2:
                return self.CATEGORY_RELATED_MATCH
            
            # Generic match for 'other'
            if cat1 == 'other' or cat2 == 'other':
                return self.CATEGORY_GENERIC_MATCH
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating category score: {str(e)}")
            return 0.0
    
    def calculate_overall_confidence(self, factors):
        """
        Calculate overall confidence score from individual factors
        
        Args:
            factors: Dict with categoryMatch, descriptionSimilarity, 
                    locationProximity, dateProximity
                    
        Returns:
            Overall confidence score (0-1)
        """
        try:
            score = (
                factors['categoryMatch'] * self.WEIGHTS['category'] +
                factors['descriptionSimilarity'] * self.WEIGHTS['description'] +
                factors['itemNameSimilarity'] * self.WEIGHTS['name'] +
                factors['attributeMatch'] * self.WEIGHTS['attributes'] +
                factors['objectTypeMatch'] * 0.18 +
                factors['locationProximity'] * self.WEIGHTS['location'] +
                factors['dateProximity'] * self.WEIGHTS['date']
            )
            score = self.apply_confidence_adjustments(score, factors)
            return float(max(0.0, min(1.0, score)))
            
        except Exception as e:
            logger.error(f"Error calculating overall confidence: {str(e)}")
            return 0.0

    def apply_confidence_adjustments(self, score, factors):
        """Apply guardrails for strong evidence and clear contradictions."""
        adjusted = score

        if factors.get('categoryMatch', 0) == 1.0 and factors.get('attributeMatch', 0) >= 0.85:
            adjusted += 0.04

        if factors.get('locationProximity', 0) >= 0.85 and factors.get('dateProximity', 0) >= 0.80:
            adjusted += 0.03

        if factors.get('descriptionSimilarity', 0) >= 0.75 and factors.get('itemNameSimilarity', 0) >= 0.70:
            adjusted += 0.04

        # A known conflicting color or brand is a meaningful negative signal.
        if factors.get('colorMatch') == 0.0:
            adjusted -= 0.08

        if factors.get('brandMatch') == 0.0:
            adjusted -= 0.10

        if factors.get('objectTypeMatch') == 0.0:
            adjusted -= 0.35

        if factors.get('descriptionSimilarity', 0) < 0.08 and factors.get('itemNameSimilarity', 0) < 0.08:
            adjusted -= 0.20

        if factors.get('dateProximity', 0) < 0.10:
            adjusted -= 0.08

        return adjusted

    def build_item_text(self, item):
        """Build a weighted text representation for one item."""
        return self.text_similarity.combine_texts(
            item.get('itemName'),
            item.get('itemName'),
            item.get('description'),
            item.get('category'),
            item.get('color', ''),
            item.get('brand', '')
        )

    def build_item_attributes(self, item):
        """Extract normalized attributes from known fields and description text."""
        return self.text_similarity.extract_attributes(
            item.get('itemName'),
            item.get('description'),
            item.get('color', ''),
            item.get('brand', '')
        )

    def should_score_candidate(self, category_score, text_score, location_score, date_score, name_score=0.0, token_overlap=0.0, object_score=0.5):
        """Reject candidates that only match broad metadata such as category/location."""
        direct_text_score = max(text_score, name_score, token_overlap)

        if object_score == 0.0:
            return False

        if object_score < 0.8 and name_score < 0.20:
            return False

        if name_score < 0.12 and token_overlap < 0.12:
            return False

        if category_score == 0.0 and direct_text_score < 0.45:
            return False

        if direct_text_score < 0.12 and object_score < 0.8:
            return False

        if direct_text_score < 0.08 and date_score < 0.20:
            return False

        blended = (
            category_score * 0.15 +
            text_score * 0.35 +
            name_score * 0.20 +
            token_overlap * 0.15 +
            location_score * 0.10 +
            date_score * 0.05
        )
        return blended >= self.prefilter_threshold

    def format_match(self, candidate, confidence, factors):
        """Format a candidate for the API response."""
        rounded_factors = {
            key: round(float(value), 3)
            for key, value in factors.items()
        }

        return {
            'matchedItemId': str(candidate['_id']),
            'confidenceScore': round(confidence, 3),
            'factors': rounded_factors
        }

    def rank_candidates(self, query_item, candidates, candidate_location_field, candidate_date_field):
        """Rank lost/found candidates using the hybrid matching model."""
        if not candidates:
            return []

        query_text = self.build_item_text(query_item)
        candidate_texts = [self.build_item_text(candidate) for candidate in candidates]
        description_scores = self.text_similarity.calculate_batch_similarity(query_text, candidate_texts)
        query_attrs = self.build_item_attributes(query_item)

        matches = []

        for index, candidate in enumerate(candidates):
            category_score = self.calculate_category_score(
                query_item.get('category'),
                candidate.get('category')
            )

            name_score = self.text_similarity.calculate_similarity(
                query_item.get('itemName'),
                candidate.get('itemName')
            )

            location_score = self.location_matcher.calculate_proximity(
                query_item.get('location'),
                candidate.get(candidate_location_field)
            )

            date_score = self.date_scorer.calculate_proximity(
                query_item.get('date'),
                candidate.get(candidate_date_field)
            )

            description_score = description_scores[index]
            token_overlap = self.text_similarity.token_overlap(query_text, candidate_texts[index])
            object_score = self.text_similarity.item_family_score(query_text, candidate_texts[index])

            if not self.should_score_candidate(category_score, description_score, location_score, date_score, name_score, token_overlap, object_score):
                continue

            candidate_attrs = self.build_item_attributes(candidate)
            attribute_score, color_score, brand_score, model_score = self.text_similarity.attribute_similarity(
                query_attrs,
                candidate_attrs
            )

            factors = {
                'categoryMatch': category_score,
                'descriptionSimilarity': description_score,
                'itemNameSimilarity': name_score,
                'attributeMatch': attribute_score,
                'objectTypeMatch': object_score,
                'locationProximity': location_score,
                'dateProximity': date_score,
                'colorMatch': color_score,
                'brandMatch': brand_score,
                'modelTokenMatch': model_score,
                'tokenOverlap': token_overlap
            }

            confidence = self.calculate_overall_confidence(factors)

            if confidence >= self.min_confidence:
                matches.append(self.format_match(candidate, confidence, factors))

        matches.sort(key=lambda x: x['confidenceScore'], reverse=True)
        return matches[:self.max_matches]
    
    def find_matches_for_lost_item(self, lost_item):
        """
        Find matching found items for a lost item
        
        Args:
            lost_item: Dict with item details
            
        Returns:
            List of matches with confidence scores
        """
        try:
            logger.info(f"Finding matches for lost item: {lost_item['itemId']}")
            
            # Get all active found items from database
            found_items = self.db.get_active_found_items()
            
            if not found_items:
                logger.info("No active found items to match against")
                return []
            
            matches = self.rank_candidates(
                lost_item,
                found_items,
                candidate_location_field='foundLocation',
                candidate_date_field='foundDate'
            )
            
            logger.info(f"Found {len(matches)} matches above threshold")
            return matches
            
        except Exception as e:
            logger.error(f"Error finding matches for lost item: {str(e)}")
            return []
    
    def find_matches_for_found_item(self, found_item):
        """
        Find matching lost items for a found item
        
        Args:
            found_item: Dict with item details
            
        Returns:
            List of matches with confidence scores
        """
        try:
            logger.info(f"Finding matches for found item: {found_item['itemId']}")
            
            # Get all active lost items from database
            lost_items = self.db.get_active_lost_items()
            
            if not lost_items:
                logger.info("No active lost items to match against")
                return []
            
            matches = self.rank_candidates(
                found_item,
                lost_items,
                candidate_location_field='lostLocation',
                candidate_date_field='lostDate'
            )
            
            logger.info(f"Found {len(matches)} matches above threshold")
            return matches
            
        except Exception as e:
            logger.error(f"Error finding matches for found item: {str(e)}")
            return []

