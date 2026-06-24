import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

# 🎨 デザイナー渾身：境界線を使わない「色面デザイン」
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; }
        /* 交互に背景色を変えてエリアを視覚化 */
        .row-even { background: #f0f2f6; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.2rem; }
        .row-odd { background: #ffffff; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.2rem; }
        
        /* 押しやすい青系ボタン */
        .stButton>button { 
            width: 100%; border-radius: 6px !important; border: none !important; 
            background-color: #0984e3 !important; color: white !important; font-weight: 600 !important;
        }
        .stButton>button:hover { background-color: #74b9ff !important; }
        
        /* 管理画面のテキストエリア拡張 */
        .stTextArea textarea { height: 350px !important; }
    </style>
""", unsafe_allow_html=True)

# 接続処理
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
sheet = gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit").sheet1
df = pd.DataFrame(sheet.get_all_records())
df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
df = df.sort_values(by="回覧順").reset_index(drop=True)

tab1, tab2 = tab1, tab2 = st.tabs(["📌 回覧状況", "⚙️ 管理"])

with tab1:
    st.subheader("📋 回覧板")
    for i, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        bg_class = "row-even" if i % 2 == 0 else "row-odd"
        
        st.markdown(f"""<div class='{bg_class}'>
            <div style='display:flex; justify-content:space-between;'>
                <strong>{int(row['回覧順'])}. {row['お名前']}</strong>
                <span>{"✅ " + str(row['確認日時']) if is_done else "⏳"}</span>
            </div>
        </div>""", unsafe_allow_html=True)
        
        if is_done:
            if st.button("取り消し", key=f"undo_{row.name}"):
                sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                st.toast("取り消しました！")
                st.rerun()
        else:
            if st.button("確認する", key=f"btn_{row.name}"):
                now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                st.toast(f"{row['お名前']} さんの確認を記録！")
                st.rerun()

with tab2:
    if st.text_input("管理パスワード", type="password") == "7777":
        if st.button("🔄 全員リセット"):
            sheet.batch_update([{'range': f'C2:D{len(df)+1}', 'values': [['未確認', ''] for _ in range(len(df))]}])
            st.toast("リセット完了")
            st.rerun()
        
        new_names = st.text_area("名簿編集（1行1名）", value="\n".join(df["お名前"].tolist()))
        if st.button("💾 名簿を保存"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.toast("保存完了！")
            st.rerun()
