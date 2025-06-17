import os
import json
import logging
import requests
import time
from flask import Flask, render_template, jsonify
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

app = Flask(__name__)

# URLs and API keys
EARTHQUAKE_URL = os.getenv("EARTHQUAKE_URL", "https://seismonepal.gov.np/earthquakes")
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

# In-memory storage for earthquake data
earthquake_data = {
    'data': [],
    'timestamp': None,
    'last_epicenter': None
}

def fetch_earthquake_data():
    """Fetch earthquake data from the source."""
    try:
        logging.info(f"Fetching earthquake data from {EARTHQUAKE_URL}")
        response = requests.get(EARTHQUAKE_URL, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if not table:
            logging.error("No table found in the response")
            return []
            
        rows = table.find_all('tr')[1:]  # Skip header row
        if not rows:
            logging.error("No earthquake data rows found")
            return []
            
        earthquakes = []
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) >= 8:
                    # Parse date and time
                    date_text = cells[0].text.strip()
                    time_text = cells[2].text.strip()
                    
                    # Extract BS and AD dates
                    bs_date = date_text.split("B.S.:")[1].split("A.D.:")[0].strip() if "B.S.:" in date_text else "Unknown"
                    ad_date = date_text.split("A.D.:")[1].strip() if "A.D.:" in date_text else "Unknown"
                    
                    # Extract local and UTC times
                    local_time = time_text.split("Local:")[1].split("UTC:")[0].strip() if "Local:" in time_text else "Unknown"
                    utc_time = time_text.split("UTC:")[1].strip() if "UTC:" in time_text else "Unknown"
                    
                    # Parse magnitude
                    try:
                        magnitude = float(cells[2].text.strip())
                    except ValueError:
                        magnitude = 0.0
                    
                    earthquake = {
                        'date_bs': bs_date,
                        'date_ad': ad_date,
                        'time_local': local_time,
                        'time_utc': utc_time,
                        'magnitude': magnitude,
                        'epicenter': cells[1].text.strip(),
                        'latitude': float(cells[3].text.strip()) if cells[3].text.strip() else 0.0,
                        'longitude': float(cells[4].text.strip()) if cells[4].text.strip() else 0.0,
                        'depth': cells[5].text.strip(),
                        'remarks': cells[6].text.strip(),
                        'source': cells[7].text.strip(),
                        'image_url': '/static/nep.png'  # Default image
                    }
                    earthquakes.append(earthquake)
            except Exception as e:
                logging.error(f"Error parsing earthquake row: {e}")
                continue
                
        logging.info(f"Successfully fetched {len(earthquakes)} earthquakes")
        return sorted(earthquakes, key=lambda x: x['date_ad'] + ' ' + x['time_utc'], reverse=True)
        
    except Exception as e:
        logging.error(f"Error fetching earthquake data: {e}")
        return []

def should_update_cache():
    """Check if cache should be updated based on time and data freshness."""
    if not earthquake_data['timestamp']:
        logging.info("Cache is empty, should update")
        return True
    
    current_time = time.time()
    cache_age = current_time - earthquake_data['timestamp']
    
    # Update if cache is older than 5 minutes
    should_update = cache_age > 300
    logging.info(f"Cache age: {cache_age:.2f}s, should update: {should_update}")
    return should_update

def update_cache():
    """Update the earthquake data cache."""
    global earthquake_data
    
    try:
        # Check if we need to update
        if not should_update_cache():
            logging.info("Using cached data")
            return earthquake_data['data']
        
        # Fetch new data
        logging.info("Fetching new earthquake data")
        earthquakes = fetch_earthquake_data()
        
        if not earthquakes:
            logging.error("No earthquakes retrieved after update")
            return earthquake_data['data'] or []
        
        # Update cache
        earthquake_data['data'] = earthquakes
        earthquake_data['timestamp'] = time.time()
        earthquake_data['last_epicenter'] = earthquakes[0]['epicenter'] if earthquakes else None
        
        logging.info(f"Cache updated with {len(earthquakes)} earthquakes")
        return earthquakes
    except Exception as e:
        logging.error(f"Error updating cache: {e}")
        return earthquake_data['data'] or []

@app.route('/')
def index():
    """Render the homepage with earthquake data."""
    try:
        earthquakes = update_cache()
        logging.info(f"Rendering index with {len(earthquakes)} earthquakes")
        return render_template('index.html', earthquakes=earthquakes)
    except Exception as e:
        logging.error(f"Error in index route: {e}")
        return render_template('index.html', earthquakes=[])

@app.route('/all-earthquakes')
def all_earthquakes():
    """Render the all earthquakes page."""
    try:
        earthquakes = update_cache()
        logging.info(f"Rendering all-earthquakes with {len(earthquakes)} earthquakes")
        return render_template('all-earthquakes.html', earthquakes=earthquakes)
    except Exception as e:
        logging.error(f"Error in all_earthquakes route: {e}")
        return render_template('all-earthquakes.html', earthquakes=[])

@app.route('/get-earthquakes')
def get_earthquakes():
    """API endpoint to get earthquake data."""
    try:
        earthquakes = update_cache()
        logging.info(f"API returning {len(earthquakes)} earthquakes")
        return jsonify(earthquakes)
    except Exception as e:
        logging.error(f"Error in get_earthquakes route: {e}")
        return jsonify([])

@app.route('/refresh')
def refresh_data():
    """Manual endpoint to refresh earthquake data."""
    try:
        global earthquake_data
        logging.info("Manual refresh requested")
        earthquakes = fetch_earthquake_data()
        
        if not earthquakes:
            logging.error("No earthquakes retrieved after manual refresh")
            return jsonify({"status": "error", "message": "No earthquakes retrieved"}), 500
        
        # Update cache
        earthquake_data['data'] = earthquakes
        earthquake_data['timestamp'] = time.time()
        earthquake_data['last_epicenter'] = earthquakes[0]['epicenter'] if earthquakes else None
        
        logging.info(f"Manual refresh completed with {len(earthquakes)} earthquakes")
        return jsonify({"status": "success", "message": "Data refreshed successfully"})
    except Exception as e:
        logging.error(f"Error in refresh_data route: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Initialize data on startup
try:
    logging.info("Initializing application")
    update_cache()
except Exception as e:
    logging.error(f"Error during initial data fetch: {e}")

# For local development
if __name__ == '__main__':
    app.run(debug=True)
