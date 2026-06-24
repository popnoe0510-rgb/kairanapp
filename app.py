import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone

# 📱 画面の基本設定
st.set_page_config(page_title="回覧板チェック", layout="centered")

# 🎨 【デザイナー監修】モダン・ディープブルーUIスタイル
st.markdown("""
    <style>
        .stApp { background-color: #242730 !important; color: #ffffff !important; }
        .block-container { padding-top: 2rem !important; }
        /* タブのスタイルをモダンに */
        div[data-testid="stTabs"] button { font-weight: 600 !important; font-size: 16px !important; }
        
        /* 🟩 ユーザー用：グリーン系の確認ボタン */
        div.stButton > button[key^="btn_"] {
            background-color: #38ef7d !important; color: #111111 !important;
            border-radius: 12px !important; border: none !important; font-weight: bold !important;
        }
        
        /* 🔵 管理者用：シックな青ボタン */
        div.stButton > button {
            background-color: #3d4357 !important; color: #ffffff !important;
            border-radius: 12px !important; border: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# 1. スプレッドシート接続（安全な接続）
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit"
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
except Exception:
    st.error("スプレッドシートへの接続に失敗しました。設定を確認してください。")
    st.stop()

# データの読み込み
data = sheet.get_all_records()
df = pd.DataFrame(data)
if not df.empty and "回覧順" in df.columns:
    df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
    df = df.sort_values(by="回覧順").reset_index(drop=True)

tab1, tab2 = st.tabs(["👤 回覧板チェック", "⚙️ 管理者メニュー"])

with tab1:
    st.subheader("✅ 現在の状況")
    if df.empty:
        st.info("メンバーが登録されていません。")
    else:
        for i, row in df.iterrows():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**{int(row['回覧順'])}. {row['お名前']}**")
                if row['確認状況'] == '確認済':
                    st.caption(f"🕒 {row['確認日時']}")
            with col2:
                if row['確認状況'] == '確認済':
                    st.success("確認済")
                else:
                    if st.button("確認する", key=f"btn_{i}"):
                        now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                        cell = sheet.find(str(row['お名前']))
                        if cell:
                            sheet.update_cell(cell.row, 3, '確認済')
                            sheet.update_cell(cell.row, 4, now)
                            st.rerun()

with tab2:
    st.subheader("⚙️ 管理者設定")
    if st.text_input("パスワード", type="password") == "7777":
        if st.button("🔄 全員を未確認にリセット"):
            total_rows = len(df) + 1
            sheet.batch_update([{'range': f'C2:D{total_rows+1}', 'values': [['未確認', ''] for _ in range(len(df))]}] if len(df) > 0 else [])
            st.rerun()
        
        st.markdown("---")
        st.write("📝 **名簿の直接編集（追加・削除・並び替え）**")
        names_text = st.text_area("1行に1人ずつ入力してください", value="\n".join(df["お名前"].tolist()), height=200)
        
        if st.button("💾 この内容で確定・保存する"):
            input_names = [n.strip() for n in names_text.split("\n") if n.strip()]
            new_rows = [[i+1, name, '未確認', ''] for i, name in enumerate(input_names)]
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            if new_rows: sheet.append_rows(new_rows)
            st.success("保存完了しました！")
            st.rerun()
