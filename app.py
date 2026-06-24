import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import json

# 📱 画面の基本設定
st.set_page_config(page_title="回覧板チェック", layout="centered")

# 🎨 アプリ全体の統一デザインCSS（赤色の徹底排除）
st.markdown("""
    <style>
        .stApp { background-color: #33363f !important; color: #ffffff !important; }
        .block-container { padding-top: 3.5rem !important; }
        [data-testid="stHeader"] { background-color: #33363f !important; }
        
        /* タブ */
        div[data-testid="stTabs"] button { flex: 1 !important; height: 48px !important; font-weight: bold !important; }
        div[data-testid="stTabs"] button[aria-selected="true"] { background-color: #1a457a !important; color: #ffffff !important; }
        
        /* 🔵 ボタンをディープブルーに統一 */
        div.stButton > button {
            background-color: #1f4068 !important;
            color: #ffffff !important;
            border: 1px solid #162447 !important;
            border-radius: 6px !important;
            transition: background-color 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #162447 !important;
            color: #ffffff !important;
        }
        
        /* 危険アクション（削除）のみ赤 */
        div.stButton > button[data-testid="baseButton-primary"] {
            background-color: #e43f5a !important;
            border: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# 1. スプレッドシート接続
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ak_gAsNeo9LfdIDCN5ym65OZvVTxlL_YBOriuKpWA9s/edit"
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
except Exception as e:
    st.error("スプレッドシートの接続設定を確認してください。")
    st.stop()

# データの読み込み
data = sheet.get_all_records()
for index, row_data in enumerate(data):
    row_data["row_num"] = index + 2

df = pd.DataFrame(data)
if not df.empty and "回覧順" in df.columns:
    df = df.sort_values(by="回覧順").reset_index(drop=True)

# タブ切り替え
tab1, tab2 = st.tabs(["👤 回覧板チェック", "⚙️ 管理者メニュー"])

# ==========================================
#  タブ1：一般回覧者用の画面
# ==========================================
with tab1:
    st.subheader("✅ 回覧板チェック状況")
    st.markdown("---")
    
    if df.empty:
        st.info("登録されているメンバーがいません。管理者メニューから追加してください。")
    else:
        for i, row in df.iterrows():
            col1, col2 = st.columns([3, 2])
            with col1:
                if row['確認状況'] == '確認済':
                    st.write(f"✅ {row['回覧順']}. {row['お名前']}")
                    st.caption(f"🕒 {row['確認日時']}")
                else:
                    st.write(f"👤 {row['回覧順']}. {row['お名前']}")
            
            with col2:
                if row['確認状況'] != '確認済':
                    if st.button("確認", key=f"btn_{i}", use_container_width=True):
                        JST = timezone(timedelta(hours=+9), 'JST')
                        now = datetime.now(JST).strftime("%m/%d %H:%M")
                        
                        target_row = int(row["row_num"])
                        sheet.update_cell(target_row, 3, '確認済') 
                        sheet.update_cell(target_row, 4, now)     
                        st.success(f"{row['お名前']}さん確認！")
                        st.rerun()
                else:
                    st.markdown("<p style='color: #2ecc71; font-weight: bold; text-align: center; margin: 0;'>確認済</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 6px 0; border:0; border-top: 1px solid #555;'>", unsafe_allow_html=True)

# ==========================================
#  タブ2：管理者用の画面
# ==========================================
with tab2:
    st.subheader("⚙️ 管理者設定")
    password = st.text_input("管理者パスワードを入力してください", type="password")
    
    if password == "7777":
        st.success("認証されました")
        
        # ------------------------------------------
        #  1. 閲覧状況のリセット
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### 🔁 1. 閲覧状況のリセット")
        if st.button("全員の確認状況を「未確認」に戻す", use_container_width=True):
            if not df.empty:
                with st.spinner("リセット中..."):
                    total_rows = len(df) + 1
                    cell_list_status = sheet.range(2, 3, total_rows, 3)
                    cell_list_time = sheet.range(2, 4, total_rows, 4)
                    
                    for cell in cell_list_status: cell.value = '未確認'
                    for cell in cell_list_time: cell.value = ''
                    
                    sheet.update_cells(cell_list_status)
                    sheet.update_cells(cell_list_time)
                    st.success("全員のステータスをリセットしました！")
                    st.rerun()
            else:
                st.info("登録されている人がいません。")

        # ------------------------------------------
        #  2. 登録されている人の一覧リスト
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### 📋 2. 登録メンバー一覧")
        if not df.empty:
            for _, row in df.iterrows():
                status_emoji = "✅" if row['確認状況'] == "確認済" else "⏳"
                time_str = f" ({row['確認日時']})" if row['確認日時'] else ""
                st.text(f"【{row['回覧順']}番】 {row['お名前']} さん  [{status_emoji}{row['確認状況']}{time_str}]")
        else:
            st.info("現在、誰も登録されていません。")

        # ------------------------------------------
        #  3. 回覧順の編集（🔥完全ネイティブ JavaScript ドラッグ＆ドロップ）
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### ↕️ 3. 回覧順の編集（ドラッグして並び替え）")
        if not df.empty and len(df) > 1:
            st.caption("👇 カードを指で掴んで上下にスライドして並び替え、下の確定ボタンを押してください")
            
            # 現在のメンバーリスト
            current_names = df["お名前"].tolist()
            
            # 🛠️ JavaScriptから最速で結果を受け取るための隠し入力フィールド
            if "js_sorted_output" not in st.session_state:
                st.session_state["js_sorted_output"] = json.dumps(current_names)
            
            # 高級HTML/CSS/JavaScriptコンポーネントをアプリ内にダイレクト注入
            # スマホのTouchEventを完全にハンドリングし、引っかかりのない滑らかなドラッグを実現
            html_items = "".join([f'<div class="draggable-item" draggable="true" data-name="{name}"><span class="drag-handle">☰</span> {name}</div>' for name in current_names])
            
            custom_html = f"""
            <div id="drag-container">
                {html_items}
            </div>

            <style>
                #drag-container {{
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    padding: 5px 0;
                    font-family: sans-serif;
                }}
                .draggable-item {{
                    display: flex;
                    align-items: center;
                    background-color: #1f4068 !important;
                    color: #ffffff !important;
                    padding: 14px 16px;
                    border-radius: 8px;
                    border: 1px solid #162447;
                    cursor: grab;
                    user-select: none;
                    font-weight: bold;
                    font-size: 16px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    touch-action: none; /* スマホの画面スクロールと競合させないための魔術 */
                }}
                .draggable-item.dragging {{
                    opacity: 0.5;
                    background-color: #162447 !important;
                    border: 1px dashed #ffffff;
                }}
                .drag-handle {{
                    margin-right: 15px;
                    color: #888;
                    font-size: 18px;
                    cursor: grab;
                }}
            </style>

            <script>
                (function() {{
                    const container = document.getElementById('drag-container');
                    let draggingElement = null;

                    // 🖥️ PC用マウスドラッグイベント
                    container.addEventListener('dragstart', (e) => {{
                        if(e.target.classList.contains('draggable-item')) {{
                            draggingElement = e.target;
                            e.target.classList.add('dragging');
                        }}
                    }});

                    container.addEventListener('dragend', (e) => {{
                        if(e.target.classList.contains('draggable-item')) {{
                            e.target.classList.remove('dragging');
                            saveOrder();
                        }}
                    }});

                    container.addEventListener('dragover', (e) => {{
                        e.preventDefault();
                        const afterElement = getDragAfterElement(container, e.clientY);
                        if (afterElement == null) {{
                            container.appendChild(draggingElement);
                        }} else {{
                            container.insertBefore(draggingElement, afterElement);
                        }}
                    }});

                    // 📱 スマホ用タッチ移動イベント (これがエリートベテランのTouch最適化ロジック)
                    container.addEventListener('touchstart', (e) => {{
                        const item = e.target.closest('.draggable-item');
                        if (item) {{
                            draggingElement = item;
                            item.classList.add('dragging');
                        }}
                    }}, {{passive: false}});

                    container.addEventListener('touchmove', (e) => {{
                        if (!draggingElement) return;
                        e.preventDefault(); // スマホ全体のスクロールを一時ロック
                        const touch = e.touches[0];
                        const afterElement = getDragAfterElement(container, touch.clientY);
                        if (afterElement == null) {{
                            container.appendChild(draggingElement);
                        }} else {{
                            container.insertBefore(draggingElement, afterElement);
                        }}
                    }}, {{passive: false}});

                    container.addEventListener('touchend', (e) => {{
                        if (draggingElement) {{
                            draggingElement.classList.remove('dragging');
                            draggingElement = null;
                            saveOrder();
                        }}
                    }});

                    function getDragAfterElement(container, y) {{
                        const draggableElements = [...container.querySelectorAll('.draggable-item:not(.dragging)')];
                        return draggableElements.reduce((closest, child) => {{
                            const box = child.getBoundingClientRect();
                            const offset = y - box.top - box.height / 2;
                            if (offset < 0 && offset > closest.offset) {{
                                return {{ offset: offset, element: child }};
                            }} else {{
                                return closest;
                            }}
                        }}, {{ offset: Number.NEGATIVE_INFINITY }}).element;
                    }}

                    // 並び順が変わるたびにStreamlitの親システムに値を即座に通知
                    function saveOrder() {{
                        const items = [...container.querySelectorAll('.draggable-item')];
                        const names = items.map(item => item.getAttribute('data-name'));
                        
                        // Streamlitの内部APIを経由してPython側に通知する高難度通信ロジック
                        const query = new URLSearchParams(window.location.search);
                        window.parent.postMessage({{
                            type: 'streamlit:set_widget_value',
                            key: 'js_sorted_output',
                            value: JSON.stringify(names)
                        }}, '*');
                    }}
                }})();
            </script>
            """
            
            # HTMLを安全に埋め込み (高さは人数に合わせて自動調整)
            st.components.v1.html(custom_html, height=len(current_names) * 60 + 20)
            
            # Python側でJavaScriptからの確定結果を受け取る用のテキスト入力
            result_json = st.text_input("内部通信バッファ", value=st.session_state["js_sorted_output"], key="js_sorted_output", label_visibility="collapsed")

            if st.button("↕️ この順番で確定して保存する", use_container_width=True):
                with st.spinner("新しい順番を保存中..."):
                    try:
                        sorted_names = json.loads(result_json)
                        
                        sorted_df_list = []
                        for name in sorted_names:
                            matched_row = df[df["お名前"] == name].copy()
                            if not matched_row.empty:
                                sorted_df_list.append(matched_row)
                        
                        updated_df = pd.concat(sorted_df_list).reset_index(drop=True)
                        
                        output_df = updated_df[["回覧順", "お名前", "確認状況", "確認日時"]].copy()
                        output_df["row_num"] = output_df.index + 2
                        output_df["回覧順"] = output_df.index + 1
                        
                        sheet.clear()
                        sheet.update([output_df[["回覧順", "お名前", "確認状況", "確認日時"]].columns.values.tolist()] + output_df[["回覧順", "お名前", "確認状況", "確認日時"]].values.tolist())
                        st.success("順番の並び替えが完了しました！")
                        st.rerun()
                    except Exception as ex:
                        st.error("並び替えデータの解析に失敗しました。もう一度動かしてください。")
        else:
            st.info("並び替えるには2人以上の登録が必要です。")

        # ------------------------------------------
        #  4. 人の追加
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### ➕ 4. メンバーの追加")
        new_name = st.text_input("追加する人のお名前を入力してください", key="add_name_input")
        
        if st.button("✨ この人を追加する", use_container_width=True):
            if new_name.strip() == "":
                st.warning("名前を入力してください。")
            else:
                with st.spinner("追加中..."):
                    next_order = int(df["回覧順"].max() + 1) if (not df.empty and "回覧順" in df.columns) else 1
                    sheet.append_row([next_order, new_name.strip(), "未確認", ""])
                    st.success(f"「{new_name}」さんを追加しました！")
                    st.rerun()

        # ------------------------------------------
        #  5. 人の削除
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### 🗑️ 5. メンバーの削除")
        if not df.empty and "お名前" in df.columns:
            delete_target = st.selectbox("削除する人を選択してください", options=df["お名前"].tolist(), key="delete_name_select")
            
            if st.button("❌ この人を削除する", type="primary", use_container_width=True):
                with st.spinner("削除中..."):
                    updated_df = df[df["お名前"] != delete_target].copy()
                    updated_df = updated_df.sort_values(by="回覧順").reset_index(drop=True)
                    
                    output_df = updated_df[["回覧順", "お名前", "確認状況", "確認日時"]].copy()
                    output_df["回覧順"] = output_df.index + 1
                    
                    sheet.clear()
                    sheet.append_row(["回覧順", "お名前", "確認状況", "確認日時"])
                    if not output_df.empty:
                        sheet.append_rows(output_df.values.tolist())
                    st.success(f"「{delete_target}」さんを削除しました。")
                    st.rerun()
        else:
            st.info("登録されている人がいません。")

    elif password != "":
        st.error("パスワードが違います。")
