import streamlit as st
import pandas as pd

# アプリのタイトル
st.title("✅ 回覧板チェック状況")
st.write("ご近所の回覧状況がリアルタイムで確認できます。")

# ⚠️ここにあなたのGoogleスプレッドシートのURLを貼り付けます
# ※URLの末尾を置き換えてCSVとして読み込んでいます
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/gviz/tq?tqx=out:csv"

# データの読み込み
try:
    df = pd.read_csv(SHEET_URL)
    # 回覧順に並び替え
    df = df.sort_values(by="回覧順")
except Exception as e:
    st.error("データの読み込みに失敗しました。スプレッドシートの共有設定またはURLを確認してください。")
    st.stop()

st.markdown("---")

# 1画面にシンプルに住民リストを表示
for index, row in df.iterrows():
    col1, col2, col3 = st.columns([1, 2, 2])
    
    with col1:
        st.write(f"**{row['回覧順']}番**")
    with col2:
        # ステータスによって見た目を変える
        if row['確認状況'] == '確認済':
            st.write(f"✅ **{row['お名前']}**")
        else:
            st.write(f"👤 {row['お名前']}")
            
    with col3:
        if row['確認状況'] == '確認済':
            st.caption(f"（{row['確認日時']} 確認）")
        else:
            st.caption("ーー")

st.markdown("---")
st.caption("※回覧板を確認したら、表紙の紙にチェックを入れて次の人に回してください。")
