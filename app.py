"""
«Жас Дарын» мектебінің асханасы
Столовая школы Жас Дарын — онлайн тапсырыс жүйесі
Деректер көзі: github.com/aidarpavl/Stolovaia27
4 апта × 5 күн мәзір жүйесі
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
CSS = """
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
.week-badge {
    background-color: #FF6B35;
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
    font-weight: bold;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ============================================================
# ТҰРАҚТЫЛАР
# ============================================================
WEEKS = ["1-я неделя", "2-я неделя", "3-я неделя", "4-я неделя"]
DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
CATEGORIES = ["Завтрак", "Обед", "Салаты", "Первое", "Второе", "Напитки"]

# ============================================================
# GITHUB КОНФИГУРАЦИЯСЫ
# ============================================================
GITHUB_OWNER = "aidarpavl"
GITHUB_REPO = "Stolovaia27"
GITHUB_BRANCH = "main"
MENU_PATH = "menu.csv"
GITHUB_TOKEN = None
GITHUB_ENABLED = False
TOKEN_ERROR = None

try:
    if hasattr(st, "secrets") and len(st.secrets) > 0:
        if "github" in st.secrets:
            gh = st.secrets["github"]
            GITHUB_TOKEN = gh.get("token")
            GITHUB_OWNER = gh.get("owner", GITHUB_OWNER)
            GITHUB_REPO = gh.get("repo", GITHUB_REPO)
            GITHUB_BRANCH = gh.get("branch", GITHUB_BRANCH)
            MENU_PATH = gh.get("menu_path", MENU_PATH)
        elif "GITHUB_TOKEN" in st.secrets:
            GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
        elif "token" in st.secrets:
            GITHUB_TOKEN = st.secrets["token"]
        else:
            TOKEN_ERROR = "Secrets-те 'github' секциясы жоқ"
    else:
        TOKEN_ERROR = "Secrets бос — Streamlit Cloud-та қосыңыз"

    if GITHUB_TOKEN and isinstance(GITHUB_TOKEN, str):
        GITHUB_TOKEN = GITHUB_TOKEN.strip()
        if (
            GITHUB_TOKEN.startswith("ghp_") or
            GITHUB_TOKEN.startswith("github_pat_") or
            GITHUB_TOKEN.startswith("gho_") or
            GITHUB_TOKEN.startswith("ghs_")
        ):
            GITHUB_ENABLED = True
        else:
            TOKEN_ERROR = f"Токен форматы дұрыс емес: {GITHUB_TOKEN[:8]}..."
            GITHUB_TOKEN = None
    elif not TOKEN_ERROR:
        TOKEN_ERROR = "Токен бос немесе жол емес"

except Exception as e:
    TOKEN_ERROR = f"Secrets оқу қатесі: {e}"
    GITHUB_TOKEN = None
    GITHUB_ENABLED = False

GITHUB_RAW_URL = (
    f"https://raw.githubusercontent.com/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{MENU_PATH}"
)
GITHUB_API_URL = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/{MENU_PATH}"
)

# 🔑 МАҢЫЗДЫ: week бағаны қосылды!
REQUIRED_COLUMNS = ["week", "day", "item_name", "category", "price", "available"]


# ============================================================
# РЕЗЕРВТІК ДЕРЕКТЕР (4 апта × 5 күн)
# ============================================================
FALLBACK_MENU = pd.DataFrame([
    # 1-ші апта
    {"week": "1-я неделя", "day": "Понедельник", "item_name": "Каша овсяная с ягодами", "category": "Завтрак", "price": 450, "available": True},
    {"week": "1-я неделя", "day": "Понедельник", "item_name": "Бутерброд с сыром", "category": "Завтрак", "price": 350, "available": True},
    {"week": "1-я неделя", "day": "Понедельник", "item_name": "Борщ со сметаной", "category": "Обед", "price": 550, "available": True},
    {"week": "1-я неделя", "day": "Понедельник", "item_name": "Котлета с пюре", "category": "Обед", "price": 650, "available": True},
    {"week": "1-я неделя", "day": "Понедельник", "item_name": "Компот из сухофруктов", "category": "Напитки", "price": 150, "available": True},
    {"week": "1-я неделя", "day": "Вторник", "item_name": "Салат овощной", "category": "Салаты", "price": 400, "available": True},
    {"week": "1-я неделя", "day": "Вторник", "item_name": "Солянка мясная", "category": "Первое", "price": 500, "available": True},
    {"week": "1-я неделя", "day": "Вторник", "item_name": "Макароны с сыром", "category": "Второе", "price": 550, "available": True},
    {"week": "1-я неделя", "day": "Среда", "item_name": "Винегрет", "category": "Салаты", "price": 450, "available": True},
    {"week": "1-я неделя", "day": "Среда", "item_name": "Суп грибной", "category": "Первое", "price": 480, "available": True},
    {"week": "1-я неделя", "day": "Среда", "item_name": "Рыба с рисом", "category": "Второе", "price": 700, "available": True},
    {"week": "1-я неделя", "day": "Четверг", "item_name": "Морковный салат", "category": "Салаты", "price": 350, "available": True},
    {"week": "1-я неделя", "day": "Четверг", "item_name": "Рассольник", "category": "Первое", "price": 470, "available": True},
    {"week": "1-я неделя", "day": "Четверг", "item_name": "Гречка с мясом", "category": "Второе", "price": 600, "available": True},
    {"week": "1-я неделя", "day": "Пятница", "item_name": "Салат Греческий", "category": "Салаты", "price": 580, "available": True},
    {"week": "1-я неделя", "day": "Пятница", "item_name": "Лагман", "category": "Второе", "price": 750, "available": True},
    {"week": "1-я неделя", "day": "Пятница", "item_name": "Сок апельсиновый", "category": "Напитки", "price": 250, "available": True},
])


# ============================================================
# КӨМЕКШІ ФУНКЦИЯЛАР
# ============================================================
def _normalize_menu(df: pd.DataFrame) -> pd.DataFrame:
    """CSV-ді бір форматқа келтіру"""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Егер 'week' бағаны жоқ болса — қосамыз (ескі CSV-лер үшін)
    if "week" not in df.columns:
        df["week"] = "1-я неделя"

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(
                f"CSV-де '{col}' бағаны жоқ. Бар бағандар: {list(df.columns)}"
            )

    df = df[REQUIRED_COLUMNS].dropna(how="all")
    df = df[df["item_name"].notna() & (df["item_name"].astype(str).str.strip() != "")]

    df["week"] = df["week"].astype(str).str.strip()
    df["day"] = df["day"].astype(str).str.strip()
    df["item_name"] = df["item_name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(int)
    df["available"] = df["available"].astype(str).str.upper().isin(["TRUE", "1", "YES"])

    return df.reset_index(drop=True)


@st.cache_data(ttl=30, show_spinner=False)
def load_menu_from_github() -> pd.DataFrame:
    """Мәзірді GitHub-тан оқу"""
    try:
        resp = requests.get(GITHUB_RAW_URL, timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            return _normalize_menu(pd.read_csv(StringIO(resp.text)))
    except Exception:
        pass

    try:
        if os.path.exists("menu.csv"):
            return _normalize_menu(pd.read_csv("menu.csv"))
    except Exception:
        pass

    return _normalize_menu(FALLBACK_MENU)


def save_menu_to_github(df: pd.DataFrame) -> bool:
    """Мәзірді GitHub-қа сақтау"""
    if not GITHUB_ENABLED or not GITHUB_TOKEN:
        st.error("❌ **GitHub токені орнатылмаған!**")
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        get_resp = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        current_sha = None

        if get_resp.status_code == 200:
            current_sha = get_resp.json().get("sha")
        elif get_resp.status_code == 401:
            st.error("❌ **Токен жарамсыз!** Қайта жасаңыз.")
            return False
        elif get_resp.status_code == 404:
            current_sha = None
        elif get_resp.status_code != 200:
            st.error(f"❌ GitHub API: {get_resp.status_code}")
            return False

        csv_content = df.to_csv(index=False)
        content_encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"Мәзірді жаңарту ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
            "content": content_encoded,
            "branch": GITHUB_BRANCH
        }
        if current_sha:
            payload["sha"] = current_sha

        put_resp = requests.put(
            GITHUB_API_URL, headers=headers, json=payload, timeout=15
        )

        if put_resp.status_code in (200, 201):
            return True
        elif put_resp.status_code == 403:
            st.error("❌ **Рұқсат жоқ!** Токенде `repo` рұқсаты бар ма?")
            return False
        else:
            st.error(f"❌ Сақтау қатесі: {put_resp.status_code}")
            return False

    except Exception as e:
        st.error(f"❌ GitHub-қа сақтау: {e}")
        return False


def load_orders() -> pd.DataFrame:
    columns = [
        "timestamp", "class", "week", "day", "item_name",
        "category", "price", "quantity", "total"
    ]
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
# МӘЗІРДІ ЖҮКТЕУ
# ============================================================
try:
    menu_df = load_menu_from_github()
except Exception as e:
    st.error(f"❌ Мәзірді жүктеу: {e}")
    st.stop()

if menu_df is None or not isinstance(menu_df, pd.DataFrame) or menu_df.empty:
    st.error("❌ Мәзір деректері бос.")
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

    if GITHUB_ENABLED:
        st.success("🔗 GitHub: оқу + жазу ✅")
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
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(f"**{item['item_name']}**")
                    st.caption(
                        f"{item['category']} · {item['price']}₸ × {item['quantity']}"
                    )
                with c2:
                    if st.button("❌", key=f"rm_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
                total_sum += item["price"] * item["quantity"]

            st.markdown(f"### 💰 Итого: **{total_sum}₸**")

            if st.button("🗑️ Очистить", use_container_width=True):
                st.session_state.cart = []
                st.rerun()

            if st.button("✅ Оформить заказ", type="primary", use_container_width=True):
                if not st.session_state.selected_class:
                    st.error("⚠️ Сначала введите класс!")
                else:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for it in st.session_state.cart:
                        save_order({
                            "timestamp": ts,
                            "class": st.session_state.selected_class,
                            "week": st.session_state.selected_week,
                            "day": st.session_state.selected_day,
                            "item_name": it["item_name"],
                            "category": it["category"],
                            "price": it["price"],
                            "quantity": it["quantity"],
                            "total": it["price"] * it["quantity"],
                        })
                    st.session_state.last_order = {
                        "timestamp": ts,
                        "class": st.session_state.selected_class,
                        "week": st.session_state.selected_week,
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
    # ==================== ОҚУШЫ РЕЖИМІ ====================
    st.markdown(
        '<div class="main-header">🍽️ Столовая школы Жас Дарын</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center; color:gray;'>Закажи обед онлайн</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Класс
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

    # Апта таңдау
    st.markdown("### 📅 Выберите неделю")
    wcols = st.columns(4)
    for i, w in enumerate(WEEKS):
        with wcols[i]:
            if st.button(
                w,
                key=f"w_{i}",
                use_container_width=True,
                type="primary" if st.session_state.selected_week == w else "secondary"
            ):
                st.session_state.selected_week = w
                st.rerun()

    # Күн таңдау
    st.markdown("### 📆 День:")
    idx = DAYS.index(st.session_state.selected_day) if st.session_state.selected_day in DAYS else 0
    sd = st.selectbox("День:", options=DAYS, index=idx, label_visibility="collapsed")
    st.session_state.selected_day = sd

    # Санат таңдау
    cats = ["Все"] + sorted(menu_df["category"].dropna().unique().tolist())
    st.markdown("### 🏷️ Категория:")
    sc = st.selectbox("Категория:", options=cats, label_visibility="collapsed")

    st.markdown("---")

    # 🔑 Таңдалған апта + күн бойынша сүзу
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
        st.warning(
            f"⚠️ **{st.session_state.selected_week}** аптасының **{sd}** "
            f"күніне тағамдар табылмады.\n\n"
            f"Асханашы режимінде осы аптаға мәзір қосыңыз."
        )
    else:
        cols = st.columns(3)
        for i, (rid, row) in enumerate(day_menu.iterrows()):
            with cols[i % 3]:
                card_html = (
                    '<div class="menu-card">'
                    f'<h4>{row["item_name"]}</h4>'
                    f'<span class="category-tag">{row["category"]}</span>'
                    f'<p class="price-tag">💰 {row["price"]}₸</p>'
                    '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                q = st.number_input("Саны", 1, 10, 1, key=f"q_{rid}")

                if st.button(
                    "🛒 В корзину",
                    key=f"a_{rid}",
                    use_container_width=True,
                    type="primary"
                ):
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

    # Соңғы тапсырыс
    if st.session_state.last_order:
        st.markdown("---")
        st.success(
            f"✅ Соңғы тапсырыс: {st.session_state.last_order['timestamp']}"
        )
        with st.expander("📋 Мәліметтер"):
            for it in st.session_state.last_order["items"]:
                st.write(f"• {it['item_name']} — {it['price']}₸ × {it['quantity']}")
            st.write(f"**Жалпы: {st.session_state.last_order['total']}₸**")


else:
    # ==================== АСХАНАШЫ РЕЖИМІ ====================
    st.markdown(
        '<div class="main-header">👨‍🍳 Панель повара</div>',
        unsafe_allow_html=True
    )

    if not GITHUB_ENABLED:
        st.warning(
            "⚠️ **GitHub токені орнатылмаған.** Мәзірді өңдеуге болады, "
            "бірақ GitHub-қа сақтау үшін токен қажет."
        )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Меню (4 апта)", "➕ Добавить", "📦 Заказы", "📊 Отчеты"]
    )

    # ============================================================
    # 1-ҚОЙЫНДЫ: 4 АПТАЛЫҚ МӘЗІРДІ ӨҢДЕУ
    # ============================================================
    with tab1:
        st.markdown("### 📋 Редактирование меню на 4 недели")

        # Апта + күн таңдау
        c1, c2 = st.columns(2)
        with c1:
            edit_week = st.selectbox(
                "Апта:",
                WEEKS,
                index=WEEKS.index(st.session_state.selected_week),
                key="edit_week"
            )
        with c2:
            edit_day = st.selectbox(
                "Күн:",
                ["Все дни"] + DAYS,
                key="edit_day"
            )

        # Таңдалған апта (және күн) бойынша сүзу
        if edit_day == "Все дни":
            filtered_df = menu_df[menu_df["week"] == edit_week].copy()
        else:
            filtered_df = menu_df[
                (menu_df["week"] == edit_week) &
                (menu_df["day"] == edit_day)
            ].copy()

        st.caption(
            f"💡 **{edit_week}** / **{edit_day}** — "
            f"{len(filtered_df)} тағам. Кестені өңдеп, «Сақтау» басыңыз."
        )

        # Редактор
        edited_df = st.data_editor(
            filtered_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "week": st.column_config.SelectboxColumn(
                    "Апта", options=WEEKS, required=True
                ),
                "day": st.column_config.SelectboxColumn(
                    "Күн", options=DAYS, required=True
                ),
                "item_name": st.column_config.TextColumn("Блюдо", required=True),
                "category": st.column_config.SelectboxColumn(
                    "Категория", options=CATEGORIES, required=True
                ),
                "price": st.column_config.NumberColumn(
                    "Цена ₸", min_value=0, format="%d₸"
                ),
                "available": st.column_config.CheckboxColumn("Доступно"),
            },
            key="menu_editor"
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(
                "💾 Сохранить в GitHub",
                use_container_width=True,
                type="primary"
            ):
                # 🔑 Маңызды: өңделгенді негізгі menu_df-ке біріктіру
                # 1. Ескі өңделген апта/күнді өшіру
                if edit_day == "Все дни":
                    keep_df = menu_df[menu_df["week"] != edit_week].copy()
                else:
                    keep_df = menu_df[
                        ~((menu_df["week"] == edit_week) &
                          (menu_df["day"] == edit_day))
                    ].copy()

                # 2. Жаңа өңделгенді қосу
                final_df = pd.concat([keep_df, edited_df], ignore_index=True)

                with st.spinner("GitHub-қа жіберілуде..."):
                    if save_menu_to_github(final_df):
                        load_menu_from_github.clear()
                        st.success(
                            f"✅ {edit_week} / {edit_day} GitHub-қа сақталды!"
                        )
                        st.rerun()

        with c2:
            if st.button("🔄 Қайта жүктеу", use_container_width=True):
                load_menu_from_github.clear()
                st.success("✅ Жаңартылды!")
                st.rerun()

        with c3:
            if st.button("📋 Барлық мәзірді көру", use_container_width=True):
                st.session_state.show_full = not st.session_state.get("show_full", False)

        # Барлық мәзірді көрсету
        if st.session_state.get("show_full"):
            st.markdown("#### 📊 Барлық апталардағы мәзір")
            summary = (
                menu_df.groupby(["week", "day"])
                .size()
                .reset_index(name="Тағам саны")
            )
            st.dataframe(summary, use_container_width=True)

            st.markdown("#### 🔍 Толық кесте")
            st.dataframe(menu_df, use_container_width=True, height=400)

    # ============================================================
    # 2-ҚОЙЫНДЫ: ЖАҢА ТАҒАМ ҚОСУ
    # ============================================================
    with tab2:
        st.markdown("### ➕ Быстрое добавление")

        with st.form("add_dish"):
            c1, c2 = st.columns(2)
            with c1:
                nd_week = st.selectbox("Апта:", WEEKS)
                nd_day = st.selectbox("Күн:", DAYS)
                nd_name = st.text_input("Тағам атауы:")
                nd_cat = st.selectbox("Санаты:", CATEGORIES)
            with c2:
                nd_price = st.number_input("Бағасы (₸):", min_value=0, value=500, step=50)
                nd_avail = st.checkbox("Қолжетімді", value=True)

            sub = st.form_submit_button(
                "➕ Қосу және GitHub-қа сақтау",
                use_container_width=True,
                type="primary"
            )

            if sub:
                if not nd_name:
                    st.error("⚠️ Тағам атауын енгізіңіз!")
                else:
                    new_row = pd.DataFrame([{
                        "week": nd_week,
                        "day": nd_day,
                        "item_name": nd_name,
                        "category": nd_cat,
                        "price": nd_price,
                        "available": nd_avail,
                    }])
                    upd = pd.concat([menu_df, new_row], ignore_index=True)
                    with st.spinner("GitHub-қа жіберілуде..."):
                        if save_menu_to_github(upd):
                            load_menu_from_github.clear()
                            st.success(
                                f"✅ «{nd_name}» ({nd_week}, {nd_day}) қосылды!"
                            )
                            st.rerun()

    # ============================================================
    # 3-ҚОЙЫНДЫ: ТАПСЫРЫСТАР
    # ============================================================
    with tab3:
        st.markdown("### 📦 Заказы")
        odf = load_orders()

        if odf.empty:
            st.info("📭 Тапсырыстар әзірге жоқ")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Тапсырыс", len(odf))
            c2.metric("Сома", f"{odf['total'].sum():,}₸")
            c3.metric("Сыныптар", odf["class"].nunique())
            if "week" in odf.columns:
                c4.metric("Апталар", odf["week"].nunique())
            else:
                c4.metric("Күндер", odf["timestamp"].astype(str).str[:10].nunique())

            st.dataframe(odf, use_container_width=True, height=400)

            csv_bytes = odf.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 CSV жүктеу",
                csv_bytes,
                "orders_export.csv",
                "text/csv",
                use_container_width=True
            )

    # ============================================================
    # 4-ҚОЙЫНДЫ: ЕСЕПТЕР
    # ============================================================
    with tab4:
        st.markdown("### 📊 Отчеты")
        odf = load_orders()

        if odf.empty:
            st.info("📭 Деректер жоқ")
        else:
            st.markdown("#### 🍽️ Тағамдар бойынша")
            item_stats = (
                odf.groupby("item_name")
                .agg({"quantity": "sum", "total": "sum"})
                .reset_index()
                .sort_values("quantity", ascending=False)
            )
            st.dataframe(item_stats, use_container_width=True)

            st.mark