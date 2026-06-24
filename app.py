import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

# ページレイアウト設定
st.set_page_config(page_title="回覧板", layout="centered")

# 🎨 モダン・デザインシステム (ダーク/ライト対応)
st.markdown("""
    <style>
        :root { --card-bg: #ffffff; --text-color: #2d3436; }
        @media (prefers-color-scheme: dark) {
            :root { --card-bg: #2d3436; --text-color: #ffffff; }
        }
        .card { background: var(--card-bg); color: var(--text-color); padding: 1.5rem; 
                border-radius: 16px; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .member-name { font-size: 1.1rem; font-weight: 700; }
        .timestamp { font-size: 0.8rem; color: #636e72; }
    </style>
""", unsafe_allow_html=True)

# 接続処理
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
sheet = gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit").sheet1
df = pd.DataFrame(sheet.get_all_records())
df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
df = df.sort_values(by="回覧順").reset_index(drop=True)

tab1, tab2 = st.tabs(["📌 回覧状況", "⚙️ 管理"])

with tab1:
    st.header("📋 回覧板")
    unconfirmed = df[df['確認状況'] != '確認済']
    if not unconfirmed.empty:
        st.info(f"次は **{unconfirmed.iloc[0]['お名前']} さん** です。")
    
    for _, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        
        # カードの描画 (HTML汚染を回避するためプレーンに)
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{int(row['回覧順'])}. {row['お名前']}**")
                if is_done: st.caption(f"🕒 {row['確認日時']}")
            with col2:
                st.markdown("✅" if is_done else "⏳")
            
            if is_done:
                if st.button("取り消す", key=f"undo_{row.name}"):
                    sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                    st.rerun()
            else:
                if st.button("確認", key=f"btn_{row.name}", type="primary"):
                    now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                    sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                    st.rerun()

with tab2:
    if st.text_input("パスワード", type="password") == "7777":
        if st.button("🔄 全員リセット"):
            sheet.batch_update([{'range': f'C2:D{len(df)+1}', 'values': [['未確認', ''] for _ in range(len(df))]}])
            st.rerun()
