#!/usr/bin/env python3
"""
Bachata King Festival - Analytics Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os
import subprocess
import shutil
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv


class AppointmentsDashboard:
    """Main dashboard class for festival analytics."""
    
    def __init__(self):
        """Initialize the dashboard."""
        self.df: Optional[pd.DataFrame] = None
        self.original_df: Optional[pd.DataFrame] = None
        self.setup_page()
    
    def setup_page(self):
        """Configure Streamlit page settings and styling."""
        st.set_page_config(
            page_title="Bachata King Festival - Dashboard",
            page_icon="💃",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
            .main-header {
                font-size: 2.5rem;
                font-weight: bold;
                color: #e74c3c;
                text-align: center;
                margin-bottom: 2rem;
            }
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 10px;
                color: white;
                text-align: center;
            }
            .filter-section {
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            }
            .stDataFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def load_users(self) -> Dict[str, str]:
        """Load users from Streamlit secrets, .env file, or system env vars."""
        users = {}
        try:
            # Priority 1: Try Streamlit secrets (for Streamlit Cloud)
            try:
                username = st.secrets["DASHBOARD_USERNAME"]
                password = st.secrets["DASHBOARD_PASSWORD"]
                if username and password:
                    users[username] = password
                    return users
            except (KeyError, FileNotFoundError):
                # Streamlit secrets not available, continue to environment variables
                pass
            
            # Priority 2: Load environment variables from .env file if it exists (for local development)
            load_dotenv()
            
            # Get credentials from environment variables
            username = os.getenv('DASHBOARD_USERNAME')
            password = os.getenv('DASHBOARD_PASSWORD')
            
            if username and password:
                users[username] = password
                return users
            else:
                # Show detailed error message about missing configuration
                missing_vars = []
                if not username:
                    missing_vars.append('DASHBOARD_USERNAME')
                if not password:
                    missing_vars.append('DASHBOARD_PASSWORD')
                
                st.error(f"❌ Missing required credentials: {', '.join(missing_vars)}")
                st.error("Please set up your dashboard credentials using one of these methods:")
                st.info("""
                **For Streamlit Cloud:**
                Add these secrets in your Streamlit Cloud app settings:
                ```toml
                DASHBOARD_USERNAME = "your_username"
                DASHBOARD_PASSWORD = "your_password"
                ```
                
                **For local development:**
                1. Create a .env file with:
                   ```
                   DASHBOARD_USERNAME=your_username
                   DASHBOARD_PASSWORD=your_password
                   ```
                2. Or set system environment variables:
                   ```
                   export DASHBOARD_USERNAME=your_username
                   export DASHBOARD_PASSWORD=your_password
                   ```
                """)
        except Exception as e:
            st.error(f"Error loading user credentials: {e}")
        return users
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user credentials."""
        users = self.load_users()
        return users.get(username) == password
    
    def show_login_form(self):
        """Display login form."""
        st.markdown('<div class="main-header">🎭 Bachata King Festival</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; margin-bottom: 2rem;"><h3>🔐 Login to Access Dashboard</h3></div>', unsafe_allow_html=True)
        
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form"):
                st.markdown("### Login Credentials")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                login_button = st.form_submit_button("🚀 Login", use_container_width=True)
                
                if login_button:
                    if username and password:
                        if self.authenticate_user(username, password):
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.success("✅ Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password!")
                    else:
                        st.warning("⚠️ Please enter both username and password!")
            
            # Show setup information
            with st.expander("ℹ️ Setup Information"):
                st.markdown("""
                **Configuration Required:**
                
                Create a `.env` file with your credentials:
                ```
                DASHBOARD_USERNAME=your_username
                DASHBOARD_PASSWORD=your_password
                ```
                
                You can copy `env.example` to `.env` and fill in your credentials.
                
                Contact your administrator if you don't have access credentials.
                """)
    
    def show_logout_option(self):
        """Show logout option in sidebar."""
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"👤 **Logged in as:** {st.session_state.get('username', 'Unknown')}")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.rerun()
    
    def check_authentication(self) -> bool:
        """Check if user is authenticated."""
        return st.session_state.get('authenticated', False)
    
    def load_data(self) -> bool:
        """Load and process the appointments data."""
        try:
            file_path = 'Appointments.csv'
            if not os.path.exists(file_path):
                st.error("❌ Appointments.csv not found! Please run the scraper first.")
                return False
            
            # Show file info
            mod_time = os.path.getmtime(file_path)
            file_size = os.path.getsize(file_path)
            st.info(f"📁 Data updated: {datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')} | Size: {file_size:,} bytes")
            
            # Load data
            self.original_df = pd.read_csv(file_path)
            self.df = self.original_df.copy()
            
            # Clean and process data
            self.process_data()
            
            st.success(f"✅ Loaded {len(self.df)} appointments with {len(self.df.columns)} columns")
            return True
            
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            return False
    
    def process_data(self):
        """Clean and process the raw data."""
        if self.df is None:
            return
        
        # Process date columns
        date_columns = [col for col in self.df.columns if 'date' in col.lower() or 'created' in col.lower()]
        for col in date_columns:
            self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
        
        # Process payment columns
        payment_columns = [col for col in self.df.columns if 'payment' in col.lower() or 'price' in col.lower()]
        for col in payment_columns:
            if self.df[col].dtype == 'object':
                # Extract numeric values from payment strings
                self.df[f'{col}_numeric'] = self.df[col].str.extract(r'€?(\d+\.?\d*)', expand=False).astype(float)
        
        # Process duration columns
        duration_columns = [col for col in self.df.columns if 'duration' in col.lower()]
        for col in duration_columns:
            if self.df[col].dtype in ['int64', 'float64']:
                self.df[f'{col}_hours'] = self.df[col] / 60  # Convert minutes to hours
    
    def get_column_options(self, pattern: str) -> List[str]:
        """Get available columns matching a pattern."""
        if self.df is None:
            return []
        return [col for col in self.df.columns if pattern.lower() in col.lower()]
    
    def get_best_column(self, patterns: List[str]) -> Optional[str]:
        """Get the best available column from a list of patterns."""
        if self.df is None:
            return None
        
        for pattern in patterns:
            matches = self.get_column_options(pattern)
            if matches:
                return matches[0]
        return None
    
    def create_sidebar_filters(self):
        """Create sidebar filters for data filtering."""
        if self.df is None:
            return
        
        # Filter summary at the top
        self.show_filter_summary()
        st.sidebar.markdown("---")
        
        # Date filter
        date_col = self.get_best_column(['appointment date', 'date', 'start'])
        if date_col:
            self.create_date_filter(date_col)
        
        # Status filter
        status_col = self.get_best_column(['status'])
        if status_col:
            self.create_status_filter(status_col)
        
        # Service filter
        service_col = self.get_best_column(['service'])
        if service_col:
            self.create_service_filter(service_col)
        
        # Role filter
        role_col = self.get_best_column(['role'])
        if role_col:
            self.create_role_filter(role_col)
        
        # Country filter
        country_col = self.get_best_column(['country'])
        if country_col:
            self.create_multiselect_filter("🌍 Country", country_col)
        
        # Price filter
        price_col = self.get_best_column(['price'])
        if price_col:
            self.create_price_filter(price_col)
        
        # Clear filters button
        st.sidebar.markdown("---")
        if st.sidebar.button("🗑️ Clear All Filters", type="primary"):
            st.rerun()
    
    def create_date_filter(self, date_col: str):
        """Create date range filter with no default filtering."""
        date_data = self.df[date_col].dropna()
        if len(date_data) == 0:
            return
        
        min_date = date_data.min().date()
        max_date = date_data.max().date()
        
        date_range = st.sidebar.date_input(
            f"📅 {date_col.title()} Range (Optional)",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key=f"date_filter_{date_col}",
            help="Leave as default to show all appointments, or adjust to filter by date range."
        )
        
        # Only apply filter if user has changed from the full range
        if len(date_range) == 2 and (date_range[0] != min_date or date_range[1] != max_date):
            self.df = self.df[
                (self.df[date_col].dt.date >= date_range[0]) & 
                (self.df[date_col].dt.date <= date_range[1])
            ]
    
    def create_status_filter(self, status_col: str):
        """Create status multiselect filter with all possible booking statuses."""
        # Get actual statuses from current data
        actual_statuses = set(self.df[status_col].dropna().unique())
        
        # Define all known possible statuses from booking systems
        all_known_statuses = {
            'Approved', 'Pending', 'Cancelled', 'Rejected', 'Done', 
            'Confirmed', 'No-show', 'Rescheduled', 'Completed', 
            'In Progress', 'Waiting', 'Draft', 'Expired'
        }
        
        # Combine actual statuses with known statuses
        all_statuses = sorted(list(actual_statuses.union(all_known_statuses)))
        
        if len(actual_statuses) == 0:
            return
        
        # Show info about current data vs all options
        if len(actual_statuses) < len(all_statuses):
            st.sidebar.info(f"📊 Current data has: {', '.join(sorted(actual_statuses))}")
        
        selected_statuses = st.sidebar.multiselect(
            f"📊 {status_col.title()} (Optional)",
            options=all_statuses,
            default=[],  # No default selection - show all data
            key=f"status_filter_{status_col}",
            help="Select specific statuses to filter, or leave empty to show all appointments."
        )
        
        if selected_statuses:
            # Only apply filter for statuses that actually exist in the data
            valid_selected = [s for s in selected_statuses if s in actual_statuses]
            if valid_selected:
                self.df = self.df[self.df[status_col].isin(valid_selected)]
            else:
                # If no valid statuses selected, show empty result
                self.df = self.df[self.df[status_col].isin([])]
    
    def create_service_filter(self, service_col: str):
        """Create service multiselect filter with only services that exist in the data."""
        # Get actual services from current data
        actual_services = self.df[service_col].dropna().unique()
        
        if len(actual_services) == 0:
            return
        
        # Sort services alphabetically for better UX
        sorted_services = sorted(actual_services)
        
        selected_services = st.sidebar.multiselect(
            f"🎯 {service_col.title()} (Optional)",
            options=sorted_services,
            default=[],  # No default selection - show all data
            key=f"service_filter_{service_col}",
            help="Select specific services to filter, or leave empty to show all appointments."
        )
        
        if selected_services:
            self.df = self.df[self.df[service_col].isin(selected_services)]
    
    def create_role_filter(self, role_col: str):
        """Create role multiselect filter for dance roles."""
        # Get actual roles from current data (excluding nulls for the filter options)
        actual_roles = self.df[role_col].dropna().unique()
        
        if len(actual_roles) == 0:
            return
        
        # Sort roles in a logical order for dance context
        role_order = ['Leader', 'Follower', 'Both']
        sorted_roles = [role for role in role_order if role in actual_roles]
        # Add any other roles not in the predefined order
        other_roles = [role for role in actual_roles if role not in role_order]
        sorted_roles.extend(sorted(other_roles))
        
        selected_roles = st.sidebar.multiselect(
            f"💃 {role_col.title()} (Optional)",
            options=sorted_roles,
            default=[],  # No default selection - show all data
            key=f"role_filter_{role_col}",
            help="Select specific dance roles to filter, or leave empty to show all appointments."
        )
        
        if selected_roles:
            self.df = self.df[self.df[role_col].isin(selected_roles)]
    
    def create_multiselect_filter(self, label: str, column: str):
        """Create a generic multiselect filter."""
        values = self.df[column].dropna().unique()
        if len(values) == 0:
            return
        
        selected_values = st.sidebar.multiselect(
            f"{label} (Optional)",
            options=sorted(values),
            default=[],  # No default selection - show all data
            key=f"filter_{column}",
            help="Select specific values to filter, or leave empty to show all appointments."
        )
        
        if selected_values:
            self.df = self.df[self.df[column].isin(selected_values)]
    
    def create_price_filter(self, price_col: str):
        """Create price range filter."""
        numeric_col = f"{price_col}_numeric"
        if numeric_col not in self.df.columns:
            return
        
        price_data = self.df[numeric_col].dropna()
        if len(price_data) == 0:
            return
        
        min_price = float(price_data.min())
        max_price = float(price_data.max())
        
        price_range = st.sidebar.slider(
            "💰 Price Range (€) - Optional",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price),
            step=10.0,
            key=f"price_filter_{price_col}",
            help="Leave as default to show all prices, or adjust to filter by price range."
        )
        
        if price_range[0] != min_price or price_range[1] != max_price:
            self.df = self.df[
                (self.df[numeric_col] >= price_range[0]) & 
                (self.df[numeric_col] <= price_range[1])
            ]
    
    def show_filter_summary(self):
        """Show filter summary in sidebar."""
        if self.original_df is None:
            return
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("**📊 Filter Summary**")
        
        original_count = len(self.original_df)
        filtered_count = len(self.df)
        
        if filtered_count < original_count:
            st.sidebar.warning(f"Showing {filtered_count} of {original_count} appointments")
            st.sidebar.caption("🔍 Filters are active. Clear filters to see all data.")
        else:
            st.sidebar.success(f"Showing all {filtered_count} appointments")
            st.sidebar.caption("🌟 No filters applied")
    
    def refresh_data(self):
        """Safely refresh data by running the scraper."""
        try:
            # Create backup of current CSV file
            csv_file = 'Appointments.csv'
            backup_file = 'Appointments_backup.csv'
            
            # Show progress
            with st.spinner("🔄 Running scraper to fetch latest data..."):
                # Backup existing file if it exists
                if os.path.exists(csv_file):
                    shutil.copy2(csv_file, backup_file)
                    st.info("📁 Backed up existing data")
                
                # Run the scraper
                result = subprocess.run(
                    ['python', 'scraper.py'], 
                    capture_output=True, 
                    text=True, 
                    timeout=300  # 5 minute timeout
                )
                
                # Check if scraper succeeded
                if result.returncode == 0:
                    # Verify the new CSV file exists and is valid
                    if os.path.exists(csv_file):
                        try:
                            # Test if the new CSV is readable
                            test_df = pd.read_csv(csv_file)
                            if len(test_df) > 0:
                                # Success! Remove backup and reload data
                                if os.path.exists(backup_file):
                                    os.remove(backup_file)
                                
                                st.success("✅ Data refreshed successfully!")
                                st.info(f"📊 New data contains {len(test_df)} appointments")
                                
                                # Reload the data in the dashboard
                                self.load_data()
                                st.rerun()
                            else:
                                raise ValueError("New CSV file is empty")
                        except Exception as e:
                            raise ValueError(f"New CSV file is invalid: {e}")
                    else:
                        raise FileNotFoundError("Scraper did not create CSV file")
                else:
                    raise subprocess.CalledProcessError(result.returncode, "scraper.py", result.stderr)
                    
        except subprocess.TimeoutExpired:
            st.error("⏰ Scraper timed out after 5 minutes")
            self.restore_backup(csv_file, backup_file)
            
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Scraper failed with error code {e.returncode}")
            if e.stderr:
                st.error(f"Error details: {e.stderr}")
            self.restore_backup(csv_file, backup_file)
            
        except Exception as e:
            st.error(f"❌ Error refreshing data: {str(e)}")
            self.restore_backup(csv_file, backup_file)
    
    def restore_backup(self, csv_file: str, backup_file: str):
        """Restore backup file if something went wrong."""
        try:
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, csv_file)
                os.remove(backup_file)
                st.warning("⚠️ Restored previous data due to error")
            else:
                st.warning("⚠️ No backup available to restore")
        except Exception as e:
            st.error(f"❌ Failed to restore backup: {e}")
    
    def show_key_metrics(self):
        """Display key metrics in the main area."""
        if self.df is None or len(self.df) == 0:
            return
        
        st.subheader("📊 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 Total Appointments", len(self.df))
        
        with col2:
            # Calculate revenue
            revenue_col = self.get_best_column(['payment', 'price'])
            if revenue_col:
                numeric_col = f"{revenue_col}_numeric"
                if numeric_col in self.df.columns:
                    total_revenue = self.df[numeric_col].sum()
                    st.metric("💰 Total Revenue", f"€{total_revenue:,.2f}")
                else:
                    st.metric("💰 Total Revenue", "N/A")
            else:
                st.metric("💰 Total Revenue", "N/A")
        
        with col3:
            # Average payment
            revenue_col = self.get_best_column(['payment', 'price'])
            if revenue_col:
                numeric_col = f"{revenue_col}_numeric"
                if numeric_col in self.df.columns:
                    avg_payment = self.df[numeric_col].mean()
                    st.metric("📈 Average Payment", f"€{avg_payment:.2f}")
                else:
                    st.metric("📈 Average Payment", "N/A")
            else:
                st.metric("📈 Average Payment", "N/A")
        
        with col4:
            # Unique customers
            email_col = self.get_best_column(['email'])
            if email_col:
                unique_customers = self.df[email_col].nunique()
                st.metric("👥 Unique Customers", unique_customers)
            else:
                st.metric("👥 Unique Customers", len(self.df))
    
    def show_charts(self):
        """Display analytics charts."""
        if self.df is None or len(self.df) == 0:
            return
        
        # Header with refresh button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("📈 Analytics")
        with col2:
            if st.button("🔄 Refresh Data", type="primary", help="Run scraper to get latest data"):
                self.refresh_data()
        

        # Row 1: Geographic and Service analysis
        col1, col2 = st.columns(2)
        
        with col1:
            self.create_country_chart()
        
        with col2:
            self.create_service_chart()

        # Row 2: Time series and Status distribution
        col1, col2 = st.columns(2)
        
        with col1:
            self.create_timeline_chart()
        
        with col2:
            self.create_status_chart()
        
        
        # Row 3: Role analysis
        col1, col2 = st.columns(2)
        
        with col1:
            self.create_role_chart()
        
        with col2:
            # Placeholder for future chart
            pass
        
        # Row 4: Revenue analysis
        self.create_revenue_charts()
    
    def create_timeline_chart(self):
        """Create appointments timeline chart."""
        date_col = self.get_best_column(['appointment date', 'date', 'created'])
        if not date_col:
            st.info("No date information available")
            return
        
        st.markdown("**📅 Appointments Over Time**")
        
        # Group by date
        daily_counts = self.df.groupby(self.df[date_col].dt.date).size().reset_index()
        daily_counts.columns = ['Date', 'Count']
        
        if len(daily_counts) > 0:
            fig = px.line(daily_counts, x='Date', y='Count', 
                         title="Daily Appointments", markers=True)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data available")
    
    def create_status_chart(self):
        """Create status distribution chart."""
        status_col = self.get_best_column(['status'])
        if not status_col:
            st.info("No status information available")
            return
        
        st.markdown("**📊 Status Distribution**")
        
        status_counts = self.df[status_col].value_counts()
        if len(status_counts) > 0:
            fig = px.pie(values=status_counts.values, names=status_counts.index,
                        title="Status Distribution")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available")
    
    def create_country_chart(self):
        """Create country distribution chart."""
        country_col = self.get_best_column(['country'])
        if not country_col:
            st.info("No country information available")
            return
        
        country_counts = self.df[country_col].value_counts()
        num_countries = len(country_counts)
        
        st.markdown(f"**🌍 All Countries ({num_countries} countries)**")
        
        if len(country_counts) > 0:
            fig = px.bar(x=country_counts.values, y=country_counts.index,
                        orientation='h', title=f"All Countries ({num_countries} countries)")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No country data available")
    
    def create_service_chart(self):
        """Create service distribution chart."""
        service_col = self.get_best_column(['service'])
        if not service_col:
            st.info("No service information available")
            return
        
        st.markdown("**🎯 Service Distribution**")
        
        service_counts = self.df[service_col].value_counts()
        if len(service_counts) > 0:
            # Create truncated labels for x-axis display
            truncated_labels = [name[:20] + '...' if len(name) > 20 else name for name in service_counts.index]
            
            # Create the bar chart
            fig = px.bar(x=truncated_labels, y=service_counts.values,
                        title="Services Booked")
            
            # Update hover template to show full service name
            fig.update_traces(
                hovertemplate='<b>%{customdata}</b><br>Count: %{y}<extra></extra>',
                customdata=service_counts.index
            )
            
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No service data available")
    
    def create_role_chart(self):
        """Create role distribution chart."""
        role_col = self.get_best_column(['role'])
        if not role_col:
            st.info("No role information available")
            return
        
        st.markdown("**💃 Role Distribution**")
        
        # Get role counts including nulls for complete picture
        role_counts = self.df[role_col].value_counts(dropna=False)
        
        # Replace NaN with 'Not Specified' for better display
        role_counts.index = role_counts.index.fillna('Not Specified')
        
        if len(role_counts) > 0:
            # Use colors that make sense for dance roles
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            
            fig = px.pie(values=role_counts.values, names=role_counts.index,
                        title="Dance Role Distribution",
                        color_discrete_sequence=colors)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show summary stats
            total_with_roles = self.df[role_col].notna().sum()
            total_appointments = len(self.df)
            
            st.caption(f"📊 {total_with_roles} of {total_appointments} appointments have role data")
        else:
            st.info("No role data available")
    
    def create_revenue_charts(self):
        """Create revenue analysis charts."""
        revenue_col = self.get_best_column(['payment', 'price'])
        if not revenue_col:
            return
        
        numeric_col = f"{revenue_col}_numeric"
        if numeric_col not in self.df.columns:
            return
        
        st.markdown("**💰 Revenue Analysis**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue by country
            country_col = self.get_best_column(['country'])
            if country_col:
                revenue_by_country = self.df.groupby(country_col)[numeric_col].sum().sort_values(ascending=False).head(10)
                if len(revenue_by_country) > 0:
                    fig = px.bar(x=revenue_by_country.index, y=revenue_by_country.values,
                               title="Revenue by Country (Top 10)")
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Revenue over time
            date_col = self.get_best_column(['created', 'date'])
            if date_col:
                daily_revenue = self.df.groupby(self.df[date_col].dt.date)[numeric_col].sum().reset_index()
                daily_revenue.columns = ['Date', 'Revenue']
                if len(daily_revenue) > 0:
                    fig = px.line(daily_revenue, x='Date', y='Revenue',
                                title="Daily Revenue", markers=True)
                    st.plotly_chart(fig, use_container_width=True)
    
    def show_data_table(self):
        """Display the data table with export functionality."""
        if self.df is None or len(self.df) == 0:
            return
        
        st.subheader("📋 Appointments Data")
        
        # Display options
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.dataframe(self.df, use_container_width=True, height=400)
        
        with col2:
            st.markdown("**Export Options**")
            
            # Download button
            csv = self.df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"appointments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
            
            # Show data info
            st.info(f"📊 {len(self.df)} appointments\n📋 {len(self.df.columns)} columns")
    
    def run(self):
        """Run the main dashboard."""
        # Check authentication first
        if not self.check_authentication():
            self.show_login_form()
            return
        
        # Show logout option in sidebar
        self.show_logout_option()
        
        # Header
        st.markdown('<h1 class="main-header">💃 Bachata King Festival - Dashboard</h1>', 
                   unsafe_allow_html=True)
        
        # Load data
        if not self.load_data():
            st.markdown("""
            ### 🚀 Getting Started
            
            1. **Run the scraper** to get your data:
               ```bash
               python scraper.py
               ```
            
            2. **Refresh this page** once the data is available.
            """)
            return
        
        # Create filters
        self.create_sidebar_filters()
        
        # Check if we have data after filtering
        if self.df is None or len(self.df) == 0:
            st.warning("⚠️ No data available with current filters. Try adjusting your filters.")
            return
        
        # Show main content
        self.show_key_metrics()
        st.markdown("---")
        self.show_charts()
        st.markdown("---")
        self.show_data_table()
        
        # Footer
        st.markdown("---")
        st.markdown("*Dashboard for Bachata King Festival appointment management*")


def main():
    """Main entry point."""
    dashboard = AppointmentsDashboard()
    dashboard.run()


if __name__ == "__main__":
    main() 