from app.analytics.services import filtered_registry_query
from app.services.ml.clustering_service import build_clusters
from app.services.ml.forecasting_service import build_forecast
from app.services.ml.preprocessing_service import build_registry_frame, readiness_summary
from app.services.ml.random_forest_service import build_risk_profile


def build_ml_dashboard(user, filters):
    records = filtered_registry_query(user, filters).all()
    frame = build_registry_frame(records)
    frequency = filters.get("forecast_frequency") or "monthly"

    readiness = readiness_summary(frame)
    risk = build_risk_profile(frame)
    clustering = build_clusters(frame)
    forecasting = build_forecast(records, frequency=frequency)

    return {
        "summary": {
            "records_analyzed": len(records),
            "model_status": risk["status"],
            "cluster_count": clustering["cluster_count"],
            "forecast_periods": len(forecasting["forecast_values"]),
            "forecast_frequency": frequency.title(),
        },
        "readiness": readiness,
        "risk": risk,
        "clustering": clustering,
        "forecasting": forecasting,
        "has_data": bool(records),
        "ethics_note": "For decision support only and not a clinical diagnosis.",
    }

