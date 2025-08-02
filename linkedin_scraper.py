import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from typing import List, Dict, Optional
import logging

from config import Config
from utils import (
    setup_logging, random_delay, extract_follower_count, 
    validate_follower_count, calculate_profile_completeness,
    calculate_confidence_score, clean_text, generate_search_url,
    is_valid_profile_url, format_timestamp
)

class LinkedInScraper:
    def __init__(self, config: Config):
        self.config = config
        self.driver = None
        self.logger = setup_logging(config.LOG_FILE)
        self.profiles_found = []
        self.searches_completed = 0
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        options = Options()
        
        # Anti-detection measures
        ua = UserAgent()
        options.add_argument(f'--user-agent={ua.random}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        if self.config.HEADLESS:
            options.add_argument('--headless')
        
        # Additional anti-detection
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set window size
        self.driver.set_window_size(1920, 1080)
        
    def login(self) -> bool:
        """Login to LinkedIn"""
        try:
            self.logger.info("Attempting to login to LinkedIn...")
            self.driver.get("https://www.linkedin.com/login")
            random_delay(3, 5)
            
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(self.config.LINKEDIN_EMAIL)
            random_delay(1, 2)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.config.LINKEDIN_PASSWORD)
            random_delay(1, 2)
            
            # Click login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".global-nav"))
            )
            
            self.logger.info("Successfully logged into LinkedIn")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
    
    def search_profiles(self, keyword: str, max_pages: int = 3) -> List[Dict]:
        """Search for profiles with specific keyword"""
        profiles = []
        
        try:
            self.logger.info(f"Searching for profiles with keyword: {keyword}")
            
            for page in range(1, max_pages + 1):
                if self.searches_completed >= self.config.MAX_SEARCHES_PER_HOUR:
                    self.logger.warning("Hourly search limit reached")
                    break
                
                search_url = generate_search_url(keyword, page)
                self.driver.get(search_url)
                random_delay(3, 5)
                
                # Wait for results to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results-container"))
                    )
                except TimeoutException:
                    self.logger.warning(f"No search results found for page {page}")
                    break
                
                # Extract profiles from current page
                page_profiles = self._extract_profiles_from_page(keyword)
                profiles.extend(page_profiles)
                
                self.searches_completed += 1
                self.logger.info(f"Page {page}: Found {len(page_profiles)} profiles")
                
                # Rate limiting
                if page < max_pages:
                    random_delay(self.config.DELAY_BETWEEN_SEARCHES, self.config.DELAY_BETWEEN_SEARCHES + 10)
                    
        except Exception as e:
            self.logger.error(f"Search failed for keyword '{keyword}': {str(e)}")
            
        return profiles
    
    def _extract_profiles_from_page(self, keyword: str) -> List[Dict]:
        """Extract profile information from search results page"""
        profiles = []
        
        try:
            # Find all profile result elements
            profile_elements = self.driver.find_elements(By.CSS_SELECTOR, ".entity-result__item")
            
            for element in profile_elements[:self.config.MAX_PROFILES_PER_SEARCH]:
                try:
                    profile_data = self._extract_single_profile(element, keyword)
                    if profile_data and self._validate_profile(profile_data):
                        profiles.append(profile_data)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to extract profile: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to extract profiles from page: {str(e)}")
            
        return profiles
    
    def _extract_single_profile(self, element, keyword: str) -> Optional[Dict]:
        """Extract data from a single profile element"""
        try:
            # Extract name
            name_element = element.find_element(By.CSS_SELECTOR, ".entity-result__title-text")
            name = clean_text(name_element.text)
            
            # Extract headline
            headline_element = element.find_element(By.CSS_SELECTOR, ".entity-result__primary-subtitle")
            headline = clean_text(headline_element.text)
            
            # Extract location
            location_element = element.find_element(By.CSS_SELECTOR, ".entity-result__secondary-subtitle")
            location = clean_text(location_element.text)
            
            # Extract profile URL
            link_element = element.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
            profile_url = link_element.get_attribute("href")
            
            # Extract company (if available)
            company = ""
            try:
                company_element = element.find_element(By.CSS_SELECTOR, ".entity-result__tertiary-subtitle")
                company = clean_text(company_element.text)
            except NoSuchElementException:
                pass
            
            # Extract follower count
            follower_count = self._extract_follower_count_from_element(element)
            
            # Calculate scores
            profile_data = {
                'name': name,
                'headline': headline,
                'location': location,
                'profile_url': profile_url,
                'company': company,
                'follower_count': follower_count,
                'keyword_matched': keyword,
                'scraped_date': format_timestamp()
            }
            
            profile_data['profile_completeness'] = calculate_profile_completeness(profile_data)
            profile_data['confidence_score'] = calculate_confidence_score(profile_data, keyword)
            
            return profile_data
            
        except Exception as e:
            self.logger.warning(f"Failed to extract profile data: {str(e)}")
            return None
    
    def _extract_follower_count_from_element(self, element) -> Optional[int]:
        """Extract follower count from profile element"""
        try:
            # Look for follower count in various possible locations
            follower_selectors = [
                ".entity-result__secondary-subtitle",
                ".entity-result__metadata",
                ".search-result__info",
                ".entity-result__tertiary-subtitle"
            ]
            
            for selector in follower_selectors:
                try:
                    follower_element = element.find_element(By.CSS_SELECTOR, selector)
                    text = follower_element.text
                    follower_count = extract_follower_count(text)
                    if follower_count:
                        return follower_count
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Failed to extract follower count: {str(e)}")
            
        return None
    
    def _validate_profile(self, profile_data: Dict) -> bool:
        """Validate if profile meets criteria"""
        # Check if profile URL is valid
        if not is_valid_profile_url(profile_data.get('profile_url', '')):
            return False
        
        # Check follower count range
        follower_count = profile_data.get('follower_count')
        if not validate_follower_count(follower_count, self.config.MIN_FOLLOWERS, self.config.MAX_FOLLOWERS):
            return False
        
        # Check profile completeness
        if profile_data.get('profile_completeness', 0) < self.config.MIN_PROFILE_COMPLETENESS:
            return False
        
        # Check confidence score
        if profile_data.get('confidence_score', 0) < self.config.CONFIDENCE_THRESHOLD:
            return False
        
        return True
    
    def search_by_company(self, company: str) -> List[Dict]:
        """Search for profiles by company"""
        keyword = f"current company:{company}"
        return self.search_profiles(keyword, max_pages=2)
    
    def run_comprehensive_search(self) -> List[Dict]:
        """Run comprehensive search using all keywords and companies"""
        all_profiles = []
        
        # Search by keywords
        for keyword in self.config.SEARCH_KEYWORDS:
            self.logger.info(f"Searching with keyword: {keyword}")
            profiles = self.search_profiles(keyword, max_pages=2)
            all_profiles.extend(profiles)
            
            # Rate limiting between searches
            random_delay(self.config.DELAY_BETWEEN_SEARCHES, self.config.DELAY_BETWEEN_SEARCHES + 10)
        
        # Search by companies
        for company in self.config.TARGET_COMPANIES:
            self.logger.info(f"Searching by company: {company}")
            profiles = self.search_by_company(company)
            all_profiles.extend(profiles)
            
            # Rate limiting between searches
            random_delay(self.config.DELAY_BETWEEN_SEARCHES, self.config.DELAY_BETWEEN_SEARCHES + 10)
        
        return all_profiles
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Browser closed") 