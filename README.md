# INGRES Virtual Assistant

This is a smart chatbot powered by Google's **Gemini 1.5 Flash** model, specialized in answering questions about the INGRES relational database management system.

## Features

-   **Specialized Knowledge**: Expert in INGRES SQL, architecture, and optimization.
-   **Voice Input**: Speak your queries directly to the assistant.
-   **Modern UI**: Sleek, dark-themed interface built with Streamlit.
-   **Chat History**: Keeps track of your conversation.

## Tech Stack

-   **Python 3.8+**
-   **Streamlit**: For the web interface.
-   **Google Gemini API**: For LLM capabilities.
-   **SpeechRecognition**: For voice-to-text functionality.

## Setup & Run

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application:**
    ```bash
    streamlit run ingres.py
    ```

## Configuration

The API Key is currently configured directly in the application for ease of use. If you wish to use environment variables, update the `.env` file and uncomment the loading logic in `ingres.py`.
