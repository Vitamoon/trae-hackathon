from dotenv import load_dotenv
import os

load_dotenv()
PINAI_API_KEY = os.getenv("PINAI_API_KEY")


import streamlit as st

st.title("Hello World")
st.markdown(
    """ 
    This is a playground for you to try Streamlit and have fun. 

    **There's :rainbow[so much] you can build!**
    
    We prepared a few examples for you to get started. Just 
    click on the buttons above and discover what you can do 
    with Streamlit. 
    """
)

if st.button("Send balloons!"):
    st.balloons()