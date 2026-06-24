import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

# CSS: 最低限の背景色指定のみ（配置は構造で制御）
st.markdown("""
    <style>
        .stApp { background-color: #0f172a !important; }
        .stButton button { background-color: #1e40af !important; color: white !important; }
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
        msg = f"📬 現在は **{unconfirmed.iloc[0]['お名前']} さん** の番です。"
        if len(unconfirmed) > 1:
            msg += f"\n\n👉 次は **{unconfirmed.iloc[1]['お名前']} さん** に回覧してください。"
        st.info(msg)
    else:
        st.success("✅ 全員確認完了です！")
    
    for _, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        with st.container(border=True):
            # 1. 情報を表示する列と、ボタンを置く列に分ける（これで右詰めを実現）
            col_info, col_btn = st.columns([3, 1])
            
            with col_info:
                time_str = f" <small style='color: #94a3b8;'>({row['確認日時']})</small>" if is_done else ""
                st.markdown(f"**{int(row['回覧順'])}. {row['お名前']}** {'✅' if is_done else '⏳'}{time_str}", unsafe_allow_html=True)
            
            with col_btn:
                if is_done:
                    if st.button("取り消し", key=f"undo_{row.name}"):
                        sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                        st.rerun()
                else:
                    if st.button("確認", key=f"btn_{row.name}", type="primary"):
                        now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                        sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                        st.rerun()

with tab2:
    st.header("⚙️ 管理機能")
    if st.text_input("パスワード", type="password") == "7777":
        if st.button("🔄 全員リセット"):
            sheet.batch_update([{'range': f'C2:D{len(df)+1}', 'values': [['未確認', ''] for _ in range(len(df))]}])
            st.rerun()
        
        new_names = st.text_area("名簿編集", value="\n".join(df["お名前"].tolist()))
        if st.button("💾 上書き保存"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.rerun()
