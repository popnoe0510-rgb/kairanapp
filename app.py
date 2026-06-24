import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone

# 📱 画面の基本設定
st.set_page_config(page_title="回覧板チェック", layout="centered")

# 🎨 スッキリしたダークモード風のデザイン
st.markdown("""
    <style>
        .stApp { background-color: #33363f !important; color: #ffffff !important; }
        .block-container { padding-top: 3.5rem !important; }
        [data-testid="stHeader"] { background-color: #33363f !important; }
        div[data-testid="stTabs"] button { flex: 1 !important; height: 48px !important; font-weight: bold !important; }
        div[data-testid="stTabs"] button[aria-selected="true"] { background-color: #1a457a !important; color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 1. スプレッドシート接続
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit"
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
except Exception as e:
    st.error("スプレッドシートの接続設定を確認してください。")
    st.stop()

# データの読み込み
data = sheet.get_all_records()
df = pd.DataFrame(data)
if not df.empty and "回覧順" in df.columns:
    df = df.sort_values(by="回覧順").reset_index(drop=True)

# タブ切り替え
tab1, tab2 = st.tabs(["👤 回覧板チェック", "⚙️ 管理者メニュー"])

# ==========================================
#  タブ1：一般回覧者用の画面
# ==========================================
with tab1:
    st.subheader("✅ 回覧板チェック状況")
    st.markdown("---")
    
    if df.empty:
        st.info("登録されているメンバーがいません。管理者メニューから追加してください。")
    else:
        for i, row in df.iterrows():
            col1, col2 = st.columns([3, 2])
            with col1:
                if row['確認状況'] == '確認済':
                    st.write(f"✅ {row['回覧順']}. {row['お名前']}")
                    st.caption(f"🕒 {row['確認日時']}")
                else:
                    st.write(f"👤 {row['回覧順']}. {row['お名前']}")
            
            with col2:
                if row['確認状況'] != '確認済':
                    if st.button("確認", key=f"btn_{i}", use_container_width=True):
                        JST = timezone(timedelta(hours=+9), 'JST')
                        now = datetime.now(JST).strftime("%m/%d %H:%M")
                        sheet.update_cell(int(i) + 2, 3, '確認済') 
                        sheet.update_cell(int(i) + 2, 4, now)     
                        st.success(f"{row['お名前']}さん確認！")
                        st.rerun()
                else:
                    st.markdown("<p style='color: #2ecc71; font-weight: bold; text-align: center; margin: 0;'>確認済</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 6px 0; border:0; border-top: 1px solid #555;'>", unsafe_allow_html=True)

# ==========================================
#  タブ2：管理者用の画面
# ==========================================
with tab2:
    st.subheader("⚙️ 管理者設定")
    password = st.text_input("管理者パスワードを入力してください", type="password")
    
    if password == "7777":
        st.success("認証されました")
        
        # ------------------------------------------
        #  1. 閲覧状況のリセット
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### 🔁 1. 閲覧状況のリセット")
        if st.button("全員の確認状況を「未確認」に戻す", use_container_width=True):
            if not df.empty:
                with st.spinner("リセット中..."):
                    total_rows = len(df) + 1
                    cell_list_status = sheet.range(2, 3, total_rows, 3)
                    cell_list_time = sheet.range(2, 4, total_rows, 4)
                    
                    for cell in cell_list_status: 
                        cell.value = '未確認'
                    for cell in cell_list_time: 
                        cell.value = ''
                    
                    sheet.update_cells(cell_list_status)
                    sheet.update_cells(cell_list_time)
                    st.success("全員のステータスをリセットしました！")
                    st.rerun()
            else:
                st.info("登録されている人がいません。")

        # ------------------------------------------
        #  2. 登録されている人の一覧リスト
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### 📋 2. 登録メンバー一覧")
        if not df.empty:
            for _, row in df.iterrows():
                status_emoji = "✅" if row['確認状況'] == "確認済" else "⏳"
                time_str = f" ({row['確認日時']})" if row['確認日時'] else ""
                st.text(f"【{row['回覧順']}番】 {row['お名前']} さん  [{status_emoji}{row['確認状況']}{time_str}]")
        else:
            st.info("現在、誰も登録されていません。")

        # ------------------------------------------
        #  3. 回覧順の編集（新規追加機能）
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### ↕️ 3. 回覧順の編集（並び替え）")
        if not df.empty and len(df) > 1:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                move_user = st.selectbox("移動させる人", options=df["お名前"].tolist(), key="move_user_select")
            with col_p2:
                # 1番から現在の最大人数までの選択肢
                target_order = st.selectbox("新しい順番（何番にするか）", options=list(range(1, len(df) + 1
