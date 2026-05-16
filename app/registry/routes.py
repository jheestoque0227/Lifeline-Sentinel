from flask import Blueprint, render_template
from flask_login import login_required
from app.auth.decorators import role_required

registry_bp = Blueprint("registry", __name__, url_prefix="/registry")

@registry_bp.route("/")
@login_required
@role_required("Admin", "Encoder")
def index():
    return render_template("registry/index.html")
