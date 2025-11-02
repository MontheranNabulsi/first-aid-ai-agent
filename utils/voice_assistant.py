"""
Voice Assistant for Accessibility
Provides voice input/output for blind and visually impaired users
"""

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from typing import Optional, Dict, Any


def speak_text(text: str, rate: float = 1.0, pitch: float = 1.0) -> bool:
    """
    Use browser's text-to-speech to speak text aloud.
    
    Args:
        text: Text to speak
        rate: Speech rate (0.1 to 10, default 1.0)
        pitch: Voice pitch (0 to 2, default 1.0)
    
    Returns:
        True if successful
    """
    try:
        # Escape quotes in text
        escaped_text = text.replace('"', '\\"').replace("'", "\\'")
        
        js_code = f"""
        (function() {{
            const utterance = new SpeechSynthesisUtterance("{escaped_text}");
            utterance.rate = {rate};
            utterance.pitch = {pitch};
            utterance.lang = 'en-US';
            window.speechSynthesis.speak(utterance);
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
                let errorMsg = "Speech recognition error";
                if (event.error === 'no-speech') {
                    errorMsg = "No speech detected. Please try again.";
                } else if (event.error === 'audio-capture') {
                    errorMsg = "Microphone not found or not accessible.";
                } else if (event.error === 'not-allowed') {
                    errorMsg = "Microphone permission denied. Please allow microphone access.";
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


def announce_page_content(page_name: str, content_summary: str) -> bool:
    """Announce page content when navigating."""
    announcement = f"Now on {page_name} page. {content_summary}"
    return speak_text(announcement)


def announce_injury_analysis(severity: str, emergency_level: str, has_steps: bool = True) -> bool:
    """Announce injury analysis results."""
    severity_announcement = {
        "SEVERE": "Severe injury detected. Urgent medical attention needed.",
        "MODERATE": "Moderate injury detected. Professional medical attention recommended within 24 hours.",
        "MINOR": "Minor injury detected. Follow first aid steps.",
        "UNKNOWN": "Injury detected. Review first aid steps."
    }
    
    emergency_announcement = {
        "EMERGENCY": "This is an emergency. Call emergency services immediately at 9-1-1.",
        "URGENT": "This is urgent. Seek medical attention within hours.",
        "ROUTINE": "This is routine. Follow first aid steps."
    }
    
    announcement = f"{severity_announcement.get(severity, '')} {emergency_announcement.get(emergency_level, '')}"
    if has_steps:
        announcement += " First aid steps are available. Press the space bar or say 'read steps' to hear them."
    
    return speak_text(announcement)


def announce_first_aid_steps(steps_text: str) -> bool:
    """Announce first aid steps in a structured way."""
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
        full_text = "First aid steps. " + ". ".join([f"Step {i+1}. {step}" for i, step in enumerate(steps_only)])
    else:
        full_text = steps_text
    
    return speak_text(full_text, rate=0.9)  # Slightly slower for instructions


def announce_record_created(record_type: str) -> bool:
    """Announce when a record is created."""
    announcement = f"Your {record_type} record has been saved successfully."
    return speak_text(announcement)


def announce_statistics(stats: Dict[str, Any]) -> bool:
    """Announce statistics in a natural way."""
    total = stats.get("total_records", 0)
    active = stats.get("active_injuries", 0)
    healed = stats.get("healed_injuries", 0)
    
    announcement = f"You have {total} total health records. {active} active injuries. {healed} healed injuries."
    return speak_text(announcement)


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


def speak_welcome_message() -> bool:
    """Welcome message for voice assistant."""
    welcome = """
    Welcome to the First Aid Assistant voice mode. 
    You can navigate using voice commands. 
    Say 'help' or 'what can I say' to hear available commands.
    Say the page name to navigate, or say 'go to' followed by the page name.
    """
    return speak_text(welcome, rate=0.9)


def speak_help_message() -> bool:
    """Help message with available commands."""
    commands = get_voice_navigation_commands()
    help_text = "Available voice commands: "
    help_text += ". ".join([f"Say '{cmd}' to {action}" for cmd, action in commands.items() if not cmd.startswith("read")])
    help_text += ". To hear first aid steps, say 'read steps'. To stop speaking, say 'stop'."
    return speak_text(help_text, rate=0.85)

