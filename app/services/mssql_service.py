import pyodbc
from flask import current_app


def get_mssql_connection():
    return pyodbc.connect(
        current_app.config["MSSQL_CONNECTION_STRING"]
    )


def search_patients(keyword):
    conn = get_mssql_connection()
    cursor = conn.cursor()

    query = """
        SELECT TOP 20
            hpercode,
            CONCAT(
                patlast,
                CASE
                    WHEN patsuffix IS NOT NULL AND patsuffix <> ''
                    THEN ' ' + patsuffix
                    ELSE ''
                END,
                ', ',
                patfirst,
                CASE
                    WHEN patmiddle IS NOT NULL AND patmiddle <> ''
                    THEN ' ' + patmiddle
                    ELSE ''
                END
            ) AS full_name
        FROM hperson
        WHERE
            hpercode LIKE ?
            OR patlast LIKE ?
            OR patfirst LIKE ?
        ORDER BY patlast, patfirst
    """

    search = f"%{keyword}%"

    cursor.execute(
        query,
        search,
        search,
        search
    )

    rows = cursor.fetchall()

    results = []

    for row in rows:
        results.append({
            "hospital_number": row.hpercode,
            "patient_name": row.full_name
        })

    cursor.close()
    conn.close()

    return results