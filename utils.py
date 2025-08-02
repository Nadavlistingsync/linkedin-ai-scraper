import logging
import random
import time
import re
from datetime import datetime
from typing import Dict, List, Optional

def setup_logging(log_file: str) -> logging.Logger:
    """Setup comprehensive logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def random_delay(min_seconds: float = 2, max_seconds: float = 5):
    """Add random delay to avoid detection"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def extract_follower_count(text: str) -> Optional[int]:
    """Extract follower count from text"""
    if not text:
        return None
    
    # Common patterns for follower counts
    patterns = [
        r'(\d{1,3}(?:,\d{3})*)\s*followers?',
        r'(\d{1,3}(?:,\d{3})*)\s*connections?',
        r'(\d{1,3}(?:,\d{3})*)\s*members?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            # Remove commas and convert to int
            count_str = match.group(1).replace(',', '')
            try:
                return int(count_str)
            except ValueError:
                continue
    
    return None

def validate_follower_count(count: Optional[int], min_followers: int, max_followers: int) -> bool:
    """Validate if follower count is in target range"""
    if count is None:
        return False
    return min_followers <= count <= max_followers

def calculate_profile_completeness(profile_data: Dict) -> float:
    """Calculate profile completeness score (0-1)"""
    required_fields = ['name', 'headline', 'location', 'profile_url']
    optional_fields = ['company', 'follower_count']
    
    score = 0.0
    total_fields = len(required_fields) + len(optional_fields)
    
    # Check required fields
    for field in required_fields:
        if profile_data.get(field) and str(profile_data[field]).strip():
            score += 1.0
    
    # Check optional fields
    for field in optional_fields:
        if profile_data.get(field) and str(profile_data[field]).strip():
            score += 0.5
    
    return score / total_fields

def calculate_confidence_score(profile_data: Dict, keyword_matched: str) -> float:
    """Calculate confidence score for profile quality"""
    base_score = 0.5
    
    # Profile completeness bonus
    completeness = calculate_profile_completeness(profile_data)
    base_score += completeness * 0.3
    
    # Follower count validation bonus
    if profile_data.get('follower_count'):
        base_score += 0.1
    
    # Keyword relevance bonus
    headline = profile_data.get('headline', '').lower()
    if keyword_matched.lower() in headline:
        base_score += 0.1
    
    return min(base_score, 1.0)

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove special characters that might cause CSV issues
    text = text.replace('"', '""')
    
    return text

def generate_search_url(keyword: str, page: int = 1) -> str:
    """Generate LinkedIn search URL"""
    encoded_keyword = keyword.replace(' ', '%20')
    return f"https://www.linkedin.com/search/results/people/?keywords={encoded_keyword}&origin=GLOBAL_SEARCH_HEADER&page={page}"

def is_valid_profile_url(url: str) -> bool:
    """Validate LinkedIn profile URL"""
    if not url:
        return False
    
    # Check if it's a LinkedIn profile URL
    linkedin_patterns = [
        r'linkedin\.com/in/',
        r'linkedin\.com/pub/'
    ]
    
    for pattern in linkedin_patterns:
        if re.search(pattern, url):
            return True
    
    return False

def format_timestamp() -> str:
    """Get formatted timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S") 