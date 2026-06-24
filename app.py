import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from datetime import timedelta, timezone

# 📱 画面の基本設定
st.set_page_config(page_title="回覧板チェック", layout="centered")

# 🎨 背景色グレー、タブを濃い青色、さらに管理者画面のフォントや隙間を最適化するCSS
st.markdown("""
    <style>
        /* 1. アプリ全体の背景色をグレーに、文字を白に統一 */
        .stApp {
            background-color: #33363f !important; /* 落ち着いたグレー */
            color: #ffffff !important;
        }

        /* 2. 上部のGitHubボタン等との被りを防ぐための安全な余白設定 */
        .block-container {
            padding-top: 3.5rem !important; /* 被らないように上に適度な隙間を空ける */
            padding-bottom: 1.5rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
        
        /* システムヘッダーの重なりを防ぐ設定 */
        [data-testid="stHeader"] {
            height: 3.5rem !important;
            background-color: #33363f !important; /* 背景色と同化させる */
        }

        /* 3. タブ全体のレイアウト調整 */
        div[data-testid="stTabs"] {
            border-bottom: none !important;
            gap: 8px !important;
        }
        div[data-testid="stTabs"] [role="tablist"] {
            gap: 10px !important;
            width: 100% !important;
        }

        /* 4. タブを大きなボタン化（未選択状態：少し暗いグレー） */
        div[data-testid="stTabs"] button {
            flex: 1 !important;
            height: 48px !important; /* 指で押しやすいサイズ */
            background-color: #25262d !important;
            color: #b0b5c0 !important;
            border-radius: 8px !important;
            border: 1px solid #4a4d5a !important;
            padding: 0px 10px !important;
            font-weight: bold !important;
            font-size: 15px !important;
            transition: all 0.2s ease;
        }

        /* 5. 選択中のタブを「濃い青色」に装飾 */
        div[data-testid="stTabs"] button[aria-selected="true"] {
            background-color: #1a457a !important; /* 視認性の高い濃い青色 */
            color: #ffffff !important;
            border: 1px solid #245fa6 !important;
            box-shadow: 0px 4px 10px rgba(26, 69, 122, 0.4) !important;
        }
        
        /* Streamlit標準の細い下線を消去 */
        div[data-testid="stTabs"] [data-baseweb="tab-highlight-bar"] {
            display: none !important;
        }

        /* 6. 管理者メニュー内の文字サイズ・フォームデザインの最適化 */
        .admin-title {
            font-size: 22px !important;
            font-weight: bold !important;
            margin-top: 10px !important;
            margin-bottom: 15px !important;
            color: #ffffff !important;
        }
        .admin-subtitle {
            font-size: 17px !important;
            font-weight: bold !important;
            margin-top: 20px !important;
            margin-bottom: 10px !important;
            color: #f1f2f6 !important;
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
#  タブ1：一般回覧者用の画面
# ==========================================
with tab1:
    st.markdown('<div class="admin-title">✅ 回覧板チェック状況</div>', unsafe_allow_html=True)
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
        
        st.markdown("<hr style='margin: 6px 0; border:0; border-top: 1px solid #555;'>", unsafe_allow_html=True)

# ==========================================
#  タブ2：管理者用の画面（直感的・シンプル操作版）
# ==========================================
with tab2:
    st.markdown('<div class="admin-title">⚙️ 管理者設定</div>', unsafe_allow_html=True)
    
    password = st.text_input("管理者パスワードを入力してください", type="password")
    if password == "7777":
        st.success("認証されました")
        
        # ------------------------------------------
        #  機能1：人を新規で追加する
        # ------------------------------------------
        st.markdown("---")
        st.markdown('<div class="admin-subtitle">➕ 人を新規で追加する</div>', unsafe_allow_html=True)
        
        new_name = st.text_input("追加する人のお名前を入力してください", key="add_name_input")
        if st.button("✨ この人を追加する", use_container_width=True):
            if new_name.strip() == "":
                st.warning("名前を入力してください。")
            else:
                with st.spinner("追加中..."):
                    # 現在の最大回覧順の次にする
                    next_order = int(df["回覧順"].max() + 1) if not df.empty else 1
                    # スプレッドシートの末尾に直接追加
                    sheet.append_row([next_order, new_name.strip(), "未確認", ""])
                    st.success(f"「{new_name}」さんを回覧順 {next_order} で追加しました！")
                    st.rerun()

        # ------------------------------------------
        #  機能2：人を削除する
        # ------------------------------------------
        st.markdown("---")
        st.markdown('<div class="admin-subtitle">🗑️ 人を削除する</div>', unsafe_allow_html=True)
        
        if not df.empty:
            # セレクトボックスから名前を選ぶだけで選べるように
            delete_target = st.selectbox(
                "削除する人を選択してください",
                options=df["お名前"].tolist(),
                key="delete_name_select"
            )
            
            if st.button("❌ この人を削除する", type="primary", use_container_width=True):
                with st.spinner("削除中..."):
                    # 該当者を抜いた新しいデータフレームを作成
                    updated_df = df[df["お名前"] != delete_target].copy()
                    
                    # 歯抜けになった回覧順を 1 から綺麗に採番し直す
                    updated_df = updated_df.sort_values(by="回覧順").reset_index(drop=True)
                    updated_df["回覧順"] = updated_df.index + 1
                    
                    # スプレッドシートをクリアして並び替えたデータを上書き
                    sheet.clear()
                    sheet.append_row(
