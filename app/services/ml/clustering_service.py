from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from app.services.ml.preprocessing_service import clustering_features, describe_cluster, encoded_frame


INSUFFICIENT_CLUSTERING_MESSAGE = "Insufficient data for meaningful clustering."


def build_clusters(frame):
    if frame.empty or len(frame) < 6:
        return _empty_result()

    feature_columns = clustering_features(frame)
    encoded = encoded_frame(frame, feature_columns)
    if encoded.empty or len(frame) < 6:
        return _empty_result()

    scaled = StandardScaler().fit_transform(encoded)
    cluster_count, diagnostics = _choose_cluster_count(scaled, len(frame))
    if cluster_count < 2:
        return _empty_result(diagnostics=diagnostics)

    model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    clusters = model.fit_predict(scaled)
    clustered = frame.copy()
    clustered["cluster"] = clusters

    profiles = []
    distribution = {}
    for cluster_id, group in clustered.groupby("cluster"):
        label, characteristics = describe_cluster(group)
        cluster_label = f"Cluster {cluster_id + 1}: {label}"
        distribution[cluster_label] = int(len(group))
        profiles.append(
            {
                "label": cluster_label,
                "count": int(len(group)),
                "median_age": round(float(group["age"].median()), 1),
                "top_sex": _mode(group["sex"]),
                "top_method_signal": _mode(group["incident_method"]),
                "top_location": _mode(group["incident_location"]),
                "substance_use_rate": _percent((group["substance_use"] == "Yes").sum(), len(group)),
                "repeated_rate": _percent((group["previous_repeated_incidents"] == "Repeated").sum(), len(group)),
                "characteristics": characteristics,
            }
        )

    return {
        "status": "K-Means",
        "is_available": True,
        "note": "Clusters describe observed behavioral and demographic patterns only; they are not clinical diagnoses.",
        "cluster_count": int(cluster_count),
        "distribution": distribution,
        "profiles": profiles,
        "diagnostics": diagnostics,
    }


def _choose_cluster_count(scaled, sample_count):
    max_clusters = min(6, sample_count - 1)
    if max_clusters < 2:
        return 0, {"method": "not_enough_records", "scores": []}

    scores = []
    best_k = 2
    best_score = -1
    for k in range(2, max_clusters + 1):
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(scaled)
        inertia = float(model.inertia_)
        score = None
        if len(set(labels)) > 1 and len(set(labels)) < sample_count:
            score = float(silhouette_score(scaled, labels))
            if score > best_score:
                best_score = score
                best_k = k
        scores.append({"k": k, "inertia": round(inertia, 3), "silhouette": round(score, 3) if score is not None else None})
    return best_k, {"method": "silhouette_with_elbow_diagnostics", "scores": scores}


def _empty_result(diagnostics=None):
    return {
        "status": "Needs more data",
        "is_available": False,
        "note": INSUFFICIENT_CLUSTERING_MESSAGE,
        "cluster_count": 0,
        "distribution": {},
        "profiles": [],
        "diagnostics": diagnostics or {"method": "not_enough_records", "scores": []},
    }


def _mode(values):
    modes = values.dropna().astype(str).mode()
    return modes.iloc[0] if not modes.empty else "Unspecified"


def _percent(numerator, denominator):
    if not denominator:
        return "0%"
    return f"{round(float(numerator) / float(denominator) * 100)}%"

