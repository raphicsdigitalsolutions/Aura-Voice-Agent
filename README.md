# Aura Voice Agent

Aura is a multilingual real-time voice assistant with an original 3D interface. The complete interface, client logic, and Python API handling live in `app.py`; separate HTML, CSS, and JavaScript files are not used.

## Run locally

1. Install Python 3.10 or newer.
2. In the project folder, install dependencies: `python -m pip install -r requirements.txt`
3. Start Aura: `streamlit run app.py`
4. Open `http://localhost:8501` if Streamlit does not open the browser automatically.
5. Enter an OpenAI API key on the setup screen. Click the central microphone and allow microphone access to talk.

Aura supports both microphone conversations and text chat without requiring microphone access. Both appear in one scrollable conversation, with web-search citations shown below the answer that used them. Live voice and research use the configured OpenAI account and may incur API charges.

For local development, you can set `OPENAI_API_KEY` in `.env` (or `.streamlit/secrets.toml`). Both `.env` and `.streamlit/secrets.toml` are ignored by Git; `.env.example` is safe to include in GitHub. Keys entered on the setup screen stay in that browser session and are not written to disk. Microphone audio is sent to OpenAI only after a voice session starts.

## Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
2. Click **Create app** (or **New app**) and select:
   - **Repository:** `raphicsdigitalsolutions/Aura-Voice-Agent`
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. Open **Advanced settings** → **Secrets** (or **App settings** → **Secrets** after deploy) and add:
   ```toml
   OPENAI_API_KEY = "sk-your-openai-api-key-here"
   ```
   *(Optional — users can also enter their own OpenAI API key on Aura's setup screen if you leave Secrets empty.)*
4. Click **Deploy**. Streamlit Community Cloud serves the app over HTTPS, which browsers require for WebRTC microphone access.
