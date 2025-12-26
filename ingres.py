import streamlit as st
import os
import google.generativeai as genai
import speech_recognition as sr
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# API Configuration - Default System Key
DEFAULT_API_KEY = "AIzaSyAA1d2mAUUu-RQA0W8p3QY7PO0poKmYns0"
MODEL_NAME = "gemini-2.5-flash" 

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
)

SYSTEM_PROMPT_GENERAL = (
    "You are a general-purpose AI assistant powered by Gemini. "
    "You are helpful, friendly, and knowledgeable about a vast array of topics. "
    "You can assist with coding, writing, math, science, and general conversation. "
    "Always provide clear, accurate responses formatted in Markdown."
)

@st.cache_resource
def get_model(sys_prompt):
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
    }
    # Create model with dynamic system instruction
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        system_instruction=sys_prompt
    )
    return model

def handle_prompt(prompt: str, sys_prompt: str):
    """Processes the user prompt with the specific system context."""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""
        with st.spinner("AI is thinking..."):
            try:
                model = get_model(sys_prompt)
                
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
                if "404" in str(e) and "models/" in str(e):
                     st.error(f"Model Error: '{MODEL_NAME}' not found. Please verify the model version.", icon="❌")
                     full_response = "I could not access the specified AI model."
                elif "400" in str(e) or "API key" in str(e) or "403" in str(e):
                     st.error(f"Authentication Error: Please check your API Key.", icon="🔒")
                     full_response = "I could not authenticate. Please check the API Key settings."
                else:
                    st.error(f"Error: {e}")
                    full_response = "Sorry, I encountered a connection error."
                
                message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

def get_voice_input():
    """Captures audio from microphone. Gracefully handles absence of microphone hardware."""
    r = sr.Recognizer()
    try:
        # Check for microphone availability before entering context
        # On cloud servers, this usually raises OSError immediately
        with sr.Microphone() as source:
            st.toast("Listening...", icon="🎤")
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                st.toast("Processing audio...", icon="⚙️")
                text = r.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                st.warning("Could not understand audio.")
            except sr.RequestError as e:
                st.error(f"Could not request results; {e}")
            except sr.WaitTimeoutError:
                st.warning("No speech detected.")
    except OSError:
        st.error("Microphone not detected. Voice input unavailable on this server.", icon="🚫")
    except Exception as e:
        st.error(f"Voice Error: {e}", icon="⚠️")
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

    # 2. Mode Selector
    st.markdown("### 🧠 AI Personality")
    mode_selection = st.radio(
        "Choose Mode:",
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
    # Voice Button Logic
    if st.button("🎤 Start Recording", use_container_width=True):
        voice_text = get_voice_input()
        if voice_text:
            st.success(f"Heard: {voice_text}")
            handle_prompt(voice_text, current_sys_prompt)
            st.rerun()

    st.markdown("---")
    st.markdown(
        f"""
        <div style='background-color: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155;'>
            <div style='font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;'>Active Model</div>
            <div style='font-size: 0.9rem; font-weight: 600; color: #38bdf8;'>{MODEL_NAME}</div>
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
    handle_prompt(prompt, current_sys_prompt)