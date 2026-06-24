import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="回覧板", layout="centered")

st.markdown("""
    <style>
        .stApp { background-color: #1e293b; color: #f1f5f9; }
        .member-card { background: #334155; padding: 1rem; border-radius: 12px; margin-bottom: 0.8rem; border: 1px solid #475569; }
        .active-alert { background: #0f172a; padding: 1rem; border-left: 5px solid #3b82f6; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# 接続処理
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets'])
sheet = gspread.authorize(creds).open_by_url("https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit").sheet1
df = pd.DataFrame(sheet.get_all_records())
df["回覧順"] = pd.to_numeric(df["回覧順"], errors='coerce').fillna(999)
df = df.sort_values(by="回覧順").reset_index(drop=True)

tab1, tab2 = st.tabs(["📌 回覧状況", "⚙️ 管理"])

with tab1:
    st.subheader("📋 回覧板")
    # 「次の方」を特定して通知
    pending = df[df['確認状況'] != '確認済']
    if not pending.empty:
        st.markdown(f"<div class='active-alert'>👉 <strong>次は {pending.iloc[0]['お名前']} さん</strong> の番です！回覧をお願いします。</div>", unsafe_allow_html=True)
    else:
        st.success("🎉 全員確認完了です！")

    for _, row in df.iterrows():
        is_done = row['確認状況'] == '確認済'
        st.markdown(f"<div class='member-card'>{int(row['回覧順'])}. {row['お名前']} {'✅' if is_done else '⏳'}</div>", unsafe_allow_html=True)
        
        if is_done:
            if st.button("確認を取り消す", key=f"undo_{row.name}"):
                sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['未確認', '']]}])
                st.success(f"{row['お名前']} さんのステータスを未確認に戻しました")
                st.rerun()
        else:
            if st.button(f"{row['お名前']} さんとして確認する", key=f"btn_{row.name}", type="primary"):
                now = datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M")
                sheet.batch_update([{'range': f'C{row.name+2}:D{row.name+2}', 'values': [['確認済', now]]}])
                st.success(f"{row['お名前']} さんの確認を記録しました！")
                st.rerun()

with tab2:
    if st.text_input("管理パスワード", type="password") == "7777":
        # 誤操作防止のため、ボタンを押した後に処理が確実に行われるように構成
        if st.button("⚠️ 全員を未確認にリセットする"):
            sheet.batch_update([{'range': f'C2:D{len(df)+1}', 'values': [['未確認', ''] for _ in range(len(df))]}])
            st.warning("全員リセットが完了しました。")
            st.rerun()
        
        st.write("---")
        st.write("#### 📝 名簿編集")
        new_names = st.text_area("ここへお名前を1行ずつ入力して保存してください", value="\n".join(df["お名前"].tolist()), height=300)
        if st.button("💾 この名簿で上書き保存する"):
            sheet.clear()
            sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
            sheet.append_rows([[i+1, n.strip(), '未確認', ''] for i, n in enumerate(new_names.split("\n")) if n.strip()])
            st.success("名簿の更新が完了しました！")
            st.rerun()
