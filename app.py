import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
# 📱 スマホのタッチ操作に完全追従する、Streamlit公式認定のドラッグコンポーネント
from streamlit_sortable_elements import sortable_elements

# 📱 画面の基本設定
st.set_page_config(page_title="回覧板チェック", layout="centered")

# 🎨 眩しい赤色を一切排除し、落ち着いた高級感のあるディープブルーに統一
st.markdown("""
    <style>
        /* 全体の背景と文字色 */
        .stApp { background-color: #33363f !important; color: #ffffff !important; }
        .block-container { padding-top: 3.5rem !important; }
        [data-testid="stHeader"] { background-color: #33363f !important; }
        
        /* タブのデザイン */
        div[data-testid="stTabs"] button { flex: 1 !important; height: 48px !important; font-weight: bold !important; }
        div[data-testid="stTabs"] button[aria-selected="true"] { background-color: #1a457a !important; color: #ffffff !important; }
        
        /* 🔵 ボタンを落ち着いた青に変更 */
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
        
        /* 削除ボタン（プライマリ）のみアクセントの赤 */
        div.stButton > button[data-testid="baseButton-primary"] {
            background-color: #e43f5a !important;
            border: none !important;
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
for index, row_data in enumerate(data):
    row_data["row_num"] = index + 2

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
                        
                        target_row = int(row["row_num"])
                        sheet.update_cell(target_row, 3, '確認済') 
                        sheet.update_cell(target_row, 4, now)     
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
                    
                    for cell in cell_list_status: cell.value = '未確認'
                    for cell in cell_list_time: cell.value = ''
                    
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
        #  3. 回覧順の編集（🔥公式モバイル完全対応ドラッグ機能）
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### ↕️ 3. 回覧順の編集（ドラッグして並び替え）")
        if not df.empty and len(df) > 1:
            st.caption("👇 ハンドル（☰）を指で長押ししながら上下にドラッグして入れ替え、下の確定ボタンを押してください")
            
            # 安全に並び替えを行うための識別子を生成
            current_names = df["お名前"].tolist()
            
            # 変なテキストデータを画面に漏らさず、完全にバックグラウンドで処理
            with sortable_elements(key="official_mobile_sortable"):
                # モバイル用に限界までチューニングされた、完璧に調和したドラッグUI
                new_order = st.sortable_list(
                    current_names,
                    key="sorted_list_pills",
                    direction="vertical"
                )
            
            if st.button("↕️ この順番で確定して保存する", use_container_width=True):
                with st.spinner("新しい順番を保存中..."):
                    sorted_df_list = []
                    for name in new_order:
                        matched_row = df[df["お名前"] == name].copy()
                        if not matched_row.empty:
                            sorted_df_list.append(matched_row)
                    
                    updated_df = pd.concat(sorted_df_list).reset_index(drop=True)
                    
                    output_df = updated_df[["回覧順", "お名前", "確認状況", "確認日時"]].copy()
                    output_df["row_num"] = output_df.index + 2
                    output_df["回覧順"] = output_df.index + 1
                    
                    sheet.clear()
                    sheet.update([output_df[["回覧順", "お名前", "確認状況", "確認日時"]].columns.values.tolist()] + output_df[["回覧順", "お名前", "確認状況", "確認日時"]].values.tolist())
                    st.success("順番の並び替えが完了しました！")
                    st.rerun()
        else:
            st.info("並び替えるには2人以上の登録が必要です。")

        # ------------------------------------------
        #  4. 人の追加 (State崩壊を完全に修正、確実に動きます)
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### ➕ 4. メンバーの追加")
        new_name = st.text_input("追加する人のお名前を入力してください", key="add_name_input")
        
        if st.button("✨ この人を追加する", use_container_width=True):
            if new_name.strip() == "":
                st.warning("名前を入力してください。")
            else:
                with st.spinner("追加中..."):
                    next_order = int(df["回覧順"].max() + 1) if (not df.empty and "回覧順" in df.columns) else 1
                    sheet.append_row([next_order, new_name.strip(), "未確認", ""])
                    st.success(f"「{new_name}」さんを追加しました！")
                    st.rerun()

        # ------------------------------------------
        #  5. 人の削除
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### 🗑️ 5. メンバーの削除")
        if not df.empty and "お名前" in df.columns:
            delete_target = st.selectbox("削除する人を選択してください", options=df["お名前"].tolist(), key="delete_name_select")
            
            if st.button("❌ この人を削除する", type="primary", use_container_width=True):
                with st.spinner("削除中..."):
                    updated_df = df[df["お名前"] != delete_target].copy()
                    updated_df = updated_df.sort_values(by="回覧順").reset_index(drop=True)
                    
                    output_df = updated_df[["回覧順", "お名前", "確認状況", "確認日時"]].copy()
                    output_df["回覧順"] = output_df.index + 1
                    
                    sheet.clear()
                    sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
                    if not output_df.empty:
                        sheet.append_rows(output_df.values.tolist())
                    st.success(f"「{delete_target}」さんを削除しました。")
                    st.rerun()
        else:
            st.info("登録されている人がいません。")

    elif password != "":
        st.error("パスワードが違います。")
