#!/usr/bin/env python3
"""
LinkedIn AI Agent Professionals Scraper
Main orchestration script for finding AI automation professionals
"""

import sys
import time
import logging
from datetime import datetime
from typing import List, Dict

from config import Config
from linkedin_scraper import LinkedInScraper
from data_processor import DataProcessor
from utils import setup_logging, random_delay

class LinkedInScrapingOrchestrator:
    def __init__(self):
        self.config = Config()
        self.logger = setup_logging(self.config.LOG_FILE)
        self.scraper = None
        self.data_processor = DataProcessor(self.config.OUTPUT_CSV)
        
    def initialize(self) -> bool:
        """Initialize the scraper and login to LinkedIn"""
        try:
            self.logger.info("Initializing LinkedIn scraper...")
            self.scraper = LinkedInScraper(self.config)
            
            # Login to LinkedIn
            if not self.scraper.login():
                self.logger.error("Failed to login to LinkedIn. Check credentials.")
                return False
            
            self.logger.info("Successfully initialized scraper")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False
    
    def run_comprehensive_search(self) -> List[Dict]:
        """Run comprehensive search using all keywords and companies"""
        all_profiles = []
        
        try:
            self.logger.info("Starting comprehensive LinkedIn search...")
            
            # Search by keywords
            self.logger.info(f"Searching with {len(self.config.SEARCH_KEYWORDS)} keywords...")
            for i, keyword in enumerate(self.config.SEARCH_KEYWORDS, 1):
                self.logger.info(f"Keyword {i}/{len(self.config.SEARCH_KEYWORDS)}: {keyword}")
                
                profiles = self.scraper.search_profiles(keyword, max_pages=2)
                all_profiles.extend(profiles)
                
                self.logger.info(f"Found {len(profiles)} profiles for keyword '{keyword}'")
                
                # Rate limiting between searches
                if i < len(self.config.SEARCH_KEYWORDS):
                    random_delay(self.config.DELAY_BETWEEN_SEARCHES, self.config.DELAY_BETWEEN_SEARCHES + 10)
            
            # Search by companies
            self.logger.info(f"Searching with {len(self.config.TARGET_COMPANIES)} companies...")
            for i, company in enumerate(self.config.TARGET_COMPANIES, 1):
                self.logger.info(f"Company {i}/{len(self.config.TARGET_COMPANIES)}: {company}")
                
                profiles = self.scraper.search_by_company(company)
                all_profiles.extend(profiles)
                
                self.logger.info(f"Found {len(profiles)} profiles for company '{company}'")
                
                # Rate limiting between searches
                if i < len(self.config.TARGET_COMPANIES):
                    random_delay(self.config.DELAY_BETWEEN_SEARCHES, self.config.DELAY_BETWEEN_SEARCHES + 10)
            
            self.logger.info(f"Total profiles found: {len(all_profiles)}")
            return all_profiles
            
        except Exception as e:
            self.logger.error(f"Comprehensive search failed: {str(e)}")
            return []
    
    def process_and_save_profiles(self, profiles: List[Dict]) -> bool:
        """Process profiles and save to CSV"""
        try:
            if not profiles:
                self.logger.warning("No profiles to process")
                return False
            
            self.logger.info(f"Processing {len(profiles)} profiles...")
            
            # Load existing profiles for deduplication
            existing_df = self.data_processor.load_existing_profiles()
            
            # Deduplicate profiles
            deduplicated_profiles = self.data_processor.deduplicate_profiles(profiles, existing_df)
            self.logger.info(f"After deduplication: {len(deduplicated_profiles)} profiles")
            
            # Filter by quality
            filtered_profiles = self.data_processor.filter_by_quality(
                deduplicated_profiles,
                min_confidence=self.config.CONFIDENCE_THRESHOLD,
                min_completeness=self.config.MIN_PROFILE_COMPLETENESS
            )
            self.logger.info(f"After quality filtering: {len(filtered_profiles)} profiles")
            
            # Sort by quality
            sorted_profiles = self.data_processor.sort_by_quality(filtered_profiles)
            
            # Save to CSV
            success = self.data_processor.save_profiles_to_csv(sorted_profiles)
            
            if success:
                # Generate and export summary report
                summary = self.data_processor.generate_summary_report(sorted_profiles)
                self.data_processor.export_summary_report(summary)
                
                self.logger.info(f"Successfully saved {len(sorted_profiles)} profiles to {self.config.OUTPUT_CSV}")
                return True
            else:
                self.logger.error("Failed to save profiles to CSV")
                return False
                
        except Exception as e:
            self.logger.error(f"Profile processing failed: {str(e)}")
            return False
    
    def run(self) -> bool:
        """Main execution method"""
        try:
            self.logger.info("Starting LinkedIn AI Agent Professionals Scraper")
            self.logger.info(f"Target: {self.config.MIN_FOLLOWERS}-{self.config.MAX_FOLLOWERS} followers")
            self.logger.info(f"Output file: {self.config.OUTPUT_CSV}")
            
            # Initialize scraper
            if not self.initialize():
                return False
            
            # Run comprehensive search
            profiles = self.run_comprehensive_search()
            
            if not profiles:
                self.logger.warning("No profiles found during search")
                return False
            
            # Process and save profiles
            success = self.process_and_save_profiles(profiles)
            
            # Cleanup
            if self.scraper:
                self.scraper.close()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Scraping operation failed: {str(e)}")
            if self.scraper:
                self.scraper.close()
            return False

def main():
    """Main entry point"""
    print("LinkedIn AI Agent Professionals Scraper")
    print("=" * 50)
    
    # Check if credentials are provided
    config = Config()
    if not config.LINKEDIN_EMAIL or not config.LINKEDIN_PASSWORD:
        print("ERROR: LinkedIn credentials not found!")
        print("Please create a .env file with:")
        print("LINKEDIN_EMAIL=your_email@example.com")
        print("LINKEDIN_PASSWORD=your_password")
        return False
    
    # Create and run orchestrator
    orchestrator = LinkedInScrapingOrchestrator()
    success = orchestrator.run()
    
    if success:
        print(f"\n✅ Scraping completed successfully!")
        print(f"📊 Check {config.OUTPUT_CSV} for the results")
        print(f"📋 Check scraping_summary.txt for detailed statistics")
    else:
        print("\n❌ Scraping failed. Check the logs for details.")
    
    return success

if __name__ == "__main__":
    main() 