"""
«Жас Дарын» мектебінің асханасы
Столовая школы Жас Дарын — онлайн тапсырыс жүйесі
Деректер көзі: github.com/aidarpavl/Stolovaia27
Мәзір GitHub-тан оқылады және GitHub-қа сақталады.
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
# CSS СТИЛЬДЕР
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
    .stButton>button {
        background-color: #FF6B35;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# GITHUB КОНФИГУРАЦИЯСЫ
# ============================================================
try:
    GITHUB_TOKEN = st.secrets["github"]["token"]
    GITHUB_OWNER = st.secrets["github"]["owner"]
    GITHUB_REPO = st.secrets["github"]["repo"]
    GITHUB_BRANCH = st.secrets["github"]["branch"]
    MENU_PATH = st.secrets["github"]["menu_path"]
    GITHUB_ENABLED = True
except Exception:
    # Егер secrets.toml болмаса — тек оқу режимі
    GITHUB_OWNER = "aidarpavl"
    GITHUB_REPO = "Stolovaia27"
    GITHUB_BRANCH = "main"
    MENU_PATH = "menu.csv"
    GITHUB_TOKEN = None
    GITHUB_ENABLED = False

# GitHub API URL-дері
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{MENU_PATH}"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{MENU_PATH}"


# ============================================================
# GITHUB ФУНКЦИЯЛАРЫ
# ============================================================
@st.cache_data(ttl=30)
def load_menu_from_github():
    """
    Мәзірді GitHub-тан оқу (raw URL арқылы).
    Егер GitHub-тан оқу мүмкін болмаса — жергілікті файлдан оқиды.
    """
    try:
        response = requests.get(GITHUB_RAW_URL, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
        else:
            raise Exception(f"HTTP {response.status_code}")
    except Exception as e:
        st.warning(f"⚠️ GitHub-тан оқу мүмкін болмады ({e}). Жергілікті файлдан оқылады.")
        if os.path.exists("menu.csv"):
            df = pd.read_csv("menu.csv")
        else:
            # Резервтік деректер
            df = pd.DataFrame({
                'day': ['Понедельник'] * 5,
                'item_name': ['Каша овсяная с ягодами', 'Бутерброд с сыром',
                              'Борщ со сметаной', 'Котлета с пюре', 'Компот из сухофруктов'],
                'category': ['Завтрак', 'Завтрак', 'Обед', 'Обед', 'Напитки'],
                'price': [450, 350, 550, 650, 150],
                'available': [True] * 5
            })

    # Баған атауларын тазалау
    df.columns = df.columns.str.strip()
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0).astype(int)
    df['available'] = df['available'].astype(str).str.upper() == 'TRUE'

    return df


def save_menu_to_github(df):
    """
    Мәзірді GitHub-қа сақтау (GitHub API арқылы).
    Қажет: GITHUB_TOKEN (repo рұқсатымен).
    """
    if not GITHUB_ENABLED or not GITHUB_TOKEN:
        st.error("❌ GitHub токені орнатылмаған! `secrets.toml` файлын тексеріңіз.")
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # 1. Ағымдағы файлдың SHA-ын алу (жаңарту үшін қажет)
        get_response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)

        if get_response.status_code == 200:
            current_sha = get_response.json().get("sha")
        elif get_response.status_code == 404:
            current_sha = None  # Файл жоқ — жаңадан жасалады
        else:
            st.error(f"❌ GitHub API қатесі: {get_response.status_code}")
            return False

        # 2. CSV-ді base64-ке айналдыру
        csv_content = df.to_csv(index=False)
        content_encoded = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')

        # 3. Commit хабарламасы
        commit_message = f"Мәзірді жаңарту ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"

        # 4. GitHub-қа жіберу
        payload = {
            "message": commit_message,
            "content": content_encoded,
            "branch": GITHUB_BRANCH
        }
        if current_sha:
            payload["sha"] = current_sha

        put_response = requests.put(
            GITHUB_API_URL,
            headers=headers,
            json=payload,
            timeout=15
        )

        if put_response.status_code in [200, 201]:
            return True
        else:
            st.error(f"❌ Сақтау қатесі: {put_response.status_code} — {put_response.text}")
            return False

    except Exception as e:
        st.error(f"❌ GitHub-қа сақтау қатесі: {e}")
        return False


# ============================================================
# ТАПСЫРЫСТАР (жергілікті CSV)
# ============================================================
@st.cache_data(ttl=10)
def load_orders():
    """Тапсырыстарды жергілікті CSV-тен оқу"""
    if os.path.exists("Orders.csv"):
        try:
            return pd.read_csv("Orders.csv")
        except Exception:
            pass
    return pd.DataFrame(columns=[
        'timestamp', 'class', 'day', 'item_name', 'category',
        'price', 'quantity', 'total'
    ])


def save_order(order_data):
    """Тапсырысты Orders.csv файлына сақтау"""
    orders_df = load_orders()
    new_order = pd.DataFrame([order_data])
    orders_df = pd.concat([orders_df, new_order], ignore_index=True)
    orders_df.to_csv("Orders.csv", index=False)
    load_orders.clear()


# ============================================================
# СЕССИЯ КҮЙІ
# ============================================================
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'role' not in st.session_state:
    st.session_state.role = 'Ученик'
if 'selected_week' not in st.session_state:
    st.session_state.selected_week = '1-я неделя'
if 'selected_day' not in st.session_state:
    st.session_state.selected_day = 'Понедельник'
if 'selected_class' not in st.session_state:
    st.session_state.selected_class = ''
if 'last_order' not in st.session_state:
    st.session_state.last_order = None


# ============================================================
# БҮЙІРҒЫ БЕТ (SIDEBAR)
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Режим работы")
    role = st.radio(
        "Роль:",
        options=['Ученик', 'Повар'],
        index=0 if st.session_state.role == 'Ученик' else 1
    )
    st.session_state.role = role

    # GitHub мәртебесі
    st.markdown("---")
    if GITHUB_ENABLED:
        st.success("🔗 GitHub: қосылған")
    else:
        st.warning("📴 GitHub: тек оқу режимі")

    st.markdown("---")

    # ===== СЕБЕТ =====
    if st.session_state.role == 'Ученик':
        st.markdown("### 🛒 Корзина")

        if len(st.session_state.cart) == 0:
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
                total_sum += item['price'] * item['quantity']

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
                            'timestamp': timestamp,
                            'class': st.session_state.selected_class,
                            'day': st.session_state.selected_day,
                            'item_name': item['item_name'],
                            'category': item['category'],
                            'price': item['price'],
                            'quantity': item['quantity'],
                            'total': item['price'] * item['quantity']
                        })
                    st.session_state.last_order = {
                        'timestamp': timestamp,
                        'class': st.session_state.selected_class,
                        'items': st.session_state.cart.copy(),
                        'total': total_sum
                    }
                    st.session_state.cart = []
                    st.success("✅ Заказ оформлен!")
                    st.balloons()
                    st.rerun()


# ============================================================
# НЕГІЗГІ БЕТ
# ============================================================

if st.session_state.role == 'Ученик':
    # ==========================================================
    # ОҚУШЫ РЕЖИМІ
    # ==========================================================
    st.markdown('<div class="main-header">🍽️ Столовая школы Жас Дарын</div>',
                unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>Закажи обед онлайн</p>",
                unsafe_allow_html=True)
    st.markdown("---")

    # ===== КЛАСС =====
    st.markdown("### 🎓 Введите ваш класс")
    col1, col2 = st.columns([1, 3])
    with col1:
        class_num = st.text_input(
            "Класс (например, 3А или 7Б):",
            value=st.session_state.selected_class if st.session_state.selected_class else "8",
            placeholder="Например: 8А"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if class_num:
            try:
                num = int(''.join(filter(str.isdigit, class_num)) or 0)
                if num <= 4:
                    group = "Младшие классы (1-4)"
                elif num <= 8:
                    group = "Средние классы (5-8)"
                else:
                    group = "Старшие классы (9-11)"
                st.success(f"🎓 {group}: {class_num}")
            except Exception:
                st.warning("Класс форматын тексеріңіз")
    st.session_state.selected_class = class_num

    st.markdown("---")

    # ===== АПТА =====
    st.markdown("### 📅 Выберите неделю")
    weeks = ['1-я неделя', '2-я неделя', '3-я неделя', '4-я неделя']
    week_cols = st.columns(4)
    for i, week in enumerate(weeks):
        with week_cols[i]:
            if st.button(
                week,
                use_container_width=True,
                type="primary" if st.session_state.selected_week == week else "secondary",
                key=f"week_{i}"
            ):
                st.session_state.selected_week = week
                st.rerun()

    # ===== КҮН =====
    st.markdown("### 📆 День:")
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
    selected_day = st.selectbox(
        "День недели:",
        options=days,
        index=days.index(st.session_state.selected_day),
        label_visibility="collapsed"
    )
    st.session_state.selected_day = selected_day

    # ===== САНАТ =====
    menu_df = load_menu_from_github()
    all_categories = ['Все'] + sorted(menu_df['category'].unique().tolist())
    st.markdown("### 🏷️ Категория:")
    selected_category = st.selectbox(
        "Категория:",
        options=all_categories,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # ===== МӘЗІР =====
    st.markdown(f"### 🍽️ Меню на {selected_day}")
    day_menu = menu_df[menu_df['day'] == selected_day].copy()
    if selected_category != 'Все':
        day_menu = day_menu[day_menu['category'] == selected_category]

    if len(day_menu) == 0:
        st.warning("⚠️ Бұл күнге тағамдар табылмады")
    else:
        cols = st.columns(3)
        for i, (idx, row) in enumerate(day_menu.iterrows()):
            with cols[i % 3]:
                st.markdown(f"""
                    <div class="menu-card">
                        <h4>{row['item_name']}</h4>
                        <span class="category-tag">{row['category']}</span>
                        <p class="price-tag">💰 {row['price']}₸</p>
                    </div>
                """, unsafe_allow_html=True)
                qty = st.number_input(
                    "Саны", min_value=1, max_value=10, value=1, key=f"qty_{idx}"
                )
                if st.button("🛒 В корзину", key=f"add_{idx}",
                             use_container_width=True, type="primary"):
                    found = False
                    for item in st.session_state.cart:
                        if item['item_name'] == row['item_name']:
                            item['quantity'] += qty
                            found = True
                            break
                    if not found:
                        st.session_state.cart.append({
                            'item_name': row['item_name'],
                            'category': row['category'],
                            'price': int(row['price']),
                            'quantity': qty
                        })
                    st.success(f"✅ {row['item_name']} добавлен!")
                    st.rerun()

    # ===== СОҢҒЫ ТАПСЫРЫС =====
    if st.session_state.last_order:
        st.markdown("---")
        st.success(f"✅ Соңғы тапсырыс: {st.session_state.last_order['timestamp']}")
        with st.expander("📋 Тапсырыс мәліметтерін көру"):
            for item in st.session_state.last_order['items']:
                st.write(f"• {item['item_name']} — {item['price']}₸ × {item['quantity']}")
            st.write(f"**Жалпы: {st.session_state.last_order['total']}₸**")


else:
    # ==========================================================
    # АСХАНАШЫ РЕЖИМІ
    # ==========================================================
    st.markdown('<div class="main-header">👨‍🍳 Панель повара</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Меню", "➕ Добавить", "📦 Заказы", "📊 Отчеты"])

    menu_df = load_menu_from_github()

    # ===== 1. МӘЗІРДІ ӨҢДЕУ =====
    with tab1:
        st.markdown("### 📋 Редактирование меню")

        col1, col2 = st.columns(2)
        with col1:
            week = st.selectbox("Неделя:",
                                ['1-я неделя', '2-я неделя', '3-я неделя', '4-я неделя'])
        with col2:
            class_type = st.selectbox("Тип:", ['5-11 классы', '1-4 классы'])

        st.caption("💡 Кестені тікелей өңдеңіз. Сақтау батырмасын басқанда GitHub-қа жіберіледі.")

        edited_df = st.data_editor(
            menu_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "day": st.column_config.SelectboxColumn(
                    "День",
                    options=['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница'],
                    required=True
                ),
                "item_name": st.column_config.TextColumn("Блюдо", required=True),
                "category": st.column_config.SelectboxColumn(
                    "Категория",
                    options=['Завтрак', 'Обед', 'Салаты', 'Первое', 'Второе', 'Напитки'],
                    required=True
                ),
                "price": st.column_config.NumberColumn("Цена ₸", min_value=0, format="%d₸"),
                "available": st.column_config.CheckboxColumn("Доступно")
            },
            key="menu_editor"
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

    # ===== 2. ЖАҢА ТАҒАМ ҚОСУ =====
    with tab2:
        st.markdown("### ➕ Быстрое добавление")

        with st.form("add_dish_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_day = st.selectbox(
                    "Күн:",
                    ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
                )
                new_name = st.text_input("Тағам атауы:")
                new_category = st.selectbox(
                    "Санаты:",
                    ['Завтрак', 'Обед', 'Салаты', 'Первое', 'Второе', 'Напитки']
                )
            with col2:
                new_price = st.number_input("Бағасы (₸):", min_value=0, value=500, step=50)
                new_available = st.checkbox("Қолжетімді", value=True)

            submitted = st.form_submit_button(
                "➕ Қосу және GitHub-қа сақтау",
                use_container_width=True,
                type="primary"
            )

            if submitted:
                if not new_name:
                    st.error("⚠️ Тағам атауын енгізіңіз!")
                else:
                    new_row = pd.DataFrame([{
                        'day': new_day,
                        'item_name': new_name,
                        'category': new_category,
                        'price': new_price,
                        'available': new_available
                    }])
                    updated_df = pd.concat([menu_df, new_row], ignore_index=True)
                    with st.spinner("GitHub-қа жіберілуде..."):
                        if save_menu_to_github(updated_df):
                            load_menu_from_github.clear()
                            st.success(f"✅ «{new_name}» қосылды және GitHub-қа сақталды!")
                            st.rerun()

    # ===== 3. ТАПСЫРЫСТАР =====
    with tab3:
        st.markdown("### 📦 Заказы")
        orders_df = load_orders()

        if len(orders_df) == 0:
            st.info("📭 Тапсырыстар әзірге жоқ")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Барлық тапсырыс", len(orders_df))
            with col2:
                total_sum = orders_df['total'].sum() if 'total' in orders_df else 0
                st.metric("Жалпы сома", f"{total_sum:,}₸")
            with col3:
                unique_classes = orders_df['class'].nunique() if 'class' in orders_df else 0
                st.metric("Сыныптар", unique_classes)
            with col4:
                if 'timestamp' in orders_df and len(orders_df) > 0:
                    unique_days = orders_df['timestamp'].astype(str).str[:10].nunique()
                    st.metric("Күндер", unique_days)

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if 'class' in orders_df:
                    class_filter = st.multiselect(
                        "Сынып бойынша сүзу:",
                        options=sorted(orders_df['class'].astype(str).unique().tolist())
                    )
                else:
                    class_filter = []
            with col2:
                if 'day' in orders_df:
                    day_filter = st.multiselect(
                        "Күн бойынша сүзу:",
                        options=sorted(orders_df['day'].astype(str).unique().tolist())
                    )
                else:
                    day_filter = []

            filtered_df = orders_df.copy()
            if class_filter and 'class' in filtered_df:
                filtered_df = filtered_df[filtered_df['class'].astype(str).isin(class_filter)]
            if day_filter and 'day' in filtered_df:
                filtered_df = filtered_df[filtered_df['day'].astype(str).isin(day_filter)]

            st.dataframe(filtered_df, use_container_width=True, height=400)
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 CSV жүктеу", csv, "orders_export.csv", "text/csv",
                use_container_width=True
            )

    # ===== 4. ЕСЕПТЕР =====
    with tab4:
        st.markdown("### 📊 Отчеты")
        orders_df = load_orders()

        if len(orders_df) == 0:
            st.info("📭 Есептер үшін тапсырыстар жоқ")
        else:
            st.markdown("#### 🍽️ Тағамдар бойынша есеп")
            if 'item_name' in orders_df:
                item_stats = orders_df.groupby('item_name').agg({
                    'quantity': 'sum', 'total': 'sum'
                }).reset_index().sort_values('quantity', ascending=False)
                item_stats.columns = ['Тағам', 'Саны', 'Жалпы сома (₸)']
                st.dataframe(item_stats, use_container_width=True)

            st.markdown("#### 🎓 Сыныптар бойынша есеп")
            if 'class' in orders_df:
                class_stats = orders_df.groupby('class').agg({
                    'quantity': 'sum', 'total': 'sum'
                }).reset_index().sort_values('total', ascending=False)
                class_stats.columns = ['Сынып', 'Тағам саны', 'Жалпы сома (₸)']
                st.dataframe(class_stats, use_container_width=True)

            st.markdown("#### 📅 Күндер бойынша есеп")
            if 'day' in orders_df:
                day_stats = orders_df.groupby('day').agg({
                    'quantity': 'sum', 'total': 'sum'
                }).reset_index()
                day_stats.columns = ['Күн', 'Тағам саны', 'Жалпы сома (₸)']
                st.dataframe(day_stats, use_container_width=True)
                st.bar_chart(day_stats.set_index('Күн')['Жалпы сома (₸)'])

            st.markdown("#### 🏷️ Санаттар бойынша есеп")
            if 'category' in orders_df:
                cat_stats = orders_df.groupby('category').agg({
                    'quantity': 'sum', 'total': 'sum'
                }).reset_index()
                cat_stats.columns = ['Санат', 'Тағам саны', 'Жалпы сома (₸)']
                st.dataframe(cat_stats, use_container_width=True)
                st.bar_chart(cat_stats.set_index('Санат')['Жалпы сома (₸)'])


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