# Voice Assistant Accessibility Guide

## Overview
The First Aid Assistant includes a comprehensive voice assistant system designed specifically for blind and visually impaired users. This system provides full access to all features through voice commands and audio announcements.

## Features

### 🎤 Voice Commands
Navigate the entire application using voice commands:

**Navigation Commands:**
- "Go to first aid" or "First aid guide" - Navigate to First Aid Guide page
- "Go to hospitals" or "Find hospitals" - Navigate to Find Nearby Hospitals page
- "Go to records" or "My records" - Navigate to Health Records page

**Action Commands:**
- "Read steps" - Hear the first aid steps read aloud
- "Repeat" - Repeat the last spoken content
- "Stop" - Stop any ongoing speech
- "Help" or "What can I say" - Hear available voice commands

### 🔊 Audio Announcements

**Automatic Announcements:**
- Page navigation: Announces current page when you switch pages
- Injury analysis: Announces severity, emergency level, and that steps are available
- Record creation: Confirms when injury records are saved
- Error messages: All important messages are spoken

**On-Demand Announcements:**
- Click "🔊 Announce Statistics" to hear your health statistics
- Click "🔊 Announce" buttons throughout the app to hear content

### 📱 How to Use

1. **Enable Voice Assistant:**
   - Look for "🎤 Voice Assistant (Accessibility)" checkbox in the sidebar
   - Check the box to enable voice features

2. **Voice Navigation:**
   - Click "🎤 Listen" button in sidebar
   - Say your command (e.g., "Go to first aid")
   - The assistant will navigate and announce the page

3. **Hear Content:**
   - After analyzing an injury, severity and emergency level are automatically announced
   - Say "Read steps" to hear first aid instructions
   - All important information is spoken automatically

4. **Control Speech:**
   - Click "🔇 Stop" to stop any ongoing speech
   - Use "❓ Voice Help" to hear all available commands

### 🎯 Voice Commands Reference

| Command | Action |
|---------|--------|
| "Go to first aid" | Navigate to First Aid Guide |
| "First aid guide" | Navigate to First Aid Guide |
| "Go to hospitals" | Navigate to Find Hospitals |
| "Find hospitals" | Navigate to Find Hospitals |
| "Go to records" | Navigate to Health Records |
| "My records" | Navigate to Health Records |
| "Read steps" | Hear first aid steps |
| "Repeat" | Repeat last content |
| "Stop" | Stop speaking |
| "Help" | List all commands |

### 🔧 Browser Requirements

**Speech Recognition (Voice Input):**
- **Chrome/Edge**: Full support ✅
- **Safari**: Full support ✅
- **Firefox**: Limited support (may not work)

**Text-to-Speech (Voice Output):**
- Works in all modern browsers ✅

**Recommendation:** Use Chrome, Edge, or Safari for best experience.

### 🎓 Usage Tips

1. **Speak Clearly:** Enunciate your commands for best recognition
2. **Wait for Listening:** The app will say "Listening for your command" before accepting input
3. **Use Natural Language:** Say commands naturally (e.g., "go to first aid" not "first aid")
4. **Check Microphone:** Ensure your microphone is enabled and working
5. **Grant Permissions:** Allow microphone access when prompted

### 📋 Complete Workflow Example

**Analyzing an Injury with Voice:**

1. Enable Voice Assistant (sidebar checkbox)
2. Say "Go to first aid" or navigate manually
3. Describe injury or upload image
4. Click "Analyze"
5. **Automatic announcements:**
   - Severity assessment
   - Emergency level
   - Confirmation that steps are available
6. Say "Read steps" to hear first aid instructions
7. Record is automatically saved (announced)

**Viewing Records with Voice:**

1. Say "Go to records"
2. Page content is announced
3. Click "🔊 Announce Statistics" to hear stats
4. Use voice commands to navigate between records
5. All record details can be read aloud

### 🌐 Accessibility Standards

This implementation follows:
- **WCAG 2.1 Level AA** guidelines
- Screen reader compatibility
- Keyboard navigation support
- ARIA labels for screen readers
- Audio alternatives for visual content

### 🚀 Future Enhancements

Planned improvements:
- Continuous listening mode
- More natural language commands
- Voice-controlled form filling
- Audio cues for interactive elements
- Support for more languages

### ❓ Troubleshooting

**Voice commands not working?**
- Check browser compatibility (use Chrome/Edge/Safari)
- Ensure microphone permissions are granted
- Check microphone is working in other apps
- Try clicking "Listen" button again

**No audio output?**
- Check system volume
- Ensure browser allows audio playback
- Try refreshing the page
- Check browser audio settings

**Commands not recognized?**
- Speak more clearly
- Try rephrasing the command
- Check available commands with "Help"
- Use exact command phrases from help menu

### 💡 Tips for Best Experience

1. **Quiet Environment:** Background noise can interfere with recognition
2. **Clear Speech:** Speak at normal pace, enunciate clearly
3. **Wait for Confirmation:** The app confirms when listening starts
4. **Use Help:** Say "help" anytime to hear available commands
5. **Practice:** Try commands to get familiar with the system

### 📞 Support

If you encounter issues with the voice assistant:
1. Check this guide first
2. Try the "Voice Help" button
3. Ensure browser and microphone permissions are correct
4. Try a different browser (Chrome recommended)

---

## For Developers

### Technical Implementation

- **Speech Recognition:** Web Speech API (`webkitSpeechRecognition` / `SpeechRecognition`)
- **Text-to-Speech:** Web Speech Synthesis API
- **Integration:** Streamlit with JavaScript evaluation
- **Browser Support:** Chrome, Edge, Safari (full support), Firefox (limited)

### Code Structure

- `utils/voice_assistant.py` - Core voice assistant functions
- Voice commands integrated throughout `app.py`
- Automatic announcements on key actions
- Session state management for voice settings

### Extending Voice Features

To add new voice commands:
1. Add command to `get_voice_navigation_commands()` in `voice_assistant.py`
2. Add handler in voice command processing section of `app.py`
3. Test with voice assistant enabled

---

**Accessibility is a priority. This feature ensures everyone can use the First Aid Assistant effectively, regardless of visual ability.**

