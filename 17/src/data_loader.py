import pandas as pd
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ORDERS_CSV = DATA_DIR / "orders.csv"
DISHES_CSV = DATA_DIR / "dishes.csv"


def load_orders():
    df = pd.read_csv(ORDERS_CSV, encoding="utf-8")
    df["订单时间"] = pd.to_datetime(df["订单时间"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["订单时间"])
    df["订单金额"] = pd.to_numeric(df["订单金额"], errors="coerce").fillna(0)
    df["桌号"] = pd.to_numeric(df["桌号"], errors="coerce").astype(int)
    df["菜品数量"] = pd.to_numeric(df["菜品数量"], errors="coerce").astype(int)
    df["订单ID"] = df.groupby(["订单时间", "桌号"]).ngroup()
    df["日期"] = df["订单时间"].dt.date
    df["小时"] = df["订单时间"].dt.hour
    df["星期"] = df["订单时间"].dt.dayofweek
    df["是否周末"] = df["星期"].isin([5, 6])
    return df


def load_dishes():
    df = pd.read_csv(DISHES_CSV, encoding="utf-8")
    df["价格"] = pd.to_numeric(df["价格"], errors="coerce").fillna(0)
    return df


def merge_data(orders_df, dishes_df):
    merged = pd.merge(
        orders_df,
        dishes_df,
        on="菜品ID",
        how="left",
        validate="m:1",
    )
    return merged


def load_all_data():
    orders = load_orders()
    dishes = load_dishes()
    merged = merge_data(orders, dishes)
    return orders, dishes, merged
