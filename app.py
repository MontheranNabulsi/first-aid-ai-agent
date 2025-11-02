import streamlit as st
import pandas as pd
from utils.map_helper import (
    find_nearby_facilities, 
    find_nearby_facilities_by_coords,
    show_facilities_map, 
    parse_facilities_to_df,
    reverse_geocode
)
from utils.ai_helpers import analyze_image, generate_first_aid_steps
from streamlit_js_eval import streamlit_js_eval


st.set_page_config(page_title="🩹 First Aid Assistant", layout="wide")

st.title("🩹 AI-Powered First Aid Assistant")
st.markdown(
    "Upload an image of an injury or describe it in text, and I’ll help you with immediate first aid steps. "
    "You can also find nearby hospitals."
)

# Sidebar options
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Go to:", ["First Aid Guide", "Find Nearby Hospitals"])

# --- PAGE 1: First Aid Guide ---
if page == "First Aid Guide":
    st.subheader("Analyze Injury")

    uploaded_image = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])
    injury_description = st.text_area("Or describe the injury:")

    if st.button("Analyze"):
        if uploaded_image:
            with st.spinner("Analyzing image..."):
                analysis = analyze_image(uploaded_image)
                st.success("✅ Image analyzed successfully.")
                st.markdown(f"**Analysis Result:** {analysis}")
                st.markdown("### 🩹 First Aid Steps")
                st.write(generate_first_aid_steps(analysis))
        elif injury_description:
            with st.spinner("Analyzing text..."):
                steps = generate_first_aid_steps(injury_description)
                st.success("✅ First aid advice ready.")
                st.markdown("### 🩹 First Aid Steps")
                st.write(steps)
        else:
            st.warning("Please upload an image or describe the injury.")

# --- PAGE 2: Find Nearby Hospitals ---
elif page == "Find Nearby Hospitals":
    st.subheader("🏥 Find Nearby Healthcare Facilities")
    
    # Initialize session state for location
    if 'user_location' not in st.session_state:
        st.session_state.user_location = None
    if 'location_requested' not in st.session_state:
        st.session_state.location_requested = False
    if 'location_permission_granted' not in st.session_state:
        st.session_state.location_permission_granted = False
    
    # Option 1: Use Device Location - automatically request native browser permission
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**📍 Option 1: Use My Location**")
        if not st.session_state.location_requested and not st.session_state.location_permission_granted:
            st.info("📍 Click below to allow location access. Your browser will show a permission popup.")
            request_location = st.button("📍 Allow Location Access", type="primary", use_container_width=True)
            if request_location:
                st.session_state.location_requested = True
    
    with col2:
        st.markdown("**🔍 Option 2: Search by Address**")
        location_query = st.text_input(
            "Enter city or address:", 
            placeholder="e.g., Austin, TX",
            label_visibility="collapsed"
        )
        search_location = st.button("🔍 Search Hospitals", use_container_width=True)
    
    # Get user's geolocation using native browser permission (triggered automatically)
    if st.session_state.location_requested and not st.session_state.location_permission_granted:
        # Use native browser geolocation API - this triggers the browser's native permission popup
        # The popup appears in the top-right corner of the browser (native browser UI)
        try:
            location_result = streamlit_js_eval(
                js_expressions="""
                new Promise((resolve, reject) => {
                    if (!navigator.geolocation) {
                        resolve({error: "Geolocation not supported"});
                        return;
                    }
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            resolve({
                                lat: position.coords.latitude,
                                lon: position.coords.longitude,
                                success: true
                            });
                        },
                        (error) => {
                            let errorMsg = "Location access denied";
                            if (error.code === 1) {
                                errorMsg = "Location permission denied by user";
                            } else if (error.code === 2) {
                                errorMsg = "Location unavailable";
                            } else if (error.code === 3) {
                                errorMsg = "Location request timeout";
                            }
                            resolve({error: errorMsg});
                        },
                        {enableHighAccuracy: true, timeout: 15000, maximumAge: 0}
                    );
                })
                """,
                key="native_location_permission",
                want_output=True
            )
            
            # Check if location was successfully obtained
            if location_result and isinstance(location_result, dict):
                if 'error' in location_result:
                    error_msg = location_result['error']
                    if "denied" in error_msg.lower() or "permission" in error_msg.lower():
                        st.warning("⚠️ Location permission denied. Please allow location access in your browser settings or try searching by address.")
                    else:
                        st.warning(f"⚠️ Unable to get your location: {error_msg}. Please try searching by address.")
                    st.session_state.location_requested = False
                elif 'lat' in location_result and 'lon' in location_result:
                    lat = location_result['lat']
                    lon = location_result['lon']
                    st.session_state.user_location = {'lat': lat, 'lon': lon}
                    st.session_state.location_permission_granted = True
                    
                    # Get address from coordinates
                    address = reverse_geocode(lat, lon)
                    
                    if address:
                        st.success(f"✅ Location detected: {address}")
                        st.caption(f"Coordinates: {lat:.6f}, {lon:.6f}")
                    else:
                        st.success(f"✅ Location detected at coordinates: {lat:.6f}, {lon:.6f}")
                    
                    # Automatically search for hospitals
                    with st.spinner("🔍 Searching nearby hospitals..."):
                        results_text = find_nearby_facilities_by_coords(lat, lon)
                        st.markdown("### 🏥 Nearby Hospitals")
                        st.markdown(results_text)
                        
                        # Parse results and show map
                        facilities_df = parse_facilities_to_df(results_text)
                        
                        if not facilities_df.empty:
                            # Add user location to map
                            user_df = pd.DataFrame([{
                                "name": "Your Location",
                                "address": address or f"Lat: {lat}, Lon: {lon}",
                                "lat": lat,
                                "lon": lon
                            }])
                            
                            # Combine user location with facilities
                            combined_df = pd.concat([user_df, facilities_df], ignore_index=True)
                            
                            st.markdown("---")
                            st.markdown("### 📍 Hospital Locations Map")
                            st.map(combined_df, zoom=13)
                            
                            # Show facilities in a list
                            st.markdown("### 📋 Hospitals Nearby")
                            for idx, row in facilities_df.iterrows():
                                if "lat" in row and "lon" in row:
                                    st.markdown(f"**{idx + 1}. {row['name']}**")
                                    st.markdown(f"📍 {row['address']}")
                                    st.markdown(f"Coordinates: ({row['lat']:.4f}, {row['lon']:.4f})")
                                else:
                                    st.markdown(f"**{idx + 1}. {row['name']}**")
                                    st.markdown(f"📍 {row['address']}")
                                st.markdown("---")
                else:
                    # Still waiting for user to respond to the native browser permission popup
                    st.info("📍 **Please respond to the browser permission popup that appeared in the top-right corner of your browser.**")
        except Exception as e:
            st.error(f"Error getting location: {e}")
            st.info("💡 Please try searching by address instead, or check your browser's location permissions.")
            st.session_state.location_requested = False
    
    # Show location status if already granted
    elif st.session_state.location_permission_granted and st.session_state.user_location:
        lat = st.session_state.user_location['lat']
        lon = st.session_state.user_location['lon']
        address = reverse_geocode(lat, lon)
        if address:
            st.success(f"✅ Using your location: {address}")
        else:
            st.success(f"✅ Using your location: {lat:.6f}, {lon:.6f}")
        
        # Option to search again with current location
        if st.button("🔍 Search Hospitals Near Me", type="primary"):
            with st.spinner("🔍 Searching nearby hospitals..."):
                results_text = find_nearby_facilities_by_coords(lat, lon)
                st.markdown("### 🏥 Nearby Hospitals")
                st.markdown(results_text)
                
                # Parse results and show map
                facilities_df = parse_facilities_to_df(results_text)
                
                if not facilities_df.empty:
                    # Add user location to map
                    user_df = pd.DataFrame([{
                        "name": "Your Location",
                        "address": address or f"Lat: {lat}, Lon: {lon}",
                        "lat": lat,
                        "lon": lon
                    }])
                    
                    # Combine user location with facilities
                    combined_df = pd.concat([user_df, facilities_df], ignore_index=True)
                    
                    st.markdown("---")
                    st.markdown("### 📍 Hospital Locations Map")
                    st.map(combined_df, zoom=13)
                    
                    # Show facilities in a list
                    st.markdown("### 📋 Hospitals Nearby")
                    for idx, row in facilities_df.iterrows():
                        if "lat" in row and "lon" in row:
                            st.markdown(f"**{idx + 1}. {row['name']}**")
                            st.markdown(f"📍 {row['address']}")
                            st.markdown(f"Coordinates: ({row['lat']:.4f}, {row['lon']:.4f})")
                        else:
                            st.markdown(f"**{idx + 1}. {row['name']}**")
                            st.markdown(f"📍 {row['address']}")
                        st.markdown("---")
    
    # Handle manual search by address (independent of location permission)
    if search_location:
        if location_query.strip():
            with st.spinner("🔍 Searching nearby hospitals..."):
                results_text = find_nearby_facilities(location_query)
                st.markdown("### 🏥 Nearby Hospitals")
                st.markdown(results_text)
                
                # Parse results and show map
                facilities_df = parse_facilities_to_df(results_text)
                
                if not facilities_df.empty:
                    st.markdown("---")
                    st.markdown("### 📍 Hospital Locations Map")
                    show_facilities_map(facilities_df)
        else:
            st.warning("Please enter a valid location.")
