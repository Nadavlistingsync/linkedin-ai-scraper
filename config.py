import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LinkedIn Credentials
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
    
    # Search Keywords for AI Agent Space
    SEARCH_KEYWORDS = [
        "AI agent", "automation specialist", "workflow automation",
        "RPA", "process automation", "business automation",
        "Zapier", "Make.com", "n8n", "automation consultant",
        "AI automation", "workflow optimization", "automation expert",
        "no-code automation", "low-code automation", "automation engineer",
        "workflow specialist", "process optimization", "business process automation",
        "digital transformation", "automation architect", "workflow consultant"
    ]
    
    # Company-based searches
    TARGET_COMPANIES = [
        "Zapier", "Make.com", "n8n", "Microsoft", "Google", "Amazon",
        "Salesforce", "HubSpot", "Notion", "Airtable", "Monday.com",
        "Asana", "Trello", "Slack", "Discord", "Figma", "Canva"
    ]
    
    # Rate Limiting Settings
    MAX_SEARCHES_PER_HOUR = 100
    DELAY_BETWEEN_SEARCHES = 30  # seconds
    DELAY_BETWEEN_PROFILES = 2   # seconds
    MAX_PROFILES_PER_SEARCH = 50
    
    # Follower Count Range
    MIN_FOLLOWERS = 1000
    MAX_FOLLOWERS = 10000
    
    # Output Settings
    OUTPUT_CSV = "ai_agent_profiles.csv"
    LOG_FILE = "linkedin_scraper.log"
    
    # Browser Settings
    HEADLESS = False  # Set to True for production
    USER_AGENT_ROTATION = True
    
    # Retry Settings
    MAX_RETRIES = 3
    RETRY_DELAY = 60  # seconds
    
    # Data Quality Settings
    MIN_PROFILE_COMPLETENESS = 0.6
    CONFIDENCE_THRESHOLD = 0.7 