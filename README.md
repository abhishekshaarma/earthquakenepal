# Earthquake Watch

## Overview
Earthquake Watch is a real-time earthquake monitoring web application that provides users with the latest seismic activity data in Nepal. The application fetches earthquake data, displays real-time information on a map, and provides emergency contacts for disaster preparedness.

## Features
- **Real-time Earthquake Monitoring**: Fetches and displays recent earthquakes with magnitude, location, and timestamps.
- **Interactive Map**: Uses Leaflet.js to visualize earthquake epicenters.
- **Emergency Contacts**: Provides essential helpline numbers for disaster response in Nepal.
- **Articles & Resources**: Links to important earthquake-related articles and preparedness guides.
- **Automated Data Fetching**: Uses web scraping to update earthquake data at regular intervals.

## Technologies Used
- **Frontend**: HTML, CSS (TailwindCSS), JavaScript
- **Backend**: Flask (Python), BeautifulSoup (Web Scraping), APScheduler
- **Database**: JSON-based storage for earthquake data
- **APIs**:
  - Leaflet.js for mapping
  - Unsplash API for fetching images

## Installation & Setup
### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- Flask
- Requests
- BeautifulSoup4
- APScheduler
- dotenv (for environment variables)

### Setup Instructions
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/earthquake-watch.git
   cd earthquake-watch
   ```
2. Create a virtual environment and activate it:
   ```sh
   python -m venv venv
   source venv/bin/activate  # For Linux/macOS
   venv\Scripts\activate  # For Windows
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   Create a `.env` file and add:
   ```env
   DATA_DIR=earthquakes_data
   EARTHQUAKE_URL=https://seismonepal.gov.np/earthquakes
   UNSPLASH_API_KEY=your_unsplash_api_key
   ```
5. Run the Flask application:
   ```sh
   python app.py
   ```
6. Access the application at `http://127.0.0.1:5000/`

## Usage
- Open the homepage to view recent earthquakes and their details.
- Click "View All Earthquakes" to access the complete list.
- Check the interactive earthquake map.
- Visit the articles section for preparedness and research.
- Use emergency contacts for immediate help.
![earthquake 1](https://github.com/user-attachments/assets/96a50aae-684b-45e2-9096-2a7f95d3b25b)
![earthquke 2](https://github.com/user-attachments/assets/6d04ac03-a983-4217-99f4-3c1d8bd1e0a5)
![earthquke 3](https://github.com/user-attachments/assets/98f73afa-07cd-4fb1-a893-cb74cb2c69b5)
![earthquke 4](https://github.com/user-attachments/assets/9d5231de-fe14-49b4-89ed-89f9add30755)


## Scheduled Tasks
- The application automatically scrapes earthquake data every 10 minutes using APScheduler.
- Image URLs for earthquake epicenters are fetched from Unsplash.



