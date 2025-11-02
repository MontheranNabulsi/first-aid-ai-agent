import streamlit as st
import google.generativeai as genai
from PIL import Image
from typing import Optional, Dict, Any, List

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Use current recommended model names/aliases
# The 'gemini-2.5-flash' model is multimodal, handling both vision and text.
VISION_MODEL = "gemini-2.5-flash"
TEXT_MODEL = "gemini-2.5-flash"

# Safety settings - Block unsafe content but allow medical discussions
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},  # Allow medical content
]

# Generation configuration - Lower temperature for more consistent, factual responses
GENERATION_CONFIG = {
    "temperature": 0.3,  # Lower = more factual, less creative
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}


def get_medical_disclaimer():
    """Returns a standard medical disclaimer."""
    return """
    ⚠️ **MEDICAL DISCLAIMER**: 
    This AI assistant provides general first aid information only and is NOT a substitute for professional medical care. 
    Always seek immediate professional medical attention for serious injuries, especially if there's:
    - Severe bleeding
    - Difficulty breathing
    - Loss of consciousness
    - Suspected broken bones
    - Head injuries
    - Burns covering large areas
    
    **In emergencies, call your local emergency number immediately (e.g., 911, 999, 112).**
    """


def analyze_image(uploaded_file, return_structured=False):
    """
    Analyze an image using the Gemini Vision model.
    Enhanced version with severity assessment and structured output.
    """
    try:
        image = Image.open(uploaded_file)
        model = genai.GenerativeModel(
            VISION_MODEL,
            safety_settings=SAFETY_SETTINGS,
            generation_config=GENERATION_CONFIG
        )

        if return_structured:
            # Enhanced prompt with structured output
            system_prompt = """You are a medical first aid assistant analyzing an injury image. 
            Your task is to:
            1. Describe the visible injury or condition clearly and medically accurately
            2. Assess the severity level: MINOR, MODERATE, or SEVERE
            3. Note any visible signs of emergency (excessive bleeding, deformity, etc.)
            4. Provide initial observations only - NOT diagnosis or treatment
            
            Respond in this structured format:
            ANALYSIS: [Detailed description of what you see]
            SEVERITY: [MINOR/MODERATE/SEVERE]
            OBSERVATIONS: [Key visible signs]
            """
            
            user_prompt = """Analyze this injury image following the guidelines. 
            Be specific about what you can see (color, size, location, any visible damage).
            Assess severity based on visible indicators only."""
            
            response = model.generate_content([system_prompt, user_prompt, image])
            
            # Check for blocked content before accessing response
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                if hasattr(response.prompt_feedback, "block_reason") and response.prompt_feedback.block_reason:
                    block_reason = str(response.prompt_feedback.block_reason)
                    raise Exception(f"Content was blocked by safety filters. Reason: {block_reason}. Please try a different image or describe the injury in text.")
            
            # Check if response has candidates
            if not hasattr(response, "candidates") or not response.candidates:
                raise Exception("API response was empty. This may be due to safety filters blocking the content.")
            
            if hasattr(response, "text") and response.text:
                analysis_text = response.text.strip()
                
                # Parse structured response
                result = {
                    "analysis": analysis_text,
                    "severity": "UNKNOWN",
                    "recommendation": "Consult with healthcare professional."
                }
                
                # Extract severity from response
                if "SEVERITY:" in analysis_text:
                    severity_line = [line for line in analysis_text.split("\n") if "SEVERITY:" in line]
                    if severity_line:
                        severity = severity_line[0].split("SEVERITY:")[-1].strip().upper()
                        result["severity"] = severity
                
                # Add recommendation based on severity
                if "SEVERE" in result["severity"]:
                    result["recommendation"] = "🚨 URGENT: Seek immediate professional medical attention. Call emergency services if needed."
                elif "MODERATE" in result["severity"]:
                    result["recommendation"] = "⚠️ Recommend seeing a healthcare professional soon, within 24 hours."
                elif "MINOR" in result["severity"]:
                    result["recommendation"] = "✅ Minor injury. Follow first aid steps and monitor. See a doctor if symptoms worsen."
                
                return result
            
            return {
                "analysis": "No visible injury detected in the image.",
                "severity": "UNKNOWN",
                "recommendation": "If you have concerns, consult a healthcare professional."
            }
        else:
            # Original simple prompt for backward compatibility
            prompt = "Describe clearly and medically what visible injury or condition appears in this image."
            response = model.generate_content([prompt, image])
            
            # Check for blocked content
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                if hasattr(response.prompt_feedback, "block_reason") and response.prompt_feedback.block_reason:
                    block_reason = str(response.prompt_feedback.block_reason)
                    raise Exception(f"Content was blocked by safety filters. Reason: {block_reason}. Please try a different image or describe the injury in text.")
            
            # Check if response has candidates
            if not hasattr(response, "candidates") or not response.candidates:
                raise Exception("API response was empty. This may be due to safety filters blocking the content.")
            
            if hasattr(response, "text") and response.text:
                return response.text.strip()
            return "No description detected."

    except Exception as e:
        # Check if the error is related to a missing model and provide a helpful tip
        if "404" in str(e) and "models" in str(e):
             st.error("Error: Model not found. Please ensure you are using the latest 'google-genai' library and supported model names.")
        else:
             st.error(f"Error analyzing image: {e}")
        
        if return_structured:
            return {
                "analysis": "Unable to analyze the image. Please try again or describe the injury.",
                "severity": "UNKNOWN",
                "recommendation": "Please consult a healthcare professional."
            }
        return "Unable to analyze the image."


def assess_emergency_level(injury_description: str) -> str:
    """
    Quickly assess if the situation requires immediate emergency attention.
    Returns: "EMERGENCY", "URGENT", or "ROUTINE"
    """
    try:
        model = genai.GenerativeModel(
            TEXT_MODEL,
            safety_settings=SAFETY_SETTINGS,
            generation_config={"temperature": 0.2, "max_output_tokens": 50}
        )

        prompt = f"""Based on this description: "{injury_description}", classify as:
        - EMERGENCY: Needs immediate 911/emergency services (severe bleeding, unconscious, not breathing)
        - URGENT: Needs medical attention within hours (broken bones, severe burns, head injury)
        - ROUTINE: Can wait for medical consultation (minor cuts, bruises, small burns)
        
        Respond with only one word: EMERGENCY, URGENT, or ROUTINE"""
        
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            level = response.text.strip().upper()
            if "EMERGENCY" in level:
                return "EMERGENCY"
            elif "URGENT" in level:
                return "URGENT"
            else:
                return "ROUTINE"
        
        return "ROUTINE"
    
    except Exception as e:
        # Default to ROUTINE on error to avoid false emergencies
        return "ROUTINE"


def generate_first_aid_steps(injury_description, severity=None, return_structured=False):
    """
    Generate short, step-by-step first aid instructions.
    Enhanced version with severity awareness and structured output.
    """
    try:
        model = genai.GenerativeModel(
            TEXT_MODEL,
            safety_settings=SAFETY_SETTINGS,
            generation_config=GENERATION_CONFIG
        )

        if return_structured:
            # Enhanced system prompt with safety guidelines
            system_prompt = """You are a certified first aid instructor providing step-by-step first aid instructions.
            
            IMPORTANT SAFETY GUIDELINES:
            - Only provide standard, well-established first aid procedures
            - Always prioritize safety: Check for danger, ensure scene is safe
            - For severe injuries, emphasize seeking professional medical care immediately
            - Never diagnose conditions - only provide first aid guidance
            - Include when to seek professional medical help
            
            Structure your response as:
            IMMEDIATE_ACTIONS: [What to do first - ensure safety]
            STEPS: [Numbered step-by-step instructions]
            WARNINGS: [Important safety warnings]
            WHEN_TO_SEEK_HELP: [Clear indicators for professional medical care]
            """

            # Context-aware user prompt
            severity_context = ""
            if severity:
                severity_context = f"Severity assessed as: {severity}. Adjust instructions accordingly. "
            
            user_prompt = f"""Provide safe, step-by-step first aid instructions for: {injury_description}.
            
            {severity_context}
            Remember:
            - Be clear and concise
            - Prioritize safety
            - Use simple language that anyone can follow
            - Include specific warnings if applicable
            - Always mention when professional medical attention is needed
            """
            
            response = model.generate_content([system_prompt, user_prompt])
            
            if hasattr(response, "text") and response.text:
                steps_text = response.text.strip()
                
                # Parse structured response
                result = {
                    "steps": steps_text,
                    "has_warnings": "WARNINGS:" in steps_text or "URGENT" in steps_text.upper(),
                    "needs_emergency": "SEVERE" in str(severity).upper() if severity else False
                }
                
                return result
            
            return {
                "steps": "Unable to generate first aid instructions. Please consult a healthcare professional.",
                "has_warnings": True,
                "needs_emergency": False
            }
        else:
            # Original simple prompt for backward compatibility
            prompt = f"Provide concise, safe, step-by-step first aid instructions for: {injury_description}."
            response = model.generate_content(prompt)
            if hasattr(response, "text") and response.text:
                return response.text.strip()
            return "No first aid steps generated."

    except Exception as e:
        st.error(f"Error generating first aid steps: {e}")
        if return_structured:
            return {
                "steps": "Unable to generate first aid instructions. Please consult a healthcare professional immediately.",
                "has_warnings": True,
                "needs_emergency": True
            }
        return "Unable to generate first aid instructions."


def analyze_existing_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze an existing health record and provide follow-up care recommendations.
    
    Args:
        record: Health record dictionary
        
    Returns:
        Dict with follow-up analysis, medication recommendations, recovery assessment
    """
    try:
        model = genai.GenerativeModel(
            TEXT_MODEL,
            safety_settings=SAFETY_SETTINGS,
            generation_config=GENERATION_CONFIG
        )
        
        # Build context from record
        injury_type = record.get('injury_type', 'Unknown')
        severity = record.get('severity', 'UNKNOWN')
        status = record.get('status', 'active')
        body_part = record.get('body_part', 'Unknown')
        initial_analysis = record.get('initial_analysis', {}).get('ai_analysis', '')
        
        # Recovery data
        recovery = record.get('recovery', {})
        progress = recovery.get('progress_percentage', 0)
        pain_level = recovery.get('pain_level')
        recovery_status = recovery.get('status', 'initial')
        recovery_updates = recovery.get('updates', [])
        
        # Medication data
        medications = record.get('medications', [])
        med_list = []
        for med in medications:
            med_list.append(f"- {med.get('name', 'Unknown')}: {med.get('dosage', '')} {med.get('frequency', '')}")
        medications_str = "\n".join(med_list) if med_list else "No medications recorded"
        
        # Time since injury
        from datetime import datetime
        try:
            injury_date = datetime.fromisoformat(record.get('timestamp', ''))
            days_since = (datetime.now() - injury_date).days
        except:
            days_since = 0
        
        # Notes
        notes = record.get('notes', [])
        recent_notes = notes[-3:] if len(notes) > 3 else notes
        notes_str = "\n".join([f"- {note.get('content', '')}" for note in recent_notes]) if recent_notes else "No recent notes"
        
        # Photos available
        photos = record.get('photos', {})
        has_progress_photos = len(photos.get('during', [])) > 0 or len(photos.get('after', [])) > 0
        
        system_prompt = """You are a certified first aid instructor and medical follow-up care advisor. 
        Your role is to analyze existing injury records and provide:
        1. Recovery progress assessment
        2. Medication management recommendations
        3. Follow-up care instructions
        4. Warning signs to watch for
        5. When to seek additional medical attention
        
        Be specific, actionable, and safety-focused. Always emphasize professional medical care when needed."""
        
        user_prompt = f"""Analyze this injury record and provide follow-up care recommendations:

INJURY INFORMATION:
- Type: {injury_type}
- Body Part: {body_part}
- Initial Severity: {severity}
- Days Since Injury: {days_since} days
- Current Status: {status}
- Recovery Status: {recovery_status}
- Recovery Progress: {progress}%
- Pain Level: {pain_level if pain_level is not None else 'Not recorded'}/10

INITIAL ANALYSIS:
{initial_analysis[:500] if initial_analysis else 'No initial analysis available'}

RECOVERY UPDATES:
{len(recovery_updates)} progress updates recorded
{notes_str}

CURRENT MEDICATIONS:
{medications_str}

PHOTOS: {'Progress photos available' if has_progress_photos else 'Initial photo only'}

Please provide:
1. RECOVERY_ASSESSMENT: How is the recovery progressing? Is it normal?
2. MEDICATION_RECOMMENDATIONS: Review current medications and suggest any changes or additions
3. FOLLOW_UP_CARE: What should the user do next? Daily care instructions
4. WARNING_SIGNS: What signs should they watch for that indicate complications?
5. WHEN_TO_SEEK_HELP: When should they seek additional medical attention?
6. RECOVERY_TIMELINE: Expected recovery timeline based on current progress

Structure your response clearly with these sections."""
        
        response = model.generate_content([system_prompt, user_prompt])
        
        if hasattr(response, "text") and response.text:
            analysis_text = response.text.strip()
            
            # Parse structured response
            result = {
                "follow_up_analysis": analysis_text,
                "recovery_assessment": "",
                "medication_recommendations": "",
                "follow_up_care": "",
                "warning_signs": "",
                "when_to_seek_help": "",
                "recovery_timeline": ""
            }
            
            # Try to extract structured sections
            sections = {
                "RECOVERY_ASSESSMENT": "recovery_assessment",
                "MEDICATION_RECOMMENDATIONS": "medication_recommendations",
                "FOLLOW_UP_CARE": "follow_up_care",
                "WARNING_SIGNS": "warning_signs",
                "WHEN_TO_SEEK_HELP": "when_to_seek_help",
                "RECOVERY_TIMELINE": "recovery_timeline"
            }
            
            for key, value in sections.items():
                if key in analysis_text:
                    # Extract section content
                    lines = analysis_text.split('\n')
                    in_section = False
                    section_content = []
                    for line in lines:
                        if key in line:
                            in_section = True
                            # Remove the section header
                            content = line.split(':', 1)
                            if len(content) > 1:
                                section_content.append(content[1].strip())
                            continue
                        if in_section:
                            if any(other_key in line for other_key in sections.keys() if other_key != key):
                                break
                            if line.strip():
                                section_content.append(line.strip())
                    result[value] = "\n".join(section_content) if section_content else ""
            
            return result
        
        return {
            "follow_up_analysis": "Unable to generate follow-up analysis. Please consult a healthcare professional.",
            "recovery_assessment": "",
            "medication_recommendations": "",
            "follow_up_care": "",
            "warning_signs": "",
            "when_to_seek_help": "",
            "recovery_timeline": ""
        }
    
    except Exception as e:
        st.error(f"Error analyzing record: {e}")
        return {
            "follow_up_analysis": f"Error: {str(e)}. Please try again or consult a healthcare professional.",
            "recovery_assessment": "",
            "medication_recommendations": "",
            "follow_up_care": "",
            "warning_signs": "",
            "when_to_seek_help": "",
            "recovery_timeline": ""
        }


def chat_about_record(record: Dict[str, Any], user_message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Have a conversational chat with AI about an existing health record.
    
    Args:
        record: Health record dictionary
        user_message: User's question/message
        chat_history: Previous conversation messages [{"role": "user/assistant", "content": "..."}]
        
    Returns:
        Dict with assistant response and updated chat history
    """
    try:
        model = genai.GenerativeModel(
            TEXT_MODEL,
            safety_settings=SAFETY_SETTINGS,
            generation_config=GENERATION_CONFIG
        )
        
        # Build record context
        injury_type = record.get('injury_type', 'Unknown')
        severity = record.get('severity', 'UNKNOWN')
        status = record.get('status', 'active')
        body_part = record.get('body_part', 'Unknown')
        days_old = 0
        try:
            from datetime import datetime
            injury_date = datetime.fromisoformat(record.get('timestamp', ''))
            days_old = (datetime.now() - injury_date).days
        except:
            pass
        
        recovery = record.get('recovery', {})
        progress = recovery.get('progress_percentage', 0)
        pain_level = recovery.get('pain_level')
        medications = record.get('medications', [])
        medications_str = "\n".join([f"- {med.get('name', '')}: {med.get('dosage', '')}" for med in medications]) if medications else "No medications"
        
        # Build system prompt with record context
        system_prompt = f"""You are a helpful medical assistant having a conversation about a patient's injury record.

INJURY RECORD CONTEXT:
- Injury Type: {injury_type}
- Body Part: {body_part}
- Initial Severity: {severity}
- Current Status: {status}
- Days Since Injury: {days_old} days
- Recovery Progress: {progress}%
- Pain Level: {pain_level if pain_level is not None else 'Not recorded'}/10
- Current Medications: {medications_str}

Your role:
- Answer questions about this injury and recovery
- Provide helpful follow-up care advice
- Review medications and suggest changes if needed
- Identify warning signs and when to seek help
- Be empathetic, clear, and safety-focused
- Always emphasize professional medical care when appropriate
- Keep responses conversational and natural

IMPORTANT: You are NOT diagnosing or prescribing. You are providing guidance based on the record information."""

        # Build conversation history
        if chat_history is None:
            chat_history = []
        
        # Add system context message
        full_conversation = [system_prompt]
        
        # Add chat history
        for msg in chat_history:
            if msg.get('role') == 'user':
                full_conversation.append(f"User: {msg.get('content', '')}")
            elif msg.get('role') == 'assistant':
                full_conversation.append(f"Assistant: {msg.get('content', '')}")
        
        # Add current user message
        full_conversation.append(f"User: {user_message}")
        full_conversation.append("Assistant:")
        
        # Combine into prompt
        conversation_text = "\n\n".join(full_conversation)
        
        user_prompt = f"""Continue the conversation. The user asked: "{user_message}"

Provide a helpful, conversational response based on the injury record context above."""
        
        response = model.generate_content([system_prompt, user_prompt])
        
        if hasattr(response, "text") and response.text:
            assistant_response = response.text.strip()
            
            # Update chat history
            updated_history = chat_history.copy()
            updated_history.append({"role": "user", "content": user_message})
            updated_history.append({"role": "assistant", "content": assistant_response})
            
            return {
                "response": assistant_response,
                "chat_history": updated_history,
                "success": True
            }
        
        return {
            "response": "I'm sorry, I couldn't generate a response. Please try again or consult a healthcare professional.",
            "chat_history": chat_history,
            "success": False
        }
    
    except Exception as e:
        st.error(f"Error in chat: {e}")
        return {
            "response": f"I encountered an error: {str(e)}. Please try again or consult a healthcare professional.",
            "chat_history": chat_history if chat_history else [],
            "success": False
        }