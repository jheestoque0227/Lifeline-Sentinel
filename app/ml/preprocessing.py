import pandas as pd

def clean_registry_dataset(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned = cleaned.drop_duplicates()
    return cleaned
