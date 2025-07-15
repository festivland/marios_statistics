# Bookly Appointments Scraper

A simplified Python script to scrape appointment data from WordPress Bookly plugin.

## Features

- ✅ Clean, object-oriented design
- ✅ Proper error handling and logging
- ✅ Configuration file support
- ✅ Environment variable support
- ✅ Single CSV export (no more merging complexity)
- ✅ Better debugging output
- ✅ Timeout handling
- ✅ Data preview

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure credentials:**
   
   **Option A: Configuration file (recommended)**
   ```bash
   cp scraper_config.json.example scraper_config.json
   # Edit scraper_config.json with your credentials
   ```
   
   **Option B: Environment variables**
   ```bash
   export WP_USERNAME="your_username"
   export WP_PASSWORD="your_password"
   ```

## Usage

Simply run the script:
```bash
python scraper.py
```

The script will:
1. 🔐 Log into WordPress admin
2. 🔍 Get CSRF token (if needed)
3. 📊 Export appointments data (2 optimized requests)
4. 🔄 Merge responses and remove duplicates
5. 💾 Save to `Appointments.csv`
6. 📈 Show data preview

## Configuration

Create `scraper_config.json`:
```json
{
    "base_url": "https://your-site.com",
    "username": "your_wp_username",
    "password": "your_wp_password"
}
```

## Output

- `Appointments.csv` - Main export file
- `export_debug.html` - Debug file (if export fails)

## What's Improved

- **Optimized**: Two targeted requests with different date filters
- **Organized**: Clean class-based structure
- **Configurable**: Easy credential management
- **Robust**: Better error handling and timeouts
- **Smart Merging**: Automatic duplicate removal based on ID
- **Informative**: Clear progress messages and emojis
- **Maintainable**: Well-documented code with type hints

## Troubleshooting

If the script fails:
1. Check your credentials in the config file
2. Look at the debug output messages
3. Check `export_debug.html` if export fails
4. Ensure your WordPress site is accessible 