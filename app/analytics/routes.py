from flask import Blueprint, render_template
from flask_login import login_required
from app.auth.decorators import role_required

analytics_bp = Blueprint("analytics", __name__, url_prefix="/dashboard")

@analytics_bp.route("/")
@login_required
@role_required("Admin", "Analyst")
def analytics_dashboard():
    return render_template("analytics/dashboard.html")

@analytics_bp.route("/registry-statistics")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def registry_statistics():
    return render_template("analytics/registry_statistics.html")
