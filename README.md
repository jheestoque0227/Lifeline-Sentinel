# Lifeline Sentinel

Lifeline Sentinel is an intelligent suicide surveillance and forecasting system using Python, Flask, MySQL, and machine learning.

## Core Features

- Fixed roles: Admin, Encoder, Analyst
- Admin-side user management
- Password reset through email
- User deactivation
- Registry management based on SSASH TRD/Data Dictionary
- Descriptive analytics
- Diagnostic analytics
- Predictive analytics using Random Forest
- Clustering analytics using K-Means
- Time Series forecasting
- PDF, Excel, and printable reports

## Local Setup

1. Create MySQL database:

```sql
CREATE DATABASE lifeline_sentinel_db;
```

2. Create virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure `.env` based on `.env.example`.

5. Run:

```bash
python run.py
```

6. Configure the initial Admin account in `.env`:

```env
INITIAL_ADMIN_EMPLOYEE_NO=
INITIAL_ADMIN_FULL_NAME=
INITIAL_ADMIN_EMAIL=
INITIAL_ADMIN_USERNAME=
INITIAL_ADMIN_PASSWORD=
```

7. Apply migrations:

```bash
flask db upgrade
```

The initial Admin is created by the migration only if no Admin account exists yet. Additional Admin accounts are managed from User Management.
