import streamlit as st
import google.generativeai as genai
from PIL import Image
from typing import Optional, Dict, Any

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