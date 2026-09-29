"""
«Жас Дарын» мектебінің асханасы
Столовая школы Жас Дарын — онлайн тапсырыс жүйесі
Деректер көзі: github.com/aidarpavl/Stolovaia27
"""

import streamlit as st
import pandas as pd
import requests
import base64
import os
from datetime import datetime
from io import StringIO

# ============================================================
# БЕТТІҢ КОНФИГУРАЦИЯСЫ
# ============================================================
st.set_page_config(
    page_title="Столовая школы Жас Дарын",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 1rem;
    }
    .menu-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #FF6B35;
        margin-bottom: 10px;
        min-height: 150px;
    }
    .price-tag {
        color: #FF6B35;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .category-tag {
        background-color: #FFE5D9;
        color: #FF6B35;
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# GITHUB КОНФИГУРАЦИЯСЫ
# ============================================================
GITHUB_OWNER = "aidarpavl"
GITHUB_REPO = "Stolovaia27"
GITHUB_BRANCH = "main"
MENU_PATH = "menu.csv"

# Secrets-тен токенді алу (бар болса)
GITHUB_TOKEN = None
try:
    if "github" in st.secrets:
        GITHUB_TOKEN = st.secrets["github"].get("token")
        GITHUB_OWNER = st.secrets["github"].get("owner", GITHUB_OWNER)
        GITHUB_REPO = st.secrets["github"].get("repo", GITHUB_REPO)
        GITHUB_BRANCH = st.secrets["github"].get("branch", GITHUB_BRANCH)
        MENU_PATH = st.secrets["github"].get("menu_path", MENU_PATH)
except Exception:
    pass

GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{MENU_PATH}"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{MENU_PATH}"


# ============================================================
# 🛡️ РЕЗЕРВТІК ДЕРЕКТЕР (GitHub істемесе)
# ============================================================
FALLBACK_MENU = pd.DataFrame([
    {"day": "Понедельник", "item_name": "Каша овсяная с ягодами", "category": "Завтрак", "price": 450, "available": True},
    {"day": "Понедельник", "item_name": "Бутерброд с сыром", "category": "Завтрак", "price": 350, "available": True},
    {"day": "Понедельник", "item_name": "Борщ со сметаной", "category": "Обед", "price": 550, "available": True},
    {"day": "Понедельник", "item_name": "Котлета с пюре", "category": "Обед", "price": 650, "available": True},
    {"day": "Понедельник", "item_name": "Компот из сухофруктов", "category": "Напитки", "price": 150, "available": True},
    {"day": "Вторник", "item_name": "Салат овощной", "category": "Салаты", "price": 400, "available": True},
    {"day": "Вторник", "item_name": "Солянка мясная", "category": "Первое", "price": 500, "available": True},
    {"day": "Вторник", "item_name": "Макароны с сыром", "category": "Второе", "price": 550, "available": True},
    {"day": "Среда", "item_name": "Винегрет", "category": "Салаты", "price": 450, "available": True},
    {"day": "Среда", "item_name": "Суп грибной", "category": "Первое", "price": 480, "available": True},
    {"day": "Среда", "item_name": "Рыба с рисом", "category": "Второе", "price": 700, "available": True},
    {"day": "Четверг", "item_name": "Морковный салат", "category": "Салаты", "price": 350, "available": True},
    {"day": "Четверг", "item_name": "Рассольник", "category": "Первое", "price": 470, "available": True},
    {"day": "Четверг", "item_name": "Гречка с мясом", "category": "Второе", "price": 600, "available": True},
    {"day": "Пятница", "item_name": "Салат Греческий", "category": "Салаты", "price": 580, "available": True},
    {"day": "Пятница", "item_name": "Лагман", "category": "Второе", "price": 750, "available": True},
    {"day": "Пятница", "item_name": "Сок апельсиновый", "category": "Напитки", "price": 250, "available": True},
])

REQUIRED_COLUMNS = ["day", "item_name", "category", "price", "available"]


# ============================================================
# 🛡️ МӘЗІРДІ ЖҮКТЕУ (қорғалған нұсқа)
# ============================================================
def _normalize_menu(df: pd.DataFrame) -> pd.DataFrame:
    """CSV-ді бір форматқа келтіру және деректерді тазалау"""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Қажетті бағандарды тексеру
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"CSV-де '{col}' бағаны жоқ. Бар бағандар: {list(df.columns)}")

    # Бағандардың ретін сақтау
    df = df[REQUIRED_COLUMNS]

    # Бос жолдарды тазалау
    df = df.dropna(how="all")
    df = df[df["item_name"].notna() & (df["item_name"].astype(str).str.strip() != "")]

    # Типтерді түзету
    df["day"] = df["day"].astype(str).str.strip()
    df["item_name"] = df["item_name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(int)
    df["available"] = df["available"].astype(str).str.upper().isin(["TRUE", "1", "YES", "ИӘ", "ИӘ"])

    return df.reset_index(drop=True)


@st.cache_data(ttl=30, show_spinner=False)
def load_menu_from_github():
    """
    Мәзірді GitHub-тан оқу. Қате болса — жергілікті файлдан, ол да болмаса — резервтен.
    Ешқашан None қайтармайды.
    """
    errors = []

    # 1-әрекет: GitHub raw
    try:
        resp = requests.get(GITHUB_RAW_URL, timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            df = pd.read_csv(StringIO(resp.text))
            return _normalize_menu(df)
        else:
            errors.append(f"GitHub HTTP {resp.status_code}")
    except Exception as e:
        errors.append(f"GitHub: {e}")

    # 2-әрекет: жергілікті файл
    try:
        if os.path.exists("menu.csv"):
            df = pd.read_csv("menu.csv")
            return _normalize_menu(df)
    except Exception as e:
        errors.append(f"Local: {e}")

    # 3-әрекет: резервтік деректер
    st.warning("⚠️ GitHub-тан мәзірді жүктеу мүмкін болмады. Резервтік деректер қолданылуда.")
    return _normalize_menu(FALLBACK_MENU)


def save_menu_to_github(df: pd.DataFrame) -> bool:
    """Мәзірді GitHub-қа сақтау"""
    if not GITHUB_TOKEN:
        st.error("❌ GitHub токені орнатылмаған! `secrets.toml` файлын тексеріңіз.")
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # SHA алу
        get_resp = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        current_sha = None
        if get_resp.status_code == 200:
            current_sha = get_resp.json().get("sha")
        elif get_resp.status_code != 404:
            st.error(f"❌ GitHub API: {get_resp.status_code}")
            return False

        # CSV → base64
        csv_content = df.to_csv(index=False)
        content_encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"Мәзірді жаңарту ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
            "content": content_encoded,
            "branch": GITHUB_BRANCH
        }
        if current_sha:
            payload["sha"] = current_sha

        put_resp = requests.put(GITHUB_API_URL, headers=headers, json=payload, timeout=15)
        if put_resp.status_code in (200, 201):
            return True
        else:
            st.error(f"❌ Сақтау қатесі: {put_resp.status_code} — {put_resp.text[:200]}")
            return False
    except Exception as e:
        st.error(f"❌ GitHub-қа сақтау: {e}")
        return False


# ============================================================
# ТАПСЫРЫСТАР
# ============================================================
def load_orders() -> pd.DataFrame:
    """Тапсырыстарды жергілікті CSV-тен оқу (әрдайым DataFrame қайтарады)"""
    columns = ["timestamp", "class", "day", "item_name", "category", "price", "quantity", "total"]
    try:
        if os.path.exists("Orders.csv"):
            df = pd.read_csv("Orders.csv")
            for c in columns:
                if c not in df.columns:
                    df[c] = None
            return df[columns]
    except Exception:
        pass
    return pd.DataFrame(columns=columns)


def save_order(order_data: dict):
    """Тапсырысты сақтау"""
    orders_df = load_orders()
    new_order = pd.DataFrame([order_data])
    orders_df = pd.concat([orders_df, new_order], ignore_index=True)
    orders_df.to_csv("Orders.csv", index=False)


# ============================================================
# СЕССИЯ КҮЙІ
# ============================================================
defaults = {
    "cart": [],
    "role": "Ученик",
    "selected_week": "1-я неделя",
    "selected_day": "Понедельник",
    "selected_class": "",
    "last_order": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# МӘЗІРДІ БІР РЕТ ЖҮКТЕУ (🔑 қатенің шешімі!)
# ============================================================
try:
    menu_df = load_menu_from_github()
except Exception as e:
    st.error(f"❌ Мәзірді жүктеу мүмкін болмады: {e}")
    st.stop()

# 🔒 Қорғаныс: menu_df міндетті түрде DataFrame болуы керек
if menu_df is None or not isinstance(menu_df, pd.DataFrame) or menu_df.empty:
    st.error("❌ Мәзір деректері бос. `menu.csv` файлын тексеріңіз.")
    st.stop()

if "category" not in menu_df.columns:
    st.error(f"❌ 'category' бағаны табылмады. Бар бағандар: {list(menu_df.columns)}")
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Режим работы")
    role = st.radio(
        "Роль:",
        options=["Ученик", "Повар"],
        index=0 if st.session_state.role == "Ученик" else 1
    )
    st.session_state.role = role

    st.markdown("---")
    if GITHUB_TOKEN:
        st.success("🔗 GitHub: жазу қосылған")
    else:
        st.warning("📴 GitHub: тек оқу режимі")

    st.markdown("---")

    if st.session_state.role == "Ученик":
        st.markdown("### 🛒 Корзина")
        if not st.session_state.cart:
            st.info("Корзина пуста")
        else:
            total_sum = 0
            for i, item in enumerate(st.session_state.cart):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{item['item_name']}**")
                    st.caption(f"{item['category']} · {item['price']}₸ × {item['quantity']}")
                with col2:
                    if st.button("❌", key=f"remove_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
                total_sum += item["price"] * item["quantity"]

            st.markdown(f"### 💰 Итого: **{total_sum}₸**")

            if st.button("🗑️ Очистить корзину", use_container_width=True):
                st.session_state.cart = []
                st.rerun()

            if st.button("✅ Оформить заказ", type="primary", use_container_width=True):
                if not st.session_state.selected_class:
                    st.error("⚠️ Сначала введите класс!")
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for item in st.session_state.cart:
                        save_order({
                            "timestamp": timestamp,
                            "class": st.session_state.selected_class,
                            "day": st.session_state.selected_day,
                            "item_name": item["item_name"],
                            "category": item["category"],
                            "price": item["price"],
                            "quantity": item["quantity"],
                            "total": item["price"] * item["quantity"],
                        })
                    st.session_state.last_order = {
                        "timestamp": timestamp,
                        "class": st.session_state.selected_class,
                        "items": st.session_state.cart.copy(),
                        "total": total_sum,
                    }
                    st.session_state.cart = []
                    st.success("✅ Заказ оформлен!")
                    st.balloons()
                    st.rerun()


# ============================================================
# НЕГІЗГІ БЕТ
# ============================================================
if st.session_state.role == "Ученик":
    # ==================== ОҚУШЫ ====================
    st.markdown('<div class="main-header">🍽️ Столовая школы Жас Дарын</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>Закажи обед онлайн</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Класс
    st.markdown("### 🎓 Введите ваш класс")
    col1, col2 = st.columns([1, 3])
    with col1:
        class_num = st.text_input(
            "Класс (например, 3А или 7Б):",
            value=st.session_state.selected_class or "8",
            placeholder="Например: 8А"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if class_num:
            num = int("".join(filter(str.isdigit, class_num)) or 0)
            if num <= 4:
                group = "Младшие классы (1-4)"
            elif num <= 8:
                group = "Средние классы (5-8)"
            else:
                group = "Старшие классы (9-11)"
            st.success(f"🎓 {group}: {class_num}")
    st.session_state.selected_class = class_num
    st.markdown("---")

    # Апта
    st.markdown("### 📅 Выберите неделю")
    weeks = ["1-я неделя", "2-я неделя", "3-я неделя", "4-я неделя"]
    week_cols = st.columns(4)
    for i, week in enumerate(weeks):
        with week_cols[i]:
            if st.button(
                week, key=f"week_{i}", use_container_width=True,
                type="primary" if st.session_state.selected_week == week else "secondary"
            ):
                st.session_state.selected_week = week
                st.rerun()

    # Күн
    st.markdown("### 📆 День:")
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
    idx = days.index(st.session_state.selected_day) if st.session_state.selected_day in days else 0
    selected_day = st.selectbox("День недели:", options=days, index=idx, label_visibility="collapsed")
    st.session_state.selected_day = selected_day

    # Санат
    all_categories = ["Все"] + sorted(menu_df["category"].dropna().unique().tolist())
    st.markdown("### 🏷️ Категория:")
    selected_category = st.selectbox("Категория:", options=all_categories, label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"### 🍽️ Меню на {selected_day}")

    day_menu = menu_df[menu_df["day"] == selected_day].copy()
    if selected_category != "Все":
        day_menu = day_menu[day_menu["category"] == selected_category]

    if day_menu.empty:
        st.warning("⚠️ Бұл күнге тағамдар табылмады")
    else:
        cols = st.columns(3)
        for i, (row_id, row) in enumerate(day_menu.iterrows()):
            with cols[i % 3]:
                st.markdown(f"""
                    <div class="menu-card">
                        <h4>{row['item_name']}</h4>
                        <span class="category-tag">{row['category']}</span>
                        <p class="price-tag">💰 {row['price']}₸</p>
                    </div>
                """, unsafe_allow_html=True)

                qty = st.number_input(
                    "Саны", min_value=1, max_value=10, value=1,
                    key=f"qty_{row_id}"
                )
                if st.button("🛒 В корзину", key=f"add_{row_id}",
                             use_container_width=True, type="primary"):
                    found = False
                    for item in st.session_state.cart:
                        if item["item_name"] == row["item_name"]:
                            item["quantity"] += qty
                            found = True
                            break
                    if not found:
                        st.session_state.cart.append({
                            "item_name": row["item_name"],
                            "category": row["category"],
                            "price": int(row["price"]),
                            "quantity": qty,
                        })
                    st.success(f"✅ {row['item_name']} добавлен!")
                    st.rerun()

    if st.session_state.last_order:
        st.markdown("---")
        st.success(f"✅ Соңғы тапсырыс: {st.session_state.last_order['timestamp']}")
        with st.expander("📋 Тапсырыс мәліметтерін көру"):
            for item in st.session_state.last_order["items"]:
                st.write(f"• {item['item_name']} — {item['price']}₸ × {item['quantity']}")
            st.write(f"**Жалпы: {st.session_state.last_order['total']}₸**")


else:
    # ==================== АСХАНАШЫ ====================
    st.markdown('<div class="main-header">👨‍🍳 Панель повара</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Меню", "➕ Добавить", "📦 Заказы", "📊 Отчеты"])

    # --- 1. Мәзірді өңдеу ---
    with tab1:
        st.markdown("### 📋 Редактирование меню")
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Неделя:", ["1-я неделя", "2-я неделя", "3-я неделя", "4-я неделя"])
        with col2:
            st.selectbox("Тип:", ["5-11 классы", "1-4 классы"])

        st.caption("💡 Кестені өңдеңіз. Сақтау батырмасы GitHub-қа жібереді.")

        edited_df = st.data_editor(
            menu_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "day": st.column_config.SelectboxColumn(
                    "День",
                    options=["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"],
                    required=True,
                ),
                "item_name": st.column_config.TextColumn("Блюдо", required=True),
                "category": st.column_config.SelectboxColumn(
                    "Категория",
                    options=["Завтрак", "Обед", "Салаты", "Первое", "Второе", "Напитки"],
                    required=True,
                ),
                "price": st.column_config.NumberColumn("Цена ₸", min_value=0, format="%d₸"),
                "available": st.column_config.CheckboxColumn("Доступно"),
            },
            key="menu_editor",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Сохранить в GitHub", use_container_width=True, type="primary"):
                with st.spinner("GitHub-қа жіберілуде..."):
                    if save_menu_to_github(edited_df):
                        load_menu_from_github.clear()
                        st.success("✅ Мәзір GitHub-қа сақталды!")
                        st.rerun()
        with col2:
            if st.button("🔄 GitHub-тан қайта жүктеу", use_container_width=True):
                load_menu_from_github.clear()
                st.success("✅ Жаңартылды!")
                st.rerun()

    # --- 2. Жаңа тағам қосу ---
    with tab2:
        st.markdown("### ➕ Быстрое добавление")
        with st.form("add_dish_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_day = st.selectbox("Күн:", ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"])
                new_name = st.text_input("Тағам атауы:")
                new_category = st.selectbox("Санаты:",
                                             ["Завтрак", "Обед", "Салаты", "Первое", "Второе", "Напитки"])
            with col2:
                new_price = st.number_input("Бағасы (₸):", min_value=0, value=500, step=50)
                new_available = st.checkbox("Қолжетімді", value=True)

            submitted = st.form_submit_button(
                "➕ Қосу және GitHub-қа сақтау",
                use_container_width=True, type="primary"
            )
            if submitted:
                if not new_name:
                    st.error("⚠️ Тағам атауын енгізіңіз!")
                else:
                    new_row = pd.DataFrame([{
                        "day": new_day, "item_name": new_name,
                        "category": new_category, "price": new_price,
                        "available": new_available,
                    }])
                    updated_df = pd.concat([menu_df, new_row], ignore_index=True)
                    with st.spinner("GitHub-қа жіберілуде..."):
                        if save_menu_to_github(updated_df):
                            load_menu_from_github.clear()
                            st.success(f"✅ «{new_name}» қосылды!")
                            st.rerun()

    # --- 3. Тапсырыстар ---
    with tab3:
        st.markdown("### 📦 Заказы")
        orders_df = load_orders()
        if orders_df.empty:
            st.info("📭 Тапсырыстар әзірге жоқ")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Барлық тапсырыс", len(orders_df))
            c2.metric("Жалпы сома", f"{orders_df['total'].sum():,}₸")
            c3.metric("Сыныптар", orders_df["class"].nunique())
            c4.metric("Күндер", orders_df["timestamp"].astype(str).str[:10].nunique())
            st.dataframe(orders_df, use_container_width=True, height=400)
            csv = orders_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 CSV жүктеу", csv, "orders_export.csv", "text/csv",
                               use_container_width=True)

    # --- 4. Есептер ---
    with tab4:
        st.markdown("### 📊 Отчеты")
        orders_df = load_orders()
        if orders_df.empty:
            st.info("📭 Есептер үшін тапсырыстар жоқ")
        else:
            st.markdown("#### 🍽️ Тағамдар бойынша")
            st.dataframe(
                orders_df.groupby("item_name").agg({"quantity": "sum", "total": "sum"})
                .reset_index().sort_values("quantity", ascending=False),
                use_container_width=True
            )
            st.markdown("#### 🎓 Сыныптар бойынша")
            st.dataframe(
                orders_df.groupby("class").agg({"quantity": "sum", "total": "sum"})
                .reset_index().sort_values("total", ascending=False),
                use_container_width=True
            )
            st.markdown("#### 📅 Күндер бойынша")
            day_stats = orders_df.groupby("day").agg({"quantity": "sum", "total": "sum"}).reset_index()
            st.dataframe(day_stats, use_container_width=True)
            if not day_stats.empty:
                st.bar_chart(day_stats.set_index("day")["total"])


# ============================================================
# ФУТЕР
# ============================================================
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray; font-size:0.85rem;'>"
    "🍽️ Столовая школы Жас Дарын · GitHub + Streamlit · 2026"
    "</p>",
    unsafe_allow_html=True
)