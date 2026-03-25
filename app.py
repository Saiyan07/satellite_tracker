import streamlit as st
import requests
import time
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="ISS Tracker", page_icon=" ", layout="wide")

st.title(" Live ISS Satellite Tracker")
st.markdown("### Watch the International Space Station moving in real-time with its path trail")

# Initializing session state for path
if "path" not in st.session_state:
    st.session_state.path = []

# Helps in auto-refresh every 5 seconds
placeholder = st.empty()

while True:
    with placeholder.container():
        try:
            response = requests.get("http://api.open-notify.org/iss-now.json")
            data = response.json()

            lat = float(data["iss_position"]["latitude"])
            lon = float(data["iss_position"]["longitude"])

            st.success(f" Current ISS Position: **{lat:.4f}° N, {lon:.4f}° E**")

            # Add to path
            st.session_state.path.append([lat, lon])
            if len(st.session_state.path) > 80:   # Keep last ~7 minutes
                st.session_state.path.pop(0)

            # # dosen't create but loads tiles of map from free open sourcee (i can't afford premium :) )
            m = folium.Map(location=[lat, lon], zoom_start=3)

            # Path trail
            if len(st.session_state.path) > 1:
                folium.PolyLine(st.session_state.path, color="blue", weight=4, opacity=0.7).add_to(m)

            # ISS marker
            folium.Marker(
                [lat, lon],
                popup=f"ISS Right Now!\nLat: {lat:.4f}° N\nLon: {lon:.4f}° E",
                icon=folium.Icon(color="red", icon="rocket", prefix="fa")
            ).add_to(m)

            # Display map in Streamlit
            st_folium(m, width=1200, height=600)

            st.caption("Map auto-refreshes every 5 seconds • Data from Open Notify API")

        except Exception as e:
            st.error(f" Error fetching data: {e}")

    time.sleep(5)
