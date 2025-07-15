#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Check if Appointments.csv exists
if [ ! -f "Appointments.csv" ]; then
    echo "⚠️  Appointments.csv not found!"
    echo "Please run the scraper first: python scraper.py"
    exit 1
fi

echo "🚀 Launching Bachata King Festival Dashboard..."
echo "📊 Dashboard will open in your browser at http://localhost:8501"
echo "🛑 Press Ctrl+C to stop the dashboard"
echo ""

# Launch the dashboard
streamlit run dashboard.py 