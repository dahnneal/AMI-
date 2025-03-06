import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os
import uuid
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
import logging
import json

# Attempt to import voice/video packages
try:
    from streamlit_webrtc import webrtc_streamer
    webrtc_available = True
except ImportError:
    webrtc_available = False

try:
    from streamlit_audiorecorder import st_audiorecorder
    audio_available = True
except ImportError:
    audio_available = False

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Load Firebase credentials from environment variable (as a JSON string)
firebase_cred_json = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_cred_json:
    st.error("⚠️ Firebase credentials not found. Please check your environment variable.")
    st.stop()
try:
    firebase_cred = json.loads(firebase_cred_json)
except json.JSONDecodeError as e:
    st.error("⚠️ Firebase credentials JSON is not valid. Please recheck the formatting.")
    st.stop()

# Initialize Firebase with the loaded credentials
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cred)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize AI Model
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("⚠️ Groq API key missing. Set it in your environment variables.")
    st.stop()
chat_model = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="mixtral-8x7b-32768")

# Session Initialization: Use dictionary-style access
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ---------- Login Page ----------
def show_login():
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
            body, .stApp {
                background-color: #ffffff !important;
                color: #000000 !important;
                font-family: 'Inter', sans-serif;
            }
            .login-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 80vh;
            }
            .login-container h1 {
                margin-bottom: 20px;
            }
            .login-container .stTextInput>div>div>input {
                font-size: 18px;
                padding: 10px;
                width: 300px;
            }
            .login-container .stButton button {
                background-color: #007bff !important;
                color: #ffffff !important;
                padding: 10px 20px;
                font-size: 18px;
                margin-top: 20px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.title("Welcome to AMI ~ Your AI Companion")
    username = st.text_input("Enter your name to continue:")
    if st.button("Login"):
        if username.strip() != "":
            st.session_state["user_name"] = username.strip()
            st.success(f"Welcome, {st.session_state['user_name']}!")
            load_chat_history()
            # Instead of forcing a rerun, the app will naturally refresh on next interaction.
        else:
            st.error("Please enter a valid name.")
    st.markdown("</div>", unsafe_allow_html=True)

def load_chat_history():
    user_ref = db.collection("users").document(st.session_state["user_id"])
    user_data = user_ref.get()
    if user_data.exists:
        st.session_state["chat_history"] = user_data.to_dict().get("chat_history", [])
    else:
        st.session_state["chat_history"] = []

# Show login page if user is not logged in
if st.session_state["user_name"] == "":
    show_login()
    st.stop()

# ---------- Main Interface Styling (After Login) ----------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        body, .stApp {
            background-color: #ffffff !important; /* White background */
            color: #002244 !important;             /* Deep blue text */
            font-family: 'Inter', sans-serif;
        }
        /* Sidebar styling: blue background with white text */
        .stSidebar {
            background-color: #007bff !important;
            color: #ffffff !important;
        }
        /* Action buttons styling: blue with white text */
        .stButton button {
            background-color: #007bff !important;
            color: #ffffff !important;
        }
        /* Chat bubbles styling: white background with deep blue text, with a subtle gray border */
        .stChatMessage {
            padding: 8px !important;
            margin-bottom: 5px !important;
            background-color: #ffffff !important;
            color: #002244 !important;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }
        /* Alert styling: red background with white text */
        .alert {
            background-color: #ff0000 !important;
            color: #ffffff !important;
            padding: 10px;
            border-radius: 5px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Sidebar: AI Character Selection and Media Options ----------
st.sidebar.title("🤖 AI Character Selection")
character_choice = st.sidebar.selectbox("Choose your AI character:", ["Papilo", "WakandaBot", "Zulu Sage", "Mama Africa", "Custom"])
if character_choice == "Custom":
    custom_name = st.sidebar.text_input("Enter your custom AI character name:")
    custom_description = st.sidebar.text_area("Describe your AI character:")
    if st.sidebar.button("Set Custom AI"):
        if custom_name and custom_description:
            character_choice = custom_name
        else:
            st.warning("⚠️ Please enter both name and description for your custom AI!")
            st.stop()

st.title(f"🌟 {character_choice} - Your AI Companion")

# Sidebar: Media Options
st.sidebar.title("🎥 Voice & Video Chat")
st.sidebar.write("Start a conversation with AI.")
if webrtc_available:
    with st.sidebar:
        webrtc_streamer(key="video_chat")
if audio_available:
    with st.sidebar:
        audio_bytes = st_audiorecorder("🎤 Record Voice Message")
        if audio_bytes is not None:
            st.audio(audio_bytes, format="audio/wav")

# ---------- Main Chat Interface ----------
st.write("### Chat History")
for chat in st.session_state["chat_history"]:
    with st.chat_message(chat["role"]):
        st.markdown(chat["message"])

def update_chat_history(role, message):
    st.session_state["chat_history"].append({"role": role, "message": message})
    db.collection("users").document(st.session_state["user_id"]).set(
        {"chat_history": st.session_state["chat_history"]}, merge=True
    )

if not st.session_state["chat_history"]:
    greeting = f"Hello {st.session_state['user_name']}! It's nice to meet you. How can I assist you today?"
    update_chat_history("assistant", f"🤖 {character_choice}: {greeting}")

user_input = st.chat_input("Type your message...", key="chat_input")
if user_input:
    with st.chat_message("user"):
        st.markdown(f"👤 {st.session_state['user_name']}: {user_input}")
    update_chat_history("user", f"👤 {st.session_state['user_name']}: {user_input}")
    response = chat_model.invoke([
        SystemMessage(content=f"{character_choice} responding"),
        HumanMessage(content=f"{st.session_state['user_name']}: {user_input}")
    ])
    with st.chat_message("assistant"):
        st.markdown(f"🤖 {character_choice}: {response.content}")
    update_chat_history("assistant", f"🤖 {character_choice}: {response.content}")
