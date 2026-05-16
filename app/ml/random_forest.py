from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

def train_random_forest(X, y, model_path="trained_models/random_forest_risk_model.joblib"):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, average="weighted", zero_division=0),
        "recall": recall_score(y_test, predictions, average="weighted", zero_division=0),
        "f1_score": f1_score(y_test, predictions, average="weighted", zero_division=0),
    }

    joblib.dump(model, model_path)
    return model, metrics
