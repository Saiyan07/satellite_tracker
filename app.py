import streamlit as st
import requests
import time
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
            if len(st.session_state.path) > 120:   # Keep last ~10 minutes
                st.session_state.path.pop(0)

            # ================== IMPROVED SPEED CALCULATION ==================
            speed_kmh = 27600.0  # Default approximate orbital speed

            if len(st.session_state.path) >= 5:
                recent_points = st.session_state.path[-10:]  # Use last 10 points for stability
                
                total_distance = 0.0
                for i in range(1, len(recent_points)):
                    dist = haversine(
                        recent_points[i-1][0], recent_points[i-1][1],
                        recent_points[i][0], recent_points[i][1]
                    )
                    total_distance += dist
                
                # Time passed in seconds = 5 seconds × number of intervals
                seconds_passed = 5 * (len(recent_points) - 1)
                calculated_speed = (total_distance / seconds_passed) * 3600  # km/h
                
                # Use calculated speed only if it looks realistic
                if 20000 < calculated_speed < 32000:
                    speed_kmh = calculated_speed
                    

                ist = pytz.timezone('Asia/Kolkata')
                current_time = datetime.now(ist).strftime('%H:%M:%S')

            # ================== UI ==================
            st.success(f"**Current ISS Position:** {lat:.4f}° N, {lon:.4f}° E")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🚀 ISS Speed", f"{speed_kmh:,.0f} km/h")
            with col2:
                st.metric("📍 Path Points", len(st.session_state.path))
            with col3:
                st.metric("Last Updated", current_time().strftime("%H:%M:%S"))

            # Try to detect current country/ocean
            try:
                geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
                geo_res = requests.get(geo_url, headers={"User-Agent": "ISS-Tracker-Saiyam"}, timeout=5)
                if geo_res.status_code == 200:
                    address = geo_res.json().get("address", {})
                    country = address.get("country", "Ocean / Remote Area")
                    st.info(f"🌍 Currently over: **{country}**")
            except:
                st.info("🌍 Currently over: **Ocean / Remote Area**")

            # ================== Create Map ==================
            m = folium.Map(location=[lat, lon], zoom_start=3, tiles="CartoDB positron")

            # Draw blue path trail
            if len(st.session_state.path) > 1:
                folium.PolyLine(
                    st.session_state.path,
                    color="blue",
                    weight=5,
                    opacity=0.85
                ).add_to(m)

            # ISS Marker with rich popup
            popup_html = f"""
            <b>ISS Satellite 🚀</b><br>
            Latitude: {lat:.4f}° N<br>
            Longitude: {lon:.4f}° E<br>
            Time: {datetime.now().strftime('%H:%M:%S')}<br>
            Speed: ~{speed_kmh:,.0f} km/h
            """
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="red", icon="rocket", prefix="fa")
            ).add_to(m)

            # Display map
            st_folium(m, use_container_width=True, height=650, returned_objects=[])

            st.caption("🔄 Auto-refreshes every 5 seconds • Data from Open Notify API")

        except Exception as e:
            st.error(f"⚠️ Error fetching ISS data: {e}")
            st.info("Retrying in 5 seconds...")

    # Auto-refresh every 5 seconds
    time.sleep(5)
    st.rerun()
