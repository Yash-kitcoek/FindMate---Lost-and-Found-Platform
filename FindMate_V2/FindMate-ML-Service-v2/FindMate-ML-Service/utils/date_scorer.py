"""
Date Proximity Calculator with Decay Function
"""

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DateScorer:
    """Calculate date proximity using exponential decay"""
    
    def __init__(self, max_days=180):
        """
        Initialize date scorer
        
        Args:
            max_days: Maximum days to consider (beyond this = 0 score)
        """
        self.max_days = max_days
    
    def parse_date(self, date_input):
        """
        Parse date from various formats
        
        Args:
            date_input: Date string or datetime object
            
        Returns:
            datetime object or None
        """
        try:
            if isinstance(date_input, datetime):
                return self._as_naive_utc(date_input)
            
            if isinstance(date_input, str):
                # Try ISO format first
                try:
                    return self._as_naive_utc(datetime.fromisoformat(date_input.replace('Z', '+00:00')))
                except:
                    pass
                
                # Try common formats
                formats = [
                    '%Y-%m-%d',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%m/%d/%Y',
                    '%d/%m/%Y'
                ]
                
                for fmt in formats:
                    try:
                        return self._as_naive_utc(datetime.strptime(date_input, fmt))
                    except:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date: {str(e)}")
            return None

    def _as_naive_utc(self, value):
        """Convert aware datetimes to naive UTC so subtraction is always safe."""
        if value.tzinfo:
            return value.astimezone().replace(tzinfo=None)
        return value
    
    def calculate_proximity(self, date1, date2):
        """
        Calculate proximity score between two dates
        
        Uses exponential decay:
        - Same day: 1.0
        - 1 day apart: ~0.97
        - 7 days apart: ~0.77
        - 14 days apart: ~0.60
        - 30 days apart: 0.0
        
        Args:
            date1: First date (string or datetime)
            date2: Second date (string or datetime)
            
        Returns:
            Proximity score (0-1)
        """
        try:
            # Parse dates
            dt1 = self.parse_date(date1)
            dt2 = self.parse_date(date2)
            
            if not dt1 or not dt2:
                return 0.0
            
            # Calculate days difference
            days_diff = abs((dt1 - dt2).days)
            
            if days_diff == 0:
                return 1.0

            if days_diff >= self.max_days:
                return 0.05

            # Smooth decay: 1 day ~= 0.99, 30 days ~= 0.60, 90 days ~= 0.25.
            score = 1.0 / (1.0 + pow(days_diff / 45.0, 1.6))
            return float(max(0.05, min(1.0, score)))
            
        except Exception as e:
            logger.error(f"Error calculating date proximity: {str(e)}")
            return 0.0
    
    def is_recent(self, date, days=7):
        """
        Check if date is within last N days
        
        Args:
            date: Date to check
            days: Number of days to consider recent
            
        Returns:
            Boolean
        """
        try:
            dt = self.parse_date(date)
            if not dt:
                return False
            
            cutoff = datetime.now() - timedelta(days=days)
            return dt >= cutoff
            
        except Exception as e:
            logger.error(f"Error checking if date is recent: {str(e)}")
            return False
    
    def days_apart(self, date1, date2):
        """
        Calculate number of days between two dates
        
        Args:
            date1: First date
            date2: Second date
            
        Returns:
            Number of days (absolute value)
        """
        try:
            dt1 = self.parse_date(date1)
            dt2 = self.parse_date(date2)
            
            if not dt1 or not dt2:
                return None
            
            return abs((dt1 - dt2).days)
            
        except Exception as e:
            logger.error(f"Error calculating days apart: {str(e)}")
            return None
    
    def calculate_batch_proximity(self, query_date, dates):
        """
        Calculate proximity between query date and multiple dates
        
        Args:
            query_date: Query date
            dates: List of dates
            
        Returns:
            List of proximity scores
        """
        try:
            return [self.calculate_proximity(query_date, d) for d in dates]
        except Exception as e:
            logger.error(f"Error calculating batch proximity: {str(e)}")
            return [0.0] * len(dates)


