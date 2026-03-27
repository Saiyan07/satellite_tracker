import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime
import pytz
import time

# Page config
st.set_page_config(page_title="Live ISS Tracker", page_icon="🛰️", layout="wide")
st.title("🛰️ Live ISS Satellite Tracker")
st.markdown("### Real-time position and speed from Where The ISS At API")

# Session state
if "path" not in st.session_state:
    st.session_state.path = []

# Main logic
try:
    # Fetch data from better API
    response = requests.get("https://api.wheretheiss.at/v1/satellites/25544", timeout=10)
    response.raise_for_status()
    data = response.json()

    lat = float(data["latitude"])
    lon = float(data["longitude"])
    speed_kmh = float(data["velocity"])          # ← Direct real speed!
    altitude = float(data.get("altitude", 0))

    # Update path trail (keep last ~10 minutes)
    st.session_state.path.append([lat, lon])
    if len(st.session_state.path) > 120:
        st.session_state.path.pop(0)

    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    current_time_str = now_ist.strftime('%H:%M:%S')

    # UI
    st.success(f"**Current ISS Position:** {lat:.4f}° N, {lon:.4f}° E")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚀 ISS Speed", f"{speed_kmh:,.0f} km/h")
    with col2:
        st.metric("📍 Path Points", len(st.session_state.path))
    with col3:
        st.metric("🌌 Altitude", f"{altitude:.1f} km")
    with col4:
        st.metric("Last Updated (IST)", current_time_str)

    # Country / Location
    try:
        geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        geo_res = requests.get(geo_url, headers={"User-Agent": "ISS-Tracker-Saiyam"}, timeout=5)
        if geo_res.status_code == 200:
            country = geo_res.json().get("address", {}).get("country", "Ocean / Remote Area")
            st.info(f"🌍 Currently over: **{country}**")
        else:
            st.info("🌍 Currently over: **Ocean / Remote Area**")
    except:
        st.info("🌍 Currently over: **Ocean / Remote Area**")

    # Map
    m = folium.Map(location=[lat, lon], zoom_start=3, tiles="CartoDB positron")

    if len(st.session_state.path) > 1:
        folium.PolyLine(st.session_state.path, color="blue", weight=5, opacity=0.8).add_to(m)

    popup_html = f"""
    <b>ISS Satellite 🚀</b><br>
    Lat: {lat:.4f}° N<br>
    Lon: {lon:.4f}° E<br>
    Speed: {speed_kmh:,.0f} km/h<br>
    Altitude: {altitude:.1f} km<br>
    Time (IST): {current_time_str}
    """
    folium.Marker(
        [lat, lon],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color="red", icon="rocket", prefix="fa")
    ).add_to(m)

    st_folium(m, use_container_width=True, height=650, returned_objects=[])

    st.caption("🔄 Auto-refreshes every 5 seconds • Data from Where The ISS At API")

except Exception as e:
    st.error(f"⚠️ Error: {e}")
    st.info("Retrying...")

# ================== AUTO REFRESH ==================
time.sleep(5)
st.rerun()
