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
DEFAULT_API_KEY = "AIzaSyBeaXUY-BUr7zrAn0o8Fw26klxtNW8gIAQ"
# Default fallback model
DEFAULT_MODEL = "gemini-2.5-flash" 

# --- Page Configuration ---
st.set_page_config(
    page_title="INGRES AI Expert",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Premium UI ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #111827 100%);
        color: #e2e8f0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0b1120;
        border-right: 1px solid #334155;
    }

    /* Header Styling */
    h1 {
        background: linear-gradient(to right, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.05em;
    }
    
    h2, h3 {
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }

    /* Chat Messages - Glassmorphism */
    .stChatMessage {
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* User Message Specifics */
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: rgba(59, 130, 246, 0.15);
        border-color: rgba(59, 130, 246, 0.3);
    }

    /* Assistant Message Specifics */
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: rgba(16, 185, 129, 0.1);
        border-color: rgba(16, 185, 129, 0.3);
    }

    /* Input Field */
    .stChatInputContainer textarea {
        background-color: #1f2937;
        color: white;
        border: 1px solid #374151;
        border-radius: 10px;
        transition: border-color 0.2s;
    }
    .stChatInputContainer textarea:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 1px #60a5fa !important;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(90deg, #3b82f6 0%, #6366f1 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton button:hover {
        opacity: 0.95;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }

    /* Radio Selection Card */
    div[role="radiogroup"] {
        background-color: #1e293b;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    
    /* Text Input */
    .stTextInput input {
        background-color: #1e293b;
        color: white;
        border: 1px solid #334155;
    }

    /* Selectbox */
    div[data-baseweb="select"] > div {
        background-color: #1e293b;
        color: white;
        border: 1px solid #334155;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0f172a; 
    }
    ::-webkit-scrollbar-thumb {
        background: #475569; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #64748b; 
    }
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

    # Configure GenAI immediately based on current sidebar state
    try:
        genai.configure(api_key=active_api_key)
    except Exception as e:
        st.error(f"Config Error: {e}")

    st.markdown("---")

    # 2. Model & Personality
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
            if st.button("📤 Send Voice Query"):
               handle_prompt(transcribed_text, current_sys_prompt, selected_model)
               st.rerun()

    st.markdown("---")
    st.markdown(
        f"""
        <div style='background-color: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155;'>
            <div style='font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;'>Active Model</div>
            <div style='font-size: 0.9rem; font-weight: 600; color: #38bdf8;'>{selected_model}</div>
        </div>
        """, 
        unsafe_allow_html=True
    )

# --- Main Area Render ---
st.title(app_title)
st.caption(app_caption)

# Initialize history
get_or_init_session_state("messages", [])

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Type your message here..."):
    handle_prompt(prompt, current_sys_prompt, selected_model)
