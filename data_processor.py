import pandas as pd
import numpy as np
from typing import List, Dict
import logging
from datetime import datetime
import os

class DataProcessor:
    def __init__(self, output_file: str):
        self.output_file = output_file
        self.logger = logging.getLogger(__name__)
        
    def save_profiles_to_csv(self, profiles: List[Dict]) -> bool:
        """Save profiles to CSV file"""
        try:
            if not profiles:
                self.logger.warning("No profiles to save")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(profiles)
            
            # Ensure all required columns exist
            required_columns = [
                'name', 'headline', 'location', 'profile_url', 'company',
                'follower_count', 'keyword_matched', 'confidence_score',
                'profile_completeness', 'scraped_date'
            ]
            
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
            
            # Reorder columns
            df = df[required_columns]
            
            # Save to CSV
            df.to_csv(self.output_file, index=False, encoding='utf-8')
            
            self.logger.info(f"Saved {len(profiles)} profiles to {self.output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save profiles to CSV: {str(e)}")
            return False
    
    def load_existing_profiles(self) -> pd.DataFrame:
        """Load existing profiles from CSV if file exists"""
        try:
            if os.path.exists(self.output_file):
                df = pd.read_csv(self.output_file)
                self.logger.info(f"Loaded {len(df)} existing profiles from {self.output_file}")
                return df
            else:
                self.logger.info("No existing CSV file found")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Failed to load existing profiles: {str(e)}")
            return pd.DataFrame()
    
    def deduplicate_profiles(self, new_profiles: List[Dict], existing_df: pd.DataFrame = None) -> List[Dict]:
        """Remove duplicate profiles based on profile URL"""
        if not new_profiles:
            return []
        
        # Convert new profiles to DataFrame
        new_df = pd.DataFrame(new_profiles)
        
        # Load existing profiles if not provided
        if existing_df is None:
            existing_df = self.load_existing_profiles()
        
        # Combine existing and new profiles
        if not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df
        
        # Remove duplicates based on profile_url
        deduplicated_df = combined_df.drop_duplicates(subset=['profile_url'], keep='first')
        
        # Convert back to list of dictionaries
        deduplicated_profiles = deduplicated_df.to_dict('records')
        
        removed_count = len(combined_df) - len(deduplicated_df)
        self.logger.info(f"Removed {removed_count} duplicate profiles")
        
        return deduplicated_profiles
    
    def filter_by_quality(self, profiles: List[Dict], min_confidence: float = 0.7, min_completeness: float = 0.6) -> List[Dict]:
        """Filter profiles by quality scores"""
        if not profiles:
            return []
        
        filtered_profiles = []
        
        for profile in profiles:
            confidence = profile.get('confidence_score', 0)
            completeness = profile.get('profile_completeness', 0)
            
            if confidence >= min_confidence and completeness >= min_completeness:
                filtered_profiles.append(profile)
        
        removed_count = len(profiles) - len(filtered_profiles)
        self.logger.info(f"Filtered out {removed_count} low-quality profiles")
        
        return filtered_profiles
    
    def sort_by_quality(self, profiles: List[Dict]) -> List[Dict]:
        """Sort profiles by quality score (confidence + completeness)"""
        if not profiles:
            return []
        
        for profile in profiles:
            confidence = profile.get('confidence_score', 0)
            completeness = profile.get('profile_completeness', 0)
            profile['quality_score'] = confidence + completeness
        
        # Sort by quality score (descending)
        sorted_profiles = sorted(profiles, key=lambda x: x.get('quality_score', 0), reverse=True)
        
        return sorted_profiles
    
    def generate_summary_report(self, profiles: List[Dict]) -> Dict:
        """Generate summary statistics for the profiles"""
        if not profiles:
            return {}
        
        df = pd.DataFrame(profiles)
        
        summary = {
            'total_profiles': len(profiles),
            'unique_companies': df['company'].nunique() if 'company' in df.columns else 0,
            'unique_locations': df['location'].nunique() if 'location' in df.columns else 0,
            'avg_confidence_score': df['confidence_score'].mean() if 'confidence_score' in df.columns else 0,
            'avg_profile_completeness': df['profile_completeness'].mean() if 'profile_completeness' in df.columns else 0,
            'avg_follower_count': df['follower_count'].mean() if 'follower_count' in df.columns else 0,
            'keyword_distribution': df['keyword_matched'].value_counts().to_dict() if 'keyword_matched' in df.columns else {}
        }
        
        # Follower count distribution
        if 'follower_count' in df.columns:
            follower_counts = df['follower_count'].dropna()
            summary['follower_ranges'] = {
                '1k-2k': len(follower_counts[(follower_counts >= 1000) & (follower_counts < 2000)]),
                '2k-5k': len(follower_counts[(follower_counts >= 2000) & (follower_counts < 5000)]),
                '5k-10k': len(follower_counts[(follower_counts >= 5000) & (follower_counts <= 10000)])
            }
        
        return summary
    
    def export_summary_report(self, summary: Dict, filename: str = "scraping_summary.txt"):
        """Export summary report to text file"""
        try:
            with open(filename, 'w') as f:
                f.write("LinkedIn Scraping Summary Report\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write(f"Total Profiles Found: {summary.get('total_profiles', 0)}\n")
                f.write(f"Unique Companies: {summary.get('unique_companies', 0)}\n")
                f.write(f"Unique Locations: {summary.get('unique_locations', 0)}\n")
                f.write(f"Average Confidence Score: {summary.get('avg_confidence_score', 0):.2f}\n")
                f.write(f"Average Profile Completeness: {summary.get('avg_profile_completeness', 0):.2f}\n")
                f.write(f"Average Follower Count: {summary.get('avg_follower_count', 0):.0f}\n\n")
                
                f.write("Follower Count Distribution:\n")
                follower_ranges = summary.get('follower_ranges', {})
                for range_name, count in follower_ranges.items():
                    f.write(f"  {range_name}: {count} profiles\n")
                
                f.write("\nKeyword Distribution:\n")
                keyword_dist = summary.get('keyword_distribution', {})
                for keyword, count in keyword_dist.items():
                    f.write(f"  {keyword}: {count} profiles\n")
            
            self.logger.info(f"Summary report exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to export summary report: {str(e)}")
    
    def validate_csv_structure(self, csv_file: str) -> bool:
        """Validate CSV file structure and data quality"""
        try:
            df = pd.read_csv(csv_file)
            
            # Check required columns
            required_columns = [
                'name', 'headline', 'location', 'profile_url', 'company',
                'follower_count', 'keyword_matched', 'confidence_score',
                'profile_completeness', 'scraped_date'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns: {missing_columns}")
                return False
            
            # Check data quality
            total_rows = len(df)
            non_empty_names = len(df[df['name'].notna() & (df['name'] != '')])
            non_empty_urls = len(df[df['profile_url'].notna() & (df['profile_url'] != '')])
            
            if non_empty_names < total_rows * 0.9:
                self.logger.warning("More than 10% of profiles have empty names")
            
            if non_empty_urls < total_rows * 0.9:
                self.logger.warning("More than 10% of profiles have empty URLs")
            
            self.logger.info(f"CSV validation passed: {total_rows} profiles")
            return True
            
        except Exception as e:
            self.logger.error(f"CSV validation failed: {str(e)}")
            return False 