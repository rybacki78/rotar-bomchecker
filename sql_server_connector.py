from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()


def sql_server_conn():
    driver = os.getenv("SQL_DRIVER", "ODBC+Driver+18+for+SQL+Server")
    server = os.getenv("SQL_SERVER")
    port = os.getenv("SQL_PORT", "1433")
    database = os.getenv("SQL_DATABASE")
    username = os.getenv("SQL_USER")
    password = os.getenv("SQL_PASSWORD")

    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server},{port}/{database}"
        f"?driver={driver}&TrustServerCertificate=yes"
    )

    engine = create_engine(connection_string)
    return engine

def sql_lite_conn():
    connection_string = "sqlite:///cache.db"
    engine = create_engine(connection_string)
    return engine
