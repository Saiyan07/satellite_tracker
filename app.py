import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import math
from datetime import datetime
import pytz

# Page configuration
st.set_page_config(
    page_title="Live ISS Tracker",
    page_icon="🛰️",
    layout="wide"
)

st.title("🛰️ Live ISS Satellite Tracker")
st.markdown("### Watch the International Space Station moving in real-time with its path trail")

# Initialize session state
if "path" not in st.session_state:
    st.session_state.path = []

# Haversine function (correct)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Auto-refresh container
placeholder = st.empty()

while True:
    with placeholder.container():
        try:
            # Fetch live ISS position
            response = requests.get("http://api.open-notify.org/iss-now.json", timeout=10)
            response.raise_for_status()
            data = response.json()

            lat = float(data["iss_position"]["latitude"])
            lon = float(data["iss_position"]["longitude"])

            # Update path
            st.session_state.path.append([lat, lon])
            if len(st.session_state.path) > 120:
                st.session_state.path.pop(0)

            # ================== IMPROVED SPEED CALCULATION ==================
            speed_kmh = 27600.0  # Default approximate orbital speed (fallback)

            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            current_time_str = now_ist.strftime('%H:%M:%S')

            # Calculate speed only when we have enough points
            if len(st.session_state.path) >= 10:
                recent_points = st.session_state.path[-20:]   # Use last 20 points for better stability (100 seconds)
                
                total_distance = 0.0
                for i in range(1, len(recent_points)):
                    dist = haversine(
                        recent_points[i-1][0], recent_points[i-1][1],
                        recent_points[i][0],   recent_points[i][1]
                    )
                    total_distance += dist

                # Time passed: 5 seconds per interval
                seconds_passed = 5 * (len(recent_points) - 1)
                
                if seconds_passed > 0:
                    calculated_speed = (total_distance / seconds_passed) * 3600
                    
                    # Accept calculated speed only if it's realistic (ISS orbital speed range)
                    if 20000*

