import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import time

st.set_page_config(page_title="回覧板アプリ", layout="centered")

# 🎨 スタイル：確認アクションの視覚フィードバックを強化
st.markdown("""
    <style>
        .stApp { background-color: #242730; color: #ffffff; }
        input, textarea { background-color: #ffffff !important; color: #333 !important; border: 2px solid #58a6ff !important; }
        .stButton>button { border-radius: 8px; font-weight: bold; transition: all 0.2s; }
        /* 完了メッセージを強調 */
        .success-box { padding: 1rem; background-color: #1a4731; border-left: 5px solid #38ef7d; color: white; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# 接続処理
try:
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sheet = gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit").sheet1
    df = pd.DataFrame(sheet.get_all_records())
    df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
    df = df.sort_values(by="回覧順").reset_index(drop=True)
except Exception: st.stop()

tab1, tab2 = st.tabs(["👤 回覧状況", "⚙️ 管理者専用"])

with tab1:
    st.subheader("📋 回覧板の現在状況")
    
    unconfirmed = df[df['確認状況'] != '確認済']
    if not unconfirmed.empty:
        target = unconfirmed.iloc[0]
        # 「次は〇〇さんの番です！」と明確に表示
        st.markdown(f"<div class='success-box'>👉 現在は **{target['お名前']} さん** の番です。<br>回覧物を確認したらボタンを押してください。</div>", unsafe_allow_html=True)
    else:
        st.success("🎉 全員確認完了しました！")
    
    for _, row in df.iterrows():
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"**{int(row['回覧順'])}. {row['お名前']}**")
        with col2:
            if row['確認状況'] == '確認済':
                st.caption(f"✅ 確認済 ({row['確認日時']})")
            else:
                # ボタンを押すとスピナーが回り、「動いた感」を演出
                if st.button("回覧板を見ました", key=f"btn_{row['お名前']}"):
                    with st.spinner("処理しています..."):
                        time.sleep(1) # 少しだけ余韻を持たせる
                        sheet.update_cell(row.name + 2, 3, '確認済')
                        sheet.update_cell(row.name + 2, 4, datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M"))
                        
                        next_msg = f"次は {unconfirmed.iloc[1]['お名前']} さんへ回ります。" if len
