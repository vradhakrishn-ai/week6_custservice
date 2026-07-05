import streamlit as st
import random
import requests
import time
import uuid
import os

FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://localhost:8000")


def response_generator(text):
    for word in text.split():
        yield word + " "
        time.sleep(0.05)


st.title("SecureBank India – Customer Service Support")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
        resp = requests.post(
            f"{FASTAPI_URL}/chat",
            json={
                "message": user_input,
                "session_id": st.session_state.session_id,
            },
            timeout=60,
        )
        if resp.status_code==200:
            data = resp.json()
            response_text = data["response"]
        else:
            response_text =f"Error in te request"

    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(response_text))
    st.session_state.messages.append({"role": "assistant", "content": response})
