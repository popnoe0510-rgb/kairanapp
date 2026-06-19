import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="回覧板チェック", layout="centered")
st.title("✅ 回覧板チェック")

# 1. 安全にスプレッドシートに接続するための設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

try:
    # Streamlitの秘密の部屋（Secrets）から鍵を読み込みます
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    # ⚠️ここにあなたのGoogleスプレッドシートのURLをそのまま貼り付けます
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit"
    
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
except Exception as e:
    st.error("スプレッドシートの接続設定（Secrets）がまだ完了していないか、URLが違います。")
    st.stop()

# 2. データの読み込み
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 3. 画面表示とチェック機能
for i, row in df.iterrows():
    col1, col2 = st.columns([3, 1])
    with col1:
        # 回覧順とお名前を表示
        if row['確認状況'] == '確認済':
            st.write(f"### ✅ {row['回覧順']}. {row['お名前']}")
            st.caption(f"（{row['確認日時']} に確認済み）")
        else:
            st.write(f"### 👤 {row['回覧順']}. {row['お名前']}")
    
    with col2:
        # まだ確認していない人のみ、大きなボタンを表示
        if row['確認状況'] != '確認済':
            if st.button("確認", key=f"btn_{i}", use_container_width=True):
                # ボタンが押されたら、現在の日時をスプレッドシートに直接書き込む
                now = datetime.now().strftime("%m/%d %H:%M")
                
                # スプレッドシートの「確認状況」列（3列目）を更新
                sheet.update_cell(i + 2, 3, '確認済') 
                # スプレッドシートの「確認日時」列（4列目）を更新
                sheet.update_cell(i + 2, 4, now)     
                
                st.success(f"{row['お名前']}さんの確認を記録しました！")
                st.rerun()
        else:
            st.write(" ")

st.markdown("---")
st.caption("回覧板を確認したら「確認」ボタンを押してください。自動で次の人に通知状態になります。")
