import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="回覧板チェック", layout="centered")

# 1. スプレッドシート接続
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    # 🔗 あなたのスプレッドシートURLを反映しました！
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit"
    
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
except Exception as e:
    st.error("スプレッドシートの接続設定を確認してください。")
    st.stop()

# データの読み込み
data = sheet.get_all_records()
df = pd.DataFrame(data)
# 回覧順で並び替え
df = df.sort_values(by="回覧順").reset_index(drop=True)

# タブ機能で「一般画面」と「管理者画面」を分ける
tab1, tab2 = st.tabs(["👤 回覧板チェック", "⚙️ 管理者メニュー"])

# ==========================================
#  タブ1：一般回覧者用の画面（いつもの画面）
# ==========================================
with tab1:
    st.title("✅ 回覧板チェック状況")
    st.markdown("---")
    
    for i, row in df.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            if row['確認状況'] == '確認済':
                st.write(f"### ✅ {row['回覧順']}. {row['お名前']}")
                st.caption(f"（{row['確認日時']} に確認済み）")
            else:
                st.write(f"### 👤 {row['回覧順']}. {row['お名前']}")
        
        with col2:
            if row['確認状況'] != '確認済':
                if st.button("確認", key=f"btn_{i}", use_container_width=True):
                    now = datetime.now().strftime("%m/%d %H:%M")
                    # スプレッドシートの元の行番号（i+2）を更新
                    sheet.update_cell(int(i) + 2, 3, '確認済') 
                    sheet.update_cell(int(i) + 2, 4, now)     
                    st.success(f"{row['お名前']}さんの確認を記録しました！")
                    st.rerun()
            else:
                st.write(" ")

# ==========================================
#  タブ2：管理者用の画面
# ==========================================
with tab2:
    st.title("⚙️ 管理者設定")
    
    # 簡易パスワード保護
    password = st.text_input("管理者パスワードを入力してください", type="password")
    if password == "7777": # 👈 好きなパスワードに変えられます
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
        st.caption("表のセルを直接ダブルクリックして、名前や順番を書き換えてください。終わったら下の保存ボタンを押します。")
        
        # 画面上で編集できる表を表示
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
