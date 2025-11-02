# Premium Voice Setup Guide

## Overview
To get Siri/Gemini-like natural voice quality, you have two options:

### Option 1: Enhanced Browser Voices (Free, Works Immediately) ✅
The app now automatically selects the **best available neural voices** in your browser:
- **Google Neural Voices** (Chrome/Edge) - Most natural, Siri-like quality
- **Microsoft Neural Voices** (Edge/Windows) - Very natural Azure TTS
- **Apple Siri Voices** (Safari/Mac/iOS) - Native Siri quality
- **Amazon Polly** (if available) - High-quality neural voices

**How it works:**
- The app automatically detects and uses the best voice available
- No setup needed - works out of the box!
- Selects neural/high-quality voices first, then falls back to standard voices

**To test:** Just enable "🎤 Voice Assistant" - it will use the best voice automatically!

---

### Option 2: Google Cloud Text-to-Speech API (Premium, Most Natural) 🌟

For the **absolute best quality** (identical to Siri/Gemini), use Google Cloud TTS API with Neural2 voices.

#### Setup Steps:

1. **Get Google Cloud TTS API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable "Cloud Text-to-Speech API"
   - Create credentials (API Key)
   - Copy your API key

2. **Add to Streamlit Secrets:**
   - Edit `.streamlit/secrets.toml`
   - Add: `GCP_TTS_API_KEY = "your-api-key-here"`

3. **Enable Premium Voices:**
   - In the app, check "🎙️ Premium Voices (Natural/Siri-like)"
   - The app will automatically use Google Cloud TTS API when available

#### Voice Quality:
- **Neural2-F** (Female): Most natural, identical to Gemini AI voice
- **Neural2-D** (Male): Natural male voice
- **Wavenet**: High-quality alternative

#### Cost:
- First 0-4 million characters/month: **FREE**
- After that: Very affordable pricing
- Perfect for personal/small use cases

---

## Voice Comparison

| Voice Source | Quality | Naturalness | Setup |
|-------------|---------|-------------|-------|
| Browser Neural (Auto) | ⭐⭐⭐⭐ | Very Good | ✅ Automatic |
| Google Cloud TTS Neural2 | ⭐⭐⭐⭐⭐ | Excellent (Siri/Gemini-like) | Requires API key |
| Standard Browser TTS | ⭐⭐⭐ | Good | ✅ Automatic |

---

## Current Implementation

The app **automatically uses the best available voice** in this priority order:

1. ✅ **Google Neural Voices** (Chrome/Edge) - **Most Natural**
2. ✅ **Microsoft Neural Voices** (Edge/Windows)
3. ✅ **Apple Siri Voices** (Safari/Mac/iOS)
4. ✅ **Any Neural/Wavenet Voices**
5. ✅ **Google Standard Voices**
6. ✅ **Microsoft Standard Voices**
7. ✅ **High-quality Female Voices**
8. ✅ **Any English Voice**

**Result:** Even without Google Cloud API, you get excellent voice quality if you're using:
- **Chrome/Edge** (Google Neural voices)
- **Safari/Mac** (Apple Siri voices)
- **Edge/Windows** (Microsoft Neural voices)

---

## Recommended Browsers for Best Voice Quality

1. **Chrome/Edge** ⭐⭐⭐⭐⭐
   - Has Google Neural voices (most natural)
   - Best voice quality available

2. **Safari (Mac/iOS)** ⭐⭐⭐⭐⭐
   - Has Apple Siri voices
   - Excellent natural quality

3. **Edge (Windows)** ⭐⭐⭐⭐
   - Has Microsoft Neural voices
   - Very good quality

4. **Firefox** ⭐⭐⭐
   - Limited neural voices
   - Good quality but fewer options

---

## Troubleshooting Voice Quality

**Voice sounds robotic?**
- Ensure you're using Chrome, Edge, or Safari
- Check "🎙️ Premium Voices" is enabled
- The app will auto-select the best voice

**Want even better quality?**
- Set up Google Cloud TTS API (see Option 2 above)
- This gives you Neural2 voices identical to Gemini AI

**Voice not working?**
- Check browser audio permissions
- Try different browser (Chrome recommended)
- Check system volume

---

## Technical Details

### Voice Selection Algorithm
The app uses a **smart voice selection algorithm** that:
1. Scans all available browser voices
2. Prioritizes neural/premium voices
3. Selects the most natural-sounding voice
4. Falls back gracefully if premium voices unavailable

### Natural Speech Features
- **Natural pauses** between sentences
- **Optimal speech rate** (0.88-0.92 for clarity)
- **Natural pitch** (1.0 for human-like tone)
- **Sentence chunking** for longer text
- **Professional tone** for medical content

---

## Quick Start

**For immediate best quality (no setup):**
1. Use **Chrome** or **Edge** browser
2. Enable "🎤 Voice Assistant"
3. Enable "🎙️ Premium Voices"
4. Done! Best voice auto-selected

**For absolute best quality (with setup):**
1. Get Google Cloud TTS API key
2. Add to `.streamlit/secrets.toml`
3. Enable "🎙️ Premium Voices"
4. Enjoy Siri/Gemini-quality voice!

---

**The voice assistant now sounds much more natural and human-like, especially in Chrome/Edge/Safari browsers!** 🎙️✨

