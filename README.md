# WordPress Appointments Scraper

This Python script logs into a WordPress site and exports appointments data as a CSV file.

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

3. Edit `scraper.py` and replace the placeholder credentials:
   - Replace `YOUR_USER` with your WordPress username
   - Replace `YOUR_PASSWORD` with your WordPress password

## Usage

Run the script:
```bash
python scraper.py
```

The script will:
1. Log into the WordPress site
2. Extract a CSRF token from the appointments page
3. Export appointments data for July 2025
4. Save the data as `Appointments.csv`

## Notes

- Make sure you have valid WordPress admin credentials
- The script is configured to export appointments with "approved" status from July 2025
- You can modify the filter parameters in the script to change the date range or status
- The CSV file will be saved in the same directory as the script 