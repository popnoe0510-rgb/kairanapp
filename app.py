import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone

# 📱 画面の基本設定
st.set_page_config(page_title="回覧板チェック", layout="centered")

# 🎨 眩しい赤色を徹底排除した、ディープブルー専用スタイル
st.markdown("""
    <style>
        .stApp { background-color: #33363f !important; color: #ffffff !important; }
        .block-container { padding-top: 3.5rem !important; }
        [data-testid="stHeader"] { background-color: #33363f !important; }
        
        /* タブのデザイン */
        div[data-testid="stTabs"] button { flex: 1 !important; height: 48px !important; font-weight: bold !important; }
        div[data-testid="stTabs"] button[aria-selected="true"] { background-color: #1a457a !important; color: #ffffff !important; }
        
        /* 🔵 ボタンを落ち着いたディープブルーに統一 */
        div.stButton > button {
            background-color: #1f4068 !important;
            color: #ffffff !important;
            border: 1px solid #162447 !important;
            border-radius: 6px !important;
            transition: background-color 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #162447 !important;
            color: #ffffff !important;
        }
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

# 読み込んだ生データを保持するDFを作成
df_raw = pd.DataFrame(data)
if not df_raw.empty and "回覧順" in df_raw.columns:
    df_raw["回覧順"] = pd.to_numeric(df_raw["回覧順"], errors='coerce').fillna(999)
    df_raw = df_raw.sort_values(by="回覧順").reset_index(drop=True)

# ==========================================
#  閲覧状況一括リセット用のコールバック関数
# ==========================================
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

# タブ切り替え
tab1, tab2 = st.tabs(["👤 回覧板チェック", "⚙️ 管理者メニュー"])

# ==========================================
#  タブ1：一般回覧者用の画面
# ==========================================
with tab1:
    st.subheader("✅ 回覧板チェック状況")
    st.markdown("---")
    
    if df_raw.empty:
        st.info("登録されているメンバーがいません。管理者メニューから追加してください。")
    else:
        for i, row in df_raw.iterrows():
            col1, col2 = st.columns([3, 2])
            with col1:
                if row['確認状況'] == '確認済':
                    st.write(f"✅ {int(row['回覧順'])}. {row['お名前']}")
                    st.caption(f"🕒 {row['確認日時']}")
                else:
                    st.write(f"👤 {int(row['回覧順'])}. {row['お名前']}")
            
            with col2:
                if row['確認状況'] != '確認済':
                    if st.button("確認", key=f"btn_{i}", use_container_width=True):
                        JST = timezone(timedelta(hours=+9), 'JST')
                        now = datetime.now(JST).strftime("%m/%d %H:%M")
                        
                        # 元のスプレッドシート上の行番号を動的に検索（同期ズレ対策）
                        # 完全に一致する名前の行を見つけて更新
                        try:
                            cell = sheet.find(row['お名前'])
                            if cell:
                                sheet.update_cell(cell.row, 3, '確認済')
                                sheet.update_cell(cell.row, 4, now)
                                st.success(f"{row['お名前']}さん確認！")
                                st.rerun()
                        except Exception:
                            st.error("データの更新に失敗しました。再読み込みしてください。")
                else:
                    st.markdown("<p style='color: #2ecc71; font-weight: bold; text-align: center; margin: 0;'>確認済</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 6px 0; border:0; border-top: 1px solid #555;'>", unsafe_allow_html=True)

# ==========================================
#  タブ2：管理者用の画面（統合スリム化版）
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
        st.button("全員の確認状況を「未確認」に戻す", use_container_width=True, on_click=callback_reset)

        # ------------------------------------------
        #  2. メンバー名簿の完全統合管理（ここが今回のコアです）
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### 📝 2. 名簿の一括管理（追加・削除・並び替え）")
        st.caption("👇 下のテキストエリアを直接編集してください。追加・削除・並び替えが同時に行えます。")
        
        # 現在のスプレッドシートの名前一覧を取得して表示
        current_names_list = df_raw["お名前"].tolist() if not df_raw.empty else []
        current_names_text = "\n".join(current_names_list)
        
        # 管理者が自由に編集するメインエリア
        managed_text = st.text_area(
            "回覧板の名簿リスト（1行にひとりずつ、回覧順に並べてください）",
            value=current_names_text,
            height=250,
            key="integrated_member_management_area",
            help="名前を追加したい場合は新しい行に入力し、削除したい場合はその行を消してください。上下を入れ替えれば並び順が変わります。"
        )

        if st.button("💾 この内容で名簿を完全に確定して保存する", use_container_width=True):
            # テキストエリアから最新の行データを取得（空行は除外）
            input_names = [line.strip() for line in managed_text.split("\n") if line.strip()]
            
            if not input_names:
                st.error("名簿を空にすることはできません。最低1人以上入力してください。")
            else:
                with st.spinner("スプレッドシートのデータを完全に同期中..."):
                    try:
                        new_rows = []
                        for idx, name in enumerate(input_names):
                            # もともとスプレッドシートにいた人なら、確認状況と日時を引き継ぐ
                            matched_old_row = df_raw[df_raw["お名前"] == name]
                            
                            if not matched_old_row.empty:
                                status = matched_old_row.iloc[0]["確認状況"]
                                c_time = matched_old_row.iloc[0]["確認日時"]
                            else:
                                # 新しく追加された人の場合は初期値
                                status = "未確認"
                                c_time = ""
                                
                            new_rows.append([idx + 1, name, status, c_time])
                        
                        # スプレッドシートを真っさらにして新しい名簿で一撃全上書き（同期ズレの可能性をゼロに）
                        sheet.clear()
                        sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
                        sheet.append_rows(new_rows)
                        
                        st.success("名簿の更新（追加・削除・並び替え）が完全に保存されました！")
                        st.rerun()
                    except Exception as ex:
                        st.error("スプレッドシートへの保存中にエラーが発生しました。接続を確認してください。")

    elif password != "":
        st.error("パスワードが違います。")
