from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib

def train_kmeans(X, n_clusters=3, model_path="trained_models/kmeans_cluster_model.joblib"):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = model.fit_predict(X_scaled)

    joblib.dump({"model": model, "scaler": scaler}, model_path)
    return clusters
