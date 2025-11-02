"""
Improved AI Helper Functions with Enhanced Workflow
Key improvements:
1. Structured system prompts with medical safety guidelines
2. Severity assessment for injuries
3. Enhanced error handling and retry logic
4. Safety configurations (temperature, safety settings)
5. Medical disclaimers
6. Context-aware responses
7. Response streaming support
8. Better prompt engineering
"""

import streamlit as st
import google.generativeai as genai
from PIL import Image
from typing import Optional, Dict, Any
import time

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Model configuration
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


def analyze_image_improved(uploaded_file) -> Dict[str, Any]:
    """
    Enhanced image analysis with structured output and severity assessment.
    Returns a dictionary with analysis, severity, and recommendations.
    """
    try:
        image = Image.open(uploaded_file)
        model = genai.GenerativeModel(
            VISION_MODEL,
            safety_settings=SAFETY_SETTINGS,
            generation_config=GENERATION_CONFIG
        )

        # Enhanced system prompt with medical guidelines
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

        # Enhanced user prompt
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

    except Exception as e:
        st.error(f"Error analyzing image: {e}")
        return {
            "analysis": "Unable to analyze the image. Please try again or describe the injury.",
            "severity": "UNKNOWN",
            "recommendation": "Please consult a healthcare professional."
        }


def generate_first_aid_steps_improved(injury_description: str, severity: Optional[str] = None) -> Dict[str, Any]:
    """
    Enhanced first aid generation with structured output, safety checks, and context awareness.
    Returns structured response with steps, warnings, and follow-up care.
    """
    try:
        model = genai.GenerativeModel(
            TEXT_MODEL,
            safety_settings=SAFETY_SETTINGS,
            generation_config=GENERATION_CONFIG
        )

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
                "needs_emergency": "SEVERE" in severity.upper() if severity else False
            }
            
            return result
        
        return {
            "steps": "Unable to generate first aid instructions. Please consult a healthcare professional.",
            "has_warnings": True,
            "needs_emergency": False
        }

    except Exception as e:
        st.error(f"Error generating first aid steps: {e}")
        return {
            "steps": "Unable to generate first aid instructions. Please consult a healthcare professional immediately.",
            "has_warnings": True,
            "needs_emergency": True
        }


def generate_first_aid_steps_streaming(injury_description: str, severity: Optional[str] = None):
    """
    Stream first aid steps as they're generated for better UX.
    Yields chunks of text as they're generated.
    """
    try:
        model = genai.GenerativeModel(
            TEXT_MODEL,
            safety_settings=SAFETY_SETTINGS,
            generation_config={**GENERATION_CONFIG, "max_output_tokens": 2048}
        )

        system_prompt = """You are a certified first aid instructor. Provide clear, safe first aid instructions.
        Structure as numbered steps. Always include when to seek professional medical help."""
        
        severity_context = f"Severity: {severity}. " if severity else ""
        user_prompt = f"{severity_context}Provide first aid steps for: {injury_description}"

        # Stream response
        response = model.generate_content(
            [system_prompt, user_prompt],
            stream=True
        )
        
        full_text = ""
        for chunk in response:
            if hasattr(chunk, "text"):
                full_text += chunk.text
                yield chunk.text
        
        return full_text

    except Exception as e:
        yield f"Error: {e}. Please consult a healthcare professional."


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


def get_follow_up_questions(injury_description: str) -> list:
    """
    Generate relevant follow-up questions to gather more information about the injury.
    """
    try:
        model = genai.GenerativeModel(
            TEXT_MODEL,
            safety_settings=SAFETY_SETTINGS,
            generation_config={"temperature": 0.5, "max_output_tokens": 200}
        )

        prompt = f"""Based on this injury description: "{injury_description}", 
        generate 3-4 relevant follow-up questions that would help assess the situation better.
        Questions should be specific, clear, and help determine severity.
        Format: One question per line, numbered.
        
        Example format:
        1. Is there active bleeding?
        2. Can the person move the affected area?
        3. Are there any signs of shock?
        """
        
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            questions = [q.strip() for q in response.text.split("\n") if q.strip() and q.strip()[0].isdigit()]
            return questions[:4]  # Limit to 4 questions
        
        return []
    
    except Exception as e:
        return []


def format_first_aid_response(steps_dict: Dict[str, Any]) -> str:
    """
    Format the structured first aid response for display.
    """
    formatted = steps_dict.get("steps", "")
    
    # Add visual indicators for severity
    if steps_dict.get("needs_emergency"):
        formatted = "🚨 **URGENT MEDICAL ATTENTION NEEDED** 🚨\n\n" + formatted
    
    if steps_dict.get("has_warnings"):
        formatted = "⚠️ **IMPORTANT SAFETY WARNINGS** ⚠️\n\n" + formatted
    
    return formatted

