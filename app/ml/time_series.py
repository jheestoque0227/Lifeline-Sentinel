import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def forecast_monthly_incidents(monthly_series: pd.Series, periods=6):
    model = ExponentialSmoothing(
        monthly_series,
        trend="add",
        seasonal=None,
        initialization_method="estimated"
    )
    fitted = model.fit()
    forecast = fitted.forecast(periods)
    return forecast
