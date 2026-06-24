import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

# 🎨 デザイナー監修：モダンカードデザイン
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; font-family: 'Helvetica Neue', sans-serif; }
        .hero { background: #2d3436; padding: 2rem; border-radius: 20px; color: white; margin-bottom: 2rem; text-align: center; }
        .card { background: white; padding: 1.2rem; border-radius: 12px; margin-bottom: 0.8rem; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .member-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .member-info { font-weight: 700; color: #2d3436; font-size: 1.1rem; }
        .time-info { font-size: 0.85rem; color: #636e72; }
        .status-pill { padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; }
        .stButton>button { border-radius: 8px !important; border: none !important; font-weight: 600 !important; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# 接続処理（文字列を1行に統合し、構文を修正）
try:
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sheet = gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit").sheet1
    df = pd.DataFrame(sheet.get_all_records())
    df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
    df = df.sort_values(by="回覧順").reset_index(drop=True)
except Exception as e:
    st.error(f"接続エラー: {e}")
    st.stop()

tab1, tab2 = st.tabs(["📌 回覧状況", "⚙️ 管理"])

with tab1:
    st.markdown("<div class='hero'><h3>回覧板チェック</h3></div>", unsafe_allow_html=True)
    unconfirmed = df[df['確認状況'] != '確認済']
    if not unconfirmed.empty:
        st.markdown(f"**次回の担当:** <span style='color:#0984e3; font-size:1.1rem;'>{unconfirmed.iloc[0]['お名前']} さん</span>", unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        st.markdown(f"""<div class='card'>
            <div class='member-header'>
                <span class='member-info'>{int(row['回覧順'])}. {row['お名前']}</span>
                <span class='status-pill' style='background: {"#e1f5fe" if is_done else "#fff3e0"}'>{ "✅ 確認済" if is_done else "⏳ 未確認" }</span>
            </div>
            {f"<div class='time-info'>🕒 {row['確認日時']}</div>" if is_done and row['確認日時'] else ""}
        </div>""", unsafe_allow_html=True)
        
        if is_done:
            if st.button("確認を取り消す", key=f"undo_{row.name}"):
                sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                st.rerun()
        else:
            if st.button(f"{row['お名前']} さんとして確認", key=f"btn_{row.name}", type="primary"):
                now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                st.rerun()

with tab2:
    if st.text_input("管理者パスワード", type="password") == "7777":
        if st.button("🔄 全員リセット"):
            sheet.batch_update([{'range': f'C2:D{len(df)+1}', 'values': [['未確認', ''] for _ in range(len(df))]}])
            st.rerun()
        new_names = st.text_area("メンバーリスト", value="\n".join(df["お名前"].tolist()))
        if st.button("💾 更新"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.rerun()
