import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="回覧板チェック", layout="centered")

# 🎨 デザイン：文字入力欄の視認性向上と、確認済表示をコンパクトに
st.markdown("""
    <style>
        .stApp { background-color: #242730 !important; color: #ffffff !important; }
        /* タブの高さとサイズ調整 */
        div[data-testid="stTabs"] button { height: 60px !important; font-size: 18px !important; }
        /* 入力エリアの視認性アップ */
        textarea { background-color: #3d4357 !important; color: white !important; border: 1px solid #7d859e !important; }
        /* 確認済み表示を小さく */
        .checked-tag { color: #38ef7d; font-size: 0.9em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# スプレッドシート接続
try:
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sheet = gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit").sheet1
    df = pd.DataFrame(sheet.get_all_records())
    if not df.empty:
        df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
        df = df.sort_values(by="回覧順").reset_index(drop=True)
except Exception:
    st.stop()

tab1, tab2 = st.tabs(["👤 回覧状況", "⚙️ 管理"])

with tab1:
    st.subheader("✅ 回覧状況")
    if df.empty:
        st.info("メンバーがいません。")
    else:
        # 未確認の人を優先表示するロジック
        unconfirmed = df[df['確認状況'] != '確認済']
        confirmed = df[df['確認状況'] == '確認済']
        
        if not unconfirmed.empty:
            st.warning(f"👉 現在のボール: **{unconfirmed.iloc[0]['お名前']}** さん")
        
        for _, row in pd.concat([unconfirmed, confirmed]).iterrows():
            col1, col2 = st.columns([2, 1])
            with col1:
                if row['確認状況'] == '確認済':
                    st.markdown(f"✅ {row['お名前']} <span class='checked-tag'>(済)</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"👤 **{row['お名前']}**")
            with col2:
                if row['確認状況'] != '確認済':
                    if st.button("確認する", key=f"btn_{row['お名前']}"):
                        sheet.update_cell(row.name + 2, 3, '確認済')
                        sheet.update_cell(row.name + 2, 4, datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M"))
                        st.rerun()

with tab2:
    if st.text_input("パスワード", type="password") == "7777":
        if st.button("🔄 全員リセット"):
            for i in range(len(df)):
                sheet.update_cell(i + 2, 3, '未確認')
                sheet.update_cell(i + 2, 4, '')
            st.rerun()
        
        st.write("📝 **名簿編集 (1行1人)**")
        new_names = st.text_area("メンバーリスト", value="\n".join(df["お名前"].tolist()), height=200)
        if st.button("💾 更新"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.rerun()
