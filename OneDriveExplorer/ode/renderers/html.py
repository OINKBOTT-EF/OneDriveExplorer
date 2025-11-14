# OneDriveExplorer
# Copyright (C) 2025
#
# This file is part of OneDriveExplorer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os
import pandas as pd
import logging
from datetime import datetime
from ode.renderers.csv_file import enrich_dataframe_with_activities

log = logging.getLogger(__name__)


def generate_html_header(account_info, total_files, total_folders, total_size_kb):
    """Generate enhanced HTML header with CSS styling and summary statistics."""

    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html_header = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OneDrive Explorer Report - {account_info}</title>
    <style>
        :root {{
            --primary-color: #0078d4;
            --success-color: #107c10;
            --warning-color: #faa21b;
            --error-color: #d13438;
            --bg-color: #f5f5f5;
            --card-bg: #ffffff;
            --border-color: #e1e1e1;
            --text-primary: #323130;
            --text-secondary: #605e5c;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-color);
            color: var(--text-primary);
        }}

        .header {{
            background: linear-gradient(135deg, #0078d4 0%, #1890ff 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
            font-weight: 600;
        }}

        .header .subtitle {{
            opacity: 0.9;
            font-size: 14px;
            margin-top: 5px;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 4px solid var(--primary-color);
        }}

        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .stat-card .value {{
            font-size: 32px;
            font-weight: 700;
            color: var(--primary-color);
            margin: 10px 0;
        }}

        .stat-card .label {{
            font-size: 12px;
            color: var(--text-secondary);
        }}

        .data-section {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            overflow-x: auto;
        }}

        .data-section h2 {{
            margin: 0 0 20px 0;
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 13px;
            background: white;
        }}

        thead {{
            background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th {{
            text-align: left;
            padding: 12px 15px;
            font-weight: 600;
            color: var(--text-primary);
            border-bottom: 2px solid var(--border-color);
            white-space: nowrap;
        }}

        td {{
            padding: 10px 15px;
            border-bottom: 1px solid var(--border-color);
        }}

        tr:hover {{
            background-color: #f8f9fa;
        }}

        .activity-badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}

        .badge-created {{ background: #d4f4dd; color: #107c10; }}
        .badge-updated {{ background: #fff4ce; color: #ca5010; }}
        .badge-downloaded {{ background: #cfe4ff; color: #0078d4; }}
        .badge-shared {{ background: #f3d6fa; color: #5c2e91; }}
        .badge-deleted {{ background: #fed9da; color: #d13438; }}
        .badge-synced {{ background: #e1dfdd; color: #323130; }}

        .status-indicator {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
        }}

        .status-active {{ background-color: var(--success-color); }}
        .status-deleted {{ background-color: var(--error-color); }}
        .status-pending {{ background-color: var(--warning-color); }}

        .footer {{
            margin-top: 30px;
            padding: 20px;
            text-align: center;
            color: var(--text-secondary);
            font-size: 12px;
        }}

        @media print {{
            body {{ background: white; }}
            .header, .stat-card, .data-section {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 OneDrive Explorer - Forensic Analysis Report</h1>
        <div class="subtitle">Account: {account_info}</div>
        <div class="subtitle">Generated: {current_date}</div>
    </div>

    <div class="summary-cards">
        <div class="stat-card">
            <h3>Total Files</h3>
            <div class="value">{total_files:,}</div>
            <div class="label">Files analyzed</div>
        </div>
        <div class="stat-card">
            <h3>Total Folders</h3>
            <div class="value">{total_folders:,}</div>
            <div class="label">Folders analyzed</div>
        </div>
        <div class="stat-card">
            <h3>Total Size</h3>
            <div class="value">{total_size_kb / 1024:.1f} MB</div>
            <div class="label">Storage used</div>
        </div>
    </div>

    <div class="data-section">
        <h2>📁 File & Folder Details</h2>
"""
    return html_header


def generate_html_footer():
    """Generate HTML footer."""
    return """
    </div>
    <div class="footer">
        Generated by OneDrive Explorer - Forensic Analysis Tool
    </div>
</body>
</html>
"""


def print_html(df, rbin_df, name, html_path, db_name, fus):
    log.info('Started writing enhanced HTML file with activity enrichment')

    if not os.path.exists(html_path):
        os.makedirs(html_path)

    # Calculate summary statistics
    total_files = 0
    total_folders = 0
    total_size_kb = 0
    account_info = db_name if db_name else "Unknown"

    if not df.empty:
        # Enrich with activity-focused columns BEFORE processing
        df = enrich_dataframe_with_activities(df)

        # Calculate statistics
        if 'Type' in df.columns:
            total_files = len(df[df['Type'] == 'File'])
            total_folders = len(df[df['Type'] == 'Folder'])

        if 'size' in df.columns:
            # Extract numeric size from KB string format (e.g., "1,234 KB")
            def parse_size(size_str):
                try:
                    if isinstance(size_str, str):
                        # Remove ' KB' and commas, then convert to float
                        return float(size_str.replace(' KB', '').replace(',', ''))
                    return float(size_str) if pd.notna(size_str) else 0
                except:
                    return 0

            total_size_kb = df['size'].apply(parse_size).sum()

        parent_col = 'parentResourceID' if 'parentResourceID' in df.columns else 'ParentFileSystemId'
        df = df.sort_values(by=['Level', parent_col, 'Type', 'FileSort', 'FolderSort', 'libraryType'],
                            ascending=[False, False, False, True, False, False])

        df = df.drop(['Level', 'FileSort', 'FolderSort'], axis=1)

    if not rbin_df.empty:
        # Enrich recycle bin data too
        rbin_df = enrich_dataframe_with_activities(rbin_df)
        df = pd.concat([df, rbin_df], ignore_index=True, axis=0)

    if not df.empty:
        df = df.apply(lambda x: x.fillna(0) if x.dtype == 'Int64' else x.fillna('') if x.dtype == 'object' else x)

    html_file = os.path.basename(name).split('.')[0]+"_OneDrive.html"
    fus_file = os.path.basename(name).split('.')[0]+"_FileUsageSync.html"
    file_extension = os.path.splitext(name)[1][1:]

    if db_name == 'Microsoft.ListSync.db':
        html_file = os.path.basename(name).split('.')[0]+"_OneDrive_list_sync.html"

    if db_name == 'Microsoft.FilesOnDemand.db':
        html_file = os.path.basename(name).split('.')[0]+"_OneDrive_fod.html"

    if file_extension == 'previous':
        html_file = os.path.basename(name).split('.')[0]+"_"+file_extension+"_OneDrive.html"
        fus_file = os.path.basename(name).split('.')[0]+"_"+file_extension+"_FileUsageSync.html"

    if not df.empty:
        output = open(html_path + '/' + html_file, 'w', encoding='utf-8')

        # Write enhanced HTML with header, styling, and summary
        output.write(generate_html_header(account_info, total_files, total_folders, total_size_kb))

        # Write the data table (without index)
        output.write(df.to_html(index=False, escape=False, classes='data-table'))

        # Write footer
        output.write(generate_html_footer())

        output.close()
        log.info(f'Enhanced HTML report saved: {html_file}')

    if not fus.empty:
        # Simple HTML for FileUsageSync (could be enhanced later)
        output = open(html_path + '/' + fus_file, 'w', encoding='utf-8')
        output.write(generate_html_header("FileUsage Sync Data", len(fus), 0, 0))
        output.write(fus.to_html(index=False, escape=False, classes='data-table'))
        output.write(generate_html_footer())
        output.close()
        log.info(f'FileUsageSync HTML report saved: {fus_file}')
