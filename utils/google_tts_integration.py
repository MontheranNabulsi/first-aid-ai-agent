"""
Google Cloud Text-to-Speech Integration
Provides premium neural voices similar to Siri/Gemini for better voice quality.
Requires Google Cloud TTS API key (optional - falls back to browser TTS if not available).
"""

import streamlit as st
import requests
import base64
import json
from typing import Optional
import io


def speak_with_google_tts(text: str, voice_name: str = "en-US-Neural2-F", use_api: bool = False) -> Optional[bytes]:
    """
    Use Google Cloud Text-to-Speech API for premium neural voices.
    Falls back to browser TTS if API key not available.
    
    Args:
        text: Text to convert to speech
        voice_name: Voice name (e.g., "en-US-Neural2-F" for natural female voice)
        use_api: Whether to use API (requires GCP_TTS_API_KEY in secrets)
    
    Returns:
        Audio bytes if using API, None if falling back to browser
    """
    if not use_api or "GCP_TTS_API_KEY" not in st.secrets:
        return None
    
    try:
        api_key = st.secrets["GCP_TTS_API_KEY"]
        
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
        
        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": "en-US",
                "name": voice_name,
                "ssmlGender": "FEMALE"
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 0.95,
                "pitch": 0,
                "volumeGainDb": 0.0
            }
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            audio_content = base64.b64decode(data["audioContent"])
            return audio_content
        else:
            st.debug(f"Google TTS API error: {response.status_code}")
            return None
    
    except Exception as e:
        st.debug(f"Google TTS API error: {e}")
        return None


def get_premium_voice_names() -> dict:
    """Get list of premium Google TTS voices (neural voices similar to Siri/Gemini)."""
    return {
        "female_natural": "en-US-Neural2-F",  # Most natural, Siri-like
        "male_natural": "en-US-Neural2-D",
        "female_gentle": "en-US-Neural2-J",
        "female_warm": "en-US-Standard-E",
        "female_clear": "en-US-Wavenet-F",
    }

