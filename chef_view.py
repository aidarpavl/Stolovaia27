"""Асханашы режимі"""
import streamlit as st
import pandas as pd
from datetime import datetime
from config import WEEKS, DAYS, CATEGORIES
from menu_utils import save_menu
from orders_utils import load_orders
from reports_utils import (
    build_daily_report, build_monthly_report,
    append_daily_to_github, append_monthly_to_github
)


def render_chef(menu_df):
    st.markdown('<div class="main-header">👨‍🍳 Панель повара</div>',
                unsafe_allow_html=True)

    if not st.session_state.chef_authenticated:
        st.warning("🔐 **Асханашы режиміне кіру үшін пароль қажет.**")
        st.info("👈 Сол жақ панельде парольді енгізіңіз.")
        st.stop()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Меню (4 апта)", "➕ Добавить", "📦 Заказы",
        "📊 Күндік есеп", "📈 Айлық есеп"
    ])

    # ===== 1. МӘЗІРДІ ӨҢДЕУ =====
    with tab1:
        _render_menu_editor(menu_df)

    # ===== 2. ЖАҢА ТАҒАМ =====
    with tab2:
        _render_add_dish(menu_df)

    # ===== 3. ТАПСЫРЫСТАР =====
    with tab3:
        _render_orders()

    # ===== 4. КҮНДІК ЕСЕП =====
    with tab4:
        _render_daily_report()

    # ===== 5. АЙЛЫҚ ЕСЕП =====
    with tab5:
        _render_monthly_report()


def _render_menu_editor(menu_df):
    st.markdown("### 📋 Редактирование меню на 4 недели")

    c1, c2 = st.columns(2)
    with c1:
        edit_week = st.selectbox("Апта:", WEEKS,
                                 index=WEEKS.index(st.session_state.selected_week))
    with c2:
        edit_day = st.selectbox("Күн:", ["Все дни"] + DAYS)

    if edit_day == "Все дни":
        filtered_df = menu_df[menu_df["week"] == edit_week].copy()
    else:
        filtered_df = menu_df[
            (menu_df["week"] == edit_week) & (menu_df["day"] == edit_day)
        ].copy()

    st.caption(f"💡 **{edit_week}** / **{edit_day}** — {len(filtered_df)} тағам.")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "week": st.column_config.SelectboxColumn("Апта", options=WEEKS, required=True),
            "day": st.column_config.SelectboxColumn("Күн", options=DAYS, required=True),
            "item_name": st.column_config.TextColumn("Блюдо", required=True),
            "category": st.column_config.SelectboxColumn("Категория",
                                                         options=CATEGORIES, required=True),
            "price": st.column_config.NumberColumn("Цена ₸", min_value=0, format="%d₸"),
            "available": st.column_config.CheckboxColumn("Доступно"),
        },
        key="menu_editor"
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Сохранить в GitHub",
                     use_container_width=True, type="primary"):
            if edit_day == "Все дни":
                keep_df = menu_df[menu_df["week"] != edit_week].copy()
            else:
                mask = ~((menu_df["week"] == edit_week) &
                         (menu_df["day"] == edit_day))
                keep_df = menu_df[mask].copy()

            final_df = pd.concat([keep_df, edited_df], ignore_index=True)

            with st.spinner("GitHub-қа жіберілуде..."):
                if save_menu(final_df):
                    st.cache_data.clear()
                    st.success(f"✅ {edit_week} / {edit_day} сақталды!")
                    st.rerun()

    with c2:
        if st.button("🔄 Қайта жүктеу", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Жаңартылды!")
            st.rerun()

    with c3:
        if st.button("📋 Барлық мәзір", use_container_width=True):
            st.session_state.show_full = not st.session_state.get("show_full", False)

    if st.session_state.get("show_full"):
        st.markdown("#### 📊 Барлық апталар")
        summary = menu_df.groupby(["week", "day"]).size().reset_index(name="Тағам саны")
        st.dataframe(summary, use_container_width=True)
        st.markdown("#### 🔍 Толық кесте")
        st.dataframe(menu_df, use_container_width=True, height=400)


def _render_add_dish(menu_df):
    st.markdown("### ➕ Быстрое добавление")
    with st.form("add_dish"):
        c1, c2 = st.columns(2)
        with c1:
            nd_week = st.selectbox("Апта:", WEEKS, key="add_week")
            nd_day = st.selectbox("Күн:", DAYS, key="add_day")
            nd_name = st.text_input("Тағам атауы:", key="add_name")
            nd_cat = st.selectbox("Санаты:", CATEGORIES, key="add_cat")
        with c2:
            nd_price = st.number_input("Бағасы (₸):", min_value=0,
                                       value=500, step=50, key="add_price")
            nd_avail = st.checkbox("Қолжетімді", value=True, key="add_avail")

        sub = st.form_submit_button("➕ Қосу және GitHub-қа сақтау",
                                    use_container_width=True, type="primary")
        if sub:
            if not nd_name:
                st.error("⚠️ Тағам атауын енгізіңіз!")
            else:
                new_row = pd.DataFrame([{
                    "week": nd_week, "day": nd_day,
                    "item_name": nd_name, "category": nd_cat,
                    "price": nd_price, "available": nd_avail,
                }])
                upd = pd.concat([menu_df, new_row], ignore_index=True)
                with st.spinner("GitHub-қа жіберілуде..."):
                    if save_menu(upd):
                        st.cache_data.clear()
                        st.success(f"✅ «{nd_name}» қосылды!")
                        st.rerun()


def _render_orders():
    st.markdown("### 📦 Заказы")
    odf = load_orders()
    if odf.empty:
        st.info("📭 Тапсырыстар әзірге жоқ")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Тапсырыс", len(odf))
    c2.metric("Сома", f"{odf['total'].fillna(0).sum():,}₸")
    c3.metric("Сыныптар", odf["class"].nunique())
    c4.metric("Күндер", odf["timestamp"].astype(str).str[:10].nunique())

    st.dataframe(odf, use_container_width=True, height=400)
    csv_bytes = odf.to_csv(index=False).encode("utf-8")
    st.download_button("📥 CSV жүктеу", csv_bytes,
                       "orders_export.csv", "text/csv",
                       use_container_width=True)


def _render_daily_report():
    st.markdown("### 📊 Күндік есеп")
    st.caption("Күндік есеп GitHub-тағы **Stolovaia ZHD1.csv** файлына сақталады.")

    c1, c2 = st.columns([2, 1])
    with c1:
        report_date = st.date_input("Есеп күні:")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊 Есеп жасау", use_container_width=True, type="primary"):
            date_str = report_date.strftime("%Y-%m-%d")
            report_df = build_daily_report(date_str)

            if report_df.empty:
                st.warning(f"⚠️ {date_str} күніне тапсырыстар жоқ.")
            else:
                st.session_state.daily_report_df = report_df
                st.success(f"✅ {date_str} күніне {len(report_df)} жазба табылды.")

    if "daily_report_df" in st.session_state and not st.session_state.daily_report_df.empty:
        df = st.session_state.daily_report_df
        st.markdown("#### 📋 Есеп мазмұны")
        st.dataframe(df, use_container_width=True)

        total_qty = df["Саны"].sum()
        total_sum = df["Жалпы сома (₸)"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Жалпы тағам саны", int(total_qty))
        c2.metric("Жалпы сома", f"{int(total_sum):,}₸")

        if st.button("💾 GitHub-қа сақтау (Stolovaia ZHD1.csv)",
                     use_container_width=True, type="primary"):
            with st.spinner("GitHub-қа жіберілуде..."):
                if append_daily_to_github(df):
                    st.success("✅ Күндік есеп GitHub-қа сақталды!")
                else:
                    st.error("❌ Сақтау мүмкін болмады.")


def _render_monthly_report():
    st.markdown("### 📈 Айлық есеп")
    st.caption("Айлық есеп GitHub-тағы **Stol_Zhd month1.csv** файлына сақталады.")

    today = datetime.now()
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        year = st.number_input("Жыл:", min_value=2024, max_value=2030,
                               value=today.year, step=1)
    with c2:
        month = st.number_input("Ай:", min_value=1, max_value=12,
                                value=today.month, step=1)
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📈 Есеп жасау", use_container_width=True, type="primary"):
            report_df = build_monthly_report(int(year), int(month))
            if report_df.empty:
                st.warning(f"⚠️ {int(year)}-{int(month):02d} айына тапсырыстар жоқ.")
            else:
                st.session_state.monthly_report_df = report_df
                st.success(f"✅ {len(report_df)} жазба табылды.")

    if "monthly_report_df" in st.session_state and not st.session_state.monthly_report_df.empty:
        df = st.session_state.monthly_report_df
        st.markdown("#### 📋 Есеп мазмұны")
        st.dataframe(df