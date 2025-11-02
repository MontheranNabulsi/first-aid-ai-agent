import streamlit as st
import pandas as pd
from utils.map_helper import (
    find_nearby_facilities, 
    find_nearby_facilities_by_coords,
    show_facilities_map, 
    parse_facilities_to_df,
    reverse_geocode,
    get_navigation_url,
    create_interactive_map
)
from streamlit_folium import folium_static
from utils.ai_helpers import (
    analyze_image, 
    generate_first_aid_steps, 
    assess_emergency_level,
    get_medical_disclaimer,
    analyze_existing_record,
    chat_about_record
)
from utils.health_records import (
    init_health_records,
    create_injury_record,
    save_record,
    get_all_records,
    get_record,
    filter_records,
    update_recovery_progress,
    mark_first_aid_step_completed,
    add_note_to_record,
    add_medication,
    get_statistics,
    format_record_date,
    get_record_age_days,
    delete_record
)
from utils.voice_assistant import (
    speak_text,
    stop_speaking,
    listen_for_command,
    announce_page_content,
    announce_injury_analysis,
    announce_first_aid_steps,
    announce_record_created,
    announce_statistics,
    process_voice_command,
    speak_welcome_message,
    speak_help_message
)
from streamlit_js_eval import streamlit_js_eval


def display_hospital_with_navigation(row, idx):
    """Display a hospital entry with navigation button to open map app"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if "lat" in row and "lon" in row:
            st.markdown(f"**{idx + 1}. {row['name']}**")
            st.markdown(f"📍 {row['address']}")
            st.caption(f"Coordinates: ({row['lat']:.4f}, {row['lon']:.4f})")
        else:
            st.markdown(f"**{idx + 1}. {row['name']}**")
            st.markdown(f"📍 {row['address']}")
    
    with col2:
        if "lat" in row and "lon" in row:
            nav_url = get_navigation_url(row['lat'], row['lon'], row['name'])
            # Open navigation URL in device's map app (Google Maps, Apple Maps, etc.)
            st.link_button("🗺️ Navigate", nav_url, use_container_width=True)


st.set_page_config(page_title="AidNexus - AI First Aid Assistant", layout="wide", page_icon="🩹")

# AidNexus Header with Logo
st.markdown("""
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 2rem;">
        <h1 style="font-size: 3.5rem; margin: 0; background: linear-gradient(90deg, #1e88e5, #00acc1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
            🩹 Aid<span style="color: #1e88e5;">Nexus</span>
        </h1>
        <p style="font-size: 1.2rem; color: #666; margin-top: 0.5rem; font-weight: 500;">
            Your AI-Powered First Aid Companion
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown(
    "Upload an image of an injury or describe it in text, and I'll help you with immediate first aid steps. "
    "You can also find nearby hospitals."
)

# Initialize health records
init_health_records()

# Initialize voice assistant
if 'voice_assistant_enabled' not in st.session_state:
    st.session_state.voice_assistant_enabled = False
if 'last_spoken' not in st.session_state:
    st.session_state.last_spoken = None
if 'use_premium_voices' not in st.session_state:
    st.session_state.use_premium_voices = True  # Use best available voices

# Sidebar options
with st.sidebar:
    # AidNexus Logo in Sidebar
    st.markdown("""
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 1.5rem; border-bottom: 2px solid #e0e0e0;">
            <h2 style="font-size: 2rem; margin: 0; color: #1e88e5;">
                🩹 Aid<span style="color: #00acc1;">Nexus</span>
            </h2>
            <p style="font-size: 0.85rem; color: #666; margin-top: 0.25rem;">
                AI First Aid Assistant
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.header("Navigation")
    
    # Voice Assistant Toggle
    st.markdown("---")
    voice_enabled = st.checkbox(
        "🎤 Voice Assistant (Accessibility)",
        value=st.session_state.voice_assistant_enabled,
        help="Enable voice commands and audio announcements for accessibility"
    )
    st.session_state.voice_assistant_enabled = voice_enabled
    
    if voice_enabled:
        # Premium voice settings
        st.session_state.use_premium_voices = st.checkbox(
            "🎙️ Premium Voices (Natural/Siri-like)", 
            value=st.session_state.get('use_premium_voices', True),
            help="Uses the best available neural voices for natural speech (like Siri/Gemini)"
        )
        
        # Welcome message on first enable
        if 'voice_welcome_shown' not in st.session_state:
            speak_welcome_message()
            st.session_state.voice_welcome_shown = True
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎤 Listen", use_container_width=True):
                st.session_state.listen_command = True
        with col2:
            if st.button("🔇 Stop", use_container_width=True):
                stop_speaking()
                st.session_state.listen_command = False
        
        if st.button("❓ Voice Help", use_container_width=True):
            speak_help_message()
    
    st.markdown("---")
    page = st.radio("Go to:", ["First Aid Guide", "Find Nearby Hospitals", "📋 My Health Records"])
    
    # Quick stats in sidebar
    if page == "📋 My Health Records":
        stats = get_statistics()
        if stats["total_records"] > 0:
            st.markdown("---")
            st.markdown("### 📊 Quick Stats")
            st.metric("Total Records", stats["total_records"])
            st.metric("Active Injuries", stats["active_injuries"])
            st.metric("Healed", stats["healed_injuries"])
            
            # Announce stats if voice enabled
            if voice_enabled and st.session_state.get('announce_stats', False):
                announce_statistics(stats)
                st.session_state.announce_stats = False

# Handle voice commands
if st.session_state.get('listen_command', False) and st.session_state.voice_assistant_enabled:
    with st.spinner("🎤 Listening..."):
        use_premium = st.session_state.get('use_premium_voices', True)
        speak_text("I'm listening. Please speak your command now.", rate=0.92, pitch=1.0, use_google_tts=use_premium and "GCP_TTS_API_KEY" in st.secrets)
        command_result = listen_for_command()
        
        if command_result and 'text' in command_result:
            command = command_result['text']
            action = process_voice_command(command)
            
            if action:
                if action in ["First Aid Guide", "Find Nearby Hospitals", "📋 My Health Records"]:
                    # Navigate to page
                    page = action
                    speak_text(f"Of course! Taking you to {action} now.", rate=0.9, pitch=1.13)
                    st.rerun()
                elif action == "read_first_aid_steps":
                    if st.session_state.get('last_spoken'):
                        announce_first_aid_steps(st.session_state.last_spoken)
                elif action == "show_voice_help":
                    speak_help_message()
                elif action == "stop_speaking":
                    stop_speaking()
                    speak_text("I've stopped speaking. How else can I help?", rate=0.9, pitch=1.12)
            else:
                speak_text(f"I'm sorry, I didn't quite catch that. You said '{command}'. Please say 'help' to hear all available commands.", rate=0.88, pitch=1.1)
        
        st.session_state.listen_command = False

# Announce page navigation if voice enabled
if st.session_state.voice_assistant_enabled:
    page_announcements = {
        "First Aid Guide": "AidNexus First Aid Guide page. Upload an image or describe an injury to get first aid instructions.",
        "Find Nearby Hospitals": "AidNexus Find Nearby Hospitals page. Search for nearby medical facilities.",
        "📋 My Health Records": "AidNexus My Health Records page. View and manage your injury history."
    }
    if 'current_page' not in st.session_state or st.session_state.current_page != page:
        if page in page_announcements:
            announce_page_content(page, page_announcements[page])
        st.session_state.current_page = page

# --- PAGE 1: First Aid Guide ---
if page == "First Aid Guide":
    st.subheader("Analyze Injury")
    
    # Accessibility: ARIA labels and keyboard navigation hints
    st.markdown("""
    <div role="region" aria-label="First Aid Guide">
    <p style="font-size: 0.9em; color: #666;">
    💡 <strong>Accessibility:</strong> Use voice assistant (sidebar) for audio navigation. 
    Say "read steps" to hear first aid instructions. Say "help" for voice commands.
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mode selection: New Injury or Existing Record Analysis
    analysis_mode = st.radio(
        "Analysis Mode:",
        ["🆕 Analyze New Injury", "📋 Analyze Existing Record"],
        horizontal=True,
        help="Choose to analyze a new injury or get follow-up care for an existing record"
    )
    
    st.markdown("---")
    
    if analysis_mode == "📋 Analyze Existing Record":
        # Show existing records for selection
        records = get_all_records()
        active_records = [r for r in records if r.get('status') in ['active', 'healing', 'recovering']]
        
        if not active_records:
            st.info("📋 No active records found. Create a record by analyzing a new injury first.")
            st.markdown("**To create a record:**")
            st.markdown("1. Switch to 'Analyze New Injury' mode")
            st.markdown("2. Upload an image or describe an injury")
            st.markdown("3. Click 'Analyze' - the record will be saved automatically")
        else:
            st.markdown("### Select Record to Analyze")
            
            # Record selection dropdown
            record_options = {}
            for record in active_records:
                record_date = format_record_date(record)
                injury_type = record.get('injury_type', 'Unknown Injury')
                severity = record.get('severity', 'UNKNOWN')
                status = record.get('status', 'active')
                progress = record.get('recovery', {}).get('progress_percentage', 0)
                
                display_text = f"{injury_type} | {record_date} | {severity} | {status.title()} ({progress}%)"
                record_options[display_text] = record.get('id')
            
            selected_record_display = st.selectbox(
                "Choose a record:",
                options=list(record_options.keys()),
                help="Select an existing injury record to get AI follow-up care recommendations"
            )
            
            selected_record_id = record_options[selected_record_display]
            selected_record = get_record(selected_record_id)
            
            if selected_record:
                # Show record summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Severity", selected_record.get('severity', 'UNKNOWN'))
                with col2:
                    st.metric("Status", selected_record.get('status', 'active').title())
                with col3:
                    progress = selected_record.get('recovery', {}).get('progress_percentage', 0)
                    st.metric("Progress", f"{progress}%")
                
                # Show record details
                with st.expander("📋 Record Details"):
                    st.write(f"**Injury:** {selected_record.get('injury_type', 'Unknown')}")
                    st.write(f"**Body Part:** {selected_record.get('body_part', 'Not specified')}")
                    st.write(f"**Date:** {format_record_date(selected_record)}")
                    days_old = get_record_age_days(selected_record)
                    st.write(f"**Age:** {days_old} days")
                    
                    if selected_record.get('medications'):
                        st.write("**Current Medications:**")
                        for med in selected_record.get('medications', []):
                            st.write(f"- {med.get('name', 'Unknown')}: {med.get('dosage', '')} {med.get('frequency', '')}")
                
                # Analyze button
                if st.button("🤖 Analyze Record & Get Follow-up Care", use_container_width=True, type="primary"):
                    with st.spinner("🤖 Analyzing record and generating follow-up care recommendations..."):
                        follow_up_analysis = analyze_existing_record(selected_record)
                        
                        st.success("✅ Follow-up analysis completed!")
                        
                        # Display structured results
                        st.markdown("### 📊 Recovery Assessment")
                        if follow_up_analysis.get('recovery_assessment'):
                            st.info(follow_up_analysis['recovery_assessment'])
                        else:
                            st.info("Review the full analysis below for recovery assessment.")
                        
                        st.markdown("### 💊 Medication Recommendations")
                        if follow_up_analysis.get('medication_recommendations'):
                            st.warning(follow_up_analysis['medication_recommendations'])
                        else:
                            st.info("Review the full analysis below for medication recommendations.")
                        
                        st.markdown("### 🩹 Follow-up Care Instructions")
                        if follow_up_analysis.get('follow_up_care'):
                            st.success(follow_up_analysis['follow_up_care'])
                        else:
                            st.info("Review the full analysis below for follow-up care.")
                        
                        st.markdown("### ⚠️ Warning Signs to Watch For")
                        if follow_up_analysis.get('warning_signs'):
                            st.error(follow_up_analysis['warning_signs'])
                        else:
                            st.info("Review the full analysis below for warning signs.")
                        
                        st.markdown("### 🏥 When to Seek Additional Medical Help")
                        if follow_up_analysis.get('when_to_seek_help'):
                            st.error(follow_up_analysis['when_to_seek_help'])
                        else:
                            st.info("Review the full analysis below for when to seek help.")
                        
                        st.markdown("### 📅 Recovery Timeline")
                        if follow_up_analysis.get('recovery_timeline'):
                            st.info(follow_up_analysis['recovery_timeline'])
                        else:
                            st.info("Review the full analysis below for recovery timeline.")
                        
                        # Full analysis
                        with st.expander("📄 Full Follow-up Analysis"):
                            st.markdown(follow_up_analysis.get('follow_up_analysis', 'No analysis available'))
                        
                        # Save analysis to record
                        if st.button("💾 Save Analysis to Record"):
                            from utils.health_records import add_note_to_record
                            from datetime import datetime
                            analysis_note = f"AI Follow-up Analysis ({datetime.now().strftime('%Y-%m-%d %H:%M')}):\n{follow_up_analysis.get('follow_up_analysis', '')[:500]}"
                            add_note_to_record(selected_record_id, analysis_note)
                            st.success("✅ Analysis saved to record!")
                            st.rerun()
                        
                        # Voice announcement if enabled
                        if st.session_state.voice_assistant_enabled:
                            from utils.voice_assistant import speak_text
                            speak_text("Follow-up care analysis completed. Please review the recommendations displayed.", rate=0.92, pitch=1.0)
                
                # Chat Interface for Record
                st.markdown("---")
                st.markdown("### 💬 Chat About This Record")
                st.markdown("Ask questions about this injury, recovery progress, medications, or any concerns you have.")
                
                # Initialize chat history for this record
                chat_key = f"chat_history_{selected_record_id}"
                if chat_key not in st.session_state:
                    st.session_state[chat_key] = []
                
                # Display chat history
                if st.session_state[chat_key]:
                    st.markdown("#### Conversation History")
                    chat_container = st.container()
                    with chat_container:
                        for i, msg in enumerate(st.session_state[chat_key]):
                            if msg.get('role') == 'user':
                                with st.chat_message("user"):
                                    st.write(msg.get('content', ''))
                            elif msg.get('role') == 'assistant':
                                with st.chat_message("assistant"):
                                    st.write(msg.get('content', ''))
                
                # Chat input
                user_question = st.text_input(
                    "Ask a question about this record:",
                    placeholder="e.g., Is my recovery normal? What should I watch for? Should I adjust my medication?",
                    key=f"chat_input_{selected_record_id}"
                )
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    send_chat = st.button("💬 Send", key=f"send_chat_{selected_record_id}", use_container_width=True)
                
                with col2:
                    if st.button("🗑️ Clear Chat", key=f"clear_chat_{selected_record_id}", use_container_width=True):
                        st.session_state[chat_key] = []
                        st.rerun()
                
                if send_chat and user_question:
                    with st.spinner("🤖 AI is thinking..."):
                        chat_result = chat_about_record(
                            selected_record,
                            user_question,
                            st.session_state[chat_key]
                        )
                        
                        if chat_result.get('success'):
                            # Update chat history
                            st.session_state[chat_key] = chat_result.get('chat_history', [])
                            st.success("✅ Response generated!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to get response. Please try again.")
                
                # Quick question suggestions
                st.markdown("#### 💡 Quick Questions:")
                quick_questions = [
                    "Is my recovery normal?",
                    "What signs should I watch for?",
                    "Should I see a doctor?",
                    "Are my medications appropriate?",
                    "What should I do next?"
                ]
                
                cols = st.columns(len(quick_questions))
                for idx, question in enumerate(quick_questions):
                    with cols[idx]:
                        if st.button(f"❓ {question}", key=f"quick_q_{idx}_{selected_record_id}", use_container_width=True):
                            with st.spinner("🤖 AI is thinking..."):
                                chat_result = chat_about_record(
                                    selected_record,
                                    question,
                                    st.session_state[chat_key]
                                )
                                
                                if chat_result.get('success'):
                                    st.session_state[chat_key] = chat_result.get('chat_history', [])
                                    st.rerun()
    
    # New Injury Analysis Mode
    if analysis_mode == "🆕 Analyze New Injury":
        # Enhanced Mode Toggle
        use_enhanced_mode = st.checkbox("✨ Enhanced Mode (Recommended)", value=True, 
                                         help="Enables severity assessment, emergency detection, and structured medical guidance")

    uploaded_image = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])
    injury_description = st.text_area("Or describe the injury:")

    if st.button("Analyze"):
        if uploaded_image:
            with st.spinner("Analyzing image..."):
                if use_enhanced_mode:
                    # Enhanced mode with structured output
                    try:
                        result = analyze_image(uploaded_image, return_structured=True)
                        st.success("✅ Image analyzed successfully.")
                        
                        # Display severity and recommendation
                        severity = result.get("severity", "UNKNOWN")
                        if severity == "SEVERE":
                            st.error(f"🚨 **SEVERE INJURY DETECTED** 🚨\n\n{result.get('recommendation', '')}")
                        elif severity == "MODERATE":
                            st.warning(f"⚠️ **MODERATE INJURY** ⚠️\n\n{result.get('recommendation', '')}")
                        elif severity == "MINOR":
                            st.success(f"✅ **MINOR INJURY** ✅\n\n{result.get('recommendation', '')}")
                        
                        # Show analysis
                        st.markdown(f"**Analysis Result:**\n{result.get('analysis', '')}")
                        
                        # Assess emergency level
                        emergency_level = assess_emergency_level(result.get('analysis', ''))
                        if emergency_level == "EMERGENCY":
                            st.error("🚨 **CALL EMERGENCY SERVICES (911/999/112) IMMEDIATELY** 🚨")
                        elif emergency_level == "URGENT":
                            st.warning("⚠️ **URGENT: Seek medical attention within hours** ⚠️")
                        
                        # Generate first aid steps with severity context
                        st.markdown("### 🩹 First Aid Steps")
                        steps_result = generate_first_aid_steps(
                            result.get('analysis', ''), 
                            severity=severity,
                            return_structured=True
                        )
                        
                        # Extract steps as list for checklist
                        steps_list = []
                        if isinstance(steps_result, dict):
                            steps_text = steps_result.get('steps', '')
                            # Try to parse steps into list
                            lines = steps_text.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-') or line.startswith('*')):
                                    # Clean up step text
                                    step_clean = line.lstrip('0123456789.•-* ).').strip()
                                    if step_clean:
                                        steps_list.append(step_clean)
                            
                            if steps_result.get('needs_emergency'):
                                st.error("🚨 **URGENT MEDICAL ATTENTION NEEDED** 🚨")
                            if steps_result.get('has_warnings'):
                                st.warning("⚠️ **IMPORTANT SAFETY WARNINGS** ⚠️")
                            st.markdown(steps_text)
                            
                            # Voice announcement for accessibility
                            if st.session_state.voice_assistant_enabled:
                                announce_injury_analysis(severity, emergency_level, True)
                                st.session_state.last_spoken = steps_text
                        else:
                            st.write(steps_result)
                            # Try to parse steps from plain text
                            if isinstance(steps_result, str):
                                lines = steps_result.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if line and (line[0].isdigit() or line.startswith('•')):
                                        step_clean = line.lstrip('0123456789.•-* ).').strip()
                                        if step_clean:
                                            steps_list.append(step_clean)
                                # Voice announcement
                                if st.session_state.voice_assistant_enabled:
                                    announce_injury_analysis(severity, emergency_level, True)
                                    st.session_state.last_spoken = steps_result
                        
                        # Auto-save to health records
                        if st.session_state.get('auto_save_records', True):
                            record = create_injury_record(
                                injury_description=injury_description or "Image analysis",
                                severity=severity,
                                emergency_level=emergency_level,
                                ai_analysis=result.get('analysis', ''),
                                first_aid_steps=steps_list if steps_list else [steps_result.get('steps', '')] if isinstance(steps_result, dict) else [steps_result],
                                images=[uploaded_image] if uploaded_image else None
                            )
                            save_record(record)
                            st.session_state.current_record = record["id"]
                            st.info("📋 Injury record automatically saved to My Health Records")
                            
                            # Voice announcement
                            if st.session_state.voice_assistant_enabled:
                                announce_record_created("injury")
                        
                        # Option to manually update record
                        if 'current_record' in st.session_state:
                            with st.expander("💾 Update Record Details"):
                                body_part = st.text_input("Body part affected (optional):", key="body_part_img")
                                location = st.text_input("Where did this occur? (optional):", key="location_img")
                                if st.button("💾 Update Record Details", key="save_img"):
                                    record = get_record(st.session_state.current_record)
                                    if record:
                                        if body_part:
                                            record['body_part'] = body_part
                                        if location:
                                            record['location'] = location
                                        save_record(record)
                                        st.success("✅ Record updated!")
                    except Exception as e:
                        st.error(f"Error analyzing image: {str(e)}")
                        st.warning("⚠️ The image may have been blocked by safety filters, or there was an API error. Please try again with a different image or describe the injury in text.")
                else:
                    # Original mode
                    try:
                        analysis = analyze_image(uploaded_image, return_structured=False)
                        st.success("✅ Image analyzed successfully.")
                        st.markdown(f"**Analysis Result:** {analysis}")
                        st.markdown("### 🩹 First Aid Steps")
                        st.write(generate_first_aid_steps(analysis, return_structured=False))
                    except Exception as e:
                        st.error(f"Error analyzing image: {str(e)}")
                        st.warning("⚠️ The image may have been blocked by safety filters, or there was an API error. Please try again with a different image or describe the injury in text.")
                
                # Always show medical disclaimer
                st.markdown("---")
                st.markdown(get_medical_disclaimer())
                
        elif injury_description:
            with st.spinner("Analyzing text..."):
                if use_enhanced_mode:
                    # Assess emergency level first
                    emergency_level = assess_emergency_level(injury_description)
                    if emergency_level == "EMERGENCY":
                        st.error("🚨 **CALL EMERGENCY SERVICES (911/999/112) IMMEDIATELY** 🚨")
                    elif emergency_level == "URGENT":
                        st.warning("⚠️ **URGENT: Seek medical attention within hours** ⚠️")
                    
                    # Generate enhanced first aid steps
                    st.success("✅ First aid advice ready.")
                    st.markdown("### 🩹 First Aid Steps")
                    steps_result = generate_first_aid_steps(injury_description, return_structured=True)
                    
                    # Extract steps as list for checklist
                    steps_list = []
                    if isinstance(steps_result, dict):
                        steps_text = steps_result.get('steps', '')
                        # Try to parse steps into list
                        lines = steps_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-') or line.startswith('*')):
                                step_clean = line.lstrip('0123456789.•-* ).').strip()
                                if step_clean:
                                    steps_list.append(step_clean)
                        
                        if steps_result.get('has_warnings'):
                            st.warning("⚠️ **IMPORTANT SAFETY WARNINGS** ⚠️")
                        st.markdown(steps_text)
                    else:
                        st.write(steps_result)
                        # Try to parse steps from plain text
                        if isinstance(steps_result, str):
                            lines = steps_result.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line and (line[0].isdigit() or line.startswith('•')):
                                    step_clean = line.lstrip('0123456789.•-* ).').strip()
                                    if step_clean:
                                        steps_list.append(step_clean)
                    
                    # Voice announcement for accessibility
                    if st.session_state.voice_assistant_enabled:
                        if isinstance(steps_result, dict):
                            steps_text = steps_result.get('steps', '')
                        else:
                            steps_text = steps_result
                        announce_injury_analysis("UNKNOWN", emergency_level, True)
                        st.session_state.last_spoken = steps_text
                    
                    # Auto-save to health records
                    if st.session_state.get('auto_save_records', True):
                        record = create_injury_record(
                            injury_description=injury_description,
                            severity="UNKNOWN",  # Can be enhanced with severity detection
                            emergency_level=emergency_level,
                            ai_analysis=injury_description,
                            first_aid_steps=steps_list if steps_list else [steps_result.get('steps', '')] if isinstance(steps_result, dict) else [steps_result]
                        )
                        save_record(record)
                        st.session_state.current_record = record["id"]
                        st.info("📋 Injury record automatically saved to My Health Records")
                        
                        # Voice announcement
                        if st.session_state.voice_assistant_enabled:
                            announce_record_created("injury")
                else:
                    # Original mode
                    steps = generate_first_aid_steps(injury_description, return_structured=False)
                st.success("✅ First aid advice ready.")
                st.markdown("### 🩹 First Aid Steps")
                st.write(steps)
                
                # Always show medical disclaimer
                st.markdown("---")
                st.markdown(get_medical_disclaimer())
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
                        st.markdown("*Click on any red marker to see hospital details and open navigation*")
                        # Create and display interactive map with clickable markers
                        interactive_map = create_interactive_map(facilities_df, lat, lon)
                        if interactive_map:
                            folium_static(interactive_map, width=700, height=500)
                        else:
                            st.map(combined_df, zoom=13)
                        
                        # Show facilities in a list with navigation buttons
                        st.markdown("### 📋 Hospitals Nearby")
                        st.markdown("*Click the 🗺️ Navigate button to open directions in your device's map app*")
                        for idx, row in facilities_df.iterrows():
                            display_hospital_with_navigation(row, idx)
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
                    st.markdown("*Click on any red marker to see hospital details and open navigation*")
                    # Create and display interactive map with clickable markers
                    interactive_map = create_interactive_map(facilities_df, lat, lon)
                    if interactive_map:
                        folium_static(interactive_map, width=700, height=500)
                    else:
                        st.map(combined_df, zoom=13)
                    
                    # Show facilities in a list with navigation buttons
                    st.markdown("### 📋 Hospitals Nearby")
                    st.markdown("*Click the 🗺️ Navigate button to open directions in your device's map app*")
                    for idx, row in facilities_df.iterrows():
                        display_hospital_with_navigation(row, idx)
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
                    st.markdown("*Click on any red marker to see hospital details and open navigation*")
                    # Create and display interactive map with clickable markers
                    interactive_map = create_interactive_map(facilities_df)
                    if interactive_map:
                        folium_static(interactive_map, width=700, height=500)
                    else:
                        show_facilities_map(facilities_df)
                    
                    # Show facilities in a list with navigation buttons
                    st.markdown("---")
                    st.markdown("### 📋 Hospitals Nearby")
                    st.markdown("*Click the 🗺️ Navigate button to open directions in your device's map app*")
                    for idx, row in facilities_df.iterrows():
                        display_hospital_with_navigation(row, idx)
                        st.markdown("---")
        else:
            st.warning("Please enter a valid location.")

# --- PAGE 3: My Health Records ---
elif page == "📋 My Health Records":
    st.header("📋 My Health Records")
    st.markdown("Track your injury history, recovery progress, and medical records")
    
    # Initialize auto-save setting
    if 'auto_save_records' not in st.session_state:
        st.session_state.auto_save_records = True
    
    # Settings
    with st.expander("⚙️ Settings"):
        st.session_state.auto_save_records = st.checkbox(
            "💾 Auto-save injury records", 
            value=st.session_state.auto_save_records,
            help="Automatically save records when analyzing injuries"
        )
    
    # Get statistics
    stats = get_statistics()
    total_records = stats["total_records"]
    
    if total_records == 0:
        st.info("📋 No health records yet. Records will be automatically created when you analyze an injury.")
        st.markdown("### Getting Started")
        st.markdown("""
        1. Go to **First Aid Guide** page
        2. Upload an image or describe an injury
        3. Click **Analyze**
        4. Your injury record will be automatically saved here!
        """)
    else:
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📋 All Records", "📊 Statistics", "🔍 Search & Filter", "➕ New Record"])
        
        with tab1:
            st.subheader("All Injury Records")
            
            # Filter quick buttons
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                filter_status = st.selectbox("Filter by Status", ["All", "active", "healing", "recovering", "healed", "archived"], key="status_filter")
            with col2:
                filter_severity = st.selectbox("Filter by Severity", ["All", "SEVERE", "MODERATE", "MINOR", "UNKNOWN"], key="severity_filter")
            with col3:
                sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Severity", "Status"], key="sort_by")
            with col4:
                if st.button("🔄 Refresh"):
                    st.rerun()
            
            # Get and filter records
            records = get_all_records()
            
            # Apply filters
            if filter_status != "All":
                records = [r for r in records if r.get("status") == filter_status]
            if filter_severity != "All":
                records = [r for r in records if r.get("severity") == filter_severity]
            
            # Sort
            if "Newest" in sort_by:
                records = get_all_records(sort_by="timestamp", reverse=True)
            elif "Oldest" in sort_by:
                records = get_all_records(sort_by="timestamp", reverse=False)
            elif "Severity" in sort_by:
                records = get_all_records(sort_by="severity", reverse=True)
            
            # Re-apply filters after sorting
            if filter_status != "All":
                records = [r for r in records if r.get("status") == filter_status]
            if filter_severity != "All":
                records = [r for r in records if r.get("severity") == filter_severity]
            
            if not records:
                st.info("No records match your filters.")
            else:
                st.metric("Total Records Found", len(records))
                
                # Display records
                for idx, record in enumerate(records):
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            # Record header
                            severity = record.get("severity", "UNKNOWN")
                            status = record.get("status", "active")
                            
                            if severity == "SEVERE":
                                st.markdown(f"### 🚨 {record.get('injury_type', 'Unknown Injury')}")
                            elif severity == "MODERATE":
                                st.markdown(f"### ⚠️ {record.get('injury_type', 'Unknown Injury')}")
                            else:
                                st.markdown(f"### {record.get('injury_type', 'Unknown Injury')}")
                            
                            # Record details
                            st.markdown(f"**Date:** {format_record_date(record)}")
                            st.markdown(f"**Severity:** {severity} | **Status:** {status.title()}")
                            if record.get("body_part"):
                                st.markdown(f"**Body Part:** {record.get('body_part')}")
                            if record.get("location"):
                                st.markdown(f"**Location:** {record.get('location')}")
                            
                            # Recovery progress
                            progress = record.get("recovery", {}).get("progress_percentage", 0)
                            st.progress(progress / 100, text=f"Recovery: {progress}%")
                        
                        with col2:
                            if st.button("👁️ View", key=f"view_{record.get('id')}"):
                                st.session_state.view_record_id = record.get('id')
                                st.rerun()
                        
                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_{record.get('id')}"):
                                if delete_record(record.get('id')):
                                    st.success("Record deleted!")
                                    st.rerun()
                        
                        st.markdown("---")
        
        with tab2:
            st.subheader("📊 Statistics & Insights")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", stats["total_records"])
            with col2:
                st.metric("Active Injuries", stats["active_injuries"])
            with col3:
                st.metric("Healed", stats["healed_injuries"])
            with col4:
                st.metric("Most Common", stats.get("most_common_body_part", "N/A"))
            
            # Voice announcement button for accessibility
            if st.session_state.voice_assistant_enabled:
                if st.button("🔊 Announce Statistics", key="announce_stats_btn"):
                    announce_statistics(stats)
            
            # Charts
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### By Severity")
                if stats.get("by_severity"):
                    st.bar_chart(stats["by_severity"])
                else:
                    st.info("No data available")
            
            with col2:
                st.markdown("### By Status")
                if stats.get("by_status"):
                    st.bar_chart(stats["by_status"])
                else:
                    st.info("No data available")
        
        with tab3:
            st.subheader("🔍 Search & Filter Records")
            search_query = st.text_input("Search by injury type, description, or body part:")
            
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                date_from = st.date_input("From Date", value=None)
            with date_col2:
                date_to = st.date_input("To Date", value=None)
            
            if st.button("🔍 Search"):
                from datetime import datetime as dt
                filtered = filter_records(
                    search_query=search_query if search_query else None,
                    date_from=dt.combine(date_from, dt.min.time()) if date_from else None,
                    date_to=dt.combine(date_to, dt.max.time()) if date_to else None
                )
                
                if filtered:
                    st.success(f"Found {len(filtered)} records")
                    for record in filtered:
                        st.markdown(f"**{record.get('injury_type')}** - {format_record_date(record)}")
                        if st.button("View", key=f"search_view_{record.get('id')}"):
                            st.session_state.view_record_id = record.get('id')
                            st.rerun()
                else:
                    st.info("No records found matching your search.")
        
        with tab4:
            st.subheader("➕ Create New Record Manually")
            injury_type = st.text_input("Injury Type/Description *")
            severity = st.selectbox("Severity", ["MINOR", "MODERATE", "SEVERE", "UNKNOWN"])
            body_part = st.text_input("Body Part (optional)")
            location = st.text_input("Location (optional)")
            notes = st.text_area("Initial Notes (optional)")
            
            if st.button("💾 Create Record"):
                if injury_type:
                    record = create_injury_record(
                        injury_description=injury_type,
                        severity=severity,
                        body_part=body_part,
                        location=location
                    )
                    if notes:
                        add_note_to_record(record["id"], notes)
                    save_record(record)
                    st.success("✅ Record created!")
                    st.rerun()
                else:
                    st.warning("Please enter an injury type.")
    
    # Detailed record view
    if 'view_record_id' in st.session_state and st.session_state.view_record_id:
        st.markdown("---")
        st.markdown("### 📋 Record Details")
        
        record = get_record(st.session_state.view_record_id)
        if record:
            # Display record details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"#### {record.get('injury_type', 'Unknown Injury')}")
                st.markdown(f"**Date:** {format_record_date(record)}")
                st.markdown(f"**Severity:** {record.get('severity')} | **Status:** {record.get('status').title()}")
                if record.get('body_part'):
                    st.markdown(f"**Body Part:** {record.get('body_part')}")
                if record.get('location'):
                    st.markdown(f"**Location:** {record.get('location')}")
                
                # Initial analysis
                if record.get('initial_analysis', {}).get('ai_analysis'):
                    with st.expander("🤖 AI Analysis"):
                        st.write(record['initial_analysis']['ai_analysis'])
                
                # First aid steps
                st.markdown("### 🩹 First Aid Steps")
                recommended = record.get('first_aid_steps', {}).get('recommended', [])
                completed = record.get('first_aid_steps', {}).get('completed', [])
                
                if recommended:
                    for idx, step in enumerate(recommended):
                        checked = "✅" if idx in completed else "☐"
                        st.checkbox(f"{checked} {step}", value=(idx in completed), key=f"step_{record.get('id')}_{idx}", 
                                   disabled=True)
                else:
                    st.info("No first aid steps recorded.")
                
                # Recovery progress
                st.markdown("### 📊 Recovery Progress")
                progress = record.get('recovery', {}).get('progress_percentage', 0)
                st.progress(progress / 100, text=f"{progress}%")
                
                new_progress = st.slider("Update Progress (%)", 0, 100, progress, key=f"progress_{record.get('id')}")
                pain_level = st.slider("Pain Level (1-10)", 0, 10, record.get('recovery', {}).get('pain_level', 0) or 0, key=f"pain_{record.get('id')}")
                progress_note = st.text_area("Progress Notes", key=f"note_{record.get('id')}")
                
                if st.button("💾 Update Progress", key=f"update_progress_{record.get('id')}"):
                    update_recovery_progress(record["id"], new_progress, pain_level, progress_note)
                    st.success("✅ Progress updated!")
                    st.rerun()
                
                # Notes
                st.markdown("### 📝 Notes")
                for note in record.get('notes', []):
                    st.text(f"{format_record_date({'timestamp': note.get('timestamp', '')})}: {note.get('content', '')}")
                
                new_note = st.text_area("Add Note", key=f"new_note_{record.get('id')}")
                if st.button("➕ Add Note", key=f"add_note_{record.get('id')}"):
                    if new_note:
                        add_note_to_record(record["id"], new_note)
                        st.success("✅ Note added!")
                        st.rerun()
            
            with col2:
                if st.button("← Back to Records"):
                    if 'view_record_id' in st.session_state:
                        del st.session_state.view_record_id
                    st.rerun()
                
                # Quick actions
                st.markdown("### Quick Actions")
                if st.button("📸 Add Photo", key=f"photo_{record.get('id')}"):
                    st.session_state.add_photo_to = record.get('id')
                
                if 'add_photo_to' in st.session_state and st.session_state.add_photo_to == record.get('id'):
                    photo = st.file_uploader("Upload Progress Photo", type=["jpg", "jpeg", "png"], key=f"upload_{record.get('id')}")
                    if photo:
                        from utils.health_records import add_photo_to_record
                        add_photo_to_record(record["id"], photo, "during")
                        st.success("✅ Photo added!")
                        st.rerun()
                
                if st.button("💊 Add Medication", key=f"med_{record.get('id')}"):
                    st.session_state.add_med_to = record.get('id')
                
                if 'add_med_to' in st.session_state and st.session_state.add_med_to == record.get('id'):
                    med_name = st.text_input("Medication Name", key=f"med_name_{record.get('id')}")
                    med_dose = st.text_input("Dosage", key=f"med_dose_{record.get('id')}")
                    if st.button("Save", key=f"save_med_{record.get('id')}"):
                        if med_name:
                            add_medication(record["id"], med_name, med_dose)
                            st.success("✅ Medication added!")
                            st.rerun()
        
        else:
            st.error("Record not found.")
            if 'view_record_id' in st.session_state:
                del st.session_state.view_record_id

# Footer with AidNexus branding
st.markdown("---")
st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #666; background: linear-gradient(180deg, rgba(30,136,229,0.05), rgba(0,172,193,0.05)); border-radius: 10px; margin-top: 2rem;">
        <h3 style="margin: 0.5rem 0; color: #1e88e5;">
            🩹 Aid<span style="color: #00acc1;">Nexus</span>
        </h3>
        <p style="margin: 0.5rem 0; font-size: 0.9rem;">
            Your AI-Powered First Aid Companion
        </p>
        <p style="margin: 0.25rem 0; font-size: 0.85rem; color: #999;">
            Powered by Google Gemini AI • Built with Streamlit
        </p>
        <p style="margin: 0.25rem 0; font-size: 0.75rem; color: #bbb;">
            © 2024 AidNexus. This application provides general first aid information only and is not a substitute for professional medical care.
        </p>
    </div>
""", unsafe_allow_html=True)
