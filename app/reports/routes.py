from flask import Blueprint, render_template
from flask_login import login_required
from app.auth.decorators import role_required

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.route("/")
@login_required
@role_required("Admin", "Analyst")
def index():
    return render_template("reports/index.html")
