"""Тапсырыс функциялары"""
import pandas as pd
import os

ORDER_COLUMNS = ["timestamp", "class", "week", "day", "item_name",
                 "category", "price", "quantity", "total"]


def load_orders():
    try:
        if os.path.exists("Orders.csv"):
            df = pd.read_csv("Orders.csv")
            for c in ORDER_COLUMNS:
                if c not in df.columns:
                    df[c] = None
            return df[ORDER_COLUMNS]
    except Exception:
        pass
    return pd.DataFrame(columns=ORDER_COLUMNS)


def save_order(order_data):
    orders_df = load_orders()
    new_order = pd.DataFrame([order_data])
    orders_df = pd.concat([orders_df, new_order], ignore_index=True)
    orders_df.to_csv("Orders.csv", index=False)