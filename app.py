import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone

# 📱 画面の基本設定
st.set_page_config(page_title="回覧板チェック", layout="centered")

# 🎨 【安全第一】Streamlitを絶対に壊さないディープブルー・スタイル
st.markdown("""
    <style>
        /* 全体の背景と文字色（標準構造を壊さない安全な定義） */
        .stApp { 
            background-color: #242730 !important; 
            color: #ffffff !important; 
        }
        
        /* 🔵 ボタンの基本デザインを統一 */
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
        
        /* 🟩 「確認する」ボタンのみ、クラスを汚さずスタイルを微調整（緑枠に変更し安全性を担保） */
        div.stButton > button:active {
            background-color: #38ef7d !important;
            color: #111111 !important;
        }
        
        /* リストの区切り線 */
        .divider { 
            margin: 16px 0; 
            border: 0; 
            border-top: 1px solid #3d4357; 
        }
        
        /* 確認済みのリッチなテキスト表現 */
        .checked-status { 
            color: #38ef7d; 
            font-weight: bold; 
            text-align: center; 
            margin: 0; 
            font-size: 15px; 
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

# 破壊原因だったカスタムCSS付きのタブを廃止し、Streamlit標準に完全準拠
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
                    if st.button("確認する", key=f"btn_{i}", use_container_width=True):
                        JST = timezone(timedelta(hours=+9), 'JST')
                        now = datetime.now(JST).strftime("%m/%d %H:%M")
                        try:
                            cell = sheet.find(str(row['お名前']))
                            if cell:
                                sheet.update_cell(cell.row, 3, '確認済')
                                sheet.update_cell(cell.row, 4, now)
                                st.success(f"{row['お名前']}さん確認！")
                                st.rerun()
                            else:
                                st.error("名簿に名前が見つかりませんでした。")
                        except Exception:
                            st.error("データの更新に失敗しました。再読み込みしてください。")
                else:
                    st.markdown("<p class='checked-status'>確認済</p>", unsafe_allow_html=True)
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ==========================================
#  タブ2：管理者用の画面
# ==========================================
with tab2:
    st.markdown("### ⚙️ 管理者設定")
    password = st.text_input("管理者パスワードを入力してください", type="password")
    
    if password == "7777":
        st.success("認証されました")
        
        # 1. 閲覧状況のリセット
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("#### 🔁 1. 閲覧状況の一括リセット")
        st.button("全員の確認状況を「未確認」に戻す", use_container_width=True, on_click=callback_reset)

        # 2. 名簿の完全統合管理
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("#### 📝 2. 名簿の一括管理（追加・削除・並び替え）")
        st.caption("※1行にひとりずつお名前を入力してください。文字を消せば削除され、行を入れ替えれば順番が変わります。")
        
        current_names_list = df_raw["お名前"].tolist() if not df_raw.empty else []
        current_names_text = "\n".join(current_names_list)
        
        managed_text = st.text_area(
            "回覧板の名簿リスト",
            value=current_names_text,
            height=220,
            placeholder="（入力例）\n山田太郎\n佐藤花子\n鈴木一郎",
            key="integrated_member_management_area"
        )

        if st.button("💾 この内容で名簿を完全に確定して保存する", use_container_width=True):
            input_names = [line.strip() for line in managed_text.split("\n") if line.strip()]
            
            if not input_names:
                st.error("名簿を空にすることはできません。最低1人以上入力してください。")
            else:
                with st.spinner("スプレッドシートのデータを完全に同期中..."):
                    try:
                        new_rows = []
                        for idx, name in enumerate(input_names):
                            matched_old_row = df_raw[df_raw["お名前"] == name]
                            if not matched_old_row.empty:
                                status = matched_old_row.iloc[0]["確認状況"]
                                c_time = matched_old_row.iloc[0]["確認日時"]
                            else:
                                status = "未確認"
                                c_time = ""
                            new_rows.append([idx + 1, name, status, c_time])
                        
                        sheet.clear()
                        sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
                        sheet.append_rows(new_rows)
                        
                        st.success("名簿の更新が完全に保存されました！")
                        st.rerun()
                    except Exception as ex:
                        st.error("保存中にエラーが発生しました。")

    elif password != "":
        st.error("パスワードが違います。")
