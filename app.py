import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import time

st.set_page_config(page_title="回覧板アプリ", layout="centered")

# 🎨 スタイル定義
st.markdown("""
    <style>
        .stApp { background-color: #242730; color: #ffffff; }
        input, textarea { background-color: #ffffff !important; color: #333 !important; border: 2px solid #58a6ff !important; }
        .stButton>button { border-radius: 8px; font-weight: bold; transition: all 0.2s; }
        .info-box { padding: 1.5rem; background-color: #1a4731; border-left: 5px solid #38ef7d; color: white; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# 状態管理：メッセージを保持
if 'status_msg' not in st.session_state:
    st.session_state.status_msg = None

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
    
    # メッセージゾーン：状況に応じて切り替え
    if st.session_state.status_msg:
        st.markdown(f"<div class='info-box'>{st.session_state.status_msg}</div>", unsafe_allow_html=True)
        time.sleep(7)
        st.session_state.status_msg = None
        st.rerun()
    elif not unconfirmed.empty:
        target = unconfirmed.iloc[0]
        st.markdown(f"<div class='info-box'>👉 現在は <strong>{target['お名前']} さん</strong> の番です。<br>回覧物を確認したら下のボタンを押してください。</div>", unsafe_allow_html=True)
    else:
        st.success("🎉 全員確認完了しました！")
    
    for _, row in df.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            if row['確認状況'] == '確認済':
                st.markdown(f"✅ {int(row['回覧順'])}. {row['お名前']} (済)")
            else:
                st.markdown(f"👤 **{int(row['回覧順'])}. {row['お名前']}**")
        with col2:
            if row['確認状況'] == '確認済':
                if st.button("❌", key=f"undo_{row['お名前']}"):
                    sheet.update_cell(row.name + 2, 3, '未確認')
                    sheet.update_cell(row.name + 2, 4, '')
                    st.rerun()
            else:
                if st.button("確認", key=f"btn_{row['お名前']}"):
                    with st.spinner("記録中..."):
                        sheet.update_cell(row.name + 2, 3, '確認済')
                        sheet.update_cell(row.name + 2, 4, datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M"))
                        
                        next_person = unconfirmed.iloc[1]['お名前'] if len(unconfirmed) > 1 else None
                        msg = f"次は {next_person} さんへ回してください。" if next_person else "全員完了です！"
                        st.session_state.status_msg = f"確認完了！ {msg}"
                        st.rerun()

with tab2:
    st.subheader("⚙️ 管理者設定")
    if st.text_input("パスワード", type="password") == "7777":
        if st.button("🔄 全員をリセットする"):
            for i in range(len(df)):
                sheet.update_cell(i + 2, 3, '未確認')
                sheet.update_cell(i + 2, 4, '')
            st.rerun()
        
        new_names = st.text_area("メンバーリスト", value="\n".join(df["お名前"].tolist()), height=200)
        if st.button("💾 名簿を更新"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.rerun()
