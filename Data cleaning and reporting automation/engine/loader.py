import os
import pandas as pd
import numpy as np

def load_dataset(file_path):
    """
    Safely loads a CSV or Excel dataset into a pandas DataFrame.
    Handles encoding issues and delimiter detection automatically.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif ext == '.csv':
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        delimiters = [',', ';', '\t', '|']
        
        df = None
        last_exception = None

        for encoding in encodings:
            for sep in delimiters:
                try:
                    temp_df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                    # Check if parsing resulted in more than 1 column or reasonable structure
                    if temp_df.shape[1] > 1 or len(delimiters) == 1:
                        df = temp_df
                        break
                except Exception as e:
                    last_exception = e
                    continue
            if df is not None:
                break

        if df is None:
            # Fallback to pandas default read_csv
            try:
                df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
            except Exception as e:
                raise ValueError(f"Could not parse CSV file: {str(e) if not last_exception else str(last_exception)}")
    else:
        raise ValueError(f"Unsupported file format: {ext}. Only CSV and Excel (.xlsx, .xls) are supported.")

    # Convert object columns containing whitespace-only strings to NaN
    df = replace_sentinels_with_nan(df)
    return df

def replace_sentinels_with_nan(df):
    """
    Standardizes typical sentinel missing value representations ('N/A', 'null', 'None', '?', 'NA', '') into np.nan.
    """
    sentinels = ['N/A', 'n/a', 'NA', 'na', 'NULL', 'null', 'None', 'none', '?', '-', 'NaN', 'nan', '']
    df_clean = df.copy()
    
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            # Strip string whitespace first for checking
            df_clean[col] = df_clean[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            df_clean[col] = df_clean[col].replace(sentinels, np.nan)
            # If string is empty whitespace
            df_clean[col] = df_clean[col].apply(lambda x: np.nan if isinstance(x, str) and not x.strip() else x)

    return df_clean
