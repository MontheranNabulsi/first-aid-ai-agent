"""
Voice Assistant for Accessibility
Provides voice input/output for blind and visually impaired users
"""

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from typing import Optional, Dict, Any


def speak_text(text: str, rate: float = 0.92, pitch: float = 1.0, volume: float = 1.0, voice_name: Optional[str] = None, use_google_tts: bool = False) -> bool:
    """
    Use browser's text-to-speech with premium voice selection for natural, Siri-like quality.
    Prioritizes neural/high-quality voices similar to Siri or Gemini AI.
    
    Args:
        text: Text to speak
        rate: Speech rate (0.1 to 10, default 0.92 - natural pace)
        pitch: Voice pitch (0 to 2, default 1.0 - natural pitch)
        volume: Voice volume (0 to 1, default 1.0)
        voice_name: Preferred voice name (optional)
    
    Returns:
        True if successful
    """
    try:
        # Try Google Cloud TTS API if available (premium neural voices - Siri/Gemini quality)
        if use_google_tts:
            try:
                from utils.google_tts_integration import speak_with_google_tts, get_premium_voice_names
                if "GCP_TTS_API_KEY" in st.secrets:
                    voice_names = get_premium_voice_names()
                    audio_data = speak_with_google_tts(text, voice_names["female_natural"], use_api=True)
                    if audio_data:
                        # Play audio using HTML5 audio element
                        import base64
                        audio_b64 = base64.b64encode(audio_data).decode()
                        audio_html = f'<audio autoplay><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mpeg"></audio>'
                        streamlit_js_eval(
                            js_expressions=f'document.body.insertAdjacentHTML("beforeend", `{audio_html}`); setTimeout(() => {{ const el = document.body.lastElementChild; if(el) el.remove(); }}, 5000);',
                            key=f"google_tts_{hash(text)}",
                            want_output=False
                        )
                        return True
            except Exception as e:
                # Fall through to browser TTS if API fails
                pass
        
        # Enhanced browser TTS with premium voice selection (Siri-like voices)
        # Clean and prepare text for natural speech with SSML-like pauses
        text = text.strip()
        # Add natural pauses and emphasis for better flow
        text = text.replace('. ', '. <break time="300ms"/> ')
        text = text.replace('! ', '! <break time="400ms"/> ')
        text = text.replace('? ', '? <break time="400ms"/> ')
        text = text.replace(', ', ', <break time="200ms"/> ')
        # Remove SSML tags (browsers don't support SSML, but we'll format for natural speech)
        text = text.replace('<break time="300ms"/>', '...')
        text = text.replace('<break time="400ms"/>', '...')
        text = text.replace('<break time="200ms"/>', '..')
        
        # Escape quotes in text
        escaped_text = text.replace('"', '\\"').replace("'", "\\'").replace('\n', ' ')
        
        js_code = f"""
        (function() {{
            // Stop any ongoing speech first
            window.speechSynthesis.cancel();
            
            const speakNatural = () => {{
                const utterance = new SpeechSynthesisUtterance("{escaped_text}");
                utterance.rate = {rate};
                utterance.pitch = {pitch};
                utterance.volume = {volume};
                utterance.lang = 'en-US';
                
                // Get all available voices
                let allVoices = window.speechSynthesis.getVoices();
                
                // If voices not loaded yet, wait for them
                if (allVoices.length === 0) {{
                    window.speechSynthesis.onvoiceschanged = () => {{
                        allVoices = window.speechSynthesis.getVoices();
                        selectBestVoice();
                    }};
                }} else {{
                    selectBestVoice();
                }}
                
                function selectBestVoice() {{
                    let selectedVoice = null;
                    
                    // Priority 1: Premium Neural Voices (Siri/Gemini quality)
                    // Google Neural TTS (most natural, available in Chrome/Edge)
                    selectedVoice = allVoices.find(v => 
                        v.name.includes('Google US English Neural') ||
                        v.name.includes('Google UK English Neural') ||
                        (v.name.includes('Google') && v.name.includes('Neural'))
                    );
                    
                    // Priority 2: Microsoft Neural Voices (Azure - very natural)
                    if (!selectedVoice) {{
                        selectedVoice = allVoices.find(v => 
                            v.name.includes('Microsoft Zira') ||
                            v.name.includes('Microsoft Aria') ||
                            v.name.includes('Microsoft Jenny Neural') ||
                            (v.name.includes('Microsoft') && v.name.includes('Neural'))
                        );
                    }}
                    
                    // Priority 3: Apple Siri Voices (Mac/iOS - very natural)
                    if (!selectedVoice) {{
                        selectedVoice = allVoices.find(v => 
                            v.name.includes('Samantha') ||
                            v.name.includes('Victoria') ||
                            v.name.includes('Fiona') ||
                            v.name.includes('Alex') ||
                            v.name.includes('Karen')
                        );
                    }}
                    
                    // Priority 4: Any Neural voice (highest quality)
                    if (!selectedVoice) {{
                        selectedVoice = allVoices.find(v => 
                            v.name.includes('Neural') ||
                            v.name.includes('Wavenet') ||
                            v.name.includes('Premium')
                        );
                    }}
                    
                    // Priority 5: Google Standard voices (still good quality)
                    if (!selectedVoice) {{
                        selectedVoice = allVoices.find(v => 
                            v.name.includes('Google US English') ||
                            v.name.includes('Google UK English')
                        );
                    }}
                    
                    // Priority 6: Microsoft standard voices
                    if (!selectedVoice) {{
                        selectedVoice = allVoices.find(v => 
                            v.name.includes('Microsoft') && v.lang.startsWith('en')
                        );
                    }}
                    
                    // Priority 7: Any high-quality female voice
                    if (!selectedVoice) {{
                        selectedVoice = allVoices.find(v => 
                            v.lang.startsWith('en') && 
                            (v.name.includes('Female') || 
                             v.name.includes('Woman'))
                        );
                    }}
                    
                    // Priority 8: Any English voice with US locale (most natural accent)
                    if (!selectedVoice) {{
                        selectedVoice = allVoices.find(v => 
                            v.lang === 'en-US' || v.lang.startsWith('en-US')
                        );
                    }}
                    
                    // Fallback: Any English voice
                    if (!selectedVoice) {{
                        selectedVoice = allVoices.find(v => v.lang.startsWith('en'));
                    }}
                    
                    if (selectedVoice) {{
                        utterance.voice = selectedVoice;
                        console.log('Using premium voice:', selectedVoice.name, 'Language:', selectedVoice.lang);
                    }}
                    
                    // Natural speech parameters for Siri/Gemini-like quality
                    utterance.rate = {rate};  // Natural pace
                    utterance.pitch = {pitch};  // Natural pitch
                    utterance.volume = {volume};
                    
                    // Speak with natural pauses for longer text
                    const sentences = "{escaped_text}".split(/(?<=[\\.!?])\\s+/).filter(s => s.trim());
                    
                    if (sentences.length > 3) {{
                        // Speak in chunks with natural pauses
                        let idx = 0;
                        const speakNext = () => {{
                            if (idx < sentences.length) {{
                                const sentUtterance = new SpeechSynthesisUtterance(sentences[idx].trim());
                                if (selectedVoice) sentUtterance.voice = selectedVoice;
                                sentUtterance.rate = utterance.rate;
                                sentUtterance.pitch = utterance.pitch;
                                sentUtterance.volume = utterance.volume;
                                
                                sentUtterance.onend = () => {{
                                    idx++;
                                    if (idx < sentences.length) {{
                                        setTimeout(speakNext, 350); // Natural pause
                                    }}
                                }};
                                
                                window.speechSynthesis.speak(sentUtterance);
                            }}
                        }};
                        speakNext();
                    }} else {{
                        window.speechSynthesis.speak(utterance);
                    }}
                }}
            }};
            
            // Trigger voice loading and speak
            speakNatural();
            
            return true;
        }})()
        """
        
        streamlit_js_eval(
            js_expressions=js_code,
            key=f"speak_{hash(text)}",
            want_output=False
        )
        return True
    except Exception as e:
        st.error(f"Error speaking text: {e}")
        return False


def stop_speaking() -> bool:
    """Stop any ongoing speech."""
    try:
        streamlit_js_eval(
            js_expressions="window.speechSynthesis.cancel(); return true;",
            key="stop_speak",
            want_output=False
        )
        return True
    except Exception as e:
        return False


def listen_for_command(callback_function: Optional[str] = None) -> Dict[str, Any]:
    """
    Listen for voice command using browser's speech recognition.
    
    Args:
        callback_function: Optional JavaScript function name to call with result
    
    Returns:
        Dict with 'text' and 'confidence' keys
    """
    try:
        js_code = """
        new Promise((resolve) => {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                resolve({error: "Speech recognition not supported in this browser. Please use Chrome, Edge, or Safari."});
                return;
            }
            
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                const confidence = event.results[0][0].confidence;
                resolve({text: transcript, confidence: confidence});
            };
            
            recognition.onerror = (event) => {
                let errorMsg = "I'm having trouble hearing you";
                if (event.error === 'no-speech') {
                    errorMsg = "I didn't hear anything. Please try speaking again.";
                } else if (event.error === 'audio-capture') {
                    errorMsg = "I can't access your microphone. Please check your microphone settings.";
                } else if (event.error === 'not-allowed') {
                    errorMsg = "Microphone permission is needed. Please allow microphone access in your browser settings.";
                }
                resolve({error: errorMsg});
            };
            
            recognition.onend = () => {
                // Recognition ended
            };
            
            recognition.start();
        })
        """
        
        result = streamlit_js_eval(
            js_expressions=js_code,
            key=f"listen_{hash(str(callback_function))}",
            want_output=True
        )
        
        return result if result else {"error": "No result from speech recognition"}
    
    except Exception as e:
        return {"error": f"Error listening: {str(e)}"}


def announce_page_content(page_name: str, content_summary: str, use_premium: bool = True) -> bool:
    """Announce page content when navigating with natural phrasing."""
    announcement = f"You're now on the {page_name} page. {content_summary} How can I help you?"
    return speak_text(announcement, rate=0.92, pitch=1.0, use_google_tts=use_premium and "GCP_TTS_API_KEY" in st.secrets if hasattr(st, 'secrets') else False)


def announce_injury_analysis(severity: str, emergency_level: str, has_steps: bool = True) -> bool:
    """Announce injury analysis results with clear, calm professional tone."""
    severity_announcement = {
        "SEVERE": "I've detected a severe injury. Urgent medical attention is needed.",
        "MODERATE": "I've identified a moderate injury. I recommend seeing a healthcare professional within 24 hours.",
        "MINOR": "I've identified a minor injury. Let me guide you through the first aid steps.",
        "UNKNOWN": "I've analyzed your injury. Let me provide first aid guidance."
    }
    
    emergency_announcement = {
        "EMERGENCY": "Please note: This appears to be an emergency situation. Please call emergency services at 9-1-1 immediately.",
        "URGENT": "Important: This requires urgent medical attention. Please seek care within the next few hours.",
        "ROUTINE": "This is a routine injury. Following the first aid steps should help."
    }
    
    announcement = f"{severity_announcement.get(severity, '')} {emergency_announcement.get(emergency_level, '')}"
    if has_steps:
        announcement += " First aid instructions are ready. Say 'read steps' anytime to hear them, or I can guide you through each step."
    
    # Use slightly slower rate for important medical information, natural pitch
    return speak_text(announcement, rate=0.88, pitch=1.0, use_google_tts=False)


def announce_first_aid_steps(steps_text: str) -> bool:
    """Announce first aid steps in a clear, structured, and reassuring way."""
    # Clean and format steps for better speech
    lines = steps_text.split('\n')
    steps_only = []
    
    for line in lines:
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
            # Clean up step text
            step_clean = line.lstrip('0123456789.•-* ).').strip()
            if step_clean:
                steps_only.append(step_clean)
    
    if steps_only:
        # More natural phrasing with pauses
        full_text = "Here are your first aid instructions. I'll go through each step clearly. "
        full_text += ". ".join([f"Step {i+1}. {step}" for i, step in enumerate(steps_only)])
        full_text += ". Remember, if the situation worsens or you're unsure, seek professional medical help immediately."
    else:
        # Format plain text for better speech
        full_text = "First aid instructions. " + steps_text.replace('\n', '. ')
    
    # Slower rate for instructions to ensure clarity, natural pitch
    return speak_text(full_text, rate=0.88, pitch=1.0, use_google_tts=False)


def announce_record_created(record_type: str) -> bool:
    """Announce when a record is created with friendly confirmation."""
    announcement = f"Perfect! I've saved your {record_type} record. You can view it anytime in your Health Records section."
    return speak_text(announcement, rate=0.92, pitch=1.0, use_google_tts=False)


def announce_statistics(stats: Dict[str, Any]) -> bool:
    """Announce statistics in a natural, conversational way."""
    total = stats.get("total_records", 0)
    active = stats.get("active_injuries", 0)
    healed = stats.get("healed_injuries", 0)
    most_common = stats.get("most_common_body_part", None)
    
    if total == 0:
        announcement = "You don't have any health records yet. Records will be created automatically when you analyze injuries."
    else:
        announcement = f"Here's a summary of your health records. You have {total} total records. "
        if active > 0:
            announcement += f"{active} active injury or injuries that need attention. "
        if healed > 0:
            announcement += f"Great news, {healed} injury or injuries have been healed. "
        if most_common:
            announcement += f"The most commonly affected area is {most_common}."
    
    return speak_text(announcement, rate=0.90, pitch=1.0, use_google_tts=False)


def get_voice_navigation_commands() -> Dict[str, str]:
    """Return map of voice commands to actions."""
    return {
        "go to first aid": "First Aid Guide",
        "first aid guide": "First Aid Guide",
        "analyze injury": "First Aid Guide",
        "go to hospitals": "Find Nearby Hospitals",
        "find hospitals": "Find Nearby Hospitals",
        "hospitals": "Find Nearby Hospitals",
        "go to records": "📋 My Health Records",
        "health records": "📋 My Health Records",
        "my records": "📋 My Health Records",
        "read steps": "read_first_aid_steps",
        "repeat": "repeat_last",
        "stop": "stop_speaking",
        "help": "show_voice_help",
        "what can i say": "show_voice_help",
    }


def process_voice_command(command: str) -> Optional[str]:
    """
    Process a voice command and return the action.
    
    Args:
        command: Voice command text (lowercase)
    
    Returns:
        Action name or None
    """
    command_lower = command.lower().strip()
    commands = get_voice_navigation_commands()
    
    # Direct match
    if command_lower in commands:
        return commands[command_lower]
    
    # Partial match
    for cmd_key, action in commands.items():
        if cmd_key in command_lower or command_lower in cmd_key:
            return action
    
    return None


def speak_welcome_message(use_premium: bool = True) -> bool:
    """Welcome message for voice assistant with friendly, professional tone."""
    welcome = """
    Hello! Welcome to the First Aid Assistant. I'm your voice assistant, and I'm here to help.
    You can navigate the entire application using voice commands.
    Simply say 'help' anytime to hear all available commands.
    To navigate, say the page name, like 'First Aid Guide' or 'My Health Records'.
    How can I assist you today?
    """
    return speak_text(welcome, rate=0.92, pitch=1.0, use_google_tts=use_premium and "GCP_TTS_API_KEY" in st.secrets if hasattr(st, 'secrets') else False)


def speak_help_message() -> bool:
    """Help message with available commands, spoken in a friendly, clear manner."""
    commands = get_voice_navigation_commands()
    help_text = "Here are all the voice commands you can use. "
    
    # Group commands by category for better understanding
    navigation_cmds = []
    action_cmds = []
    
    for cmd, action in commands.items():
        if action in ["First Aid Guide", "Find Nearby Hospitals", "📋 My Health Records"]:
            navigation_cmds.append(f"'{cmd}' to go to {action}")
        elif action == "read_first_aid_steps":
            action_cmds.append("'read steps' to hear first aid instructions")
        elif action == "stop_speaking":
            action_cmds.append("'stop' to stop me from speaking")
        elif action == "show_voice_help":
            action_cmds.append("'help' to hear this message again")
    
    if navigation_cmds:
        help_text += "For navigation, " + ". ".join(navigation_cmds) + ". "
    if action_cmds:
        help_text += "Other commands: " + ". ".join(action_cmds) + ". "
    
    help_text += "Just speak naturally, and I'll understand. How can I help you?"
    
    return speak_text(help_text, rate=0.88, pitch=1.0, use_google_tts=False)

