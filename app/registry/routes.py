from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.auth.decorators import role_required
from app.extensions import db
from app.models.registry import Registry
from app.registry.forms import DeleteRegistryForm, RegistryForm, RegistrySearchForm
from app.registry.services import (
    create_registry,
    populate_form,
    registry_query,
    registry_snapshot,
    registry_statistics,
    search_registries,
    soft_delete_registry,
    update_registry,
)
from app.services.audit import record_audit

registry_bp = Blueprint("registry", __name__, url_prefix="/registry")


@registry_bp.route("/")
@login_required
@role_required("Admin", "Encoder")
def index():
    registries = search_registries(
        q=request.args.get("q"),
        risk_level=request.args.get("risk_level"),
        reporting_department=request.args.get("reporting_department"),
        include_deleted=request.args.get("include_deleted") == "1" and current_user.role == "Admin",
    ).all()
    return render_template("registry/index.html", registries=registries)


@registry_bp.route("/search", methods=["GET", "POST"])
@login_required
@role_required("Admin", "Encoder")
def search():
    form = RegistrySearchForm()
    if form.validate_on_submit():
        return redirect(
            url_for(
                "registry.index",
                q=form.q.data,
                risk_level=form.risk_level.data,
                reporting_department=form.reporting_department.data,
            )
        )
    registries = search_registries(q=request.args.get("q")).limit(25).all()
    return render_template("registry/search.html", form=form, registries=registries)


@registry_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("Admin", "Encoder")
def create():
    form = RegistryForm()
    if form.validate_on_submit():
        registry = create_registry(form, current_user)
        record_audit(
            "create",
            "registry",
            remarks=f"Created registry entry {registry.registry_code}.",
            new_values=registry_snapshot(registry),
        )
        db.session.commit()
        flash("Registry entry created.", "success")
        return redirect(url_for("registry.view", registry_id=registry.id))
    return render_template("registry/create.html", form=form)


@registry_bp.route("/<int:registry_id>")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def view(registry_id):
    registry = _get_registry_for_view(registry_id)
    record_audit(
        "view",
        "registry",
        remarks=f"Viewed registry entry {registry.registry_code}.",
        new_values={"registry_id": registry.id, "registry_code": registry.registry_code},
    )
    db.session.commit()
    return render_template("registry/view.html", registry=registry, delete_form=DeleteRegistryForm())


@registry_bp.route("/<int:registry_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("Admin", "Encoder")
def edit(registry_id):
    registry = registry_query().filter(Registry.id == registry_id).first_or_404()
    form = RegistryForm()
    if form.validate_on_submit():
        old_values = registry_snapshot(registry)
        update_registry(registry, form, current_user)
        record_audit(
            "update",
            "registry",
            remarks=f"Updated registry entry {registry.registry_code}.",
            old_values=old_values,
            new_values=registry_snapshot(registry),
        )
        db.session.commit()
        flash("Registry entry updated.", "success")
        return redirect(url_for("registry.view", registry_id=registry.id))
    if request.method == "GET":
        populate_form(form, registry)
    return render_template("registry/edit.html", form=form, registry=registry)


@registry_bp.route("/<int:registry_id>/delete", methods=["POST"])
@login_required
@role_required("Admin", "Encoder")
def delete(registry_id):
    registry = registry_query().filter(Registry.id == registry_id).first_or_404()
    form = DeleteRegistryForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("registry.view", registry_id=registry.id))

    old_values = registry_snapshot(registry)
    soft_delete_registry(registry, current_user, form.deleted_remarks.data)
    record_audit(
        "delete",
        "registry",
        remarks=f"Soft deleted registry entry {registry.registry_code}.",
        old_values=old_values,
        new_values=registry_snapshot(registry),
    )
    db.session.commit()
    flash("Registry entry deleted.", "success")
    return redirect(url_for("registry.index"))


@registry_bp.route("/<int:registry_id>/print")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def print_view(registry_id):
    registry = _get_registry_for_view(registry_id)
    record_audit(
        "view",
        "registry",
        remarks=f"Opened print view for registry entry {registry.registry_code}.",
        new_values={"registry_id": registry.id, "registry_code": registry.registry_code, "print": True},
    )
    db.session.commit()
    return render_template("registry/print.html", registry=registry)


@registry_bp.route("/statistics")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def statistics():
    stats = registry_statistics()
    return render_template("registry/statistics.html", stats=stats)


def _get_registry_for_view(registry_id):
    query = Registry.query if current_user.role == "Admin" else registry_query()
    return query.filter(Registry.id == registry_id).first_or_404()
