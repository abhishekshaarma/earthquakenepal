import os
import json
import logging
import requests
import time
from flask import Flask, render_template, jsonify
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Directory to store earthquake data
DATA_DIR = os.getenv("DATA_DIR", "earthquakes_data")
os.makedirs(DATA_DIR, exist_ok=True)

# URLs and API keys
EARTHQUAKE_URL = os.getenv("EARTHQUAKE_URL", "https://seismonepal.gov.np/earthquakes")
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

# Cache for earthquake data with timestamp
earthquake_cache = {
    'data': None,
    'timestamp': None,
    'last_epicenter': None
}

def should_update_cache():
    """Check if cache should be updated based on time and data freshness."""
    if not earthquake_cache['timestamp']:
        return True
    
    current_time = time.time()
    cache_age = current_time - earthquake_cache['timestamp']
    
    # Update if cache is older than 5 minutes
    return cache_age > 300

def fetch_latest_earthquake():
    """Fetch the latest earthquake data from the source."""
    try:
        response = requests.get(EARTHQUAKE_URL, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if not table:
            return None
            
        rows = table.find_all('tr')[1:]  # Skip header row
        if not rows:
            return None
            
        # Get the first row (most recent earthquake)
        cells = rows[0].find_all('td')
        if len(cells) >= 8:
            epicenter = cells[1].text.strip()
            return epicenter
            
    except Exception as e:
        logging.error(f"Error fetching latest earthquake: {e}")
    
    return None

def update_cache():
    """Update the earthquake data cache."""
    global earthquake_cache
    
    try:
        # Check if we need to update
        if not should_update_cache():
            return earthquake_cache['data']
        
        # Fetch latest earthquake to check for updates
        latest_epicenter = fetch_latest_earthquake()
        
        # If we have cached data and the latest earthquake hasn't changed, don't update
        if (earthquake_cache['data'] and 
            earthquake_cache['last_epicenter'] and 
            latest_epicenter == earthquake_cache['last_epicenter']):
            return earthquake_cache['data']
        
        # Fetch and store new data
        fetch_and_store_earthquake_data()
        earthquakes = get_all_earthquakes()
        
        # Update cache
        earthquake_cache['data'] = earthquakes
        earthquake_cache['timestamp'] = time.time()
        earthquake_cache['last_epicenter'] = latest_epicenter
        
        return earthquakes
    except Exception as e:
        logging.error(f"Error updating cache: {e}")
        # Return cached data if available, otherwise empty list
        return earthquake_cache['data'] or []

def fetch_earthquake_data():
    """Fetch earthquake data from the specified URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(EARTHQUAKE_URL, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.text
    except requests.RequestException as e:
        logging.error(f"Failed to fetch earthquake data: {e}")
        return None


def parse_earthquake_data(html):
    """Parse earthquake data from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    if not tables:
        logging.warning("No tables found on the page.")
        return []

    rows = tables[0].find_all("tr")
    earthquakes = []

    def safe_float(value, default=0.0):
        try:
            return float(value) if value.strip() else default
        except ValueError:
            return default

    for index, row in enumerate(rows[1:], start=1):  # Skip header
        cells = [cell.get_text(strip=True) for cell in row.find_all("td")]

        if len(cells) >= 7:
            try:
                bs_date = cells[1].split("B.S.:")[1].split("A.D.:")[0].strip() if "B.S.:" in cells[1] else "Unknown"
                ad_date = cells[1].split("A.D.:")[1].strip() if "A.D.:" in cells[1] else "Unknown"
                local_time = cells[2].split("Local:")[1].split("UTC:")[0].strip() if "Local:" in cells[2] else "Unknown"
                utc_time = cells[2].split("UTC:")[1].strip() if "UTC:" in cells[2] else "Unknown"
                latitude = safe_float(cells[3]) if len(cells) > 3 else 0.0
                longitude = safe_float(cells[4]) if len(cells) > 4 else 0.0
                magnitude = safe_float(cells[5]) if len(cells) > 5 else 0.0
                epicenter = cells[6] if len(cells) > 6 else "Unknown"

                # Skip entries with invalid or unknown data
                if ad_date == "Unknown" or magnitude == 0.0 or epicenter == "Unknown":
                    logging.warning(f"Skipping row {index} due to incomplete data")
                    continue

                earthquake_info = {
                    "date_bs": bs_date,
                    "date_ad": ad_date,
                    "time_local": local_time,
                    "time_utc": utc_time,
                    "latitude": float(latitude) if latitude != "Unknown" else 0.0,
                    "longitude": float(longitude) if longitude != "Unknown" else 0.0,
                    "magnitude": float(magnitude) if magnitude != "Unknown" else 0.0,
                    "epicenter": epicenter,
                    "image_url": get_epicenter_image(epicenter)  # Fetch image URL for the epicenter
                }

                earthquakes.append(earthquake_info)
            except Exception as e:
                logging.error(f"Failed to parse row {index}: {cells} - Error: {e}")
        else:
            logging.warning(f"Row {index} skipped due to insufficient columns: {cells}")
    
    # Sort earthquakes by date, most recent first
    sorted_earthquakes = sort_earthquakes_by_date(earthquakes)
    return sorted_earthquakes


def sort_earthquakes_by_date(earthquakes):
    """Sort earthquakes by date and time, most recent first."""
    # Filter out entries with Unknown dates first
    valid_earthquakes = [quake for quake in earthquakes if quake['date_ad'] != "Unknown" and quake['time_utc'] != "Unknown"]
    
    # Then sort the valid entries
    return sorted(valid_earthquakes, key=lambda x: x['date_ad'] + ' ' + x['time_utc'], reverse=True)


def get_epicenter_image(epicenter):
    """Fetch an image URL for the given epicenter using Unsplash API."""
    if not UNSPLASH_API_KEY or epicenter == "Unknown":
        logging.warning(f"Unsplash API key missing or invalid epicenter: {epicenter}")
        return "/static/default.jpg"  # Fallback to a default image

    try:
        response = requests.get(
            UNSPLASH_API_URL,
            params={"query": epicenter, "per_page": 1},
            headers={"Authorization": f"Client-ID {UNSPLASH_API_KEY}"}
        )
        response.raise_for_status()
        data = response.json()
        if data["results"]:
            return data["results"][0]["urls"]["small"]  # Use the small-sized image URL
        else:
            logging.warning(f"No image found for epicenter: {epicenter}")
            return "/static/default.jpg"  # Fallback to a default image
    except requests.RequestException as e:
        logging.error(f"Failed to fetch image for {epicenter}: {e}")
        return "/static/default.jpg"  # Fallback to a default image


def store_earthquake_data(earthquakes):
    """Store earthquake data as JSON files, avoiding duplicates."""
    # Skip if no valid earthquakes were found
    if not earthquakes:
        logging.warning("No valid earthquakes to store")
        return
        
    # Clear existing files first to avoid duplicates
    for file in os.listdir(DATA_DIR):
        if file.endswith('.json'):
            os.remove(os.path.join(DATA_DIR, file))
    
    # Store new data
    for index, quake in enumerate(earthquakes, start=1):
        file_path = os.path.join(DATA_DIR, f"quake_{index}.json")
        with open(file_path, 'w') as f:
            json.dump(quake, f, indent=4)


def fetch_and_store_earthquake_data():
    """Fetch, parse, and store earthquake data."""
    html = fetch_earthquake_data()
    if html:
        earthquakes = parse_earthquake_data(html)
        if earthquakes:  # Only store if we have valid earthquakes
            store_earthquake_data(earthquakes)
            logging.info(f"Stored {len(earthquakes)} earthquakes.")
        else:
            logging.warning("No valid earthquakes found to store")


def get_all_earthquakes():
    """Read all earthquake data from stored files."""
    earthquakes = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(DATA_DIR, filename), 'r') as f:
                    data = json.load(f)
                    # Additional validation to filter out incomplete data
                    if data['date_ad'] != "Unknown" and data['magnitude'] > 0.0:
                        earthquakes.append(data)
            except (json.JSONDecodeError, KeyError) as e:
                logging.error(f"Error reading file {filename}: {e}")
    
    # Sort by date just to ensure ordering is consistent
    return sort_earthquakes_by_date(earthquakes)


@app.route('/')
def index():
    """Render the homepage with earthquake data."""
    try:
        earthquakes = update_cache()
        return render_template('index.html', earthquakes=earthquakes)
    except Exception as e:
        logging.error(f"Error in index route: {e}")
        return render_template('index.html', earthquakes=[])


@app.route('/all-earthquakes')
def all_earthquakes():
    """Render the all earthquakes page."""
    try:
        earthquakes = update_cache()
        return render_template('all-earthquakes.html', earthquakes=earthquakes)
    except Exception as e:
        logging.error(f"Error in all_earthquakes route: {e}")
        return render_template('all-earthquakes.html', earthquakes=[])


@app.route('/get-earthquakes')
def get_earthquakes():
    """API endpoint to get earthquake data."""
    try:
        earthquakes = update_cache()
        return jsonify(earthquakes)
    except Exception as e:
        logging.error(f"Error in get_earthquakes route: {e}")
        return jsonify([])


@app.route('/refresh')
def refresh_data():
    """Manual endpoint to refresh earthquake data."""
    try:
        global earthquake_cache
        fetch_and_store_earthquake_data()
        earthquakes = get_all_earthquakes()
        
        # Update cache
        earthquake_cache['data'] = earthquakes
        earthquake_cache['timestamp'] = time.time()
        earthquake_cache['last_epicenter'] = fetch_latest_earthquake()
        
        return jsonify({"status": "success", "message": "Data refreshed successfully"})
    except Exception as e:
        logging.error(f"Error in refresh_data route: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Initialize data on startup
try:
    update_cache()
except Exception as e:
    logging.error(f"Error during initial data fetch: {e}")

# For local development
if __name__ == '__main__':
    app.run(debug=True)
