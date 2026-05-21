import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from app.services.ml.preprocessing_service import (
    RISK_LABELS,
    classification_features,
    encoded_frame,
    risk_profile_rows,
)


INSUFFICIENT_RISK_MESSAGE = "Insufficient labeled data for reliable risk profiling."


def build_risk_profile(frame):
    distribution = _empty_distribution()
    if frame.empty:
        return _empty_result("No registry records match the selected filters.")

    feature_columns = classification_features(frame)
    if "risk_label" not in frame.columns or not feature_columns:
        return _empty_result(INSUFFICIENT_RISK_MESSAGE)

    labeled = frame[frame["risk_label"].isin(RISK_LABELS)].copy()
    distribution.update(labeled["risk_label"].value_counts().reindex(RISK_LABELS, fill_value=0).to_dict())
    if len(labeled) < 8 or labeled["risk_label"].nunique() < 2 or labeled["risk_label"].value_counts().min() < 2:
        return {
            **_empty_result(INSUFFICIENT_RISK_MESSAGE),
            "distribution": distribution,
            "profile_rows": risk_profile_rows(labeled),
            "label_source": "Derived from historical registry patterns",
        }

    encoded = encoded_frame(labeled, feature_columns)
    if encoded.empty:
        return _empty_result(INSUFFICIENT_RISK_MESSAGE)

    model = RandomForestClassifier(n_estimators=250, random_state=42, class_weight="balanced", min_samples_leaf=1)
    can_test = len(labeled) >= 12 and labeled["risk_label"].value_counts().min() >= 3
    metrics = {}
    confusion = {}
    if can_test:
        x_train, x_test, y_train, y_test = train_test_split(
            encoded,
            labeled["risk_label"],
            test_size=0.25,
            random_state=42,
            stratify=labeled["risk_label"],
        )
        model.fit(x_train, y_train)
        test_predictions = model.predict(x_test)
        metrics = {
            "accuracy": _round(accuracy_score(y_test, test_predictions)),
            "precision": _round(precision_score(y_test, test_predictions, average="weighted", zero_division=0)),
            "recall": _round(recall_score(y_test, test_predictions, average="weighted", zero_division=0)),
            "f1_score": _round(f1_score(y_test, test_predictions, average="weighted", zero_division=0)),
        }
        matrix = confusion_matrix(y_test, test_predictions, labels=RISK_LABELS)
        confusion = {"labels": RISK_LABELS, "matrix": matrix.astype(int).tolist()}
    else:
        model.fit(encoded, labeled["risk_label"])
        metrics = {"training_records": int(len(labeled)), "evaluation_note": "Held-out test data is not large enough for reliable metrics."}

    predictions = pd.Series(model.predict(encoded), index=labeled.index)
    probabilities = _probability_scores(model, encoded, labeled.index)
    predicted_distribution = predictions.value_counts().reindex(RISK_LABELS, fill_value=0).to_dict()
    importances = sorted(zip(encoded.columns, model.feature_importances_), key=lambda item: item[1], reverse=True)[:12]

    return {
        "status": "Random Forest",
        "is_available": True,
        "note": "Estimated risk profiles are based on historical registry patterns for decision support only and are not a clinical diagnosis.",
        "label_source": "Derived from historical registry patterns",
        "metrics": metrics,
        "confusion_matrix": confusion,
        "distribution": predicted_distribution,
        "feature_importance": [{"label": _clean_feature_label(label), "value": _round(value, 4)} for label, value in importances],
        "profile_rows": risk_profile_rows(labeled, predictions, probabilities),
    }


def _probability_scores(model, encoded, indexes):
    classes = list(model.classes_)
    probabilities = model.predict_proba(encoded)
    scores = {}
    for row_index, row_probability in zip(indexes, probabilities):
        scores[row_index] = _round(max(row_probability))
    return scores


def _empty_result(note):
    return {
        "status": "Needs more labeled data",
        "is_available": False,
        "note": note,
        "label_source": None,
        "metrics": {},
        "confusion_matrix": {},
        "distribution": _empty_distribution(),
        "feature_importance": [],
        "profile_rows": [],
    }


def _empty_distribution():
    return {label: 0 for label in RISK_LABELS}


def _round(value, places=3):
    return round(float(value), places)


def _clean_feature_label(label):
    return str(label).replace("_", " ").replace("=", " ").strip().title()

