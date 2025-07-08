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
    "503_4": 6
}


def save_boms_to_cache(boms):
    conn = sql_lite_conn()
    boms.to_sql('boms_cache', conn, if_exists='replace', index=False)



def fetch_boms_from_server():
    conn = sql_server_conn()
    query = """WITH cleaned_recipe AS (SELECT TRIM(itemprod)                             AS item_prod,
                                              TRIM(itemreq)                              AS item_required,
                                              TRIM(costcenter)                           AS cost_center,
                                              operation,
                                              CAST(REPLACE(quantity, ',', '.') AS FLOAT) AS quant
                                       FROM recipe
               with (nolock)
               WHERE version = 1
                   )
    SELECT item_prod,
           cost_center,
           CASE
               WHEN item_required LIKE '%_LH' OR item_required LIKE '%_MH'
                   THEN operation
               ELSE item_required
               END    AS item_req,
           SUM(quant) AS quantity
    FROM cleaned_recipe with (nolock)
    GROUP BY
        item_prod,
        cost_center,
        CASE
        WHEN item_required LIKE '%_LH' OR item_required LIKE '%_MH'
        THEN operation
        ELSE item_required
    END;"""
    df = pd.read_sql(query, conn)
    save_boms_to_cache(df)
    return df


def fetch_boms():
    try:
        conn = sql_lite_conn()
        df = pd.read_sql('select * from boms_cache', conn)
    except (SQLiteError, SQLAlchemyError, DatabaseError) as err:
        logger.error(
            "Failed to fetch data from cache",
            extra={
                'error_type': type(err).__name__,
                'error_message': str(err)
            }
        )
        df = fetch_boms_from_server()
    return df


def root_items(boms):
    prod_items = set(boms['item_prod'].unique())
    req_items = set(boms['item_req'].dropna().unique())
    top_level_items = sorted(prod_items - req_items)
    return top_level_items


def cost_center_map(boms):
    df = boms[boms['item_req'].isna()]
    cc_map = dict(zip(df['item_prod'], df['cost_center']))
    return cc_map


def build_graph(boms):
    bom_graph = defaultdict(list)
    for _, row in boms.iterrows():
        if row['item_req'] is not None:
            bom_graph[row['item_prod']].append(row['item_req'])
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


def dfs_violations_and_depth(current_item, bom_graph, cc, violations, level=0, path=None, parent_item=None,
                             levels_seen=None):
    if path is None:
        path = set()
    if levels_seen is None:
        levels_seen = set()

    if current_item in path:
        return level

    current_cc = cc.get(current_item)
    levels_seen.add(level)

    # Check cost center violation if we have a parent
    if parent_item and current_cc:
        parent_cc = cc.get(parent_item)
        if parent_cc:
            parent_prio = COST_CENTER_ORDER.get(parent_cc)
            current_prio = COST_CENTER_ORDER.get(current_cc)

            if (parent_prio is not None and
                    current_prio is not None and
                    current_prio <= parent_prio):
                violations['cc_violations'].append({
                    'child_item': current_item,
                    'child_cc': current_cc,
                    'parent_item': parent_item,
                    'parent_cc': parent_cc
                })

    path.add(current_item)
    max_depth = level
    for child in bom_graph.get(current_item, []):
        child_depth = dfs_violations_and_depth(
            child, bom_graph, cc, violations,
            level + 1, path, current_item, levels_seen
        )
        max_depth = max(max_depth, child_depth)
    path.remove(current_item)

    return max_depth


def check_all_root_items():
    boms = fetch_boms()
    max_levels = 7

    results = {
        'cc_violations': [],
        'deep_boms': []
    }

    # Get necessary data structures
    bom_graph = build_graph(boms)
    cc = cost_center_map(boms)
    root_item_list = root_items(boms)

    for root_item in root_item_list:
        levels_seen = set()
        max_depth = dfs_violations_and_depth(
            root_item,
            bom_graph,
            cc,
            results,
            levels_seen=levels_seen
        )

        if max_depth > max_levels:
            results['deep_boms'].append({
                'root_item': root_item,
                'max_depth': max_depth,
            })

    return results
