def as_choices(values):
    return [("", "Select...")] + [(value, value) for value in values]


REPORTING_DEPARTMENTS = [("ER", "Emergency Room"), ("OPS", "Outpatient Service")]
INTENTS = [("Intentional", "Intentional"), ("Accidental", "Accidental")]
INFLICTIONS = [("Self-inflicted", "Self-inflicted"), ("Inflicted by another", "Inflicted by another")]
TYPE_OF_CONSULTS = ["Initial consult", "Follow-up consult", "Referral", "Other"]
SEX_AT_BIRTH = ["Female", "Male", "Intersex", "Unknown"]
SEXUAL_ORIENTATIONS = ["Heterosexual", "Gay", "Lesbian", "Bisexual", "Asexual", "Prefer not to say", "Other"]
GENDER_IDENTITIES = ["Woman", "Man", "Transgender woman", "Transgender man", "Non-binary", "Prefer not to say", "Other"]
MARITAL_STATUSES = ["Single", "Married", "Separated", "Widowed", "Annulled", "Live-in partner"]
EDUCATIONAL_ATTAINMENTS = [
    "No formal education",
    "Elementary",
    "High school",
    "Vocational",
    "College",
    "Postgraduate",
]
EMPLOYMENT_STATUSES = ["Employed", "Unemployed", "Student", "Homemaker", "Retired", "Self-employed"]
RELIGIONS = ["Roman Catholic", "Islam", "Iglesia ni Cristo", "Protestant", "None", "Other"]
YES_NO = [("", "Select..."), ("yes", "Yes"), ("no", "No")]
INCIDENT_TIME_PERIODS = ["Morning", "Afternoon", "Evening", "Night", "Unknown"]
INCIDENT_PLACES = ["Home", "School", "Workplace", "Public place", "Health facility", "Other"]
SELF_POISONING_METHODS = [
    "X60 Nonopioid analgesics",
    "X61 Antiepileptic, sedative-hypnotic, antiparkinsonism and psychotropic drugs",
    "X62 Narcotics and psychodysleptics",
    "X63 Other drugs acting on the autonomic nervous system",
    "X64 Other and unspecified drugs",
    "X65 Alcohol",
    "X66 Organic solvents and halogenated hydrocarbons",
    "X67 Other gases and vapours",
    "X68 Pesticides",
    "X69 Other and unspecified chemicals",
]
SELF_HARM_METHODS = [
    "X70 Hanging, strangulation and suffocation",
    "X71 Drowning and submersion",
    "X72 Handgun discharge",
    "X73 Rifle, shotgun and larger firearm discharge",
    "X74 Other and unspecified firearm discharge",
    "X75 Explosive material",
    "X76 Smoke, fire and flames",
    "X77 Steam, hot vapours and hot objects",
    "X78 Sharp object",
    "X79 Blunt object",
    "X80 Jumping from a high place",
    "X81 Lying before or jumping before moving object",
    "X82 Crashing of motor vehicle",
    "X83 Other specified means",
    "X84 Unspecified means",
]
SUBSTANCES = ["Alcohol", "Methamphetamine", "Cannabinoids", "Prescription drugs"]
MENTAL_HEALTH_ICD10_CODES = [(f"F{code:02d}", f"F{code:02d}") for code in range(0, 100)]
DISPOSITIONS = [
    "Sent home",
    "Admitted to hospital",
    "Died",
    "Abscond",
    "Discharged against medical advice",
    "Transfer to another facility",
    "Other",
]
RISK_LEVELS = [("Low", "Low"), ("Moderate", "Moderate"), ("High", "High")]
