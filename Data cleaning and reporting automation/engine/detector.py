import pandas as pd
import numpy as np
from scipy import stats

def analyze_dataset_quality(df):
    """
    Comprehensive Data Quality Analysis & Issue Detection.
    Returns structured JSON-serializable dictionary with issues, metrics, and Data Quality Score.
    """
    total_rows, total_cols = df.shape
    total_cells = total_rows * total_cols

    # 1. Missing Values Detection
    missing_by_col = df.isnull().sum().to_dict()
    missing_pct_by_col = (df.isnull().sum() / total_rows * 100).round(2).to_dict()
    total_missing_cells = int(df.isnull().sum().sum())
    missing_cells_pct = round((total_missing_cells / total_cells * 100), 2) if total_cells > 0 else 0.0

    cols_with_missing = {k: v for k, v in missing_by_col.items() if v > 0}

    # 2. Duplicate Rows Detection
    duplicate_rows_count = int(df.duplicated().sum())
    duplicate_pct = round((duplicate_rows_count / total_rows * 100), 2) if total_rows > 0 else 0.0

    # 3. Data Type Analysis & Type Mismatches / Inferences
    col_dtypes = {}
    type_inferences = {}
    
    for col in df.columns:
        curr_type = str(df[col].dtype)
        col_dtypes[col] = curr_type
        
        non_null_series = df[col].dropna()
        if len(non_null_series) == 0:
            continue

        # Check if object/string column can be converted to numeric
        if curr_type == 'object':
            # Check numeric conversion
            numeric_converted = pd.to_numeric(non_null_series, errors='coerce')
            valid_num_count = numeric_converted.notnull().sum()
            if valid_num_count / len(non_null_series) > 0.7:  # >70% numeric values
                type_inferences[col] = {
                    'current_type': curr_type,
                    'suggested_type': 'numeric (int/float)',
                    'reason': f"{valid_num_count}/{len(non_null_series)} non-null values appear numeric.",
                    'invalid_count': int(len(non_null_series) - valid_num_count)
                }
                continue

            # Check datetime conversion
            try:
                date_converted = pd.to_datetime(non_null_series, errors='coerce', format='mixed')
                valid_date_count = date_converted.notnull().sum()
                if valid_date_count / len(non_null_series) > 0.7 and non_null_series.dtype == 'object':
                    # Avoid treating pure short numbers as dates
                    if not non_null_series.astype(str).str.isnumeric().all():
                        type_inferences[col] = {
                            'current_type': curr_type,
                            'suggested_type': 'datetime',
                            'reason': f"{valid_date_count}/{len(non_null_series)} values match datetime format.",
                            'invalid_count': int(len(non_null_series) - valid_date_count)
                        }
            except Exception:
                pass

    # 4. Invalid Values Detection
    invalid_value_issues = []
    
    for col in df.columns:
        series = df[col]
        # Whitespace issues in string columns
        if series.dtype == 'object':
            string_vals = series.dropna().astype(str)
            unstripped = string_vals[string_vals != string_vals.str.strip()]
            if len(unstripped) > 0:
                invalid_value_issues.append({
                    'column': col,
                    'issue_type': 'whitespace_padding',
                    'count': int(len(unstripped)),
                    'description': f"{len(unstripped)} values contain leading/trailing whitespace."
                })

        # Negative values in numeric columns where all non-negative is expected (heuristics based on col name or overwhelmingly positive numbers)
        if pd.api.types.is_numeric_dtype(series):
            num_series = series.dropna()
            neg_count = (num_series < 0).sum()
            pos_count = (num_series > 0).sum()
            if neg_count > 0 and pos_count > (neg_count * 5):
                invalid_value_issues.append({
                    'column': col,
                    'issue_type': 'unexpected_negative_value',
                    'count': int(neg_count),
                    'description': f"{neg_count} negative value(s) found in predominantly positive column."
                })

    # 5. Outliers Detection (IQR and Z-Score)
    outliers_by_col = {}
    total_outlier_count = 0

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 5:
            continue

        # IQR Method
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        iqr_outliers = series[(series < lower_bound) | (series > upper_bound)]

        # Z-Score Method
        z_scores = np.abs(stats.zscore(series)) if len(series) > 1 and series.std() > 0 else np.zeros(len(series))
        z_outliers_count = int((z_scores > 3).sum())

        outlier_count = int(len(iqr_outliers))
        if outlier_count > 0:
            total_outlier_count += outlier_count
            outliers_by_col[col] = {
                'count': outlier_count,
                'pct': round((outlier_count / len(series)) * 100, 2),
                'lower_bound': float(round(lower_bound, 4)),
                'upper_bound': float(round(upper_bound, 4)),
                'z_score_outlier_count': z_outliers_count,
                'sample_values': iqr_outliers.head(5).tolist()
            }

    # 6. Data Quality Score Calculation (0 - 100%)
    # Metrics Weights:
    # - Completeness (35%): ratio of non-missing cells
    # - Uniqueness (25%): ratio of non-duplicate rows
    # - Validity & Data Types (25%): penalty for type mismatch & invalid values
    # - Consistency / Outlier Health (15%): penalty for extreme outliers

    completeness_score = max(0, 100 - missing_cells_pct)
    uniqueness_score = max(0, 100 - duplicate_pct)

    # Validity score penalty
    total_invalid_issues_count = sum(item['count'] for item in invalid_value_issues)
    type_mismatch_count = sum(item.get('invalid_count', 1) for item in type_inferences.values())
    validity_penalty = min(50, ((total_invalid_issues_count + type_mismatch_count) / total_rows) * 100) if total_rows > 0 else 0
    validity_score = max(0, 100 - validity_penalty)

    # Outlier health score
    outlier_pct = (total_outlier_count / (total_rows * max(1, len(numeric_cols)))) * 100 if total_rows > 0 else 0
    outlier_score = max(0, 100 - (outlier_pct * 3))

    quality_score = round(
        (completeness_score * 0.35) +
        (uniqueness_score * 0.25) +
        (validity_score * 0.25) +
        (outlier_score * 0.15),
        1
    )
    quality_score = max(0.0, min(100.0, quality_score))

    # Grade determination
    if quality_score >= 90:
        grade = 'A (Excellent)'
    elif quality_score >= 75:
        grade = 'B (Good)'
    elif quality_score >= 60:
        grade = 'C (Fair)'
    elif quality_score >= 40:
        grade = 'D (Poor)'
    else:
        grade = 'F (Critical Action Needed)'

    return {
        'summary': {
            'total_rows': total_rows,
            'total_cols': total_cols,
            'total_cells': total_cells,
            'quality_score': quality_score,
            'grade': grade,
            'completeness_score': round(completeness_score, 1),
            'uniqueness_score': round(uniqueness_score, 1),
            'validity_score': round(validity_score, 1),
            'outlier_score': round(outlier_score, 1),
        },
        'missing_values': {
            'total_missing_cells': total_missing_cells,
            'missing_cells_pct': missing_cells_pct,
            'cols_with_missing': cols_with_missing,
            'missing_pct_by_col': missing_pct_by_col
        },
        'duplicates': {
            'duplicate_rows_count': duplicate_rows_count,
            'duplicate_pct': duplicate_pct
        },
        'type_inferences': type_inferences,
        'col_dtypes': col_dtypes,
        'invalid_values': invalid_value_issues,
        'outliers': {
            'total_outlier_count': total_outlier_count,
            'by_column': outliers_by_col
        }
    }
