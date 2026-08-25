from datetime import date, datetime

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
            patbdate,
            patsex,
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
        birthdate = _date_value(row.patbdate)
        sex_at_birth = _sex_at_birth_label(row.patsex)
        results.append({
            "hospital_number": row.hpercode,
            "patient_name": row.full_name,
            "birthdate": birthdate.isoformat() if birthdate else "",
            "age": _age_from_birthdate(birthdate),
            "sex_at_birth": sex_at_birth,
            "patsex": row.patsex or "",
        })

    cursor.close()
    conn.close()

    return results


def _date_value(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    return None


def _age_from_birthdate(birthdate, as_of=None):
    if not birthdate:
        return None
    as_of = as_of or date.today()
    age = as_of.year - birthdate.year - ((as_of.month, as_of.day) < (birthdate.month, birthdate.day))
    return max(age, 0)


def _sex_at_birth_label(value):
    normalized = (value or "").strip().upper()
    if normalized in {"M", "MALE"}:
        return "Male"
    if normalized in {"F", "FEMALE"}:
        return "Female"
    if normalized in {"I", "INTERSEX"}:
        return "Intersex"
    if normalized in {"U", "UNK", "UNKNOWN"}:
        return "Unknown"
    return ""


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
