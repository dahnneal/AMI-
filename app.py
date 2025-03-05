import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os
import uuid
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
import logging

# Attempt to import streamlit_webrtc and streamlit_audio_recorder
try:
    from streamlit_webrtc import webrtc_streamer
    webrtc_available = True
except ImportError:
    webrtc_available = False

try:
    from streamlit_audio_recorder import st_audio_recorder
    audio_available = True
except ImportError:
    audio_available = False

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)

import json

firebase_cred_json = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_cred_json:
    st.error("⚠️ Firebase credentials not found. Please check your environment variable.")
    st.stop()

# Load Firebase credentials from the JSON string
firebase_cred = json.loads(firebase_cred_json)

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

# Session Initialization
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Load chat history from Firestore
def load_chat_history():
    user_ref = db.collection("users").document(st.session_state.user_id)
    user_data = user_ref.get()
    if user_data.exists:
        st.session_state.chat_history = user_data.to_dict().get("chat_history", [])
    else:
        st.session_state.chat_history = []

# Sidebar for AI Character Selection
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

st.title(f"🌟 {character_choice} - Your AI Companion")

# User Authentication
if not st.session_state.user_name:
    user_name = st.text_input("Enter your name:")
    if user_name:
        st.session_state.user_name = user_name
        st.success(f"Welcome, {st.session_state.user_name}!")
        load_chat_history()
    else:
        st.stop()

# Chat Input & Response Handling
def update_chat_history(role, message):
    st.session_state.chat_history.append({"role": role, "message": message})
    db.collection("users").document(st.session_state.user_id).set({"chat_history": st.session_state.chat_history}, merge=True)

st.write("### Chat History")
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["message"])

if not st.session_state.chat_history:
    greeting = f"Hello {st.session_state.user_name}! It's nice to meet you. How can I assist you today?"
    update_chat_history("assistant", f"🤖 {character_choice}: {greeting}")

user_input = st.chat_input("Type your message...")
if user_input:
    with st.chat_message("user"):
        st.markdown(f"👤 {st.session_state.user_name}: {user_input}")
    update_chat_history("user", f"👤 {st.session_state.user_name}: {user_input}")

    response = chat_model.invoke([
        SystemMessage(content=f"{character_choice} responding"),
        HumanMessage(content=f"{st.session_state.user_name}: {user_input}")
    ])
    
    with st.chat_message("assistant"):
        st.markdown(f"🤖 {character_choice}: {response.content}")
    update_chat_history("assistant", f"🤖 {character_choice}: {response.content}")

# Video & Audio Chat Feature (Side Panel)
st.sidebar.title("🎥 Voice & Video Chat")
st.sidebar.write("Start a conversation with AI.")
if webrtc_available:
    with st.sidebar:
        webrtc_streamer(key="video_chat")
if audio_available:
    with st.sidebar:
        st_audio_recorder("🎤 Record Voice Message")

# UI Enhancements
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        body, .stApp {
            background-color: #121212 !important;
            color: #ffffff !important;
            font-family: 'Inter', sans-serif;
        }
        .stChatMessage {
            padding: 8px !important;
            margin-bottom: 5px !important;
            color: white !important;
        }
        .stTextInput input {
            border-radius: 10px;
            padding: 10px;
            width: 100%;
            font-size: 16px;
            color: white !important;
            background-color: #333333 !important;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            cursor: pointer;
            border-radius: 5px;
            font-size: 16px;
        }
        .stButton button:hover {
            background-color: #45a049;
        }
    </style>
    """,
    unsafe_allow_html=True
)
