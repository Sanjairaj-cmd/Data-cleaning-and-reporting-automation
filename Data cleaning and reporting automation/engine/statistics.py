import pandas as pd
import numpy as np

def compute_summary_statistics(df):
    """
    Computes comprehensive column-by-column statistics for numeric and categorical fields.
    """
    stats_list = []
    
    for col in df.columns:
        series = df[col]
        missing_count = int(series.isnull().sum())
        total_count = len(series)
        unique_count = int(series.nunique(dropna=True))
        dtype_str = str(series.dtype)

        col_stat = {
            'column': col,
            'dtype': dtype_str,
            'count': total_count,
            'non_null_count': total_count - missing_count,
            'missing_count': missing_count,
            'missing_pct': round((missing_count / total_count * 100), 2) if total_count > 0 else 0.0,
            'unique_count': unique_count,
        }

        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if len(non_null) > 0:
                col_stat.update({
                    'type_category': 'numeric',
                    'mean': float(round(non_null.mean(), 4)),
                    'std': float(round(non_null.std(), 4)) if len(non_null) > 1 else 0.0,
                    'min': float(round(non_null.min(), 4)),
                    'q25': float(round(non_null.quantile(0.25), 4)),
                    'median': float(round(non_null.median(), 4)),
                    'q75': float(round(non_null.quantile(0.75), 4)),
                    'max': float(round(non_null.max(), 4)),
                    'skewness': float(round(non_null.skew(), 4)) if len(non_null) > 2 else 0.0,
                })
            else:
                col_stat.update({'type_category': 'numeric', 'mean': None, 'std': None, 'min': None, 'median': None, 'max': None})
        else:
            non_null = series.dropna()
            top_val = str(non_null.mode()[0]) if len(non_null) > 0 else 'N/A'
            top_freq = int((non_null == top_val).sum()) if len(non_null) > 0 else 0
            col_stat.update({
                'type_category': 'categorical/text',
                'top_value': top_val,
                'top_frequency': top_freq,
                'top_frequency_pct': round((top_freq / len(non_null) * 100), 2) if len(non_null) > 0 else 0.0
            })

        stats_list.append(col_stat)

    return stats_list


def compute_correlation_matrix(df):
    """
    Computes correlation matrix for numerical columns in JSON serializable format.
    """
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) < 2:
        return {'columns': [], 'matrix': []}

    corr_df = df[num_cols].corr().fillna(0).round(3)
    
    return {
        'columns': num_cols,
        'matrix': corr_df.values.tolist()
    }


def get_column_distribution(df, column_name):
    """
    Extracts distribution data for a specific column for interactive charts.
    """
    if column_name not in df.columns:
        return None

    series = df[column_name].dropna()
    is_num = pd.api.types.is_numeric_dtype(series)

    if is_num:
        return {
            'column': column_name,
            'type': 'numeric',
            'values': series.tolist()[:1000]  # sample up to 1000 items
        }
    else:
        val_counts = series.value_counts().head(15).to_dict()
        return {
            'column': column_name,
            'type': 'categorical',
            'categories': list(val_counts.keys()),
            'counts': list(val_counts.values())
        }
