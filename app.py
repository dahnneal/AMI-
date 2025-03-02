from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import streamlit as st
import os

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Chat Model
chat_model = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="mixtral-8x7b-32768"
)

# AI Character Options
ai_characters = {
    "wise_scholar": {"name": "Professor Wole", "description": "A wise AI with deep insights.", "icon": "🧠"},
    "friendly_companion": {"name": "BFF", "description": "A warm and friendly AI that loves to chat.", "icon": "😊"},
    "mysterious_mentor": {"name": "GreatOne", "description": "A cryptic AI that speaks in riddles.", "icon": "🔮"},
}

# Streamlit UI Config
st.set_page_config(page_title="AI Character Chat", page_icon="🤖")
st.title("🎭 AI Character Chatbot")
st.markdown("**Select an AI character and start chatting!**")

# Select AI Character
character_choice = st.selectbox("Choose your AI character:", list(ai_characters.keys()))
selected_ai = ai_characters[character_choice]
st.markdown(f"### {selected_ai['icon']} {selected_ai['name']} - {selected_ai['description']}")

# Initialize Memory
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory()

# Display Chat History
st.subheader("💬 Chat History")
for message in st.session_state.memory.chat_memory.messages:
    with st.chat_message("user" if isinstance(message, HumanMessage) else "assistant"):
        st.markdown(f"{selected_ai['icon']} **{selected_ai['name'] if isinstance(message, SystemMessage) else 'You'}:** {message.content}")

# User Input with Enter Key
user_input = st.chat_input("Type your message...")
if user_input:
    # AI Response
    messages = [
        SystemMessage(content=f"You are {selected_ai['name']}, {selected_ai['description']}"),
        HumanMessage(content=user_input),
    ]
    response = chat_model.invoke(messages)
    
    # Store conversation
    st.session_state.memory.chat_memory.add_user_message(user_input)
    st.session_state.memory.chat_memory.add_ai_message(response.content)

    # Display User Message
    with st.chat_message("user"):
        st.markdown(f"👤 **You:** {user_input}")

    # Display AI Response
    with st.chat_message("assistant"):
        st.markdown(f"{selected_ai['icon']} **{selected_ai['name']}:** {response.content}")

# Clear Chat Button
if st.button("🗑️ Clear Chat"):
    st.session_state.memory.clear()
    st.experimental_rerun()
