"""Ponto de entrada do Streamlit:  streamlit run app.py"""
import streamlit as st

from composition_root import build_main_page

build_main_page(secrets=st.secrets, session_state=st.session_state).render()
