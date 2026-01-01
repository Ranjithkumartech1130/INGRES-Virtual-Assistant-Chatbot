import streamlit as st
import os
import google.generativeai as genai
import speech_recognition as sr
from dotenv import load_dotenv
from audiorecorder import audiorecorder
import io

# --- Configuration ---
load_dotenv()

# API Configuration - Default System Key
DEFAULT_API_KEY = "AIzaSyDYQdKUHAtXxby2rOv22KPce2Ef8Put63E"
# Default fallback model
DEFAULT_MODEL = "gemini-2.5-flash" 

# --- Page Configuration ---
st.set_page_config(
    page_title="INGRES AI Expert",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

import base64

# --- Helper Functions for UI ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def get_img_with_href(local_img_path):
    img_format = local_img_path.split(".")[-1]
    binary_data = get_base64_of_bin_file(local_img_path)
    return f"data:image/{img_format};base64,{binary_data}"

# Load Assets
try:
    bg_img = get_img_with_href("assets/background.png")
    logo_img = get_img_with_href("assets/logo.png")
except:
    bg_img = ""
    logo_img = ""

# --- Custom Premium UI ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    /* Main Background */
    .stApp {{
        background: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.85)), url("{bg_img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Space Grotesk', sans-serif;
        color: #e2e8f0;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: rgba(11, 17, 32, 0.8);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }}

    /* Header Styling */
    .main-header {{
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 2rem;
        padding: 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
    }}
    
    .logo-img {{
        width: 80px;
        filter: drop-shadow(0 0 15px rgba(56, 189, 248, 0.5));
        animation: pulse 4s infinite ease-in-out;
    }}

    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); filter: drop-shadow(0 0 15px rgba(56, 189, 248, 0.5)); }}
        50% {{ transform: scale(1.05); filter: drop-shadow(0 0 25px rgba(167, 139, 250, 0.7)); }}
    }}

    h1 {{
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.5rem !important;
        margin: 0;
    }}
    
    /* Chat Messages - Glassmorphism */
    .stChatMessage {{
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
        backdrop-filter: blur(15px) !important;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5) !important;
        transition: all 0.3s ease;
        animation: fadeIn 0.5s ease-out;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .stChatMessage:hover {{
        border-color: rgba(255, 255, 255, 0.1) !important;
        transform: scale(1.01);
    }}
    
    /* User Message Specifics */
    [data-testid="stChatMessage"][data-testid="user"] {{
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05)) !important;
        border-left: 4px solid #3b82f6 !important;
    }}

    /* Assistant Message Specifics */
    [data-testid="stChatMessage"][data-testid="assistant"] {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(5, 150, 105, 0.02)) !important;
        border-left: 4px solid #10b981 !important;
    }}

    /* Input Field */
    .stChatInputContainer {{
        padding: 0 1rem !important;
        background: transparent !important;
    }}

    .stChatInputContainer textarea {{
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
        backdrop-filter: blur(10px) !important;
        color: white !important;
    }}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: rgba(15, 23, 42, 0.1); 
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(96, 165, 250, 0.3); 
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(96, 165, 250, 0.5); 
    }}

    /* Sidebar Improvements */
    .sidebar-content {{
        background: rgba(255, 255, 255, 0.02);
        padding: 15px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 20px;
    }}

    /* Button Styling */
    .stButton > button {{
        width: 100%;
        border-radius: 12px !important;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }}

    .stButton > button:hover {{
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-2px) !important;
    }}

    </style>
""", unsafe_allow_html=True)


# --- Helper Functions ---
def get_or_init_session_state(key, default_value):
    if key not in st.session_state:
        st.session_state[key] = default_value
    return st.session_state[key]

# --- Prompt Definitions ---
SYSTEM_PROMPT_INGRES = (
    "You are 'INGRES Assistant', a highly advanced AI specialized in the INGRES RDBMS. "
    "Your responses should be technical, precise, and formatted with Markdown. "
    "Use plenty of code blocks for SQL examples. "
    "If asked about anything other than database concepts, SQL, or INGRES, politely redirect the conversation."
    "You are developed by master Ranjith Kumar"
)

SYSTEM_PROMPT_GENERAL = (
    "You are a general-purpose AI assistant powered by Gemini. "
    "You are helpful, friendly, and knowledgeable about a vast array of topics. "
    "You can assist with coding, writing, math, science, and general conversation. "
    "Always provide clear, accurate responses formatted in Markdown."
    "You are developed by master Ranjith Kumar"
)

@st.cache_resource
def get_model(sys_prompt, model_name):
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
    }
    # Create model with dynamic system instruction and selected model
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
        system_instruction=sys_prompt
    )
    return model

def handle_prompt(prompt: str, sys_prompt: str, model_name: str):
    """Processes the user prompt with the specific system context and model."""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""
        with st.spinner(f"{model_name} is thinking..."):
            try:
                model = get_model(sys_prompt, model_name)
                
                # History Mapping
                history = []
                for msg in st.session_state.messages:
                    role = "user" if msg["role"] == "user" else "model"
                    history.append({"role": role, "parts": [msg["content"]]})
                
                # Use history excluding the very last message (which we just added)
                chat_history = history[:-1]
                user_message = history[-1]["parts"][0]
                
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(user_message, stream=True)
                
                for chunk in response:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                err_msg = str(e)
                if "404" in err_msg and "models/" in err_msg:
                     st.error(f"Model Error: '{model_name}' not found. Please verify the model version or switch models.", icon="❌")
                     full_response = "I could not access the specified AI model."
                elif "429" in err_msg:
                     st.warning(f"⏳ Rate Limit Exceeded for {model_name}. Please switch to a different model in the sidebar.", icon="⚠️")
                     full_response = "Rate limit hit. Please try a different model from the sidebar settings."
                elif "400" in err_msg or "API key" in err_msg or "403" in err_msg:
                     st.error(f"Authentication Error: Please check your API Key.", icon="🔒")
                     full_response = "I could not authenticate. Please check the API Key settings."
                else:
                    st.error(f"Error: {e}")
                    full_response = "Sorry, I encountered a connection error."
                
                message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

def transcribe_audio_file(audio_bytes):
    """Transcribes audio using Google Speech Recognition."""
    r = sr.Recognizer()
    try:
        # Convert bytes to a file-like object that recognizer can read
        # Note: audiorecorder returns wav bytes usually
        audio_file = io.BytesIO(audio_bytes)
        
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            return text
    except Exception as e:
        st.error(f"Transcription Error: {e}")
        return None

# --- Main Interface ---

with st.sidebar:
    st.title("⚙️ Cortex Controls")
    
    # 1. API Key Configuration
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.markdown("### 🔑 API Access")
    user_api_key = st.text_input(
        "Custom API Key (Optional)", 
        type="password", 
        placeholder="Paste your Gemini AI key here...",
        help="If left empty, the system will use the built-in Cortex credentials."
    )
    
    # Logic to select and configure key
    if user_api_key:
        active_api_key = user_api_key
        st.caption("✅ Using **Custom User Key**")
    else:
        active_api_key = DEFAULT_API_KEY
        st.caption("🔒 Using **System Default Key**")
    st.markdown('</div>', unsafe_allow_html=True)

    # Configure GenAI immediately based on current sidebar state
    try:
        genai.configure(api_key=active_api_key)
    except Exception as e:
        st.error(f"Config Error: {e}")

    # 2. Model & Personality
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.markdown("### 🧠 AI Settings")
    
    # Model Selector
    selected_model = st.selectbox(
        "Choose AI Model:",
        ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro"],
        index=0,
        help="Switch models if you hit rate limits (Error 429)."
    )
    
    mode_selection = st.radio(
        "Choose Personality:",
        ["INGRES Expert", "General Assistant"],
        index=0,
        captions=["Specialized DB Admin", "Helpful General AI"]
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if mode_selection == "INGRES Expert":
        current_sys_prompt = SYSTEM_PROMPT_INGRES
        app_title = "INGRES Database Assistant"
        app_caption = "Specialized in OpenINGRES / Actian Ingres SQL & Administration."
    else:
        current_sys_prompt = SYSTEM_PROMPT_GENERAL
        app_title = "General AI Assistant"
        app_caption = "Your personal AI companion for any task."

    st.markdown("---")
    
    # 3. Actions
    col1, col2 = st.columns(2)
    with col1:
         if st.button("🗑️ Reset", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        pass

    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.markdown("### 🎙️ Voice Interaction")
    
    # BROWSER-BASED AUDIO RECORDER
    audio = audiorecorder("🎤 Click to Speak", "🔴 Recording...")
    
    if len(audio) > 0:
        st.audio(audio.export().read())  # Play back for confirmation
        
        # Audio is an AudioSegment from pydub. Export to wav bytes.
        wav_bytes = audio.export(format="wav").read()
        
        transcribed_text = transcribe_audio_file(wav_bytes)
        
        if transcribed_text:
            st.success(f"Heard: {transcribed_text}")
            if st.button("📤 Send"):
               handle_prompt(transcribed_text, current_sys_prompt, selected_model)
               st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style='background: rgba(56, 189, 248, 0.1); padding: 15px; border-radius: 12px; border: 1px solid rgba(56, 189, 248, 0.2);'>
            <div style='font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 5px;'>Active Engine</div>
            <div style='font-size: 1rem; font-weight: 700; color: #38bdf8; font-family: "Space Grotesk";'>{selected_model}</div>
        </div>
        """, 
        unsafe_allow_html=True
    )

# --- Main Area Render ---
st.markdown(f"""
    <div class="main-header">
        <img src="{logo_img}" class="logo-img">
        <div>
            <h1>{app_title}</h1>
            <p style="color: #94a3b8; margin: 0; font-size: 1.1rem;">{app_caption}</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Initialize history
get_or_init_session_state("messages", [])

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Type your message here..."):
    handle_prompt(prompt, current_sys_prompt, selected_model)
