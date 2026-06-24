import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板 - Modern Edition", layout="centered")

# 🎨 デザイナー渾身のモダン・CSS
st.markdown("""
    <style>
        .stApp { background-color: #f4f7f6; font-family: 'Inter', sans-serif; }
        .card { background: white; padding: 1.2rem; border-radius: 16px; margin-bottom: 1rem; 
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 6px solid #4834d4; }
        .member-name { font-size: 1.1rem; font-weight: 700; color: #2d3436; }
        .status-tag { font-size: 0.8rem; font-weight: 600; color: #636e72; }
    </style>
""", unsafe_allow_html=True)

# 接続処理
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
sheet = gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit").sheet1
df = pd.DataFrame(sheet.get_all_records())
df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
df = df.sort_values(by="回覧順").reset_index(drop=True)

tab1, tab2 = st.tabs(["📌 今日の回覧状況", "⚙️ 管理"])

with tab1:
    unconfirmed = df[df['確認状況'] != '確認済']
    if not unconfirmed.empty:
        st.success(f"📍 次の担当：**{unconfirmed.iloc[0]['お名前']} さん**")
    
    for _, row in df.iterrows():
        # カードUIで表示をスタイリッシュに
        with st.container():
            st.markdown(f"""<div class='card'>
                <span class='member-name'>{int(row['回覧順'])}. {row['お名前']}</span>
                <span class='status-tag'>{'✅ 確認済' if row['確認状況']=='確認済' else '⏳ 未確認'}</span>
            </div>""", unsafe_allow_html=True)
            
            if row['確認状況'] == '確認済':
                if st.button("取り消す", key=f"undo_{row.name}"):
                    sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                    st.rerun()
            else:
                if st.button(f"{row['お名前']} さんとして確認", key=f"btn_{row.name}", type="primary"):
                    now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                    sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                    st.rerun()

with tab2:
    if st.text_input("パスワード", type="password") == "7777":
        if st.button("🔄 全員を未確認にリセット"):
            sheet.batch_update([{'range': f'C2:D{len(df)+1}', 'values': [['未確認', ''] for _ in range(len(df))]}])
            st.rerun()
        # 名簿編集部も同様にスタイリッシュに
