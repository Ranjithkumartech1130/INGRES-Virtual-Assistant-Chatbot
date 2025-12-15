# INGRES Chatbot

This is a chatbot powered by Google's Gemini model, specialized in answering questions about the INGRES database system.

## Project Structure

- `ingres.py`: Main application file (Streamlit app).
- `.env`: Environment variables (API keys).
- `requirements.txt`: Python dependencies.

## Setup & Run

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application:**
    ```bash
    streamlit run ingres.py
    ```

## Notes

- Ensure you have your Google API key configured in `.env` as `GOOGLE_API_KEY`.
