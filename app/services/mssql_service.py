import pyodbc
from flask import current_app


def get_mssql_connection():
    conn = pyodbc.connect(
        current_app.config["MSSQL_CONNECTION_STRING"]
    )

    return conn