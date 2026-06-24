import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import time

st.set_page_config(page_title="回覧板アプリ", layout="centered")

st.markdown("""
    <style>
        .stApp { background-color: #242730; color: #ffffff; }
        .info-box { padding: 1rem; background-color: #1a4731; border-left: 5px solid #38ef7d; color: white; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

if 'status_msg' not in st.session_state: st.session_state.status_msg = None

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
    
    if st.session_state.status_msg:
        st.markdown(f"<div class='info-box'>{st.session_state.status_msg}</div>", unsafe_allow_html=True)
        time.sleep(7)
        st.session_state.status_msg = None
        st.rerun()
    elif not unconfirmed.empty:
        st.markdown(f"<div class='info-box'>👉 現在は <strong>{unconfirmed.iloc[0]['お名前']} さん</strong> の番です。</div>", unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{int(row['回覧順'])}. {row['お名前']}** " + ("(済)" if row['確認状況']=='確認済' else ""))
        with col2:
            if row['確認状況'] == '確認済':
                if st.button("❌", key=f"undo_{row.name}"):
                    # 爆速バッチ削除
                    sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                    st.rerun()
            else:
                if st.button("確認", key=f"btn_{row.name}"):
                    # ✅ 爆速バッチ更新（1通信で完了）
                    now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                    sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                    
                    next_person = unconfirmed.iloc[1]['お名前'] if len(unconfirmed) > 1 else None
                    msg = f"次は {next_person} さんへ回してください。" if next_person else "全員完了です！"
                    st.session_state.status_msg = f"確認完了！ {msg}"
                    st.rerun()

with tab2:
    if st.text_input("パスワード", type="password") == "7777":
        if st.button("🔄 全員リセット"):
            # リセットもバッチ処理で高速化
            updates = [{'range': f'C{i+2}:D{i+2}', 'values': [['未確認', '']]} for i in range(len(df))]
            sheet.batch_update(updates)
            st.rerun()
        # (以下名簿編集省略)
