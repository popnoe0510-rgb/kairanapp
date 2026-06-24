import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

# CSS: ボタンの配置と青系配色を調整
st.markdown("""
    <style>
        .stApp { background-color: #0f172a; color: #f1f5f9; }
        .inline-time { font-size: 0.8rem; color: #94a3b8; margin-left: 8px; }
        /* ボタンを右寄せするための調整 */
        div[data-testid="column"] { display: flex; align-items: center; }
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
        st.info(f"👉 次は **{unconfirmed.iloc[0]['お名前']} さん** の番です。")
    else:
        st.success("✅ 全員確認完了です！")
    
    for _, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        with st.container(border=True):
            # カラムを使って名前とボタンを横並びにする
            col1, col2 = st.columns([3, 1])
            
            with col1:
                time_text = f"<span class='inline-time'>{row['確認日時']}</span>" if is_done else ""
                st.markdown(f"**{int(row['回覧順'])}. {row['お名前']}** {'✅' if is_done else '⏳'} {time_text}", unsafe_allow_html=True)
            
            with col2:
                # ボタンを配置（取り消しは右寄せ、確認は primary=青）
                if is_done:
                    if st.button("取り消し", key=f"undo_{row.name}"):
                        sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                        st.rerun()
                else:
                    if st.button("確認", key=f"btn_{row.name}", type="primary"):
                        now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                        sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                        st.rerun()

with tab2:
    st.header("⚙️ 管理機能")
    if st.text_input("管理パスワードを入力", type="password") == "7777":
        st.subheader("1. 回覧状況リセット")
        if "reset_
