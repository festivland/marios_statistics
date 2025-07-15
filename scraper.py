#!/usr/bin/env python3
"""
Bookly Appointments Scraper
Logs into WordPress admin and exports appointment data as CSV.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import json


class BooklyAppointmentsScraper:
    """Scraper for Bookly appointments from WordPress admin."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the scraper with configuration."""
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        })
        self.csrf_token: Optional[str] = None
    
    def login(self) -> bool:
        """Log into WordPress admin."""
        print("🔐 Logging into WordPress...")
        
        login_data = {
            'log': self.config['username'],
            'pwd': self.config['password'],
            'rememberme': 'forever',
            'wp-submit': 'Log In',
            'redirect_to': f"{self.config['base_url']}/wp-admin/",
        }
        
        try:
            resp = self.session.post(
                f"{self.config['base_url']}/wp-login.php",
                data=login_data,
                allow_redirects=True,
                timeout=30
            )
            resp.raise_for_status()
            
            # Check login success
            success_indicators = ['dashboard', 'wp-admin', 'welcome', 'howdy']
            if any(indicator in resp.text.lower() for indicator in success_indicators):
                print("✅ Login successful!")
                return True
            elif any(error in resp.text.lower() for error in ['error', 'incorrect']):
                print("❌ Login failed - check credentials")
                return False
            else:
                print("⚠️  Login status unclear, continuing...")
                return True
                
        except requests.RequestException as e:
            print(f"❌ Login request failed: {e}")
            return False
    
    def get_csrf_token(self) -> Optional[str]:
        """Extract CSRF token from appointments page."""
        print("🔍 Getting CSRF token...")
        
        try:
            appointments_url = f"{self.config['base_url']}/wp-admin/admin.php?page=bookly-appointments"
            resp = self.session.get(appointments_url, timeout=30)
            resp.raise_for_status()
            
            # Check if redirected to login
            if 'wp-login' in resp.url:
                print("❌ Redirected to login - authentication failed")
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Look for various token names
            token_names = ['csrf_token', '_wpnonce', 'bookly_csrf_token', '_token', 'nonce']
            
            for token_name in token_names:
                # Check input fields
                token_input = soup.find('input', {'name': token_name})
                if token_input and token_input.get('value'):
                    token = token_input['value']
                    print(f"✅ Found CSRF token: {token[:20]}...")
                    return token
                
                # Check meta tags
                meta_token = soup.find('meta', {'name': token_name})
                if meta_token and meta_token.get('content'):
                    token = meta_token['content']
                    print(f"✅ Found CSRF token in meta: {token[:20]}...")
                    return token
            
            # Look for nonce in input names
            nonce_inputs = soup.find_all('input', {'name': lambda x: x and 'nonce' in x.lower()})
            for inp in nonce_inputs:
                if inp.get('value'):
                    token = inp['value']
                    print(f"✅ Found nonce token: {token[:20]}...")
                    return token
            
            print("⚠️  No CSRF token found, proceeding without it")
            return None
            
        except requests.RequestException as e:
            print(f"❌ Failed to get CSRF token: {e}")
            return None
    
    def get_export_fields(self, date_filter: str = "any") -> Dict[str, str]:
        """Get the export fields configuration."""
        # Exact fields as specified by the user
        return {
            'action': 'bookly_pro_export_appointments',
            'delimiter': ',',
            'exp[id]': 'on',
            'exp[start_date]': 'on',
            'exp[staff_name]': 'on',
            'exp[customer_full_name]': 'on',
            'exp[customer_phone]': 'on',
            'exp[customer_email]': 'on',
            'exp[service_title]': 'on',
            'exp[service_duration]': 'on',
            'exp[status]': 'on',
            'exp[payment]': 'on',
            'exp[notes]': 'on',
            'exp[created_date]': 'on',
            'exp[customer_address]': 'on',
            'exp[customer_birthday]': 'on',
            'exp[online_meeting]': 'on',
            'exp[custom_fields_23664]': 'on',
            'exp[custom_fields_19734]': 'on',
            'filter': json.dumps({
                "id": "",
                "date": date_filter,
                "created_date": "any",
                "staff": None,
                "customer": None,
                "service": None,
                "status": ["pending", "approved", "cancelled", "rejected", "done"]
            })
        }
    
    def export_appointments(self) -> Optional[bytes]:
        """Export appointments as CSV with two optimized requests."""
        print("📊 Exporting appointments with optimized dual requests...")
        
        export_url = f"{self.config['base_url']}/wp-admin/admin-ajax.php"
        
        # First request with date filter "any"
        print("🔄 Making first request (date: any)...")
        payload_1 = self.get_export_fields("any")
        if self.csrf_token:
            payload_1['csrf_token'] = self.csrf_token
        
        try:
            resp_1 = self.session.post(export_url, data=payload_1, timeout=60)
            resp_1.raise_for_status()
            print(f"✅ First request successful ({len(resp_1.content)} bytes)")
        except requests.RequestException as e:
            print(f"❌ First export request failed: {e}")
            return None
        
        # Second request with date filter "null"
        print("🔄 Making second request (date: null)...")
        payload_2 = self.get_export_fields("null")
        if self.csrf_token:
            payload_2['csrf_token'] = self.csrf_token
        
        try:
            resp_2 = self.session.post(export_url, data=payload_2, timeout=60)
            resp_2.raise_for_status()
            print(f"✅ Second request successful ({len(resp_2.content)} bytes)")
        except requests.RequestException as e:
            print(f"❌ Second export request failed: {e}")
            return None
        
        # Merge the two CSV responses
        try:
            merged_csv = self.merge_csv_responses(resp_1.content, resp_2.content)
            if merged_csv:
                print(f"✅ Successfully merged responses ({len(merged_csv)} bytes total)")
                return merged_csv
            else:
                print("⚠️  Merge failed, returning first response")
                return resp_1.content
        except Exception as e:
            print(f"❌ Error merging responses: {e}")
            print("⚠️  Returning first response as fallback")
            return resp_1.content
    
    def merge_csv_responses(self, csv_1: bytes, csv_2: bytes) -> Optional[bytes]:
        """Merge two CSV responses, removing duplicates based on ID."""
        try:
            # Save temporary files for debugging
            with open('temp_export_1.csv', 'wb') as f:
                f.write(csv_1)
            with open('temp_export_2.csv', 'wb') as f:
                f.write(csv_2)
            
            # Read both CSV files
            df1 = pd.read_csv('temp_export_1.csv')
            df2 = pd.read_csv('temp_export_2.csv')
            
            print(f"📊 First CSV: {len(df1)} rows, {len(df1.columns)} columns")
            print(f"📊 Second CSV: {len(df2)} rows, {len(df2.columns)} columns")
            
            # Check if both have ID columns
            if 'ID' in df1.columns and 'ID' in df2.columns:
                # Concatenate and remove duplicates based on ID
                merged_df = pd.concat([df1, df2], ignore_index=True)
                merged_df = merged_df.drop_duplicates(subset=['ID'], keep='first')
                merged_df = merged_df.sort_values('ID')
                
                print(f"📊 Merged CSV: {len(merged_df)} rows (duplicates removed)")
                
                # Convert back to CSV bytes
                csv_string = merged_df.to_csv(index=False)
                
                # Clean up temporary files
                os.remove('temp_export_1.csv')
                os.remove('temp_export_2.csv')
                
                return csv_string.encode('utf-8')
            else:
                print("⚠️  No ID column found, cannot merge properly")
                # Clean up temporary files
                os.remove('temp_export_1.csv')
                os.remove('temp_export_2.csv')
                return None
                
        except Exception as e:
            print(f"❌ Error in merge_csv_responses: {e}")
            # Clean up temporary files if they exist
            for temp_file in ['temp_export_1.csv', 'temp_export_2.csv']:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            return None
    
    def save_csv(self, csv_data: bytes, filename: str = 'Appointments.csv') -> bool:
        """Save CSV data to file."""
        try:
            # Remove existing file
            if os.path.exists(filename):
                os.remove(filename)
            
            # Save new data
            with open(filename, 'wb') as f:
                f.write(csv_data)
            
            # Show file info
            file_size = os.path.getsize(filename)
            mod_time = datetime.fromtimestamp(os.path.getmtime(filename))
            
            print(f"💾 Saved to {filename}")
            print(f"📁 File size: {file_size:,} bytes")
            print(f"🕐 Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show data preview if it's valid CSV
            try:
                df = pd.read_csv(filename)
                print(f"📊 Total appointments: {len(df)}")
                print(f"📋 Columns: {len(df.columns)}")
                
                if len(df) > 0:
                    print(f"\n📈 First few rows:")
                    print(df.head(3).to_string())
                    
            except Exception as e:
                print(f"⚠️  Could not parse CSV for preview: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save CSV: {e}")
            return False
    
    def run(self) -> bool:
        """Run the complete scraping process."""
        print("🚀 Starting Bookly appointments scraper...")
        
        # Step 1: Login
        if not self.login():
            return False
        
        # Step 2: Get CSRF token
        self.csrf_token = self.get_csrf_token()
        
        # Step 3: Export appointments
        csv_data = self.export_appointments()
        if not csv_data:
            return False
        
        # Step 4: Save CSV
        if not self.save_csv(csv_data):
            return False
        
        print("✅ Scraping completed successfully!")
        return True


def load_config() -> Dict[str, Any]:
    """Load configuration from config file or environment variables."""
    config_file = 'scraper_config.json'
    
    # First, try to load from config file
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"📄 Loaded config from {config_file}")
            
            # Validate required fields
            required_fields = ['base_url', 'username', 'password']
            missing_fields = [field for field in required_fields if field not in config or not config[field]]
            
            if missing_fields:
                print(f"❌ Missing required fields in {config_file}: {missing_fields}")
                print("Please ensure your config file contains: base_url, username, password")
                sys.exit(1)
                
            return config
            
        except Exception as e:
            print(f"❌ Could not load config file {config_file}: {e}")
            print("Please check that the file exists and contains valid JSON")
            sys.exit(1)
    
    # Fallback to environment variables if config file doesn't exist
    print(f"⚠️  Config file {config_file} not found, trying environment variables...")
    config = {
        'base_url': os.getenv('WP_BASE_URL'),
        'username': os.getenv('WP_USERNAME'),
        'password': os.getenv('WP_PASSWORD'),
    }
    
    # Validate environment variables
    missing_env_vars = [var for var in ['WP_BASE_URL', 'WP_USERNAME', 'WP_PASSWORD'] 
                       if not os.getenv(var)]
    
    if missing_env_vars:
        print(f"❌ Missing environment variables: {missing_env_vars}")
        print(f"Please create {config_file} with your credentials or set environment variables")
        print(f"\nExample {config_file}:")
        print('''{
    "base_url": "https://your-site.com",
    "username": "your-username",
    "password": "your-password"
}''')
        sys.exit(1)
    
    print("📄 Loaded config from environment variables")
    return config


def main():
    """Main entry point."""
    try:
        config = load_config()
        scraper = BooklyAppointmentsScraper(config)
        
        success = scraper.run()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()