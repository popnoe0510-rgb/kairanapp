import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from datetime import timedelta, timezone

# 📱 画面の基本設定
st.set_page_config(page_title="回覧板チェック", layout="centered")

# 🎨 タブを大きくして色をつけるカスタムCSS
st.markdown("""
    <style>
        /* 1. 画面上部の余白削減（クリックを邪魔しない設定） */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
        [data-testid="stHeader"] {
            height: 0px !important;
            background: transparent !important;
            pointer-events: none;
        }

        /* 2. タブ全体の並びと背景の調整 */
        div[data-testid="stTabs"] {
            border-bottom: none !important;
            gap: 8px !important;
        }
        div[data-testid="stTabs"] [role="tablist"] {
            gap: 10px !important;
            width: 100% !important;
        }

        /* 3. 【最重要】タブのタッチ領域を広げてボタン化 */
        div[data-testid="stTabs"] button {
            flex: 1 !important;              /* 2つのタブで画面の横幅を等分する */
            height: 48px !important;          /* 高さを出してタップしやすく（指のサイズ） */
            background-color: #262730 !important; /* 選択されていないタブの背景色（暗いグレー） */
            color: #a3a8b4 !important;        /* 選択されていないタブの文字色 */
            border-radius: 8px !important;    /* 角を少し丸める */
            border: 1px solid #464855 !important;
            padding: 0px 10px !important;
            font-weight: bold !important;
            font-size: 15px !important;
            transition: all 0.2s ease;
        }

        /* 4. 【選択中】現在選んでいるタブの明確な色付け */
        div[data-testid="stTabs"] button[aria-selected="true"] {
            background-color: #ff4b4b !important; /* 選択中の背景色（アクセントの赤系） */
            color: #ffffff !important;           /* 選択中の文字色（白） */
            border: 1px solid #ff4b4b !important;
            box-shadow: 0px 4px 10px rgba(255, 75, 75, 0.3) !important; /* 少し光らせる */
        }
        
        /* Streamlit標準の細い下線を消す */
        div[data-testid="stTabs"] [data-baseweb="tab-highlight-bar"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# 1. スプレッドシート接続
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    # 🔗 あなたのスプレッドシートURL
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit"
    
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
except Exception as e:
    st.error("スプレッドシートの接続設定を確認してください。")
    st.stop()

# データの読み込み
data = sheet.get_all_records()
df = pd.DataFrame(data)
df = df.sort_values(by="回覧順").reset_index(drop=True)

# タブ機能
tab1, tab2 = st.tabs(["👤 回覧板チェック", "⚙️ 管理者メニュー"])

# ==========================================
#  タブ1：一般回覧者用の画面（確実な横並び版）
# ==========================================
with tab1:
    st.subheader("✅ 回覧板チェック状況")
    st.markdown("---")
    
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
        
        st.markdown("<hr style='margin: 6px 0; border:0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

# ==========================================
#  タブ2：管理者用の画面
# ==========================================
with tab2:
    st.title("⚙️ 管理者設定")
    
    password = st.text_input("管理者パスワードを入力してください", type="password")
    if password == "7777":
        st.success("認証されました")
        
        st.markdown("---")
        st.subheader("🔁 回覧状況のリセット")
        if st.button("全員の確認状況をクリアする", type="primary"):
            with st.spinner("リセット中..."):
                total_rows = len(df) + 1
                cell_list_status = sheet.range(2, 3, total_rows, 3)
                cell_list_time = sheet.range(2, 4, total_rows, 4)
                
                for cell in cell_list_status: cell.value = '未確認'
                for cell in cell_list_time: cell.value = ''
                
                sheet.update_cells(cell_list_status)
                sheet.update_cells(cell_list_time)
                st.success("全員のステータスをリセットしました！")
                st.rerun()

        st.markdown("---")
        st.subheader("📝 名前の編集と順番の入れ替え")
        
        edited_df = st.data_editor(
            df, 
            column_config={
                "回覧順": st.column_config.NumberColumn("回覧順", min_value=1, step=1),
                "確認状況": st.column_config.SelectboxColumn("確認状況", options=["未確認", "確認済"]),
            },
            disabled=["確認日時"],
            hide_index=True
        )
        
        if st.button("編集内容をスプレッドシートに保存する"):
            with st.spinner("保存中..."):
                final_df = edited_df.sort_values(by="回覧順")
                sheet.clear()
                sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
                sheet.append_rows(final_df.values.tolist())
                
                st.success("スプレッドシートへの保存が完了しました！")
                st.rerun()
    elif password != "":
        st.error("パスワードが違います。")
