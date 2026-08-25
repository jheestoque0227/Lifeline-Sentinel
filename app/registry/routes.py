from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.services.mssql_service import get_diagnosis_choice, search_diagnoses, search_patients

from app.auth.decorators import role_required
from app.extensions import db
from app.models.registry import Registry
from app.registry.forms import DeleteRegistryForm, RegistryForm, RegistrySearchForm
from app.registry import options
from app.registry.services import (
    apply_user_hospital_scope,
    create_registry,
    populate_form,
    incident_payloads,
    registry_query,
    registry_snapshot,
    registry_statistics,
    search_registries,
    soft_delete_registry,
    update_registry,
)
from app.services.audit import record_audit
from app.services.hospitals import get_configured_hospital_code, hospital_filter_choices
from app.services.locations import get_cities_municipalities, get_provinces, get_regions

registry_bp = Blueprint("registry", __name__, url_prefix="/registry")


@registry_bp.route("/")
@login_required
@role_required("Admin", "Encoder")
def index():
    registries = search_registries(
        q=request.args.get("q"),
        reporting_department=request.args.get("reporting_department"),
        hospital_code=request.args.get("hospital_code"),
        include_deleted=False,
        user=current_user,
    ).all()
    hospital_codes = [
        value for (value,) in apply_user_hospital_scope(Registry.query, current_user)
        .with_entities(Registry.hospital_code)
        .filter(Registry.hospital_code.is_not(None))
        .distinct()
        .order_by(Registry.hospital_code)
        .all()
        if value
    ]
    hospital_options = hospital_filter_choices(hospital_codes)
    hospital_labels = dict(hospital_options)
    return render_template(
        "registry/index.html",
        registries=registries,
        hospital_options=hospital_options,
        hospital_labels=hospital_labels,
        filters=request.args,
    )

@registry_bp.route("/api/patient-search")
@login_required
@role_required("Admin", "Encoder")
def patient_search():
    keyword = request.args.get("q", "").strip()

    if not keyword:
        return jsonify([])

    results = search_patients(keyword)

    return jsonify(results)


@registry_bp.route("/api/diagnosis-search")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def diagnosis_search():
    keyword = request.args.get("q", "").strip()
    results = search_diagnoses(keyword)

    return jsonify({"results": results})


@registry_bp.route("/api/locations/regions")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def location_regions():
    return jsonify({"results": get_regions()})


@registry_bp.route("/api/locations/provinces")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def location_provinces():
    region = request.args.get("region", "").strip()
    return jsonify({"results": get_provinces(region)})


@registry_bp.route("/api/locations/cities-municipalities")
@login_required
@role_required("Admin", "Encoder", "Analyst")
def location_cities_municipalities():
    province = request.args.get("province", "").strip()
    return jsonify({"results": get_cities_municipalities(province)})

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
                reporting_department=form.reporting_department.data,
            )
        )
    registries = search_registries(q=request.args.get("q"), user=current_user).limit(25).all()
    return render_template("registry/search.html", form=form, registries=registries)


@registry_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("Admin", "Encoder")
def create():
    form = RegistryForm()
    form.data_steward_code.data = current_user.employee_no
    form.hospital_code.data = get_configured_hospital_code(current_user)
    if form.validate_on_submit() and validate_incident_payloads():
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
    ensure_location_choices(form)
    ensure_diagnosis_choices(form)
    incidents = two_incident_payloads(incident_payloads_from_request() if request.method == "POST" else [{}])
    return render_template("registry/create.html", form=form, options=options, location_regions=get_regions(), incidents=incidents)


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
    registry = registry_query(user=current_user).filter(Registry.id == registry_id).first_or_404()
    form = RegistryForm()
    if form.validate_on_submit() and validate_incident_payloads():
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
    ensure_location_choices(form)
    ensure_diagnosis_choices(form)
    incidents = two_incident_payloads(incident_payloads_from_request() if request.method == "POST" else incident_payloads(registry))
    return render_template("registry/edit.html", form=form, registry=registry, options=options, location_regions=get_regions(), incidents=incidents)


@registry_bp.route("/<int:registry_id>/delete", methods=["POST"])
@login_required
@role_required("Admin", "Encoder")
def delete(registry_id):
    registry = registry_query(user=current_user).filter(Registry.id == registry_id).first_or_404()
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
    stats = registry_statistics(current_user)
    return render_template("registry/statistics.html", stats=stats)


def _get_registry_for_view(registry_id):
    query = Registry.query if current_user.role == "Admin" else registry_query(user=current_user)
    return query.filter(Registry.id == registry_id).first_or_404()


def ensure_diagnosis_choices(form):
    for field in [form.primary_diagnosis_code, form.secondary_diagnosis_code]:
        if not field.data:
            continue
        if all(value != field.data for value, _ in field.choices):
            field.choices.append(get_diagnosis_choice(field.data) or (field.data, field.data))


def ensure_location_choices(form):
    region = form.incident_region.data
    province_city = form.incident_province_city.data
    region_options = options.LOCATION_OPTIONS.get(region, {})

    form.incident_province_city.choices = [("", "Select...")] + [
        (value, value) for value in region_options.keys()
    ]

    municipality_options = region_options.get(province_city, [])
    form.incident_municipality.choices = [("", "Select...")] + [
        (value, value) for value in municipality_options
    ]

    if province_city and all(value != province_city for value, _ in form.incident_province_city.choices):
        form.incident_province_city.choices.append((province_city, province_city))
    if form.incident_municipality.data and all(value != form.incident_municipality.data for value, _ in form.incident_municipality.choices):
        form.incident_municipality.choices.append((form.incident_municipality.data, form.incident_municipality.data))


def incident_payloads_from_request():
    indexes = sorted(
        {
            key.split("[", 1)[1].split("]", 1)[0]
            for key in request.form.keys()
            if key.startswith("incidents[") and "][" in key
        },
        key=lambda value: int(value) if value.isdigit() else value,
    )
    payloads = []
    for index in indexes:
        prefix = f"incidents[{index}]"
        if request.form.get(f"{prefix}[remove]") == "1":
            continue
        poisoning = request.form.getlist(f"{prefix}[self_poisoning_methods]")
        harm = request.form.getlist(f"{prefix}[self_harm_methods]")
        notes = {}
        for method in poisoning + harm:
            notes[method] = request.form.get(f"{prefix}[method_notes][{method}]", "")
        payloads.append(
            {
                "incident_date": request.form.get(f"{prefix}[incident_date]", ""),
                "incident_day": request.form.get(f"{prefix}[incident_day]", ""),
                "incident_time_range": request.form.get(f"{prefix}[incident_time_range]", ""),
                "incident_place": request.form.get(f"{prefix}[incident_place]", ""),
                "incident_place_other": request.form.get(f"{prefix}[incident_place_other]", ""),
                "incident_region": request.form.get(f"{prefix}[incident_region]", ""),
                "province_or_city": request.form.get(f"{prefix}[province_or_city]", ""),
                "municipality": request.form.get(f"{prefix}[municipality]", ""),
                "self_poisoning_methods": poisoning,
                "self_harm_methods": harm,
                "method_notes": notes,
                "remarks": request.form.get(f"{prefix}[remarks]", ""),
            }
        )
    return payloads or [{}]


def two_incident_payloads(payloads):
    items = list(payloads or [{}])[:2]
    while len(items) < 2:
        items.append({})
    return items


def validate_incident_payloads():
    payloads = incident_payloads_from_request()
    valid = True
    for index, incident in enumerate(payloads, start=1):
        missing = []
        for key, label in [
            ("incident_date", "date"),
            ("incident_day", "day"),
            ("incident_time_range", "time of day"),
            ("incident_place", "place"),
            ("incident_region", "region"),
            ("province_or_city", "province"),
            ("municipality", "city / municipality"),
        ]:
            if not incident.get(key):
                missing.append(label)
        if incident.get("incident_place") == "Other" and not incident.get("incident_place_other"):
            missing.append("other place")
        if not incident.get("self_poisoning_methods") and not incident.get("self_harm_methods"):
            missing.append("at least one ICD-10 method")
        if missing:
            flash(f"Incident #{index}: This field is required for {', '.join(missing)}.", "danger")
            valid = False
    return valid
