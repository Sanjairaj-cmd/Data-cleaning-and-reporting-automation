import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_pdf_report(filename, report_output_path, raw_analysis, cleaned_analysis, cleaning_actions):
    """
    Generates a professional multi-page Data Cleaning & Quality Audit PDF Report.
    """
    doc = SimpleDocTemplate(
        report_output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1E293B'),
        alignment=0,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # 1. Header Banner & Title
    story.append(Paragraph("DATA QUALITY & CLEANING AUDIT REPORT", title_style))
    meta_str = f"<b>Dataset:</b> {filename} | <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | <b>Engine:</b> AutoCleanPro v2.0"
    story.append(Paragraph(meta_str, subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=15))

    # 2. Executive Score Comparison Card
    raw_score = raw_analysis['summary']['quality_score']
    clean_score = cleaned_analysis['summary']['quality_score']
    score_diff = round(clean_score - raw_score, 1)
    diff_str = f"+{score_diff}% Improvement" if score_diff >= 0 else f"{score_diff}%"

    raw_grade = raw_analysis['summary']['grade']
    clean_grade = cleaned_analysis['summary']['grade']

    score_data = [
        [
            Paragraph("<font size=10 color='#64748B'>INITIAL QUALITY SCORE</font><br/><br/><font size=24 color='#DC2626'><b>{:.1f}%</b></font><br/><font size=9 color='#64748B'>Grade: {}</font>".format(raw_score, raw_grade), body_style),
            Paragraph("<font size=10 color='#64748B'>POST-CLEANING SCORE</font><br/><br/><font size=24 color='#16A34A'><b>{:.1f}%</b></font><br/><font size=9 color='#16A34A'>Grade: {}</font>".format(clean_score, clean_grade), body_style),
            Paragraph("<font size=10 color='#64748B'>NET IMPROVEMENT</font><br/><br/><font size=20 color='#2563EB'><b>{}</b></font><br/><font size=9 color='#64748B'>Status: Fully Optimized</font>".format(diff_str), body_style)
        ]
    ]

    score_table = Table(score_data, colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#FEF2F2')),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#F0FDF4')),
        ('BACKGROUND', (2,0), (2,0), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (0,0), 1, colors.HexColor('#FCA5A5')),
        ('BOX', (1,0), (1,0), 1, colors.HexColor('#86EFAC')),
        ('BOX', (2,0), (2,0), 1, colors.HexColor('#BFDBFE')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))

    story.append(score_table)
    story.append(Spacer(1, 15))

    # 3. Before vs After Key Metrics Comparison Table
    story.append(Paragraph("1. Data Health Comparison (Before vs. After)", section_heading))
    
    comp_header = [
        Paragraph("Metric", table_header_style),
        Paragraph("Raw Dataset", table_header_style),
        Paragraph("Cleaned Dataset", table_header_style),
        Paragraph("Impact / Status", table_header_style)
    ]

    comp_rows = [
        comp_header,
        [
            Paragraph("Total Rows", table_cell_bold),
            Paragraph(str(raw_analysis['summary']['total_rows']), table_cell_style),
            Paragraph(str(cleaned_analysis['summary']['total_rows']), table_cell_style),
            Paragraph(f"{cleaned_analysis['summary']['total_rows'] - raw_analysis['summary']['total_rows']} rows change", table_cell_style)
        ],
        [
            Paragraph("Total Columns", table_cell_bold),
            Paragraph(str(raw_analysis['summary']['total_cols']), table_cell_style),
            Paragraph(str(cleaned_analysis['summary']['total_cols']), table_cell_style),
            Paragraph("Retained", table_cell_style)
        ],
        [
            Paragraph("Missing Cells", table_cell_bold),
            Paragraph(f"{raw_analysis['missing_values']['total_missing_cells']} ({raw_analysis['missing_values']['missing_cells_pct']}%)", table_cell_style),
            Paragraph(f"{cleaned_analysis['missing_values']['total_missing_cells']} ({cleaned_analysis['missing_values']['missing_cells_pct']}%)", table_cell_style),
            Paragraph("<font color='#16A34A'><b>Resolved</b></font>" if cleaned_analysis['missing_values']['total_missing_cells'] == 0 else "Partially Imputed", table_cell_style)
        ],
        [
            Paragraph("Duplicate Rows", table_cell_bold),
            Paragraph(f"{raw_analysis['duplicates']['duplicate_rows_count']} ({raw_analysis['duplicates']['duplicate_pct']}%)", table_cell_style),
            Paragraph(f"{cleaned_analysis['duplicates']['duplicate_rows_count']} ({cleaned_analysis['duplicates']['duplicate_pct']}%)", table_cell_style),
            Paragraph("<font color='#16A34A'><b>Removed</b></font>" if cleaned_analysis['duplicates']['duplicate_rows_count'] == 0 else "Retained", table_cell_style)
        ],
        [
            Paragraph("Outliers Identified", table_cell_bold),
            Paragraph(str(raw_analysis['outliers']['total_outlier_count']), table_cell_style),
            Paragraph(str(cleaned_analysis['outliers']['total_outlier_count']), table_cell_style),
            Paragraph("<font color='#16A34A'><b>Handled</b></font>" if cleaned_analysis['outliers']['total_outlier_count'] < raw_analysis['outliers']['total_outlier_count'] else "Maintained", table_cell_style)
        ],
        [
            Paragraph("Completeness Sub-Score", table_cell_bold),
            Paragraph(f"{raw_analysis['summary']['completeness_score']}%", table_cell_style),
            Paragraph(f"{cleaned_analysis['summary']['completeness_score']}%", table_cell_style),
            Paragraph(f"+{round(cleaned_analysis['summary']['completeness_score'] - raw_analysis['summary']['completeness_score'], 1)}%", table_cell_style)
        ],
        [
            Paragraph("Uniqueness Sub-Score", table_cell_bold),
            Paragraph(f"{raw_analysis['summary']['uniqueness_score']}%", table_cell_style),
            Paragraph(f"{cleaned_analysis['summary']['uniqueness_score']}%", table_cell_style),
            Paragraph(f"+{round(cleaned_analysis['summary']['uniqueness_score'] - raw_analysis['summary']['uniqueness_score'], 1)}%", table_cell_style)
        ]
    ]

    comp_table = Table(comp_rows, colWidths=[2.0*inch, 1.7*inch, 1.7*inch, 1.8*inch])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))

    story.append(comp_table)
    story.append(Spacer(1, 15))

    # 4. Cleaning Actions Executed Log
    story.append(Paragraph("2. Automated Cleaning Pipeline Log", section_heading))
    
    if cleaning_actions:
        action_rows = [[Paragraph("#", table_header_style), Paragraph("Cleaning Operation Performed", table_header_style)]]
        for idx, act in enumerate(cleaning_actions, 1):
            action_rows.append([
                Paragraph(str(idx), table_cell_bold),
                Paragraph(act, table_cell_style)
            ])
        
        action_table = Table(action_rows, colWidths=[0.5*inch, 6.7*inch])
        action_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F1F5F9')])
        ]))
        story.append(action_table)
    else:
        story.append(Paragraph("No automated cleaning operations were required; dataset passed all checks.", body_style))

    story.append(Spacer(1, 15))

    # 5. Detected Issues & Type Inferences Detail
    story.append(Paragraph("3. Detailed Column Issues & Type Analysis", section_heading))
    
    issue_rows = [[
        Paragraph("Column Name", table_header_style),
        Paragraph("Detected Data Type", table_header_style),
        Paragraph("Missing Count (%)", table_header_style),
        Paragraph("Outliers (IQR)", table_header_style),
        Paragraph("Suggested Fix", table_header_style)
    ]]

    col_dtypes = raw_analysis.get('col_dtypes', {})
    missing_by_col = raw_analysis['missing_values']['cols_with_missing']
    missing_pct_by_col = raw_analysis['missing_values']['missing_pct_by_col']
    outliers_by_col = raw_analysis['outliers']['by_column']
    type_inferences = raw_analysis.get('type_inferences', {})

    for col in col_dtypes.keys():
        curr_dt = col_dtypes[col]
        miss_cnt = missing_by_col.get(col, 0)
        miss_pct = missing_pct_by_col.get(col, 0.0)
        outlier_info = outliers_by_col.get(col, {})
        out_cnt = outlier_info.get('count', 0)

        sug_fix = []
        if miss_cnt > 0:
            sug_fix.append("Impute missing")
        if out_cnt > 0:
            sug_fix.append("Cap/clip outliers")
        if col in type_inferences:
            sug_fix.append(f"Convert to {type_inferences[col]['suggested_type']}")
        
        fix_str = ", ".join(sug_fix) if sug_fix else "Passed All Checks"

        issue_rows.append([
            Paragraph(col, table_cell_bold),
            Paragraph(curr_dt, table_cell_style),
            Paragraph(f"{miss_cnt} ({miss_pct}%)", table_cell_style),
            Paragraph(str(out_cnt), table_cell_style),
            Paragraph(fix_str, table_cell_style)
        ])

    issue_table = Table(issue_rows, colWidths=[1.6*inch, 1.3*inch, 1.4*inch, 1.1*inch, 1.8*inch])
    issue_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))

    story.append(issue_table)
    story.append(Spacer(1, 15))

    # Build Document
    doc.build(story)
    return report_output_path
