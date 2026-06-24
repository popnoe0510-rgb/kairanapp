import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_config = st.set_page_config(page_title="回覧板", layout="centered")

# 🎨 究極のダークUI：目に優しく、情報が映えるデザイン
st.markdown("""
    <style>
        .stApp { background-color: #1e293b !important; color: #f1f5f9 !important; }
        .member-card { 
            background: #334155 !important; padding: 1rem; border-radius: 12px; 
            margin-bottom: 0.8rem; border: 1px solid #475569;
        }
        .name-text { font-size: 1.1rem; font-weight: 700; color: #f8fafc; }
        .time-text { font-size: 0.85rem; color: #94a3b8; }
        .stButton>button { 
            width: 100%; border-radius: 6px !important; border: none !important; 
            background-color: #3b82f6 !important; color: white !important; font-weight: 600 !important;
        }
        .stTextArea textarea { background: #334155 !important; color: white !important; }
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
    st.subheader("📋 回覧板")
    for _, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        st.markdown(f"""<div class='member-card'>
            <div class='name-text'>{int(row['回覧順'])}. {row['お名前']}</div>
            <div class='time-text'>{ '✅ ' + str(row['確認日時']) if is_done else '⏳ 未確認' }</div>
        </div>""", unsafe_allow_html=True)
        
        if is_done:
            if st.button("取り消し", key=f"undo_{row.name}"):
                sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                st.rerun()
        else:
            if st.button("確認する", key=f"btn_{row.name}"):
                now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                st.rerun()

with tab2:
    if st.text_input("パスワード", type="password") == "7777":
        if st.button("🔄 全員リセット"):
            sheet.batch_update([{'range': f'C2:D{len(df)+1}', 'values': [['未確認', ''] for _ in range(len(df))]}])
            st.rerun()
        new_names = st.text_area("名簿編集", value="\n".join(df["お名前"].tolist()), height=300)
        if st.button("💾 保存"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.rerun()
