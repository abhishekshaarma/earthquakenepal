import os
import json
import logging
import requests
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
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")  # Add your Unsplash API key to .env
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"


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

    for index, row in enumerate(rows[1:], start=1):  # Skip header
        cells = [cell.get_text(strip=True) for cell in row.find_all("td")]

        if len(cells) >= 7:
            try:
                bs_date = cells[1].split("B.S.:")[1].split("A.D.:")[0].strip() if "B.S.:" in cells[1] else "Unknown"
                ad_date = cells[1].split("A.D.:")[1].strip() if "A.D.:" in cells[1] else "Unknown"
                local_time = cells[2].split("Local:")[1].split("UTC:")[0].strip() if "Local:" in cells[2] else "Unknown"
                utc_time = cells[2].split("UTC:")[1].strip() if "UTC:" in cells[2] else "Unknown"
                latitude = cells[3] if len(cells) > 3 else "Unknown"
                longitude = cells[4] if len(cells) > 4 else "Unknown"
                magnitude = cells[5] if len(cells) > 5 else "Unknown"
                epicenter = cells[6] if len(cells) > 6 else "Unknown"

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

    return earthquakes

def get_epicenter_image(epicenter):
    """Fetch an image URL for the given epicenter using Unsplash API."""
    if not UNSPLASH_API_KEY:
        logging.warning("Unsplash API key is missing.")
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
    """Store earthquake data as JSON files."""
    for index, quake in enumerate(earthquakes, start=1):
        file_path = os.path.join(DATA_DIR, f"quake_{index}.json")
        with open(file_path, 'w') as f:
            json.dump(quake, f, indent=4)

def fetch_and_store_earthquake_data():
    """Fetch, parse, and store earthquake data."""
    html = fetch_earthquake_data()
    if html:
        earthquakes = parse_earthquake_data(html)
        store_earthquake_data(earthquakes)
        logging.info(f"Stored {len(earthquakes)} earthquakes.")

# Schedule data fetching every 10 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_store_earthquake_data, 'interval', minutes=10)
scheduler.start()

@app.route('/')
def index():
    """Render the homepage with earthquake data."""
    fetch_and_store_earthquake_data()

    # Read all earthquake files
    earthquake_cards = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(DATA_DIR, filename), 'r') as f:
                data = json.load(f)
                earthquake_cards.append(data)

    return render_template('index.html', earthquakes=earthquake_cards)



@app.route('/all-earthquakes')
def all_earthquakes():
    # Read all earthquake files
    earthquake_cards = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(DATA_DIR, filename), 'r') as f:
                data = json.load(f)
                earthquake_cards.append(data)

    return render_template('all-earthquakes.html', earthquakes=earthquake_cards)


@app.route('/get-earthquakes')
def get_earthquakes():
    """Serve earthquake data as JSON."""
    earthquakes = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(DATA_DIR, filename), 'r') as f:
                data = json.load(f)
                earthquakes.append(data)
    return jsonify(earthquakes)

if __name__ == '__main__':
    app.run(debug=True)