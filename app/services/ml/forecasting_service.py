from collections import defaultdict
from math import sqrt

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing


INSUFFICIENT_FORECASTING_MESSAGE = "Insufficient time series data for reliable forecasting."


def build_forecast(records, frequency="monthly", periods=6):
    series = _incident_series(records, frequency)
    if len(series) < 4 or series.sum() <= 0:
        return _empty_result(frequency)

    moving_average = series.rolling(window=min(3, len(series)), min_periods=1).mean()
    fitted_values = None
    metrics = {}
    status = "Exponential smoothing"
    try:
        if len(series) >= 8:
            train = series.iloc[:-min(3, max(1, len(series) // 4))]
            test = series.iloc[len(train):]
            fitted_model = _fit_model(train)
            comparison = fitted_model.forecast(len(test)).clip(lower=0)
            metrics = _metrics(test, comparison)
        model = _fit_model(series)
        fitted_values = model.fittedvalues.reindex(series.index).clip(lower=0)
        forecast = model.forecast(periods).clip(lower=0)
    except Exception:
        status = "Moving average baseline"
        baseline = float(series.tail(min(3, len(series))).mean())
        fitted_values = moving_average
        forecast = pd.Series([baseline] * periods, index=_future_index(series, frequency, periods))
        if len(series) >= 5:
            metrics = _metrics(series.iloc[1:], moving_average.iloc[:-1].reindex(series.index[1:]).fillna(baseline))

    forecast_index = forecast.index if hasattr(forecast, "index") else _future_index(series, frequency, periods)
    residual_std = float((series - fitted_values).std()) if fitted_values is not None and len(series) > 1 else 0
    lower = [max(0, round(float(value - 1.96 * residual_std), 2)) for value in forecast]
    upper = [round(float(value + 1.96 * residual_std), 2) for value in forecast]

    seasonal = _seasonal_patterns(records)
    return {
        "status": status,
        "is_available": True,
        "note": "Forecasts estimate incident volume from historical registry patterns and should be interpreted as planning signals.",
        "frequency": frequency,
        "observed_labels": [_label(index, frequency) for index in series.index],
        "observed_values": [int(value) for value in series.values],
        "moving_average_values": [round(float(value), 2) for value in moving_average.values],
        "fitted_values": [round(float(value), 2) for value in fitted_values.values],
        "forecast_labels": [_label(index, frequency) for index in forecast_index],
        "forecast_values": [round(float(value), 2) for value in forecast],
        "confidence_interval": {"lower": lower, "upper": upper},
        "metrics": metrics,
        "seasonal_patterns": seasonal,
    }


def _incident_series(records, frequency):
    counts = defaultdict(int)
    for registry in records:
        incidents = list(registry.incidents or [])
        if not incidents and registry.date_of_presentation:
            counts[pd.Timestamp(registry.date_of_presentation)] += 1
        for incident in incidents:
            date_value = incident.incident_date or registry.date_of_presentation
            if date_value:
                counts[pd.Timestamp(date_value)] += 1
    if not counts:
        return pd.Series(dtype=float)

    freq = "W-MON" if frequency == "weekly" else "MS"
    raw = pd.Series(counts).sort_index()
    start = raw.index.min().to_period("W" if frequency == "weekly" else "M").start_time
    end = raw.index.max().to_period("W" if frequency == "weekly" else "M").start_time
    index = pd.date_range(start, end, freq=freq)
    return raw.resample(freq).sum().reindex(index, fill_value=0).astype(float)


def _fit_model(series):
    return ExponentialSmoothing(series, trend="add", seasonal=None, initialization_method="estimated").fit(optimized=True)


def _future_index(series, frequency, periods):
    freq = "W-MON" if frequency == "weekly" else "MS"
    return pd.date_range(series.index.max() + pd.tseries.frequencies.to_offset(freq), periods=periods, freq=freq)


def _metrics(actual, forecast):
    actual_values = np.asarray(actual, dtype=float)
    forecast_values = np.asarray(forecast, dtype=float)
    mae = mean_absolute_error(actual_values, forecast_values)
    rmse = sqrt(mean_squared_error(actual_values, forecast_values))
    nonzero = actual_values != 0
    mape = float(np.mean(np.abs((actual_values[nonzero] - forecast_values[nonzero]) / actual_values[nonzero])) * 100) if nonzero.any() else None
    return {
        "mae": round(float(mae), 3),
        "rmse": round(float(rmse), 3),
        "mape": round(mape, 3) if mape is not None else None,
    }


def _seasonal_patterns(records):
    counts = defaultdict(int)
    for registry in records:
        for incident in list(registry.incidents or []):
            date_value = incident.incident_date or registry.date_of_presentation
            if date_value:
                counts[date_value.strftime("%B")] += 1
        if not registry.incidents and registry.date_of_presentation:
            counts[registry.date_of_presentation.strftime("%B")] += 1
    month_order = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    return {"labels": month_order, "values": [counts[month] for month in month_order]}


def _label(index, frequency):
    return index.strftime("%Y-W%W") if frequency == "weekly" else index.strftime("%Y-%m")


def _empty_result(frequency):
    return {
        "status": "Needs more incident dates",
        "is_available": False,
        "note": INSUFFICIENT_FORECASTING_MESSAGE,
        "frequency": frequency,
        "observed_labels": [],
        "observed_values": [],
        "moving_average_values": [],
        "fitted_values": [],
        "forecast_labels": [],
        "forecast_values": [],
        "confidence_interval": {"lower": [], "upper": []},
        "metrics": {},
        "seasonal_patterns": {"labels": [], "values": []},
    }

