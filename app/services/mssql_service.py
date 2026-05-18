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


def search_diagnoses(keyword=""):
    conn = get_mssql_connection()
    cursor = conn.cursor()

    query = """
        SELECT TOP 20
            diagcode,
            diagdesc
        FROM hdiag
        WHERE
            diagcode LIKE 'F%'
            AND (
                ? = ''
                OR diagcode LIKE ?
                OR diagdesc LIKE ?
            )
        ORDER BY diagcode
    """

    keyword = (keyword or "").strip()
    search = f"%{keyword}%"

    cursor.execute(
        query,
        keyword,
        search,
        search
    )

    rows = cursor.fetchall()

    results = []
    for row in rows:
        diagnosis_code = row.diagcode
        diagnosis_description = row.diagdesc
        results.append({
            "id": diagnosis_code,
            "text": f"{diagnosis_code} - {diagnosis_description}",
            "diagcode": diagnosis_code,
            "diagdesc": diagnosis_description,
        })

    cursor.close()
    conn.close()

    return results


def get_diagnosis_choice(diagnosis_code):
    if not diagnosis_code:
        return None

    conn = get_mssql_connection()
    cursor = conn.cursor()

    query = """
        SELECT TOP 1
            diagcode,
            diagdesc
        FROM hdiag
        WHERE diagcode = ?
    """

    cursor.execute(query, diagnosis_code)
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return None

    return (
        row.diagcode,
        f"{row.diagcode} - {row.diagdesc}",
    )
