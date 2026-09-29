"""Тұрақтылар мен GitHub конфигурациясы"""
import streamlit as st

WEEKS = ["1-я неделя", "2-я неделя", "3-я неделя", "4-я неделя"]
DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
CATEGORIES = ["Завтрак", "Обед", "Салаты", "Первое", "Второе", "Напитки"]

GITHUB_OWNER = "aidarpavl"
GITHUB_REPO = "Stolovaia27"
GITHUB_BRANCH = "main"
MENU_PATH = "menu.csv"
DAILY_REPORT_PATH = "Stolovaia ZHD1.csv"
MONTHLY_REPORT_PATH = "Stol_Zhd month1.csv"
GITHUB_TOKEN = None
GITHUB_ENABLED = False
CHEF_PASSWORD = "povar2026"


def init_config():
    """Secrets-тен конфигурацияны оқу"""
    global GITHUB_TOKEN, GITHUB_ENABLED, GITHUB_OWNER, GITHUB_REPO
    global GITHUB_BRANCH, MENU_PATH, DAILY_REPORT_PATH
    global MONTHLY_REPORT_PATH, CHEF_PASSWORD

    try:
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            if "github" in st.secrets:
                gh = st.secrets["github"]
                GITHUB_TOKEN = gh.get("token")
                GITHUB_OWNER = gh.get("owner", GITHUB_OWNER)
                GITHUB_REPO = gh.get("repo", GITHUB_REPO)
                GITHUB_BRANCH = gh.get("branch", GITHUB_BRANCH)
                MENU_PATH = gh.get("menu_path", MENU_PATH)
                DAILY_REPORT_PATH = gh.get("daily_report_path", DAILY_REPORT_PATH)
                MONTHLY_REPORT_PATH = gh.get("monthly_report_path", MONTHLY_REPORT_PATH)
            if "auth" in st.secrets:
                CHEF_PASSWORD = st.secrets["auth"].get("chef_password", CHEF_PASSWORD)

        if GITHUB_TOKEN and isinstance(GITHUB_TOKEN, str):
            GITHUB_TOKEN = GITHUB_TOKEN.strip()
            if (GITHUB_TOKEN.startswith("ghp_") or
                    GITHUB_TOKEN.startswith("github_pat_") or
                    GITHUB_TOKEN.startswith("gho_") or
                    GITHUB_TOKEN.startswith("ghs_")):
                GITHUB_ENABLED = True
            else:
                GITHUB_TOKEN = None
    except Exception:
        GITHUB_TOKEN = None
        GITHUB_ENABLED = False


def gh_url(path, api=False):
    """GitHub URL генераторы"""
    if api:
        return f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    return f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{path}"