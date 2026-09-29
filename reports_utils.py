"""Есеп функциялары — күндік және айлық"""
import pandas as pd
import requests
from datetime import datetime
from io import StringIO

from config import DAILY_REPORT_PATH, MONTHLY_REPORT_PATH, gh_url
from menu_utils import _save_csv_to_github
from orders_utils import load_orders


def build_daily_report(report_date):
    odf = load_orders()
    if odf.empty:
        return pd.DataFrame()
    odf["date_only"] = odf["timestamp"].astype(str).str[:10]
    day_df = odf[odf["date_only"] == report_date].copy()
    if day_df.empty:
        return pd.DataFrame()
    report = day_df.groupby(["item_name", "category"]).agg(
        {"quantity": "sum", "total": "sum"}).reset_index()
    report.columns = ["Тағам", "Санат", "Саны", "Жалпы сома (₸)"]
    report["Есеп күні"] = report_date
    report["Есеп уақыты"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return report


def build_monthly_report(year, month):
    odf = load_orders()
    if odf.empty:
        return pd.DataFrame()
    odf["date_only"] = odf["timestamp"].astype(str).str[:10]
    odf["date_obj"] = pd.to_datetime(odf["date_only"], errors="coerce")
    month_df = odf[(odf["date_obj"].dt.year == year) &
                   (odf["date_obj"].dt.month == month)].copy()
    if month_df.empty:
        return pd.DataFrame()
    report = month_df.groupby(["item_name", "category"]).agg(
        {"quantity": "sum", "total": "sum"}).reset_index()
    report.columns = ["Тағам", "Санат", "Саны", "Жалпы сома (₸)"]
    report["Ай"] = f"{year}-{month:02d}"
    report["Есеп уақыты"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return report


def append_daily_to_github(report_df):
    if report_df.empty:
        return False
    report_date = report_df["Есеп күні"].iloc[0]
    existing = pd.DataFrame()
    try:
        resp = requests.get(gh_url(DAILY_REPORT_PATH), timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            existing = pd.read_csv(StringIO(resp.text))
    except Exception:
        pass
    if not existing.empty and "Есеп күні" in existing.columns:
        existing = existing[existing["Есеп күні"].astype(str) != report_date]
    final_df = pd.concat([existing, report_df], ignore_index=True)
    if "Есеп күні" in final_df.columns:
        final_df = final_df.sort_values("Есеп күні").reset_index(drop=True)
    msg = f"Күндік есеп: {report_date}"
    return _save_csv_to_github(final_df, DAILY_REPORT_PATH, msg)


def append_monthly_to_github(report_df):
    if report_df.empty:
        return False
    report_month = report_df["Ай"].iloc[0]
    existing = pd.DataFrame()
    try:
        resp = requests.get(gh_url(MONTHLY_REPORT_PATH), timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            existing = pd.read_csv(StringIO(resp.text))
    except Exception:
        pass
    if not existing.empty and "Ай" in existing.columns:
        existing = existing[existing["Ай"].astype(str) != report_month]
    final_df = pd.concat([existing, report_df], ignore_index=True)
    if "Ай" in final_df.columns:
        final_df = final_df.sort_values("Ай").reset_index(drop=True)
    msg = f"Айлық есеп: {report_month}"
    return _save_csv_to_github(final_df, MONTHLY_REPORT_PATH, msg)