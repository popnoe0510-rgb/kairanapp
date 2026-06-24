import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

# 🎨 ダークモード完全対応のモダンCSS
st.markdown("""
    <style>
        :root { --card-bg: #ffffff; --text: #262730; }
        @media (prefers-color-scheme: dark) {
            :root { --card-bg: #262730; --text: #ffffff; }
        }
        .compact-card { 
            background: var(--card-bg); color: var(--text); padding: 0.5rem 0.8rem; 
            border-radius: 8px; margin-bottom: 0.4rem; border: 1px solid #ddd;
            display: flex; align-items: center; justify-content: space-between;
        }
        .stButton>button { padding: 0.1rem 0.6rem !important; font-size: 0.8rem !important; }
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
        st.markdown(f"""<div class='compact-card'>
            <span>{int(row['回覧順'])}. {row['お名前']} { "✅" if is_done else "⏳" }</span>
            <span>{row['確認日時'] if is_done else ""}</span>
        </div>""", unsafe_allow_html=True)
        
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
    if st.text_input("管理パスワード", type="password") == "7777":
        if st.button("🔄 全員リセット"):
            sheet.batch_update([{'range': f'C2:D{len(df)+1}', 'values': [['未確認', ''] for _ in range(len(df))]}])
            st.rerun()
        
        st.write("---")
        new_names = st.text_area("名簿編集（1行1名）", value="\n".join(df["お名前"].tolist()))
        if st.button("💾 名簿を保存"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.rerun()
