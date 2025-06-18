import os
import json
import logging
import requests
from flask import Flask, render_template, jsonify, request
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Directory to store earthquake data
DATA_DIR = os.getenv("DATA_DIR", "earthquakes_data")
os.makedirs(DATA_DIR, exist_ok=True)

# URLs and API keys
EARTHQUAKE_URL = "https://seismonepal.gov.np/earthquakes"
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")  # Add your Unsplash API key to .env
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"


def fetch_earthquake_data():
    """Fetch earthquake data from the specified URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        logging.info(f"Fetching data from {EARTHQUAKE_URL}")
        response = requests.get(EARTHQUAKE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        logging.info("Successfully fetched earthquake data")
        return response.text
    except requests.RequestException as e:
        logging.error(f"Failed to fetch earthquake data: {e}")
        return None


def parse_earthquake_data(html):
    """Parse earthquake data from HTML."""
    if not html:
        logging.error("No HTML content to parse")
        return []
        
    try:
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        if not table:
            logging.error("No table found in HTML")
            return []

        earthquakes = []
        rows = table.find_all('tr')[1:]  # Skip header row

        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 8:  # Ensure we have enough cells
                try:
                    # Parse date (format: "B.S.: YYYY-MM-DD A.D.: YYYY-MM-DD")
                    date_text = cells[0].text.strip()
                    date_parts = date_text.split('A.D.:')
                    date_bs = date_parts[0].replace('B.S.:', '').strip()
                    date_ad = date_parts[1].strip() if len(date_parts) > 1 else "Unknown"

                    # Parse time (format: "Local: HH:MM UTC: HH:MM")
                    time_text = cells[1].text.strip()
                    time_parts = time_text.split('UTC:')
                    time_local = time_parts[0].replace('Local:', '').strip()
                    time_utc = time_parts[1].strip() if len(time_parts) > 1 else "Unknown"

                    # Parse coordinates
                    latitude = float(cells[2].text.strip())
                    longitude = float(cells[3].text.strip())

                    # Parse magnitude (remove 'M' prefix if present)
                    magnitude_text = cells[4].text.strip()
                    magnitude = float(magnitude_text.replace('M', ''))

                    # Parse epicenter
                    epicenter = cells[5].text.strip()
                    # Remove BS/AD date if present in epicenter
                    if 'B.S.' in epicenter or 'A.D.' in epicenter:
                        epicenter = "Nepal"

                    # Get source
                    source = cells[7].text.strip() if len(cells) > 7 else "Nepal Seismological Center"

                    earthquake = {
                        'date_bs': date_bs,
                        'date_ad': date_ad,
                        'time_local': time_local,
                        'time_utc': time_utc,
                        'latitude': latitude,
                        'longitude': longitude,
                        'magnitude': magnitude,
                        'epicenter': epicenter,
                        'source': source,
                        'image_url': '/static/earthquake.jpg'  # Default image
                    }
                    earthquakes.append(earthquake)
                except Exception as e:
                    logging.error(f"Error parsing row: {e}")
                    continue

        # Sort by UTC time
        earthquakes.sort(key=lambda x: x['time_utc'], reverse=True)
        logging.info(f"Successfully parsed {len(earthquakes)} earthquakes")
        return earthquakes
    except Exception as e:
        logging.error(f"Error parsing earthquake data: {e}")
        return []


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
    """Store earthquake data in JSON files."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    for i, quake in enumerate(earthquakes, 1):
        filename = os.path.join(DATA_DIR, f"quake_{i}.json")
        with open(filename, 'w') as f:
            json.dump(quake, f, indent=4)


def get_all_earthquakes():
    """Get all stored earthquake data."""
    earthquakes = []
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json'):
                with open(os.path.join(DATA_DIR, filename), 'r') as f:
                    earthquakes.append(json.load(f))
    return sorted(earthquakes, key=lambda x: x['time_utc'], reverse=True)


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
    else:
        logging.warning("No valid earthquake data found to store")


# Schedule data fetching every 10 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_store_earthquake_data, 'interval', minutes=10)
scheduler.start()


@app.route('/')
def index():
    """Render the main page."""
    try:
        html = fetch_earthquake_data()
        earthquakes = parse_earthquake_data(html)
        logging.info(f"Rendering index page with {len(earthquakes)} earthquakes")
        return render_template('index.html', earthquakes=earthquakes)
    except Exception as e:
        logging.error(f"Error in index route: {e}")
        return render_template('index.html', earthquakes=[])


@app.route('/all-earthquakes')
def all_earthquakes():
    """Render the all earthquakes page."""
    try:
        html = fetch_earthquake_data()
        earthquakes = parse_earthquake_data(html)
        logging.info(f"Rendering all-earthquakes page with {len(earthquakes)} earthquakes")
        return render_template('all-earthquakes.html', earthquakes=earthquakes)
    except Exception as e:
        logging.error(f"Error in all_earthquakes route: {e}")
        return render_template('all-earthquakes.html', earthquakes=[])


@app.route('/get-earthquakes')
def get_earthquakes_api():
    """Serve earthquake data as JSON."""
    try:
        html = fetch_earthquake_data()
        earthquakes = parse_earthquake_data(html)
        logging.info(f"Serving {len(earthquakes)} earthquakes via API")
        return jsonify(earthquakes)
    except Exception as e:
        logging.error(f"Error in get_earthquakes_api route: {e}")
        return jsonify([])


@app.route('/refresh')
def refresh_data():
    """Manually trigger data refresh."""
    try:
        html = fetch_earthquake_data()
        earthquakes = parse_earthquake_data(html)
        return jsonify({"status": "success", "message": "Data refreshed successfully", "count": len(earthquakes)})
    except Exception as e:
        logging.error(f"Error in refresh_data route: {e}")
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    # Fetch data on startup
    fetch_and_store_earthquake_data()
    app.run(debug=True)
