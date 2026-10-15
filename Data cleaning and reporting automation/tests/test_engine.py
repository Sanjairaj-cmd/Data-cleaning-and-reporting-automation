import os
import sys
import pandas as pd

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.loader import load_dataset
from engine.detector import analyze_dataset_quality
from engine.cleaner import auto_clean_dataset, custom_clean_dataset
from engine.statistics import compute_summary_statistics, compute_correlation_matrix
from engine.pdf_generator import generate_pdf_report
from database import init_db, save_history_record, get_all_history

def test_full_pipeline():
    sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../samples/sample_customer_churn.csv'))
    print(f"Testing pipeline with sample file: {sample_path}")
    
    # 1. Load dataset
    df_raw = load_dataset(sample_path)
    print(f"Loaded DataFrame Shape: {df_raw.shape}")
    assert df_raw.shape[0] > 0, "DataFrame should not be empty"

    # 2. Analyze quality before cleaning
    raw_analysis = analyze_dataset_quality(df_raw)
    print(f"Raw Quality Score: {raw_analysis['summary']['quality_score']}% (Grade: {raw_analysis['summary']['grade']})")
    print(f"Missing Cells: {raw_analysis['missing_values']['total_missing_cells']}")
    print(f"Duplicate Rows: {raw_analysis['duplicates']['duplicate_rows_count']}")

    # 3. Auto Clean
    df_cleaned, actions = auto_clean_dataset(df_raw)
    print(f"Cleaned DataFrame Shape: {df_cleaned.shape}")
    print(f"Actions executed: {len(actions)}")
    for act in actions:
        print(f" - {act}")

    # 4. Analyze quality after cleaning
    cleaned_analysis = analyze_dataset_quality(df_cleaned)
    print(f"Cleaned Quality Score: {cleaned_analysis['summary']['quality_score']}% (Grade: {cleaned_analysis['summary']['grade']})")
    assert cleaned_analysis['summary']['quality_score'] >= raw_analysis['summary']['quality_score']

    # 5. Statistics
    stats = compute_summary_statistics(df_cleaned)
    print(f"Summary stats computed for {len(stats)} columns.")

    # 6. PDF Generation
    pdf_out = os.path.abspath(os.path.join(os.path.dirname(__file__), '../processed/test_report.pdf'))
    generate_pdf_report("sample_customer_churn.csv", pdf_out, raw_analysis, cleaned_analysis, actions)
    print(f"PDF Report generated: {pdf_out}, exists: {os.path.exists(pdf_out)}")
    assert os.path.exists(pdf_out)

    # 7. Database history test
    init_db()
    save_history_record(
        session_id="test_sess_001",
        filename="sample_customer_churn.csv",
        original_file_path=sample_path,
        cleaned_file_path=sample_path,
        pdf_report_path=pdf_out,
        raw_score=raw_analysis['summary']['quality_score'],
        cleaned_score=cleaned_analysis['summary']['quality_score'],
        rows_before=df_raw.shape[0],
        rows_after=df_cleaned.shape[0],
        cols_count=df_cleaned.shape[1],
        issues_count=len(actions),
        actions_list=actions
    )
    history = get_all_history()
    print(f"Database history items retrieved: {len(history)}")
    assert len(history) > 0

    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_full_pipeline()
