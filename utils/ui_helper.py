import streamlit as st

def show_footer():
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; color: #666;">
        <p style="margin: 0.5rem 0;">
            <strong>🩹 AidNexus</strong> - AI-Powered First Aid Assistant
        </p>
        <p style="margin: 0.25rem 0; font-size: 0.85rem;">
            Powered by Google Gemini AI • Built with Streamlit
        </p>
        <p style="margin: 0.25rem 0; font-size: 0.75rem; color: #999;">
            © 2024 AidNexus. This application provides general first aid information only and is not a substitute for professional medical care.
        </p>
    </div>
    """, unsafe_allow_html=True)
