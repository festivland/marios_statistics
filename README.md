# Marios Statistics - WordPress Appointments Dashboard

This project includes a WordPress appointments scraper and a Streamlit dashboard for analytics.

## Setup

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure credentials by creating a `.env` file:
   ```bash
   cp env.example .env
   ```
   Then edit `.env` and fill in your actual credentials

## Usage

### Running the Scraper
```bash
python scraper.py
```

The script will:
1. Log into the WordPress site
2. Extract a CSRF token from the appointments page
3. Export appointments data for July 2025
4. Save the data as `Appointments.csv`

### Running the Dashboard
```bash
streamlit run dashboard.py
```

Or use the provided script:
```bash
./run_dashboard.sh
```

The dashboard provides:
- Real-time analytics and visualizations
- Data filtering and export capabilities
- Authentication via environment variables

## Configuration

### For Local Development

Create a `.env` file (copy from `env.example`) with the following variables:

**WordPress Scraper:**
- `WP_BASE_URL` - Your WordPress site URL
- `WP_USERNAME` - Your WordPress admin username  
- `WP_PASSWORD` - Your WordPress admin password

**Dashboard Authentication:**
- `DASHBOARD_USERNAME` - Your dashboard login username
- `DASHBOARD_PASSWORD` - Your dashboard login password

### For Streamlit Cloud Deployment

In your Streamlit Cloud app settings, add these secrets in TOML format:

```toml
# WordPress Scraper Configuration (not used in cloud, but kept for consistency)
WP_BASE_URL = "https://your-wordpress-site.com"
WP_USERNAME = "your_wordpress_username"
WP_PASSWORD = "your_wordpress_password"

# Dashboard Authentication
DASHBOARD_USERNAME = "your_dashboard_username"
DASHBOARD_PASSWORD = "your_dashboard_password"
```

## Notes

- Both applications use only environment variables for configuration (no JSON config files)
- Make sure you have valid WordPress admin credentials for the scraper
- The scraper exports appointments with "approved" status from July 2025
- You can modify the filter parameters in the script to change the date range or status
- The CSV file will be saved in the same directory as the script
- All authentication is secure and uses environment variables only 