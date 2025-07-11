from collections import defaultdict
import pandas as pd
from sqlite3 import Error as SQLiteError
from sqlalchemy.exc import SQLAlchemyError
from pandas.io.sql import DatabaseError
from logger import logger
from sql_server_connector import *

COST_CENTER_ORDER = {
    "502_2": 1,
    "503": 2,
    "503_1": 3,
    "503_2": 4,
    "503_3": 5,
    "503_4": 6,
}


def save_boms_to_cache(boms):
    conn = sql_lite_conn()
    boms.to_sql("boms_cache", conn, if_exists="replace", index=False)


def save_it_data_to_cache(it_data):
    conn = sql_lite_conn()
    it_data.to_sql("it_data_cache", conn, if_exists="replace", index=False)


def fetch_boms_from_server():
    conn = sql_server_conn()
    query = """SELECT * FROM CSPRY_BOMsummary;"""
    df = pd.read_sql(query, conn)
    save_boms_to_cache(df)
    return df


def fetch_it_data_from_server():
    conn = sql_server_conn()
    query = """select ItemCode, Description_1, Condition from items where type = 'S';"""
    df = pd.read_sql(query, conn)
    save_it_data_to_cache(df)
    return df


def fetch_boms():
    try:
        conn = sql_lite_conn()
        df = pd.read_sql("select * from boms_cache", conn)
    except (SQLiteError, SQLAlchemyError, DatabaseError) as err:
        logger.error(
            "Failed to fetch bom data from cache",
            extra={"error_type": type(err).__name__, "error_message": str(err)},
        )
        df = fetch_boms_from_server()
    return df

def fetch_it_data():
    try:
        conn = sql_lite_conn()
        df = pd.read_sql("select * from it_data_cache", conn)
    except (SQLiteError, SQLAlchemyError, DatabaseError) as err:
        logger.error(
            "Failed to fetch items data from cache",
            extra={"error_type": type(err).__name__, "error_message": str(err)},
        )
        df = fetch_it_data_from_server()
    return df


def root_items(boms):
    prod_items = set(boms["item_prod"].unique())
    req_items = set(boms["item_req"].dropna().unique())
    top_level_items = sorted(prod_items - req_items)
    return top_level_items


def cost_center_map(boms):
    df = boms[boms["item_req"].isna()]
    cc_map = dict(zip(df["item_prod"], df["cost_center"]))
    return cc_map


def build_graph(boms):
    bom_graph = defaultdict(list)
    for _, row in boms.iterrows():
        if row["item_req"] is not None:
            bom_graph[row["item_prod"]].append(row["item_req"])
    return bom_graph


def dfs(current_item, level, path, bom_graph, cc, result, parent_cc=None):
    if current_item in path:
        return

    current_cc = cc.get(current_item)
    violation = str()

    # Check cost center violation
    if parent_cc and current_cc:
        parent_prio = COST_CENTER_ORDER.get(parent_cc)
        current_prio = COST_CENTER_ORDER.get(current_cc)
        if (
            parent_prio is not None
            and current_prio is not None
            and current_prio <= parent_prio
        ):
            violation = f" >= than parent {parent_cc} !!!"

    result.append((current_item, level, current_cc, violation))

    for child in bom_graph.get(current_item, []):
        dfs(child, level + 1, path | {current_item}, bom_graph, cc, result, current_cc)


def traverse_bom(item, boms):
    result = []
    bom_graph = build_graph(boms)
    cc = cost_center_map(boms)
    dfs(item, 0, set(), bom_graph, cc, result)
    return result


def traverse_all_issues(root_items, boms):
    result_all = {}
    bom_graph = build_graph(boms)
    cc = cost_center_map(boms)
    for item in root_items:
        result = []
        dfs(item, 0, set(), bom_graph, cc, result)

        max_level = max((entry[1] for entry in result), default=0)
        violation_count = sum(1 for entry in result if entry[3] != "")

        if max_level >= 8 or violation_count > 0:
            result_all[item] = {
                "bom_data": result,
                "issues": {"max_level": max_level, "violation_count": violation_count},
            }

    return result_all
