from PIL import Image
import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
import time
from gtts import gTTS
import io  # To handle in-memory audio

from configs import SYSTEM_PROMPT, SAFETY_SETTINGS, GENERATION_CONFIG, MODEL_NAME

# ---- App Configuration ----
st.set_page_config(
    page_title='HealthMate AI: X-Ray Imaging Diagnosis',
    layout='centered',
    initial_sidebar_state="expanded"
)

# ---- Theme Toggle ----
theme = st.sidebar.selectbox("🌗 Theme", ["Light", "Dark"])

# ---- Apply Custom CSS ----
if theme == "Light":
    css = """
        <style>
            .main { background-color: #f8f9fa; }
            .report-box {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .disclaimer {
                font-size: 14px;
                color: #6c757d;
                margin-top: 30px;
                font-style: italic;
            }
            .stButton button {
                background-color: #198754 !important;
                color: white !important;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px 20px;
            }
        </style>
    """
else:
    css = """
        <style>
            .main { background-color: #1e1e1e; color: #ffffff; }
            .report-box {
                background-color: #2c2c2c;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 0 10px rgba(255,255,255,0.1);
                color: #ffffff;
            }
            .disclaimer {
                font-size: 14px;
                color: #b0b0b0;
                margin-top: 30px;
                font-style: italic;
            }
            .stButton button {
                background-color: #0d6efd !important;
                color: white !important;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px 20px;
            }
        </style>
    """
st.markdown(css, unsafe_allow_html=True)

# ---- Header ----
st.markdown("<h1 style='text-align: center;'>🩺 HealthMate AI</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Analyzing X-Ray medical images with AI insights</h4>", unsafe_allow_html=True)

# ---- Sidebar Info ----
st.sidebar.markdown("## ℹ️ How to Use")
st.sidebar.markdown("""
1. Upload a clear X-Ray image (under 5MB).  
2. Click **Analyze** to get AI feedback.  
3. Download the report if needed.
""")
st.sidebar.markdown("## 💡 Tips")
st.sidebar.markdown("""
- Use high-quality chest or bone X-Rays.
- Avoid blurry or noisy images.
- Note: AI can make Mistakes!
""")

# ---- Configure Gemini AI ----
genai.configure(api_key='AIzaSyDhO8U7Pdod8g-WGuN_VM1JFyl06cUcn2I')
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    safety_settings=SAFETY_SETTINGS,
    generation_config=GENERATION_CONFIG,
    system_instruction=SYSTEM_PROMPT
)

# ---- Initialize session state for chatbot history and image analysis ----
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'image_uploaded' not in st.session_state:
    st.session_state['image_uploaded'] = False
if 'image_data' not in st.session_state:
    st.session_state['image_data'] = None

# ---- Upload and Analyze UI ----
uploaded_file = st.file_uploader("📤 Upload X-Ray Image (PNG/JPG, <5MB)", type=["png", "jpg", "jpeg"])
submit_btn = st.button("🔍 Analyze X-Ray Image")

# ---- Display Image and Run Analysis ----
if uploaded_file:
    if uploaded_file.size > 5 * 1024 * 1024:
        st.warning("⚠️ File too large. Please upload an image under 5MB.")
    else:
        image_data = Image.open(uploaded_file)
        st.image(image_data, caption="🖼️ Uploaded X-Ray Image", width=300)
        st.session_state['image_uploaded'] = True
        st.session_state['image_data'] = image_data

        if submit_btn:
            # Progress Bar (Fake for UX)
            progress = st.progress(0)
            for i in range(1, 6):
                progress.progress(i * 20)
                time.sleep(0.3)

            history = st.session_state.get('history', [])
            content = ["Analyze this image and describe possible medical conditions.", image_data]
            history.append({"role": "user", "parts": content})

            with st.spinner("🧠 AI is analyzing your image..."):
                chat_session = model.start_chat()
                response = chat_session.send_message(content)

            report_text = response.text
            st.markdown("<div class='report-box'><h4>📝 Analysis Report:</h4>", unsafe_allow_html=True)
            st.write(report_text)
            st.markdown("</div>", unsafe_allow_html=True)

            # Download Button
            download_str = StringIO(report_text)
            st.download_button(
                label="📥 Download Report",
                data=download_str.getvalue(),
                file_name="xray_diagnosis_report.txt",
                mime="text/plain"
            )

            st.session_state['history'] = chat_session.history

            # Audio Feedback using gTTS (with in-memory audio)
            if st.button("🔊 Listen to Report"):
                tts = gTTS(text=report_text, lang='en')
                audio_io = io.BytesIO()
                tts.save(audio_io)
                audio_io.seek(0)  # Rewind the audio buffer to the beginning
                st.audio(audio_io, format="audio/mp3")

# ---- Chatbot Interaction ----
user_message = st.text_input("💬 Chat with the AI:", "")
if user_message:
    # Check if image has been uploaded
    if st.session_state['image_uploaded'] and st.session_state['image_data'] is not None:
        # Add user's message to history
        st.session_state.history.append({"role": "user", "content": user_message})

        # Send message to AI
        with st.spinner("🧠 AI is responding..."):
            chat_session = model.start_chat()
            response = chat_session.send_message([user_message])

        # Show AI's response
        st.write(f"**AI Response:** {response.text}")

        # Save AI response to history
        st.session_state.history.append({"role": "assistant", "content": response.text})
    else:
        st.warning("⚠️ Please upload an X-ray image first for analysis before chatting.")

# ---- Disclaimer ----
st.markdown("<div class='disclaimer'>⚠️ This tool is for educational and experimental purposes only. It does not replace professional medical advice or diagnosis.</div>", unsafe_allow_html=True)
