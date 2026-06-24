import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from datetime import timedelta, timezone

# 📱 画面の基本設定
st.set_page_config(page_title="回覧板チェック", layout="centered")

# 🎨 背景色グレー、タブを濃い青色、さらに管理者画面のフォントや隙間を最適化するCSS
st.markdown("""
    <style>
        /* 1. アプリ全体の背景色をグレーに、文字を白に統一 */
        .stApp {
            background-color: #33363f !important; 
            color: #ffffff !important;
        }

        /* 2. 上部のGitHubボタン等との被りを防ぐための安全な余白設定 */
        .block-container {
            padding-top: 3.5rem !important; 
            padding-bottom: 1.5rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
        
        /* システムヘッダーの重なりを防ぐ設定 */
        [data-testid="stHeader"] {
            height: 3.5rem !important;
            background-color: #33363f !important; 
        }

        /* 3. タブ全体のレイアウト調整 */
        div[data-testid="stTabs"] {
            border-bottom: none !important;
            gap: 8px !important;
        }
        div[data-testid="stTabs"] [role="tablist"] {
            gap: 10px !important;
            width: 100% !important;
        }

        /* 4. タブを大きなボタン化（未選択状態：少し暗いグレー） */
        div[data-testid="stTabs"] button {
            flex: 1 !important;
            height: 48px !important; 
            background-color: #25262d !important;
            color: #b0b5c0 !important;
            border-radius: 8px !important;
            border: 1px solid #4a4d5a !important;
            padding: 0px 10px !important;
            font-weight: bold !important;
            font-size:
