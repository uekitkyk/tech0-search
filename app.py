# =============================================================
# answers/w3/app.py — Tech0 Search（W3 完成版：DB化＋全文検索）
# データの読み込み先が pages_w2.json → SQLite に変わり、検索が全文検索になった版。
# 起動： streamlit run app.py
# （schema.sql / database.py / search_fulltext.py / crawler.py / pages_w2.json が同じフォルダに必要）
# =============================================================
import streamlit as st
from database import init_db, insert_page, get_all_pages, migrate_from_json
from search_fulltext import search_fulltext          # W3 の全文検索（match_count版）
from crawler import crawl_url                        # W2 から流用

# アプリ起動時に DB を初期化する（テーブルが未作成なら作る）
init_db()

st.set_page_config(page_title="Tech0 Search（W3）", page_icon="🔍")
st.title("🔍 Tech0 Search")
st.caption("PROJECT ZERO — 社内ナレッジ検索エンジン【DB化＋全文検索】")

# サイドバー：pages_w2.json → DB への移行（W3 の移行作業）
with st.sidebar:
    st.header("DB の状態")

    # st.rerun() をまたいでメッセージを持ち越す（W1 と同じ仕組み）
    if st.session_state.get("migrated") is not None:
        st.success(f"{st.session_state['migrated']} 件を DB に移行しました")
        st.session_state["migrated"] = None
    pages = get_all_pages()                          # ← 読み込み先は DB！
    st.metric("登録ページ数", f"{len(pages)} 件")
    if st.button("📦 pages_w2.json から DB へ移行"):
        n = migrate_from_json("pages_w2.json")
        st.session_state["migrated"] = n   # 件数を印として残す
        st.rerun()

tab1, tab2, tab3 = st.tabs(["検索", "クロール", "一覧"])

# ── 検索タブ（DB → 全文検索の2行がキモ） ──
with tab1:
    st.subheader("🔍 全文検索（本文まで探す）")
    query = st.text_input("🔑 キーワードを入力")
    if query:
        pages   = get_all_pages()                    # DB から全ページを読む（Step 2）
        results = search_fulltext(query, pages)      # 全文検索する（Step 3）

        st.markdown(f"**検索結果: {len(results)}件**（match_count順）")
        st.divider()
        for r in results:
            st.markdown(f"### [{r['title']}]({r['url']})")
            st.markdown(f"🔢 マッチ数: **{r['match_count']}** 回")
            if r.get("preview"):
                st.caption(r["preview"])
            st.divider()

# ── クロールタブ（登録先が DB に変わった） ──
with tab2:
    st.subheader("🤖 クロールして DB に登録")
    url_input = st.text_input("クロールしたいURL")
    if st.button("🤖 クロール実行"):
        if url_input:
            with st.spinner(f"クロール中: {url_input}"):
                result = crawl_url(url_input)
            if result.get("crawl_status") == "success":
                insert_page(result)                  # ← 保存先は DB！（同じURLは上書き）
                st.success(f"✅ DB に登録: {result['title']}（{result['word_count']} 語）")
            else:
                st.error(f"❌ 取得失敗: {result.get('error')}")

    st.divider()
    st.markdown("**一括クロール**（URLを改行区切りで入力）")
    urls_text = st.text_area("URLリスト", height=120)
    if st.button("📋 一括クロール実行"):
        urls = [u.strip() for u in urls_text.splitlines() if u.strip().startswith("http")]
        ok = 0
        for u in urls:
            with st.spinner(f"クロール中: {u}"):
                result = crawl_url(u)
            if result.get("crawl_status") == "success":
                insert_page(result)
                ok += 1
        st.info(f"{ok} / {len(urls)} 件を DB に登録しました")

# ── 一覧タブ ──
with tab3:
    pages = get_all_pages()
    st.subheader(f"📚 DB 登録済みページ一覧（{len(pages)}件）")
    for page in pages:
        with st.expander(f"📄 {page['title']}"):
            st.markdown(page.get("description", "") or "（説明なし）")
            st.caption(f"👤 {page.get('author') or '不明'}　📊 {page.get('word_count', 0)} 語")
            st.caption(f"🔗 {page['url']}")
