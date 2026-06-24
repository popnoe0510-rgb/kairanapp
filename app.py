import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

# CSS: 青系で統一し、カード構造を安定させる
st.markdown("""
    <style>
        .stApp { background-color: #0f172a; color: #f1f5f9; }
        .inline-time { font-size: 0.8rem; color: #94a3b8; margin-left: 8px; }
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
        st.info(f"現在 **{unconfirmed.iloc[0]['お名前']} さん** の番です。\n 👉 次は **{unconfirmed.iloc[1]['お名前']} さん** です。")
    else:
        st.success("✅ 全員確認完了です！")
    
    for _, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        with st.container(border=True):
            time_text = f"<span class='inline-time'>{row['確認日時']}</span>" if is_done else ""
            st.markdown(f"**{int(row['回覧順'])}. {row['お名前']}** {'✅' if is_done else '⏳'} {time_text}", unsafe_allow_html=True)
            
            if is_done:
                if st.button("取り消し", key=f"undo_{row.name}"):
                    sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                    st.rerun()
            else:
                if st.button("確認", key=f"btn_{row.name}"):
                    now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                    sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                    st.rerun()

with tab2:
    st.header("⚙️ 管理機能")
    if st.text_input("管理パスワードを入力", type="password") == "7777":
        
        # 1. リセットの確認プロセスを復活
        st.subheader("1. 回覧状況リセット")
        if "reset_confirm" not in st.session_state:
            if st.button("🔄 全員をリセットする"):
                st.session_state.reset_confirm = True
                st.rerun()
        
        if st.session_state.get("reset_confirm"):
            st.warning("⚠️ 本当に全員の回覧状況をリセットしますか？")
            col1, col2 = st.columns(2)
            if col1.button("✅ はい（実行）"):
                sheet.batch_update([{'range': f'C2:D{len(df)+1}', 'values': [['未確認', ''] for _ in range(len(df))]}])
                del st.session_state.reset_confirm
                st.success("✅ リセットが完了しました！")
                st.rerun()
            if col2.button("❌ キャンセル"):
                del st.session_state.reset_confirm
                st.rerun()
        
        st.write("---")
        st.subheader("2. 名簿の編集")
        new_names = st.text_area("1行1名で入力。", value="\n".join(df["お名前"].tolist()), height=300)
        if st.button("💾 上書き保存"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.success("✅ 名簿を更新しました。")
            st.rerun()
