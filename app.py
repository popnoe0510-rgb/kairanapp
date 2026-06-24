import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

# CSS: ボタンの視認性を高め、管理メニューを明確に分離
st.markdown("""
    <style>
        .stApp { background-color: #1e293b; color: #f1f5f9; }
        .member-card { background: #334155; padding: 1rem; border-radius: 12px; margin-bottom: 0.8rem; border: 1px solid #475569; }
        .admin-section { background: #0f172a; padding: 1.5rem; border-radius: 12px; margin-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# 接続処理
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
sheet = gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit").sheet1
df = pd.DataFrame(sheet.get_all_records())
df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
df = df.sort_values(by="回覧順").reset_index(drop=True)

tab1, tab2 = st.tabs(["📌 回覧状況", "⚙️ 管理画面"])

with tab1:
    st.subheader("📋 現在の回覧状況")
    unconfirmed = df[df['確認状況'] != '確認済']
    if not unconfirmed.empty:
        st.info(f"👉 次は **{unconfirmed.iloc[0]['お名前']} さん** の番です。")
    
    for _, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        st.markdown(f"<div class='member-card'><strong>{int(row['回覧順'])}. {row['お名前']}</strong> {'✅' if is_done else '⏳'}<br><small>{row['確認日時'] if is_done else '未確認'}</small></div>", unsafe_allow_html=True)
        
        if is_done:
            if st.button("取り消し", key=f"undo_{row.name}"):
                sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                st.rerun()
        else:
            if st.button(f"{row['お名前']} さんとして確認", key=f"btn_{row.name}", type="primary"):
                now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]]}])
                st.rerun()

with tab2:
    st.header("⚙️ 管理機能")
    if st.text_input("管理パスワードを入力", type="password") == "7777":
        
        # 1. 全員リセット機能
        st.subheader("1. 全員リセット")
        st.caption("回覧状況を初期化（全員未確認）します。")
        if st.button("🔄 全員リセットを実行"):
            sheet.batch_update([{'range': f'C2:D{len(df)+1}', 'values': [['未確認', ''] for _ in range(len(df))]}])
            st.success("リセットが完了しました！全員未確認の状態です。")
            st.rerun()
        
        # 2. 名簿編集機能
        st.subheader("2. 名簿の編集")
        st.caption("名前を1行ずつ入力してください。保存すると自動でリストが更新されます。")
        new_names = st.text_area("メンバー名簿", value="\n".join(df["お名前"].tolist()), height=300)
        if st.button("💾 名簿を保存して更新"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.success("名簿の更新が完了しました！")
            st.rerun()
    else:
        st.warning("正しいパスワードを入力してください。")
