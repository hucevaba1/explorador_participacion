import streamlit as st

st.set_page_config(
    page_title="Explorador de participación electoral",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from app.main import main

if __name__ == "__main__":
    main()