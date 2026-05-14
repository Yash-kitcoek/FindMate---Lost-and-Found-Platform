"""
Location Proximity Calculator using Fuzzy String Matching
"""

from difflib import SequenceMatcher
import logging
import re

logger = logging.getLogger(__name__)

class LocationMatcher:
    """Calculate location proximity using fuzzy string matching"""
    
    # Location hierarchy for campus-specific matching
    LOCATION_GROUPS = {
        'departments': [
            'BSH-Department', 'CIVIL-Department', 'BIOTECH-Department',
            'ENTC-Department', 'AIML-building', 'MBA-building'
        ],
        'residential': [
            'boys-hostel', 'Girls-hostel', 'South-enclave', 'North-enclave'
        ],
        'common': ['Ground', 'Library', 'other']
    }
    
    def __init__(self):
        # Create reverse mapping
        self.location_to_group = {}
        for group, locations in self.LOCATION_GROUPS.items():
            for loc in locations:
                self.location_to_group[self.normalize_location(loc)] = group

    def normalize_location(self, location):
        """Normalize campus location text for reliable matching."""
        if not location:
            return ""

        normalized = str(location).strip().lower()
        normalized = normalized.replace("&", " and ")
        normalized = re.sub(r"[^a-z0-9\s-]", " ", normalized)
        normalized = normalized.replace("_", "-")
        normalized = re.sub(r"\s+", " ", normalized).strip()

        aliases = {
            "lib": "library",
            "central library": "library",
            "hostel boys": "boys-hostel",
            "boy hostel": "boys-hostel",
            "boys hostel": "boys-hostel",
            "girls hostel": "girls-hostel",
            "girl hostel": "girls-hostel",
            "playground": "ground",
            "main ground": "ground",
            "aiml building": "aiml-building",
            "mba building": "mba-building"
        }

        return aliases.get(normalized, normalized)
    
    def calculate_proximity(self, location1, location2):
        """
        Calculate proximity score between two locations
        
        Args:
            location1: First location string
            location2: Second location string
            
        Returns:
            Proximity score (0-1)
        """
        try:
            if not location1 or not location2:
                return 0.0
            
            # Normalize location strings
            loc1 = self.normalize_location(location1)
            loc2 = self.normalize_location(location2)
            
            # Exact match
            if loc1 == loc2:
                return 1.0
            
            # Same group match
            group1 = self.location_to_group.get(loc1)
            group2 = self.location_to_group.get(loc2)
            
            if group1 and group2 and group1 == group2:
                return 0.7  # High score for same group (e.g., both departments)
            
            # Fuzzy string matching for partial matches
            similarity = SequenceMatcher(None, loc1.lower(), loc2.lower()).ratio()
            
            # Boost score if locations share keywords
            loc1_words = set(re.split(r"[\s-]+", loc1.lower()))
            loc2_words = set(re.split(r"[\s-]+", loc2.lower()))
            common_words = loc1_words.intersection(loc2_words)
            
            if common_words:
                similarity = min(1.0, similarity + 0.25)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating location proximity: {str(e)}")
            return 0.0
    
    def is_nearby(self, location1, location2, threshold=0.5):
        """
        Check if two locations are nearby
        
        Args:
            location1: First location
            location2: Second location
            threshold: Minimum proximity score to consider nearby
            
        Returns:
            Boolean indicating if locations are nearby
        """
        proximity = self.calculate_proximity(location1, location2)
        return proximity >= threshold
    
    def get_location_group(self, location):
        """
        Get the group a location belongs to
        
        Args:
            location: Location string
            
        Returns:
            Group name or None
        """
        return self.location_to_group.get(location)
    
    def calculate_batch_proximity(self, query_location, locations):
        """
        Calculate proximity between query and multiple locations
        
        Args:
            query_location: Query location
            locations: List of locations
            
        Returns:
            List of proximity scores
        """
        try:
            return [self.calculate_proximity(query_location, loc) for loc in locations]
        except Exception as e:
            logger.error(f"Error calculating batch proximity: {str(e)}")
            return [0.0] * len(locations)
