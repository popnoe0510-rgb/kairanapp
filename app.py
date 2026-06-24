import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

# CSS: ボタンを消し、日時と取り消しアイコンを小さく配置するための調整
st.markdown("""
    <style>
        .stApp { background-color: #0f172a !important; }
        .member-info { display: flex; align-items: center; gap: 8px; font-size: 0.9rem; }
        .date-text { font-size: 0.75rem; color: #94a3b8; }
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
        st.info(f"📬 **{unconfirmed.iloc[0]['お名前']} さん** の番です。")
    else:
        st.success("✅ 全員確認完了です！")
    
    for _, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        with st.container(border=True):
            # 行全体のレイアウト
            col_left, col_right = st.columns([4, 1])
            
            with col_left:
                if is_done:
                    # 確認済：名前 ＋ 日時 ＋ 🗑️ボタン
                    st.markdown(f"<div class='member-info'>**{int(row['回覧順'])}. {row['お名前']}** ✅ <span class='date-text'>{row['確認日時']}</span></div>", unsafe_allow_html=True)
                else:
                    # 未確認：名前 ＋ ⏳
                    st.markdown(f"**{int(row['回覧順'])}. {row['お名前']}** ⏳", unsafe_allow_html=True)
            
            with col_right:
                if is_done:
                    # 取り消しをアイコンボタンとして右詰めで配置
                    if st.button("🗑️", key=f"undo_{row.name}", help="取り消し"):
                        sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                        st.rerun()
                else:
                    # 確認を青いボタンで配置
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
