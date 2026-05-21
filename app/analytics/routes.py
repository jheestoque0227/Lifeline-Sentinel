from datetime import datetime

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.analytics.services import (
    applied_filter_payload,
    clean_filters,
    descriptive_dashboard,
    filter_options,
)
from app.auth.decorators import role_required
from app.extensions import db
from app.services.ml.model_service import build_ml_dashboard
from app.services.audit import record_audit

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("")
@analytics_bp.route("/")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def analytics_dashboard():
    return redirect(url_for("analytics.descriptive"))


@analytics_bp.route("/descriptive")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def descriptive():
    filters = clean_filters(request.args)
    dashboard = descriptive_dashboard(current_user, filters)
    record_audit(
        "view",
        "analytics",
        remarks="Viewed descriptive analytics dashboard.",
        new_values={
            "user_id": current_user.id,
            "role": current_user.role,
            "timestamp": datetime.utcnow().isoformat(),
            "filters": applied_filter_payload(filters),
        },
    )
    db.session.commit()
    return render_template(
        "analytics/descriptive.html",
        dashboard=dashboard,
        filters=filters,
        filter_options=filter_options(current_user),
    )


@analytics_bp.route("/descriptive/data")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def descriptive_data():
    filters = clean_filters(request.args)
    dashboard = descriptive_dashboard(current_user, filters)
    return jsonify(
        {
            "summary": dashboard["summary"],
            "charts": dashboard["charts"],
            "has_data": dashboard["has_data"],
            "filters": applied_filter_payload(filters),
        }
    )


@analytics_bp.route("/ml")
@login_required
@role_required("Admin", "Analyst")
def ml_models():
    filters = clean_filters(request.args)
    dashboard = build_ml_dashboard(current_user, filters)
    record_audit(
        "view",
        "analytics",
        remarks="Viewed ML models and forecasting dashboard.",
        new_values={
            "user_id": current_user.id,
            "role": current_user.role,
            "timestamp": datetime.utcnow().isoformat(),
            "filters": applied_filter_payload(filters),
        },
    )
    db.session.commit()
    return render_template(
        "analytics/ml.html",
        dashboard=dashboard,
        filters=filters,
        filter_options=filter_options(current_user),
    )


@analytics_bp.route("/ml/data")
@login_required
@role_required("Admin", "Analyst")
def ml_models_data():
    filters = clean_filters(request.args)
    dashboard = build_ml_dashboard(current_user, filters)
    return jsonify(
        {
            "summary": dashboard["summary"],
            "risk": dashboard["risk"],
            "clustering": dashboard["clustering"],
            "forecasting": dashboard["forecasting"],
            "has_data": dashboard["has_data"],
            "filters": applied_filter_payload(filters),
        }
    )
