from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    HiddenField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

from app.registry import options

REQUIRED_MESSAGE = "This field is required"


class RegistryForm(FlaskForm):
    data_steward_code = StringField("Data steward code", validators=[DataRequired(REQUIRED_MESSAGE), Length(max=50)])
    hospital_code = StringField("Hospital code", validators=[DataRequired(REQUIRED_MESSAGE), Length(max=50)])
    date_of_presentation = DateField("Date of presentation", validators=[DataRequired(REQUIRED_MESSAGE)])
    time_of_presentation = TimeField("Time of presentation", validators=[Optional()])
    reporting_department = SelectField("Reporting department", choices=[("", "Select...")] + options.REPORTING_DEPARTMENTS, validators=[DataRequired(REQUIRED_MESSAGE)])

    intent = SelectField("Intent", choices=options.INTENTS, validators=[DataRequired(REQUIRED_MESSAGE)])
    infliction = SelectField("Infliction", choices=options.INFLICTIONS, validators=[DataRequired(REQUIRED_MESSAGE)])
    type_of_consult = SelectField("Type of consult", choices=options.as_choices(options.TYPE_OF_CONSULTS), validators=[DataRequired(REQUIRED_MESSAGE)])
    type_of_consult_other = StringField("Other consult type", validators=[Length(max=150)])

    patient_identifier = StringField("Patient identifier", validators=[DataRequired(REQUIRED_MESSAGE), Length(max=100)])
    age = IntegerField("Age", validators=[DataRequired(REQUIRED_MESSAGE), NumberRange(min=0, max=130, message="Age must be between 0 and 130.")])
    sex_at_birth = SelectField("Sex at birth", choices=options.as_choices(options.SEX_AT_BIRTH), validators=[DataRequired(REQUIRED_MESSAGE)])
    sexual_orientation = SelectField("Sexual orientation", choices=options.as_choices(options.SEXUAL_ORIENTATIONS), validators=[DataRequired(REQUIRED_MESSAGE)])
    sexual_orientation_other = StringField("Other sexual orientation", validators=[Length(max=150)])
    gender_identity = SelectField("Gender identity", choices=options.as_choices(options.GENDER_IDENTITIES), validators=[DataRequired(REQUIRED_MESSAGE)])
    gender_identity_other = StringField("Other gender identity", validators=[Length(max=150)])
    marital_status = SelectField("Marital status", choices=options.as_choices(options.MARITAL_STATUSES), validators=[DataRequired(REQUIRED_MESSAGE)])
    highest_educational_attainment = SelectField("Highest educational attainment", choices=options.as_choices(options.EDUCATIONAL_ATTAINMENTS), validators=[DataRequired(REQUIRED_MESSAGE)])
    employment_status = SelectField("Employment status", choices=options.as_choices(options.EMPLOYMENT_STATUSES), validators=[DataRequired(REQUIRED_MESSAGE)])
    nationality = StringField("Nationality", validators=[DataRequired(REQUIRED_MESSAGE), Length(max=100)])
    religion = SelectField("Religion", choices=options.as_choices(options.RELIGIONS), validators=[DataRequired(REQUIRED_MESSAGE)])
    religion_other = StringField("Other religion", validators=[Length(max=150)])

    is_first_incident = SelectField("Is this the first incident of suicide attempt or self-harm?", choices=options.YES_NO, validators=[DataRequired(REQUIRED_MESSAGE)])
    has_past_2_month_incident = SelectField("Was there an incident of suicide attempt or self-harm in the past 2 months?", choices=options.YES_NO, validators=[Optional()])
    incident_date = DateField("(INCIDENT) Date of incident", validators=[Optional()])
    incident_day = SelectField("(INCIDENT) Day of incident", choices=options.as_choices(options.INCIDENT_DAYS), validators=[Optional()])
    incident_time_period = SelectField("(INCIDENT) Time of day of the incident", choices=options.as_choices(options.INCIDENT_TIME_PERIODS), validators=[Optional()])
    incident_place = SelectField("(INCIDENT) Place of incident", choices=options.as_choices(options.INCIDENT_PLACES), validators=[Optional()])
    incident_place_other = StringField("Other incident place", validators=[Length(max=150)])
    incident_region = SelectField("Region", choices=options.as_choices(list(options.LOCATION_OPTIONS.keys())), validators=[Optional()])
    incident_province_city = SelectField("Province", choices=[("", "Select...")], validators=[Optional()], validate_choice=False)
    incident_municipality = SelectField("City / Municipality", choices=[("", "Select...")], validators=[Optional()], validate_choice=False)
    self_poisoning_methods = SelectMultipleField("Self-poisoning methods (X60-X69)", choices=[(v, v) for v in options.SELF_POISONING_METHODS], validators=[Optional()])
    self_harm_methods = SelectMultipleField("Self-harm methods (X70-X84)", choices=[(v, v) for v in options.SELF_HARM_METHODS], validators=[Optional()])
    incident_remarks = TextAreaField("Incident remarks", validators=[Optional()])

    previous_consultation = SelectField(
        "With previous consultation with a health professional about previous suicidal thoughts, plans, or attempts?",
        choices=options.YES_NO,
        validators=[DataRequired(REQUIRED_MESSAGE)],
    )
    previous_consultation_notes = TextAreaField("Previous consultation notes", validators=[Optional()])
    family_history = SelectField(
        "Any history of suicide or suicide attempts in the family?",
        choices=options.YES_NO,
        validators=[DataRequired(REQUIRED_MESSAGE)],
    )
    family_history_notes = TextAreaField("Family history notes", validators=[Optional()])
    friends_history = SelectField(
        "Any history of suicide or suicide attempt among friends, schoolmates, or work colleagues?",
        choices=options.YES_NO,
        validators=[DataRequired(REQUIRED_MESSAGE)],
    )
    friends_history_notes = TextAreaField("Friends, schoolmates, or colleagues history notes", validators=[Optional()])
    substance_use = SelectField(
        "Any lifetime history of substance use?",
        choices=options.YES_NO,
        validators=[DataRequired(REQUIRED_MESSAGE)],
    )
    substances = SelectMultipleField("Substances", choices=[(v, v) for v in options.SUBSTANCES])
    alcohol_type = StringField("Alcohol type", validators=[Length(max=150)])
    methamphetamine_type = StringField("Methamphetamine type", validators=[Length(max=150)])
    cannabinoids_type = StringField("Cannabinoids type", validators=[Length(max=150)])
    prescription_drugs_type = StringField("Prescription drugs type", validators=[Length(max=150)])
    substance_notes = TextAreaField("Substance notes", validators=[Optional()])

    primary_diagnosis_code = SelectField(
        "Primary mental health diagnosis, if any",
        choices=[("", "Select ICD-10 F code...")],
        validators=[Optional()],
        validate_choice=False,
    )
    secondary_diagnosis_code = SelectField(
        "Secondary mental health diagnosis, if any",
        choices=[("", "Select ICD-10 F code...")],
        validators=[Optional()],
        validate_choice=False,
    )
    disposition = SelectField("Disposition", choices=options.as_choices(options.DISPOSITIONS), validators=[Optional()])
    disposition_other = StringField("Other disposition", validators=[Length(max=150)])
    diagnosis_remarks = TextAreaField("Diagnosis/disposition remarks", validators=[Optional()])

    submit = SubmitField("Save registry entry")

    def validate_intent(self, field):
        if field.data == "Accidental":
            raise ValidationError("Accidental incidents cannot proceed as valid suicide/self-harm registry cases.")

    def validate_infliction(self, field):
        if field.data == "Inflicted by another":
            raise ValidationError("Incidents inflicted by another person cannot proceed as valid suicide/self-harm registry cases.")

    def validate_substances(self, field):
        if self.substance_use.data == "yes" and not field.data:
            raise ValidationError(REQUIRED_MESSAGE)

    def validate_alcohol_type(self, field):
        _validate_checked_substance(self.substances.data, "Alcohol", field)

    def validate_methamphetamine_type(self, field):
        _validate_checked_substance(self.substances.data, "Methamphetamine", field)

    def validate_cannabinoids_type(self, field):
        _validate_checked_substance(self.substances.data, "Cannabinoids", field)

    def validate_prescription_drugs_type(self, field):
        _validate_checked_substance(self.substances.data, "Prescription drugs", field)

    def validate_type_of_consult_other(self, field):
        _validate_other_pair(self.type_of_consult.data, field)

    def validate_sexual_orientation_other(self, field):
        _validate_other_pair(self.sexual_orientation.data, field)

    def validate_gender_identity_other(self, field):
        _validate_other_pair(self.gender_identity.data, field)

    def validate_religion_other(self, field):
        _validate_other_pair(self.religion.data, field)

    def validate_incident_place_other(self, field):
        _validate_other_pair(self.incident_place.data, field)

    def validate_disposition_other(self, field):
        _validate_other_pair(self.disposition.data, field)


def _validate_other_pair(parent_value, field):
    if (parent_value or "").lower() == "other" and not (field.data or "").strip():
        raise ValidationError(REQUIRED_MESSAGE)


def _validate_checked_substance(selected_substances, substance, field):
    if substance in (selected_substances or []) and not (field.data or "").strip():
        raise ValidationError(REQUIRED_MESSAGE)


class RegistrySearchForm(FlaskForm):
    q = StringField("Search", validators=[Optional(), Length(max=100)])
    reporting_department = SelectField("Department", choices=[("", "All departments")] + options.REPORTING_DEPARTMENTS, validators=[Optional()])
    include_deleted = HiddenField(default="")
    submit = SubmitField("Search")


class DeleteRegistryForm(FlaskForm):
    deleted_remarks = TextAreaField("Deletion remarks", validators=[DataRequired(REQUIRED_MESSAGE), Length(max=255)])
    submit = SubmitField("Delete registry entry")
