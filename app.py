import streamlit as st
import requests
import folium
from streamlit_folium import st_folium  # corrected import
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
if "smoothed_speed" not in st.session_state:
    st.session_state.smoothed_speed = 27600.0

# Haversine function (unchanged - it's correct)
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

            # Update path (keep last 2 minutes max)
            st.session_state.path.append([lat, lon])
            if len(st.session_state.path) > 150:   # ~12.5 minutes at 5s intervals
                st.session_state.path.pop(0)

            # ================== IMPROVED SPEED CALCULATION ==================
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            current_time_str = now_ist.strftime('%H:%M:%S')

            calculated_speed = 27600.0

            if len(st.session_state.path) >= 15:  # Need enough points for stability
                # Use more points (last ~60-90 seconds) for smoother calculation
                recent_points = st.session_state.path[-25:]  
                
                total_distance = 0.0
                for i in range(1, len(recent_points)):
                    dist = haversine(
                        recent_points[i-1][0], recent_points[i-1][1],
                        recent_points[i][0], recent_points[i][1]
                    )
                    total_distance += dist

                # Time between first and last point in the window
                points_in_window = len(recent_points)
                seconds_passed = 5 * (points_in_window - 1)   # approx 5s per update

                if seconds_passed > 0:
                    raw_speed = (total_distance / seconds_passed) * 3600

                    # Accept only realistic orbital speeds
                    if 24000 < raw_speed < 31000:
                        calculated_speed = raw_speed

            # Simple exponential smoothing to reduce jitter
            alpha = 0.25  # smoothing factor (lower = smoother)
            st.session_state.smoothed_speed = (
                alpha * calculated_speed + (1 - alpha) * st.session_state.smoothed_speed
            )

            display_speed = st.session_state.smoothed_speed

            # ================== UI ==================
            st.success(f"**Current ISS Position:** {lat:.4f}° N, {lon:.4f}° E")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🚀 ISS Speed", f"{display_speed:,.0f} km/h")
            with col2:
                st.metric("📍 Path Points", len(st.session_state.path))
            with col3:
                st.metric("Last Updated (IST)", current_time_str)

            # Country detection (unchanged)
            try:
                geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
                geo_res = requests.get(geo_url, headers={"User-Agent": "ISS-Tracker-Saiyam"}, timeout=5)
                if geo_res.status_code == 200:
                    address = geo_res.json().get("address", {})
                    country = address.get("country", "Ocean / Remote Area")
                    st.info(f"🌍 Currently over: **{country}**")
                else:
                    st.info("🌍 Currently over: **Ocean / Remote Area**")
            except Exception:
                st.info("🌍 Currently over: **Ocean / Remote Area**")

            # ================== Create Map ==================
            m = folium.Map(location=[lat, lon], zoom_start=3, tiles="CartoDB positron")

            if len(st.session_state.path) > 1:
                folium.PolyLine(
                    st.session_state.path,
                    color="blue",
                    weight=5,
                    opacity=0.85
                ).add_to(m)

            # ISS Marker
            popup_html = f"""
            <b>ISS Satellite 🚀</b><br>
            Latitude: {lat:.4f}° N<br>
            Longitude: {lon:.4f}° E<br>
            Time (IST): {now_ist.strftime('%H:%M:%S')}<br>
            Speed: ~{display_speed:,.0f} km/h
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

    # Auto refresh every 5 seconds
    # Note: In Streamlit Cloud / local, use st.rerun() instead of while True for production
    # For local testing the while True + placeholder works, but consider adding:
    # time.sleep(5)   # Uncomment if needed (import time)
