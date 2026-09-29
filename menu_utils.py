"""Мәзір функциялары — GitHub-тан оқу және жазу"""
import streamlit as st
import pandas as pd
import requests
import base64
import os
from datetime import datetime
from io import StringIO

from config import (
    GITHUB_ENABLED, GITHUB_TOKEN, MENU_PATH, GITHUB_BRANCH, gh_url
)

REQUIRED_COLUMNS = ["week", "day", "item_name", "category", "price", "available"]

FALLBACK_MENU = pd.DataFrame([
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


def normalize_menu(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "week" not in df.columns:
        df["week"] = "1-я неделя"
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"CSV-де '{col}' бағаны жоқ.")
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
def load_menu():
    try:
        resp = requests.get(gh_url(MENU_PATH), timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            return normalize_menu(pd.read_csv(StringIO(resp.text)))
    except Exception:
        pass
    try:
        if os.path.exists("menu.csv"):
            return normalize_menu(pd.read_csv("menu.csv"))
    except Exception:
        pass
    return normalize_menu(FALLBACK_MENU)


def _save_csv_to_github(df, path, commit_msg):
    if not GITHUB_ENABLED or not GITHUB_TOKEN:
        return False
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    api_url = gh_url(path, api=True)
    try:
        get_resp = requests.get(api_url, headers=headers, timeout=10)
        current_sha = None
        if get_resp.status_code == 200:
            current_sha = get_resp.json().get("sha")
        elif get_resp.status_code == 401:
            st.error("❌ Токен жарамсыз!")
            return False

        csv_content = df.to_csv(index=False)
        content_encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": commit_msg,
            "content": content_encoded,
            "branch": GITHUB_BRANCH
        }
        if current_sha:
            payload["sha"] = current_sha

        put_resp = requests.put(api_url, headers=headers, json=payload, timeout=15)
        if put_resp.status_code in (200, 201):
            return True
        elif put_resp.status_code == 403:
            st.error("❌ Рұқсат жоқ! Токенде `repo` рұқсаты бар ма?")
            return False
        else:
            st.error(f"❌ Сақтау қатесі: {put_resp.status_code}")
            return False
    except Exception as e:
        st.error(f"❌ GitHub: {e}")
        return False


def save_menu(df):
    msg = f"Мәзірді жаңарту ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
    return _save_csv_to_github(df, MENU_PATH, msg)