"""Оқушы режимі"""
import streamlit as st
from datetime import datetime
from config import WEEKS, DAYS
from orders_utils import save_order


def render_student(menu_df):
    st.markdown('<div class="main-header">🍽️ Столовая школы Жас Дарын</div>',
                unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>Закажи обед онлайн</p>",
                unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 🎓 Введите ваш класс")
    c1, c2 = st.columns([1, 3])
    with c1:
        class_num = st.text_input(
            "Класс:",
            value=st.session_state.selected_class or "8",
            placeholder="Например: 8А"
        )
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if class_num:
            n = int("".join(filter(str.isdigit, class_num)) or 0)
            if n <= 4:
                grp = "Младшие классы (1-4)"
            elif n <= 8:
                grp = "Средние классы (5-8)"
            else:
                grp = "Старшие классы (9-11)"
            st.success(f"🎓 {grp}: {class_num}")
    st.session_state.selected_class = class_num
    st.markdown("---")

    st.markdown("### 📅 Выберите неделю")
    wcols = st.columns(4)
    for i, w in enumerate(WEEKS):
        with wcols[i]:
            is_active = st.session_state.selected_week == w
            if st.button(w, key=f"w_{i}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.selected_week = w
                st.rerun()

    st.markdown("### 📆 День:")
    idx = DAYS.index(st.session_state.selected_day) if st.session_state.selected_day in DAYS else 0
    sd = st.selectbox("День:", options=DAYS, index=idx, label_visibility="collapsed")
    st.session_state.selected_day = sd

    cats = ["Все"] + sorted(menu_df["category"].dropna().unique().tolist())
    st.markdown("### 🏷️ Категория:")
    sc = st.selectbox("Категория:", options=cats, label_visibility="collapsed")

    st.markdown("---")
    st.markdown(
        f"### 🍽️ Меню на {sd} "
        f"<span class='week-badge'>{st.session_state.selected_week}</span>",
        unsafe_allow_html=True
    )

    day_menu = menu_df[
        (menu_df["week"] == st.session_state.selected_week) &
        (menu_df["day"] == sd)
    ].copy()
    if sc != "Все":
        day_menu = day_menu[day_menu["category"] == sc]

    if day_menu.empty:
        st.warning(f"⚠️ **{st.session_state.selected_week}** аптасының "
                   f"**{sd}** күніне тағамдар табылмады.")
    else:
        cols = st.columns(3)
        for i, (rid, row) in enumerate(day_menu.iterrows()):
            with cols[i % 3]:
                st.markdown(
                    '<div class="menu-card">'
                    f'<h4>{row["item_name"]}</h4>'
                    f'<span class="category-tag">{row["category"]}</span>'
                    f'<p class="price-tag">💰 {row["price"]}₸</p>'
                    '</div>',
                    unsafe_allow_html=True
                )
                q = st.number_input("Саны", 1, 10, 1, key=f"q_{rid}")
                if st.button("🛒 В корзину", key=f"a_{rid}",
                             use_container_width=True, type="primary"):
                    found = False
                    for it in st.session_state.cart:
                        if it["item_name"] == row["item_name"]:
                            it["quantity"] += q
                            found = True
                            break
                    if not found:
                        st.session_state.cart.append({
                            "item_name": row["item_name"],
                            "category": row["category"],
                            "price": int(row["price"]),
                            "quantity": q,
                        })
                    st.success(f"✅ {row['item_name']} добавлен!")
                    st.rerun()

    if st.session_state.last_order:
        st.markdown("---")
        st.success(f"✅ Соңғы тапсырыс: {st.session_state.last_order['timestamp']}")
        with st.expander("📋 Мәліметтер"):
            for it in st.session_state.last_order["items"]:
                st.write(f"• {it['item_name']} — {it['price']}₸ × {it['quantity']}")
            st.write(f"**Жалпы: {st.session_state.last_order['total']}₸**")