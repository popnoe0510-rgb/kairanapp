import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

# 🎨 デザイナー監修：日時情報を美しく組み込んだカードデザイン
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; font-family: 'Helvetica Neue', sans-serif; }
        .hero { background: #2d3436; padding: 2rem; border-radius: 20px; color: white; margin-bottom: 2rem; text-align: center; }
        .card { background: white; padding: 1.2rem; border-radius: 12px; margin-bottom: 0.8rem; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .member-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .member-info { font-weight: 700; color: #2d3436; font-size: 1.1rem; }
        .time-info { font-size: 0.85rem; color: #636e72; }
        .status-pill { padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; }
        .stButton>button { border-radius: 8px !important; border: none !important; font-weight: 600 !important; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# 接続処理
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
sheet = gspread.authorize(creds).open_by_url("
