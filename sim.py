"""Compatibilidade com o comando antigo: streamlit run sim.py."""
from frontend.views.main_page import MainPage
from composition_root import build_main_page
import streamlit as st

build_main_page(st.secrets, st.session_state).render()
