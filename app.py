"""
«Жас Дарын» мектебінің асханасы
GitHub-тан оқу + GitHub-қа жазу (токен болса)
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

st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #FF6B35;
                  text-align: center; margin-bottom: 1rem;}
    .menu-card {background-color: #f9f9f9; border-radius: 10px; padding: 15px;
                border-left: 5px solid #FF6B35; margin-bottom: 10px; min-height: 150px;}
    .price-tag {color: #FF6B35; font-weight: bold; font-size: 1.2rem;}
    .category-tag {background-color: #FFE5D9; color: #FF6B35; padding: 3px 10px;
                   border-radius: 15px; font-size: 0.85rem; display: inline-block;
                   margin-bottom: 8px;}
    </style>
""", unsafe_allow_html=True)

# ============================================================
# GITHUB КОНФИГУРАЦИЯСЫ (қауіпсіз оқу)
# ============================================================
GITHUB_OWNER = "aidarpavl"
GITHUB_REPO = "Stolovaia27"
GITHUB_BRANCH = "main"
MENU_PATH = "menu.csv"
GITHUB_TOKEN = None
GITHUB_ENABLED = False

# Secrets-ті біртіндеп оқу (әртүрлі форматқа төзімді)
try:
    if hasattr(st, "secrets") and len(st.secrets) > 0:
        # 1) [github] секциясы бар ма?
        if "github" in st.secrets:
            gh = st.secrets["github"]
            GITHUB_TOKEN = gh.get("token") or gh.get("GITHUB_TOKEN")
            GITHUB_OWNER = gh.get("owner", GITHUB_OWNER)
            GITHUB_REPO = gh.get("repo", GITHUB_REPO)
            GITHUB_BRANCH = gh.get("branch", GITHUB_BRANCH)
            MENU_PATH = gh.get("menu_path", MENU_PATH)
        # 2) Тікелей GITHUB_TOKEN бар ма?
        elif "GITHUB_TOKEN" in st.secrets:
            GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
        # 3) token тікелей бар ма?
        elif "token" in st.secrets:
            GITHUB_TOKEN = st.secrets["token"]

    # Токеннің жарамдылығын тексеру
    if GITHUB_TOKEN and isinstance(GITHUB_TOKEN, str) and GITHUB_TOKEN.startswith("ghp_"):
        GITHUB_ENABLED = True
    else:
        GITHUB_TOKEN = None
        GITHUB_ENABLED = False
except Exception:
    GITHUB_TOKEN = None
    GITHUB_ENABLED = False

GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{MENU_PATH}"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{MENU_PATH}"

REQUIRED_COLUMNS = ["day", "item_name", "category", "price", "available"]


# ============================================================
# РЕЗЕРВТІК ДЕРЕКТЕР
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


# ============================================================
# КӨМЕКШІ ФУНКЦИЯЛАР
# ============================================================
def _normalize_menu(df: pd.DataFrame) -> pd.DataFrame:
    """CSV-ді бір форматқа келтіру"""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"CSV-де '{col}' бағаны жоқ. Бар: {list(df.columns)}")
    df = df[REQUIRED_COLUMNS].dropna(how="all")
    df = df[df["item_name"].notna() & (df["item_name"].astype(str).str.strip() != "")]
    df["day"] = df["day"].astype(str).str.strip()
    df["item_name"] = df["item_name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(int)
    df["available"] = df["available"].astype(str).str.upper().isin(["TRUE", "1", "YES"])
    return df.reset_index(drop=True)


@st.cache_data(ttl=30, show_spinner=False)
def load_menu_from_github():
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
    """
    Мәзірді GitHub-қа сақтау.
    Егер токен жоқ болса — егжей-тегжейлі нұсқаулық көрсетеді.
    """
    # 🔑 ТОКЕН ЖОҚ — НҰСҚАУЛЫҚ КӨРСЕТУ
    if not GITHUB_ENABLED or not GITHUB_TOKEN:
        st.error("❌ **GitHub токені орнатылмаған!**")
        with st.expander("📖 Токенді қалай орнату керек? (нұсқаулық)", expanded=True):
            st.markdown("""
            ### 🔑 GitHub токен алу (5 минут)

            **1-қадам.** GitHub-қа кіріңіз: https://github.com/settings/tokens

            **2-қадам.** **Generate new token (classic)** басыңыз.

            **3-қадам.** Атын жазыңыз: `streamlit-stolovaia27`
            - **Expiration:** 90 days
            - **Scopes:** ✅ `repo` (толық рұқсат)

            **4-қадам.** **Generate token** → токенді көшіріңіз (`ghp_...`)

            ---

            ### 🌐 Streamlit Cloud-та Secrets қосу

            **1-қадам.** https://share.streamlit.io → қосымшаңыз

            **2-қадам.** **⋮** → **Settings** → **Secrets**

            **3-қадам.** Мына мазмұнды қойыңыз:

            ```toml
            [github]
            token = "ghp_СІЗДІҢ_ТОКЕНІҢІЗ"
            owner = "aidarpavl"
            repo = "Stolovaia27"
            branch = "main"
            menu_path = "menu.csv"