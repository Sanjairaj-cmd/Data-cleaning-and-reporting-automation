import pandas as pd
import numpy as np

def auto_clean_dataset(df):
    """
    Applies automatic full dataset cleaning rules.
    Returns: (cleaned_df, actions_performed_list)
    """
    cleaned_df = df.copy()
    actions = []

    # 1. Remove duplicate rows
    initial_rows = len(cleaned_df)
    dup_count = cleaned_df.duplicated().sum()
    if dup_count > 0:
        cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)
        actions.append(f"Removed {dup_count} duplicate row(s).")

    # 2. Trim whitespace & standardize empty strings
    string_cols = cleaned_df.select_dtypes(include=['object', 'string']).columns
    for col in string_cols:
        cleaned_df[col] = cleaned_df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        cleaned_df[col] = cleaned_df[col].replace(['', 'N/A', 'n/a', 'NA', 'na', 'NULL', 'null', 'None', 'none', '?'], np.nan)
    if len(string_cols) > 0:
        actions.append(f"Trimmed leading/trailing whitespace across {len(string_cols)} string column(s).")

    # 3. Detect and fix data types
    for col in cleaned_df.columns:
        if cleaned_df[col].dtype == 'object' or str(cleaned_df[col].dtype).startswith('string'):
            non_null = cleaned_df[col].dropna()
            if len(non_null) == 0:
                continue
            
            # Try numeric
            num_series = pd.to_numeric(non_null, errors='coerce')
            if num_series.notnull().sum() / len(non_null) > 0.8:
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                actions.append(f"Converted column '{col}' from string to numeric.")
                continue

            # Try datetime
            try:
                if not non_null.astype(str).str.isnumeric().all():
                    date_series = pd.to_datetime(non_null, errors='coerce', format='mixed')
                    if date_series.notnull().sum() / len(non_null) > 0.8:
                        cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce', format='mixed')
                        actions.append(f"Converted column '{col}' to datetime format.")
            except Exception:
                pass

    # 4. Handle invalid negative values in numeric columns (where positive expected)
    num_cols = cleaned_df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        series = cleaned_df[col].dropna()
        neg_count = (series < 0).sum()
        pos_count = (series > 0).sum()
        if neg_count > 0 and pos_count > neg_count * 5:
            cleaned_df[col] = cleaned_df[col].apply(lambda x: abs(x) if pd.notnull(x) and x < 0 else x)
            actions.append(f"Converted {neg_count} negative value(s) in column '{col}' to positive values.")

    # 5. Handle missing values
    for col in cleaned_df.columns:
        missing_cnt = cleaned_df[col].isnull().sum()
        if missing_cnt > 0:
            if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                median_val = cleaned_df[col].median()
                cleaned_df[col] = cleaned_df[col].fillna(median_val)
                actions.append(f"Imputed {missing_cnt} missing value(s) in numeric column '{col}' with median ({round(median_val, 2)}).")
            else:
                mode_res = cleaned_df[col].mode()
                mode_val = mode_res[0] if len(mode_res) > 0 else 'Unknown'
                cleaned_df[col] = cleaned_df[col].fillna(mode_val)
                actions.append(f"Imputed {missing_cnt} missing value(s) in categorical column '{col}' with mode ('{mode_val}').")

    # 6. Outlier Handling (Clip outliers to IQR 1.5 bounds)
    for col in num_cols:
        series = cleaned_df[col].dropna()
        if len(series) < 5:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        
        outliers_count = ((cleaned_df[col] < lower) | (cleaned_df[col] > upper)).sum()
        if outliers_count > 0:
            cleaned_df[col] = cleaned_df[col].clip(lower=lower, upper=upper)
            actions.append(f"Clipped {outliers_count} outlier(s) in column '{col}' to IQR bounds [{round(lower, 2)}, {round(upper, 2)}].")

    return cleaned_df, actions


def custom_clean_dataset(df, rules):
    """
    Applies custom user-specified cleaning configuration rules.
    """
    cleaned_df = df.copy()
    actions = []

    # 1. Columns to drop
    cols_to_drop = rules.get('columns_to_drop', [])
    if cols_to_drop:
        existing_to_drop = [c for c in cols_to_drop if c in cleaned_df.columns]
        if existing_to_drop:
            cleaned_df = cleaned_df.drop(columns=existing_to_drop)
            actions.append(f"Dropped {len(existing_to_drop)} column(s): {', '.join(existing_to_drop)}.")

    # 2. Duplicate Removal
    if rules.get('remove_duplicates', False):
        dup_count = cleaned_df.duplicated().sum()
        if dup_count > 0:
            cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)
            actions.append(f"Removed {dup_count} duplicate row(s).")

    # 3. Trim Whitespace & Casing
    if rules.get('trim_whitespace', True):
        string_cols = cleaned_df.select_dtypes(include=['object', 'string']).columns
        casing = rules.get('text_casing', 'none')
        for col in string_cols:
            if casing == 'lower':
                cleaned_df[col] = cleaned_df[col].apply(lambda x: x.lower().strip() if isinstance(x, str) else x)
            elif casing == 'upper':
                cleaned_df[col] = cleaned_df[col].apply(lambda x: x.upper().strip() if isinstance(x, str) else x)
            elif casing == 'title':
                cleaned_df[col] = cleaned_df[col].apply(lambda x: x.title().strip() if isinstance(x, str) else x)
            else:
                cleaned_df[col] = cleaned_df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        if len(string_cols) > 0:
            actions.append(f"Standardized text formatting and whitespace across {len(string_cols)} text column(s).")

    # 4. Type Conversions
    type_conversions = rules.get('type_conversions', {})
    for col, target_type in type_conversions.items():
        if col in cleaned_df.columns:
            try:
                if target_type == 'numeric':
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                    actions.append(f"Converted column '{col}' to numeric.")
                elif target_type == 'datetime':
                    cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce', format='mixed')
                    actions.append(f"Converted column '{col}' to datetime.")
                elif target_type == 'string':
                    cleaned_df[col] = cleaned_df[col].astype(str)
                    actions.append(f"Converted column '{col}' to string.")
                elif target_type == 'category':
                    cleaned_df[col] = cleaned_df[col].astype('category')
                    actions.append(f"Converted column '{col}' to categorical.")
            except Exception as e:
                actions.append(f"Failed to convert column '{col}' to {target_type}: {str(e)}")

    # 5. Missing Value Rules
    missing_rules = rules.get('missing_value_rules', {})
    for col, rule in missing_rules.items():
        if col not in cleaned_df.columns:
            continue
        strategy = rule.get('strategy', 'none')
        missing_cnt = cleaned_df[col].isnull().sum()
        if missing_cnt == 0 or strategy == 'none':
            continue

        if strategy == 'drop_row':
            cleaned_df = cleaned_df.dropna(subset=[col]).reset_index(drop=True)
            actions.append(f"Dropped {missing_cnt} row(s) with missing values in column '{col}'.")
        elif strategy == 'mean' and pd.api.types.is_numeric_dtype(cleaned_df[col]):
            mean_val = cleaned_df[col].mean()
            cleaned_df[col] = cleaned_df[col].fillna(mean_val)
            actions.append(f"Imputed missing values in '{col}' with mean ({round(mean_val, 2)}).")
        elif strategy == 'median' and pd.api.types.is_numeric_dtype(cleaned_df[col]):
            med_val = cleaned_df[col].median()
            cleaned_df[col] = cleaned_df[col].fillna(med_val)
            actions.append(f"Imputed missing values in '{col}' with median ({round(med_val, 2)}).")
        elif strategy == 'mode':
            mode_res = cleaned_df[col].mode()
            mode_val = mode_res[0] if len(mode_res) > 0 else 'Unknown'
            cleaned_df[col] = cleaned_df[col].fillna(mode_val)
            actions.append(f"Imputed missing values in '{col}' with mode ('{mode_val}').")
        elif strategy == 'fill':
            fill_val = rule.get('fill_value', 'N/A')
            cleaned_df[col] = cleaned_df[col].fillna(fill_val)
            actions.append(f"Filled missing values in '{col}' with constant '{fill_val}'.")
        elif strategy == 'ffill':
            cleaned_df[col] = cleaned_df[col].ffill()
            actions.append(f"Forward filled missing values in '{col}'.")

    # 6. Outlier Handling Rules
    outlier_rules = rules.get('outlier_rules', {})
    for col, rule in outlier_rules.items():
        if col not in cleaned_df.columns or not pd.api.types.is_numeric_dtype(cleaned_df[col]):
            continue
        strategy = rule.get('strategy', 'none')
        if strategy == 'none':
            continue

        series = cleaned_df[col].dropna()
        if len(series) < 5:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outlier_mask = (cleaned_df[col] < lower) | (cleaned_df[col] > upper)
        outlier_count = outlier_mask.sum()
        
        if outlier_count > 0:
            if strategy == 'clip':
                cleaned_df[col] = cleaned_df[col].clip(lower=lower, upper=upper)
                actions.append(f"Clipped {outlier_count} outlier(s) in '{col}' to bounds [{round(lower,2)}, {round(upper,2)}].")
            elif strategy == 'drop':
                cleaned_df = cleaned_df[~outlier_mask].reset_index(drop=True)
                actions.append(f"Dropped {outlier_count} outlier row(s) based on column '{col}'.")
            elif strategy == 'median':
                med_val = series.median()
                cleaned_df.loc[outlier_mask, col] = med_val
                actions.append(f"Replaced {outlier_count} outlier(s) in '{col}' with median ({round(med_val, 2)}).")

    return cleaned_df, actions
