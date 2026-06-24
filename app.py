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
        /* 全体の背景とベースフォント */
        .stApp { background-color: #242730 !important; color: #ffffff !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .block-container { padding-top: 3.5rem !important; }
        [data-testid="stHeader"] { background-color: #242730 !important; }
        
        /* タブをよりフラットでモダンなデザインに */
        div[data-testid="stTabs"] button { flex: 1 !important; height: 50px !important; font-weight: 600 !important; font-size: 15px !important; color: #8e94a6 !important; border: none !important; }
        div[data-testid="stTabs"] button[aria-selected="true"] { background-color: #2f3442 !important; color: #38ef7d !important; border-radius: 8px 8px 0 0 !important; }
        
        /* 🟩 一般ユーザー用の「確認ボタン」：押しやすさを最優先したクリーンなグリーン */
        div.stButton > button[key^="btn_"] {
            background-color: #38ef7d !important;
            color: #111111 !important;
            font-weight: bold !important;
            border: none !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 12px rgba(56, 239, 125, 0.2);
            height: 42px !important;
        }
        
        /* 🔵 管理者用の「セカンダリボタン」（リセットなど）：背景に溶け込むシックなデザイン */
        div.stButton > button {
            background-color: #2f3442 !important;
            color: #ffffff !important;
            border: 1px solid #41485c !important;
            border-radius: 8px !important;
            height: 42px !important;
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            background-color: #3d4357 !important;
            border-color: #525b75 !important;
        }
        
        /* 🚀 管理者用の「メイン保存ボタン」：最重要アクションとして輝かせる青 */
        div.stButton > button[key="save_master_btn"] {
            background: linear-gradient(135deg, #0072ff 0%, #00c6ff 100%) !important;
            color: #ffffff !important;
            font-weight: bold !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(0, 114, 255, 0.3);
        }
        
        /* リストの区切り線 */
        .divider { margin: 12px 0; border: 0; border-top: 1px solid #3d4357; }
        
        /* 確認済みのリッチなテキスト表現 */
        .checked-status { color: #38ef7d; font-weight: bold; text-align: center; margin: 0; font-size: 15px; }
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
df_raw = pd.DataFrame(data)
if not df_raw.empty and "回覧順" in df_raw.columns:
    df_raw["回覧順"] = pd.to_numeric(df_raw["回覧順"], errors='coerce').fillna(999)
    df_raw = df_raw.sort_values(by="回覧順").reset_index(drop=True)

def callback_reset():
    if not df_raw.empty:
        total_rows = len(df_raw) + 1
        cell_list_status = sheet.range(2, 3, total_rows, 3)
        cell_list_time = sheet.range(2, 4, total_rows, 4)
        for cell in cell_list_status: cell.value = '未確認'
        for cell in cell_list_time: cell.value = ''
        sheet.update_cells(cell_list_status)
        sheet.update_cells(cell_list_time)
        st.toast("🔄 全員のステータスをリセットしました")

tab1, tab2 = st.tabs(["👤 回覧板チェック", "⚙️ 管理者メニュー"])

# ==========================================
#  タブ1：一般回覧者用の画面
# ==========================================
with tab1:
    st.markdown("### ✅ 回覧板チェック状況")
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    if df_raw.empty:
        st.info("登録されているメンバーがいません。管理者メニューから追加してください。")
    else:
        for i, row in df_raw.iterrows():
            col1, col2 = st.columns([3, 2])
            with col1:
                if row['確認状況'] == '確認済':
                    st.markdown(f"**✅ {int(row['回覧順'])}. {row['お名前']}**")
                    st.caption(f" 🕒 {row['確認日時']}")
                else:
                    st.markdown(f"👤 {int(row['回覧順'])}. {row['お名前']}")
            
            with col2:
                if row['確認状況'] != '確認済':
                    # デザイナー注：keyに一工夫入れてCSSを部分適用
                    if st.button("確認する", key=f"btn_{i}", use_container_width=True):
                        JST = timezone(timedelta(hours=+9), 'JST')
                        now = datetime.now(JST).strftime("%m/%d %H:%M")
                        try:
                            cell = sheet.find(row['お名前'])
                            if cell:
