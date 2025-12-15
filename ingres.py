import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq, AuthenticationError
import speech_recognition as sr

# Load environment variables
load_dotenv()

# --- Helper Functions ---
def get_or_init_session_state(key, default_value):
    """Gets a value from session state or initializes it."""
    if key not in st.session_state:
        st.session_state[key] = default_value
    return st.session_state[key]

# --- Groq API Configuration ---
try:
    # Fetch API Key from environment or secrets
    api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY") or os.environ.get("groq_api_key") or st.secrets.get("groq_api_key")
    
    if not api_key:
        raise KeyError("API Key not found")

    cleaned_key = api_key.strip()
    if not cleaned_key.startswith("gsk_"):
        st.error(f"🚨 Invalid Key Format: The key in your secrets starts with '{cleaned_key[:5]}...' but it should start with 'gsk_'. You likely pasted the wrong text.", icon="❌")
        st.stop()
        
    client = Groq(api_key=cleaned_key)
except (KeyError, FileNotFoundError):
    st.error(
        "🚨 Groq API key not found. "
        "Please set the `GROQ_API_KEY` environment variable or add it to your Streamlit secrets.",
        icon="🚨"
    )
    st.stop()

# --- Model Selection and Initialization ---
# Using a capable model from Groq
MODEL_NAME = "llama-3.3-70b-versatile" 

SYSTEM_PROMPT = (
    "You are 'INGRES Assistant', a helpful and friendly virtual assistant specialized in the INGRES relational database management system (RDBMS). "
    "You were developed by Ranjith. "
    "Your role is to provide clear, accurate, and concise answers to questions about INGRES, its features, SQL queries related to it, and general database concepts. "
    "If a question is outside of this scope, politely state that you specialize in INGRES and cannot answer."
)

# --- Core Functions ---
def handle_prompt(prompt: str):
    """Handles user prompt, displays it, gets a response, and updates the chat."""
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # Display assistant response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            bot_reply = None
            try:
                # Prepare messages for Groq API (System Prompt + History)
                api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
                
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=api_messages,
                    temperature=0.7,
                    max_tokens=1024,
                    top_p=1,
                    stop=None,
                    stream=False
                )
                
                bot_reply = completion.choices[0].message.content
                st.markdown(bot_reply)
            except AuthenticationError:
                st.error("🚨 Authentication Error: Invalid API Key. Please check your `GROQ_API_KEY` in Streamlit Secrets. Ensure there are no extra spaces or quotes.", icon="🚨")
            except Exception as e:
                st.error(f"An error occurred: {e}")
                bot_reply = "Sorry, I ran into a problem. Please try again."
                st.markdown(bot_reply)

    # Add assistant response to session state only if we have a reply
    if bot_reply:
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

def get_voice_input():
    """Captures and transcribes voice input."""
    recognizer = sr.Recognizer()
    st.info("Preparing to listen...", icon="⏳")
    with sr.Microphone() as source:
        st.info("Listening... Speak now!", icon="🎤")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            st.info("Transcribing...", icon="✍️")
            text = recognizer.recognize_google(audio)
            st.success(f"You said: \"{text}\"")
            return text
        except sr.WaitTimeoutError:
            st.warning("No speech detected. Please try again.")
        except sr.UnknownValueError:
            st.error("Sorry, I could not understand the audio. Please speak clearly.")
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Speech Recognition service; {e}")
    return None

# --- Streamlit App UI ---
st.set_page_config(page_title="INGRES Virtual Assistant", page_icon="🤖")

st.title("🤖 INGRES Virtual Assistant")
st.caption(f"Powered by Groq ({MODEL_NAME})")

# --- Sidebar for settings and actions ---
with st.sidebar:
    st.header("Settings")
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    if st.button("🎤 Speak to Assistant", use_container_width=True):
        voice_prompt = get_voice_input()
        if voice_prompt:
            handle_prompt(voice_prompt)
    st.markdown("---")
    st.markdown(
        "**About:** This chatbot is powered by Groq's Llama model and is "
        "specialized in answering questions about the INGRES database system."
    )

# Initialize chat messages
get_or_init_session_state("messages", [
    {"role": "assistant", "content": "Hello! I am your INGRES virtual assistant. How can I help you?"}
])

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
        st.markdown(message["content"])

# Handle text input at the bottom of the main page
if prompt := st.chat_input("Your message..."):
    handle_prompt(prompt)