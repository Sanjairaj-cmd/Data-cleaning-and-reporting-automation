import os
import uuid
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename

from config import Config
from database import init_db, save_history_record, get_all_history, get_history_by_session
from engine.loader import load_dataset
from engine.detector import analyze_dataset_quality
from engine.cleaner import auto_clean_dataset, custom_clean_dataset
from engine.statistics import compute_summary_statistics, compute_correlation_matrix, get_column_distribution
from engine.pdf_generator import generate_pdf_report

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
init_db()

# In-memory session cache for fast interactive dashboard state (session_id -> data dict)
SESSION_CACHE = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Handles CSV/Excel file uploads or sample file loading.
    Returns initial dataset analysis and preview.
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Check if loading sample or uploading file
        if 'sample_name' in request.form and request.form['sample_name']:
            sample_name = request.form['sample_name']
            sample_path = os.path.join(Config.BASE_DIR, 'samples', sample_name)
            if not os.path.exists(sample_path):
                return jsonify({'error': f"Sample file '{sample_name}' not found."}), 404
            
            filename = sample_name
            save_path = os.path.join(Config.UPLOAD_FOLDER, f"{session_id}_{filename}")
            # Copy sample file to upload folder
            df_raw = load_dataset(sample_path)
            if sample_name.endswith('.csv'):
                df_raw.to_csv(save_path, index=False)
            else:
                df_raw.to_excel(save_path, index=False)
        else:
            if 'file' not in request.files:
                return jsonify({'error': 'No file part in request.'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected.'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'error': 'Invalid file format. Allowed formats: CSV, XLSX, XLS'}), 400

            filename = secure_filename(file.filename)
            save_path = os.path.join(Config.UPLOAD_FOLDER, f"{session_id}_{filename}")
            file.save(save_path)
            
            df_raw = load_dataset(save_path)

        # Analyze initial dataset quality
        raw_analysis = analyze_dataset_quality(df_raw)
        stats = compute_summary_statistics(df_raw)
        corr = compute_correlation_matrix(df_raw)

        # Cache session data
        SESSION_CACHE[session_id] = {
            'filename': filename,
            'raw_file_path': save_path,
            'df_raw': df_raw,
            'raw_analysis': raw_analysis,
            'df_cleaned': None,
            'cleaned_analysis': None,
            'cleaning_actions': [],
            'cleaned_csv_path': None,
            'cleaned_xlsx_path': None,
            'pdf_path': None
        }

        # Preview data (first 50 rows, JSON safe)
        preview_data = df_raw.head(50).fillna("").to_dict(orient='records')
        columns = df_raw.columns.tolist()

        return jsonify({
            'session_id': session_id,
            'filename': filename,
            'columns': columns,
            'raw_analysis': raw_analysis,
            'summary_statistics': stats,
            'correlation': corr,
            'preview_data': preview_data,
            'total_rows': len(df_raw),
            'total_cols': len(columns)
        })

    except Exception as e:
        return jsonify({'error': f"Processing error: {str(e)}"}), 500


@app.route('/api/clean', methods=['POST'])
def clean_dataset():
    """
    Executes automated or customized data cleaning pipeline.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        mode = data.get('mode', 'auto')  # 'auto' or 'custom'
        custom_rules = data.get('rules', {})

        if not session_id or session_id not in SESSION_CACHE:
            return jsonify({'error': 'Invalid or expired session ID.'}), 400

        sess = SESSION_CACHE[session_id]
        df_raw = sess['df_raw']

        if mode == 'auto':
            df_cleaned, actions = auto_clean_dataset(df_raw)
        else:
            df_cleaned, actions = custom_clean_dataset(df_raw, custom_rules)

        cleaned_analysis = analyze_dataset_quality(df_cleaned)
        cleaned_stats = compute_summary_statistics(df_cleaned)
        cleaned_corr = compute_correlation_matrix(df_cleaned)

        # Export cleaned dataset to CSV and Excel in processed folder
        base_name = os.path.splitext(sess['filename'])[0]
        cleaned_csv_filename = f"cleaned_{session_id}_{base_name}.csv"
        cleaned_xlsx_filename = f"cleaned_{session_id}_{base_name}.xlsx"
        pdf_filename = f"report_{session_id}_{base_name}.pdf"

        cleaned_csv_path = os.path.join(Config.PROCESSED_FOLDER, cleaned_csv_filename)
        cleaned_xlsx_path = os.path.join(Config.PROCESSED_FOLDER, cleaned_xlsx_filename)
        pdf_path = os.path.join(Config.PROCESSED_FOLDER, pdf_filename)

        df_cleaned.to_csv(cleaned_csv_path, index=False)
        try:
            df_cleaned.to_excel(cleaned_xlsx_path, index=False)
        except Exception:
            cleaned_xlsx_path = None  # fallback if openpyxl fails

        # Generate PDF Audit Report
        generate_pdf_report(
            filename=sess['filename'],
            report_output_path=pdf_path,
            raw_analysis=sess['raw_analysis'],
            cleaned_analysis=cleaned_analysis,
            cleaning_actions=actions
        )

        # Update Session Cache
        sess['df_cleaned'] = df_cleaned
        sess['cleaned_analysis'] = cleaned_analysis
        sess['cleaning_actions'] = actions
        sess['cleaned_csv_path'] = cleaned_csv_path
        sess['cleaned_xlsx_path'] = cleaned_xlsx_path
        sess['pdf_path'] = pdf_path

        # Save to DB history
        save_history_record(
            session_id=session_id,
            filename=sess['filename'],
            original_file_path=sess['raw_file_path'],
            cleaned_file_path=cleaned_csv_path,
            pdf_report_path=pdf_path,
            raw_score=sess['raw_analysis']['summary']['quality_score'],
            cleaned_score=cleaned_analysis['summary']['quality_score'],
            rows_before=len(df_raw),
            rows_after=len(df_cleaned),
            cols_count=len(df_cleaned.columns),
            issues_count=len(actions),
            actions_list=actions
        )

        raw_preview = df_raw.head(50).fillna("").to_dict(orient='records')
        cleaned_preview = df_cleaned.head(50).fillna("").to_dict(orient='records')

        return jsonify({
            'session_id': session_id,
            'raw_analysis': sess['raw_analysis'],
            'cleaned_analysis': cleaned_analysis,
            'cleaning_actions': actions,
            'summary_statistics': cleaned_stats,
            'correlation': cleaned_corr,
            'raw_preview': raw_preview,
            'cleaned_preview': cleaned_preview,
            'download_urls': {
                'csv': url_for('download_cleaned', session_id=session_id, file_format='csv'),
                'xlsx': url_for('download_cleaned', session_id=session_id, file_format='xlsx'),
                'pdf': url_for('download_pdf', session_id=session_id)
            }
        })

    except Exception as e:
        return jsonify({'error': f"Cleaning failed: {str(e)}"}), 500


@app.route('/api/chart-data/<session_id>', methods=['GET'])
def get_chart_data(session_id):
    """
    Returns chart data for Plotly (column distributions, box plots, missing matrix).
    """
    if session_id not in SESSION_CACHE:
        return jsonify({'error': 'Session not found'}), 404

    sess = SESSION_CACHE[session_id]
    col_name = request.args.get('col')
    target = request.args.get('target', 'raw')  # 'raw' or 'cleaned'

    df = sess['df_cleaned'] if (target == 'cleaned' and sess['df_cleaned'] is not None) else sess['df_raw']

    if col_name:
        dist_data = get_column_distribution(df, col_name)
        if not dist_data:
            return jsonify({'error': f"Column '{col_name}' not found."}), 400
        return jsonify(dist_data)

    # General chart package
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    missing_by_col = df.isnull().sum().to_dict()

    return jsonify({
        'missing_matrix': missing_by_col,
        'numeric_columns': num_cols,
        'columns': df.columns.tolist()
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    Returns processing history records.
    """
    records = get_all_history()
    return jsonify({'history': records})


@app.route('/download/cleaned/<session_id>')
def download_cleaned(session_id):
    file_format = request.args.get('file_format', 'csv')
    if session_id in SESSION_CACHE:
        sess = SESSION_CACHE[session_id]
        file_path = sess['cleaned_csv_path'] if file_format == 'csv' else sess['cleaned_xlsx_path']
        if file_path and os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
    
    # Try finding in DB
    db_rec = get_history_by_session(session_id)
    if db_rec and db_rec.get('cleaned_file_path') and os.path.exists(db_rec['cleaned_file_path']):
        return send_file(db_rec['cleaned_file_path'], as_attachment=True)

    return "Cleaned file not found", 404


@app.route('/download/pdf/<session_id>')
def download_pdf(session_id):
    if session_id in SESSION_CACHE:
        sess = SESSION_CACHE[session_id]
        pdf_path = sess.get('pdf_path')
        if pdf_path and os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name=f"Data_Audit_Report_{session_id[:8]}.pdf")
    
    db_rec = get_history_by_session(session_id)
    if db_rec and db_rec.get('pdf_report_path') and os.path.exists(db_rec['pdf_report_path']):
        return send_file(db_rec['pdf_report_path'], as_attachment=True, download_name=f"Data_Audit_Report_{session_id[:8]}.pdf")

    return "PDF Report not found", 404


if __name__ == '__main__':
    print("Starting AutoCleanPro Flask Server...")
    app.run(host='127.0.0.1', port=5000, debug=True)
