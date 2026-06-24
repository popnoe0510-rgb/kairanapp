import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板アプリ", layout="centered")

# 🎨 スタイル定義：入力ボックスを明確化
st.markdown("""
    <style>
        .stApp { background-color: #242730; color: #ffffff; }
        input, textarea { background-color: #ffffff !important; color: #333 !important; border: 2px solid #58a6ff !important; }
        .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 接続処理（省略）
try:
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sheet = gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit").sheet1
    df = pd.DataFrame(sheet.get_all_records())
    df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
    df = df.sort_values(by="回覧順").reset_index(drop=True)
except Exception: st.stop()

tab1, tab2 = st.tabs(["👤 回覧状況", "⚙️ 管理者専用"])

with tab1:
    st.subheader("📋 回覧板の現在状況")
    
    unconfirmed = df[df['確認状況'] != '確認済']
    if not unconfirmed.empty:
        # 「自分ボール」を分かりやすく
        target = unconfirmed.iloc[0]
        st.info(f"👉 【現在、あなたの番です】\n回覧物を確認したら、下の「回覧板を見ました」ボタンを押してください。")
    
    for _, row in df.iterrows():
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"**{int(row['回覧順'])}. {row['お名前']}**")
        with col2:
            if row['確認状況'] == '確認済':
                st.caption(f"✅ 確認済 ({row['確認日時']})")
            else:
                if st.button("回覧板を見ました", key=f"btn_{row['お名前']}"):
                    sheet.update_cell(row.name + 2, 3, '確認済')
                    sheet.update_cell(row.name + 2, 4, datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M"))
                    # アクション後のポップアップ的通知
                    st.success(f"確認しました！次は{unconfirmed.iloc[1]['お名前'] if len(unconfirmed)>1 else '全員確認済み'}さんへ回ります。")
                    st.rerun()

with tab2:
    st.subheader("⚙️ 管理者設定")
    if st.text_input("パスワード", type="password") == "7777":
        # 具体的な説明を追加
        st.write("---")
        st.write("### 🔁 全員のリセット")
        st.write("全員の「確認済み」状態をクリアし、全員「未確認」に戻します。新しい回覧板を回す際に使用してください。")
        if st.button("全員のステータスをリセットする"):
            for i in range(len(df)):
                sheet.update_cell(i + 2, 3, '未確認')
                sheet.update_cell(i + 2, 4, '')
            st.rerun()
        
        st.write("---")
        st.write("### 📝 名簿の編集")
        st.write("1行に1人名前を入力してください。名前を消すと削除、行を入れ替えると回覧順が変わります。")
        new_names = st.text_area("メンバーリスト", value="\n".join(df["お名前"].tolist()), height=200)
        if st.button("💾 名簿を確定・更新する"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.rerun()
