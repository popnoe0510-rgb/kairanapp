import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

# CSS: ボタンの青色化、背景色・フォント設定
st.markdown("""
    <style>
        .stApp { background-color: #0f172a !important; }
        /* ✗ボタンと確認ボタンを青系に強制変更 */
        div.stButton > button { background-color: #1e40af !important; color: white !important; border: 1px solid #3b82f6 !important; }
        .member-info { font-size: 0.9rem; color: #f1f5f9; }
        .date-text { font-size: 0.75rem; color: #94a3b8; }
    </style>
""", unsafe_allow_html=True)

# 接続処理
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
sheet = gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit").sheet1
df = pd.DataFrame(sheet.get_all_records())
df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
df = df.sort_values(by="回覧順").reset_index(drop=True)

tab1, tab2 = st.tabs(["📌 回覧状況", "⚙️ 管理画面"])

with tab1:
    st.subheader("📋 現在の回覧状況")
    unconfirmed = df[df['確認状況'] != '確認済']
    if not unconfirmed.empty:
        st.info(f"📬 現在は **{unconfirmed.iloc[0]['お名前']} さん** の番です。")
    else:
        st.success("✅ 全員確認完了です！")
    
    for _, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        with st.container(border=True):
            col_l, col_r = st.columns([4, 1])
            with col_l:
                if is_done:
                    st.markdown(f"<div class='member-info'>**{int(row['回覧順'])}. {row['お名前']}** ✅ <span class='date-text'>{row['確認日時']}</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='member-info'>**{int(row['回覧順'])}. {row['お名前']}** ⏳</div>", unsafe_allow_html=True)
            with col_r:
                if is_done:
                    # ✗ アイコンに変更
                    if st.button("✗", key=f"undo_{row.name}"):
                        sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                        st.rerun()
                else:
                    if st.button("確認", key=f"btn_{row.name}"):
                        now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                        sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                        st.rerun()

with tab2:
    st.header("⚙️ 管理機能")
    if st.text_input
