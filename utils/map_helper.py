import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import requests
from typing import Tuple, Optional
from streamlit_js_eval import streamlit_js_eval



def request_location_permission():
    """
    Requests location access from the user's browser and stores coordinates in session_state.
    """
    st.subheader("📍 Location Access Required")

    result = streamlit_js_eval(
        js_expressions="navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}))",
        key="get_location",
        want_output=True,
    )

    if result and isinstance(result, dict) and "lat" in result:
        st.session_state["user_location"] = result
        st.success("✅ Location access granted.")
        return True
    elif result is False:
        st.error("❌ Location access denied. Please enter your location manually.")
        return False
    else:
        st.info("Waiting for location permission...")
        return None

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Geocodes an address to get latitude and longitude using Nominatim (OpenStreetMap).
    Free service, no API key required.
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "FirstAid-AI-Agent/1.0"  # Required by Nominatim
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                return (lat, lon)
        return None
    except Exception as e:
        st.debug(f"Geocoding error for {address}: {e}")
        return None


def get_navigation_url(lat: float, lon: float, name: str = None) -> str:
    """
    Generates a navigation URL that opens the device's default map application.
    Works with Google Maps, Apple Maps, Waze, and other map apps.
    
    The URL format used is Google Maps Directions API, which:
    - Opens Google Maps app on mobile if installed
    - Falls back to Apple Maps on iOS if Google Maps not installed
    - Works on desktop browsers (opens Google Maps web)
    - Compatible with Waze and other map apps that handle Google Maps URLs
    """
    # Google Maps Directions URL - works across platforms and opens native app if installed
    # Using 'dir' parameter for turn-by-turn navigation with destination
    if name:
        # URL encode the name for better compatibility
        import urllib.parse
        encoded_name = urllib.parse.quote(name)
        return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&destination_place_id=&q={encoded_name}"
    else:
        return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"


def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """
    Reverse geocodes coordinates to get an address using Nominatim (OpenStreetMap).
    Free service, no API key required.
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        headers = {
            "User-Agent": "FirstAid-AI-Agent/1.0"  # Required by Nominatim
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and "display_name" in data:
                return data["display_name"]
        return None
    except Exception as e:
        st.debug(f"Reverse geocoding error for ({lat}, {lon}): {e}")
        return None


def find_nearby_facilities_by_coords(lat: float, lon: float, radius_km: float = 10.0) -> str:
    """
    Finds nearby healthcare facilities using coordinates and Gemini AI.
    Uses the user's exact location to find the closest hospitals.
    """
    try:
        # 1. Configure Gemini API
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

        # 2. Use the grounded (Google search) mode
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            # generation_config={"mode": "google_search_retrieval"}
        )

        # 3. Build prompts - request structured format with coordinates
        system_prompt = (
            "You are a helpful emergency assistant. "
            "Find the top 3-5 nearest public or general hospitals near the given coordinates. "
            "For each hospital, provide: Name, Full Address, and if possible Latitude and Longitude coordinates. "
            "Format each result on a new line starting with a number, followed by the hospital name, address, and coordinates if available."
        )

        user_prompt = (
            f"Find hospitals near latitude {lat}, longitude {lon} within {radius_km} km radius. "
            "Format as: Number. Hospital Name | Address | Latitude, Longitude (if available)"
        )

        # 4. Generate response
        response = model.generate_content([system_prompt, user_prompt])

        # 5. Return formatted text
        if response and hasattr(response, "text") and response.text:
            return response.text.strip()
        else:
            return "⚠️ No hospitals found near your location. Try another location."

    except Exception as e:
        st.error(f"Error finding facilities: {e}")
        return "⚠️ Could not search for hospitals. Please check your Gemini API key and network connection."


def find_nearby_facilities(location_query: str):
    """
    Finds nearby healthcare facilities using Gemini's grounded search tool
    based on a text-based location query (e.g., "Austin, TX").
    """
    try:
        # 1. Configure Gemini API
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

        # 2. Use the grounded (Google search) mode
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            # generation_config={"mode": "google_search_retrieval"}
        )

        # 3. Build prompts - request structured format with coordinates
        system_prompt = (
            "You are a helpful emergency assistant. "
            "Find the top 3-5 nearest public or general hospitals near the user's requested location. "
            "For each hospital, provide: Name, Full Address, and if possible Latitude and Longitude coordinates. "
            "Format each result on a new line starting with a number, followed by the hospital name, address, and coordinates if available."
        )

        user_prompt = (
            f"Find hospitals near: {location_query}. "
            "Format as: Number. Hospital Name | Address | Latitude, Longitude (if available)"
        )

        # 4. Generate response
        response = model.generate_content([system_prompt, user_prompt])

        # 5. Return formatted text
        if response and hasattr(response, "text") and response.text:
            return response.text.strip()
        else:
            return "⚠️ No hospitals found. Try another location."

    except Exception as e:
        st.error(f"Error finding facilities: {e}")
        return "⚠️ Could not search for hospitals. Please check your Gemini API key and network connection."


def parse_facilities_to_df(text_result: str) -> pd.DataFrame:
    """
    Converts Gemini's text output (numbered list) into a DataFrame with coordinates.
    Tries to extract coordinates from text, or geocodes addresses if coordinates not found.
    """
    data = []
    lines = text_result.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or not re.match(r'^\d+\.', line):
            continue
            
        # Try multiple patterns to extract information
        # Pattern 1: "1. Name | Address | Lat, Lon"
        match1 = re.match(r'^\d+\.\s*(.+?)\s*\|\s*(.+?)\s*\|\s*([+-]?\d+\.?\d*),\s*([+-]?\d+\.?\d*)', line)
        if match1:
            name, address, lat, lon = match1.groups()
            try:
                data.append({
                    "name": name.strip(),
                    "address": address.strip(),
                    "lat": float(lat),
                    "lon": float(lon)
                })
                continue
            except ValueError:
                pass
        
        # Pattern 2: "1. Name, Address (Lat, Lon)" or "1. Name - Address - Lat, Lon"
        match2 = re.search(r'([+-]?\d+\.?\d*)\s*,\s*([+-]?\d+\.?\d*)', line)
        if match2:
            lat, lon = match2.groups()
            # Extract name and address (everything before the coordinates)
            prefix = line[:match2.start()].strip()
            # Remove leading number and period
            prefix = re.sub(r'^\d+\.\s*', '', prefix)
            # Try to split name and address
            parts = re.split(r'[|,\-–—]', prefix, 1)
            name = parts[0].strip() if parts else prefix
            address = parts[1].strip() if len(parts) > 1 else prefix
            
            try:
                data.append({
                    "name": name,
                    "address": address,
                    "lat": float(lat),
                    "lon": float(lon)
                })
                continue
            except ValueError:
                pass
        
        # Pattern 3: "1. Name, Address" - extract name and address, then geocode
        match3 = re.match(r'^\d+\.\s*(.+?),\s*(.+)$', line)
        if match3:
            name, address = match3.groups()
            name = name.strip()
            address = address.strip()
            
            # Try to geocode the address
            coords = geocode_address(address)
            if coords:
                data.append({
                    "name": name,
                    "address": address,
                    "lat": coords[0],
                    "lon": coords[1]
                })
            else:
                # If geocoding fails, still add it without coordinates
                data.append({
                    "name": name,
                    "address": address
                })
            continue
        
        # Pattern 4: Simple numbered list - try to parse manually
        match4 = re.match(r'^\d+\.\s*(.+)$', line)
        if match4:
            content = match4.group(1).strip()
            # Try to split by common delimiters
            parts = [p.strip() for p in re.split(r'[|,\-–—]', content) if p.strip()]
            if len(parts) >= 2:
                name = parts[0]
                address = ' '.join(parts[1:])
                coords = geocode_address(address)
                if coords:
                    data.append({
                        "name": name,
                        "address": address,
                        "lat": coords[0],
                        "lon": coords[1]
                    })
                else:
                    data.append({
                        "name": name,
                        "address": address
                    })

    return pd.DataFrame(data)


def show_facilities_results(location_query: str):
    """
    Combines search + display logic for Streamlit.
    """
    st.subheader("🗺️ Nearby Healthcare Facilities")

    with st.spinner("Searching for nearby hospitals..."):
        result_text = find_nearby_facilities(location_query)

    st.markdown(result_text)

    facilities_df = parse_facilities_to_df(result_text)

    if not facilities_df.empty:
        st.dataframe(facilities_df, use_container_width=True)
    else:
        st.info("Gemini returned text results only — no coordinates available for mapping.")


def show_facilities_map(facilities_df: pd.DataFrame):
    """
    Displays a map if lat/lon are available.
    """
    if not facilities_df.empty and {"lat", "lon"}.issubset(facilities_df.columns):
        st.map(facilities_df[["lat", "lon"]])
        st.markdown("### 🏥 Nearby Healthcare Facilities (Map)")
        for _, row in facilities_df.iterrows():
            st.markdown(f"**{row['name']}** \n📍 ({row['lat']:.4f}, {row['lon']:.4f})")
    else:
        st.warning("Map skipped — Gemini results do not include coordinates.")


# --- Streamlit UI Layout ---
st.set_page_config(page_title="Nearby Healthcare Finder", page_icon="🏥", layout="centered")

st.title("🏥 Nearby Healthcare Facilities Finder")
st.write("Enter a city, state, or area to find hospitals near you.")

location_query = st.text_input("📍 Enter a location", placeholder="e.g., Austin, TX")

if st.button("Find Hospitals") and location_query:
    show_facilities_results(location_query)
