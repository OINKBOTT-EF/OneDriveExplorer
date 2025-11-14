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

"""
Duplicate File Detection Report

Analyzes file hashes (SHA1, quickXor) to identify duplicate files across
OneDrive storage. Provides insights into:
- Exact duplicates (same content, different paths/names)
- Storage waste from duplication
- Potential deduplication savings
- Duplicate file groups and families

Uses:
- Forensics: Identify copied/moved files
- Storage optimization: Find redundant files
- Data integrity: Verify file consistency
- Investigation: Track file distribution
"""

import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
import pandas as pd
from pandastable import Table
import logging
from collections import defaultdict
from ode.helpers.report_ui_utils import (
    ToolTip, InfoPanel, StatisticCard, SearchBox,
    format_number, format_bytes
)

log = logging.getLogger(__name__)


class DuplicateDetectionFrame(ttk.Frame):
    """
    Duplicate File Detection - Identifies duplicate files by hash analysis
    """

    def __init__(self, master, cache_data, hash_algorithm="SHA1", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.cache_data = cache_data
        self.hash_algorithm = hash_algorithm  # "SHA1" or "quickXor"

        self.duplicate_groups = []  # List of duplicate file groups
        self.duplicate_files_df = pd.DataFrame()

        self.setup_ui()
        self.analyze_duplicates()

    def setup_ui(self):
        """Create the UI components"""
        # Create notebook for different views
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Overview
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="Overview")

        # Tab 2: Duplicate Groups
        self.groups_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.groups_frame, text="Duplicate Groups")

        # Tab 3: All Duplicates (Flat List)
        self.flat_list_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.flat_list_frame, text="All Duplicates")

        # Tab 4: Largest Duplicates
        self.largest_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.largest_frame, text="Largest Duplicates")

        # Status bar
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.status_label = ttk.Label(self.status_frame, text="Analyzing for duplicates...")
        self.status_label.pack(side=tk.LEFT)

        # Export button
        export_btn = ttk.Button(self.status_frame, text="Export Report (CSV)",
                               command=self.export_report)
        export_btn.pack(side=tk.RIGHT, padx=5)
        ToolTip(export_btn, "Export duplicate file report to CSV format")

    def parse_size(self, size_str):
        """Convert size string (e.g., '1,234 KB') to integer KB"""
        try:
            if isinstance(size_str, str) and 'KB' in size_str:
                return int(size_str.replace('KB', '').replace(',', '').strip())
            elif isinstance(size_str, (int, float)):
                return int(size_str)
            return 0
        except:
            return 0

    def analyze_duplicates(self):
        """Analyze files for duplicates based on hash values"""
        try:
            # Group files by hash
            hash_groups = defaultdict(list)
            total_files = 0
            files_with_hash = 0

            if self.cache_data:
                for item_id, item_data in self.cache_data.items():
                    if not isinstance(item_data, dict):
                        continue

                    if item_data.get('Type') == 'File':
                        total_files += 1
                        file_hash = item_data.get('Hash', '')

                        # Skip files without hash or with empty hash
                        if not file_hash or file_hash == '' or file_hash == 'N/A':
                            continue

                        files_with_hash += 1

                        # Build file info
                        file_info = {
                            'Hash': file_hash,
                            'Name': item_data.get('Name', 'Unknown'),
                            'Path': item_data.get('Path', ''),
                            'Size': item_data.get('size', '0 KB'),
                            'SizeKB': self.parse_size(item_data.get('size', '0 KB')),
                            'LastChange': item_data.get('lastChange', ''),
                            'FileStatus': item_data.get('fileStatus', 0),
                            'SharedItem': item_data.get('sharedItem', 0)
                        }

                        hash_groups[file_hash].append(file_info)

            # Filter to only groups with duplicates (2+ files)
            self.duplicate_groups = []
            all_duplicates = []

            for file_hash, files in hash_groups.items():
                if len(files) >= 2:
                    # Sort by path for consistent ordering
                    files.sort(key=lambda x: x['Path'])

                    group = {
                        'Hash': file_hash,
                        'Count': len(files),
                        'Files': files,
                        'Size': files[0]['Size'],  # All should be same size
                        'SizeKB': files[0]['SizeKB'],
                        'WastedKB': files[0]['SizeKB'] * (len(files) - 1)  # All but one copy
                    }
                    self.duplicate_groups.append(group)

                    # Add all files to flat list
                    for file_info in files:
                        file_info['DuplicateCount'] = len(files)
                        file_info['GroupHash'] = file_hash
                        all_duplicates.append(file_info)

            # Create DataFrame for flat list
            self.duplicate_files_df = pd.DataFrame(all_duplicates)

            # Sort by size (largest first)
            self.duplicate_groups.sort(key=lambda x: x['WastedKB'], reverse=True)

            # Calculate statistics
            self.stats = {
                'total_files': total_files,
                'files_with_hash': files_with_hash,
                'duplicate_groups': len(self.duplicate_groups),
                'total_duplicate_files': len(all_duplicates),
                'unique_files': files_with_hash - len(all_duplicates),
                'wasted_space_kb': sum(g['WastedKB'] for g in self.duplicate_groups),
                'hash_algorithm': self.hash_algorithm
            }

            # Populate all tabs
            self.populate_overview()
            self.populate_groups()
            self.populate_flat_list()
            self.populate_largest()

            # Update status
            if self.stats['duplicate_groups'] > 0:
                wasted_mb = self.stats['wasted_space_kb'] / 1024
                self.status_label.config(
                    text=f"Found {self.stats['duplicate_groups']} duplicate groups "
                         f"({self.stats['total_duplicate_files']} files), "
                         f"wasting {wasted_mb:.2f} MB"
                )
            else:
                self.status_label.config(text="No duplicate files found")

        except Exception as e:
            log.error(f"Error analyzing duplicates: {e}")
            self.status_label.config(text=f"Error: {e}")

    def populate_overview(self):
        """Populate overview tab with statistics"""
        # Clear existing widgets
        for widget in self.overview_frame.winfo_children():
            widget.destroy()

        # Create scrollable canvas
        canvas = tk.Canvas(self.overview_frame)
        scrollbar = ttk.Scrollbar(self.overview_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Title
        title = ttk.Label(scrollable_frame, text="Duplicate File Detection Overview",
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Info panel
        if self.stats['duplicate_groups'] == 0:
            info_panel = InfoPanel(
                scrollable_frame,
                title="No Duplicates Found",
                message="No duplicate files detected in this OneDrive dataset.",
                type="success",
                details=f"Analyzed {self.stats['files_with_hash']} files with {self.stats['hash_algorithm']} hashes. All files appear to be unique."
            )
            info_panel.pack(fill=tk.X, padx=20, pady=(0, 10))
        else:
            info_panel = InfoPanel(
                scrollable_frame,
                title="Duplicate Detection Report",
                message="Analysis of duplicate files based on cryptographic hash values (SHA1 or quickXor).",
                type="info",
                details=f"Files with identical {self.stats['hash_algorithm']} hash values have identical content, regardless of filename or location. This report helps identify redundant storage and track file copies/moves."
            )
            info_panel.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Summary statistics using StatisticCard
        summary_frame = ttk.LabelFrame(scrollable_frame, text="Detection Statistics", padding=15)
        summary_frame.pack(fill=tk.X, padx=20, pady=10)

        stats_grid = ttk.Frame(summary_frame)
        stats_grid.pack(fill=tk.X)

        # Row 1: Files analyzed
        card1 = StatisticCard(
            stats_grid,
            title="Total Files",
            value=format_number(self.stats['total_files']),
            subtitle="In OneDrive",
            icon="📄"
        )
        card1.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        ToolTip(card1, "Total number of files found in OneDrive data")

        card2 = StatisticCard(
            stats_grid,
            title="Files with Hash",
            value=format_number(self.stats['files_with_hash']),
            subtitle=f"{self.stats['hash_algorithm']} computed",
            icon="🔐"
        )
        card2.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ToolTip(card2, f"Files with computed {self.stats['hash_algorithm']} hash values available for comparison")

        card3 = StatisticCard(
            stats_grid,
            title="Unique Files",
            value=format_number(self.stats['unique_files']),
            subtitle="No duplicates",
            icon="✅"
        )
        card3.grid(row=0, column=2, padx=5, pady=5, sticky='ew')
        ToolTip(card3, "Files with unique content (no duplicates found)")

        # Row 2: Duplicates found
        card4 = StatisticCard(
            stats_grid,
            title="Duplicate Groups",
            value=format_number(self.stats['duplicate_groups']),
            subtitle="Unique file contents",
            icon="📦"
        )
        card4.grid(row=1, column=0, padx=5, pady=5, sticky='ew')
        ToolTip(card4, "Number of distinct file contents that have duplicates")

        card5 = StatisticCard(
            stats_grid,
            title="Duplicate Files",
            value=format_number(self.stats['total_duplicate_files']),
            subtitle=f"{(self.stats['total_duplicate_files']/max(self.stats['files_with_hash'],1)*100):.1f}% of analyzed",
            icon="🔄"
        )
        card5.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ToolTip(card5, "Total number of files that are duplicates of other files")

        wasted_bytes = self.stats['wasted_space_kb'] * 1024
        card6 = StatisticCard(
            stats_grid,
            title="Wasted Space",
            value=format_bytes(wasted_bytes),
            subtitle=f"{format_number(self.stats['wasted_space_kb'])} KB",
            icon="💾"
        )
        card6.grid(row=1, column=2, padx=5, pady=5, sticky='ew')
        ToolTip(card6, "Storage space consumed by duplicate copies (excludes one original)")

        # Configure grid columns
        for i in range(3):
            stats_grid.grid_columnconfigure(i, weight=1)

        # Deduplication potential
        if self.stats['duplicate_groups'] > 0:
            dedup_frame = ttk.LabelFrame(scrollable_frame, text="Deduplication Potential", padding=15)
            dedup_frame.pack(fill=tk.X, padx=20, pady=10)

            total_size_kb = sum(g['SizeKB'] * g['Count'] for g in self.duplicate_groups)
            deduplicated_size_kb = sum(g['SizeKB'] for g in self.duplicate_groups)
            savings_kb = total_size_kb - deduplicated_size_kb
            savings_pct = (savings_kb / max(total_size_kb, 1)) * 100

            info_text = f"""If all duplicate files were removed (keeping one copy of each):
• Current storage used by duplicates: {format_bytes(total_size_kb * 1024)}
• Storage after deduplication: {format_bytes(deduplicated_size_kb * 1024)}
• Potential savings: {format_bytes(savings_kb * 1024)} ({savings_pct:.1f}%)
• Files that could be removed: {self.stats['total_duplicate_files'] - self.stats['duplicate_groups']}"""

            ttk.Label(dedup_frame, text=info_text, font=('Courier', 9),
                     justify=tk.LEFT).pack(anchor='w', padx=10, pady=5)

        # Top duplicate groups preview
        if len(self.duplicate_groups) > 0:
            top_frame = ttk.LabelFrame(scrollable_frame, text="Top 10 Duplicate Groups (by wasted space)", padding=15)
            top_frame.pack(fill=tk.X, padx=20, pady=10)

            for i, group in enumerate(self.duplicate_groups[:10]):
                row_frame = ttk.Frame(top_frame)
                row_frame.pack(fill=tk.X, pady=3)

                ttk.Label(row_frame, text=f"{i+1}.", width=3).pack(side=tk.LEFT)
                ttk.Label(row_frame, text=f"{group['Count']} copies",
                         font=('Arial', 9, 'bold'), width=12).pack(side=tk.LEFT)
                ttk.Label(row_frame, text=f"Size: {group['Size']}",
                         font=('Arial', 9), width=15).pack(side=tk.LEFT)
                ttk.Label(row_frame, text=f"Wasted: {format_bytes(group['WastedKB'] * 1024)}",
                         font=('Arial', 9), width=20).pack(side=tk.LEFT)
                ttk.Label(row_frame, text=f"File: {group['Files'][0]['Name'][:50]}",
                         font=('Arial', 9), foreground='blue').pack(side=tk.LEFT)

    def populate_groups(self):
        """Populate duplicate groups tab"""
        # Clear existing widgets
        for widget in self.groups_frame.winfo_children():
            widget.destroy()

        if len(self.duplicate_groups) == 0:
            ttk.Label(self.groups_frame,
                     text="No duplicate file groups found",
                     font=('Arial', 12)).pack(pady=20)
            return

        # Create scrollable canvas
        canvas = tk.Canvas(self.groups_frame)
        scrollbar = ttk.Scrollbar(self.groups_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Display each group
        for group_idx, group in enumerate(self.duplicate_groups):
            group_frame = ttk.LabelFrame(
                scrollable_frame,
                text=f"Group {group_idx + 1}: {group['Count']} copies of '{group['Files'][0]['Name']}' "
                     f"(Wasted: {format_bytes(group['WastedKB'] * 1024)})",
                padding=10
            )
            group_frame.pack(fill=tk.X, padx=20, pady=5)

            # Hash info
            hash_row = ttk.Frame(group_frame)
            hash_row.pack(fill=tk.X, pady=(0, 5))
            ttk.Label(hash_row, text=f"Hash ({self.stats['hash_algorithm']}):",
                     font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            ttk.Label(hash_row, text=group['Hash'],
                     font=('Courier', 8)).pack(side=tk.LEFT, padx=10)

            # File list
            for file_info in group['Files']:
                file_row = ttk.Frame(group_frame)
                file_row.pack(fill=tk.X, pady=2)

                ttk.Label(file_row, text="📄", font=('Arial', 10)).pack(side=tk.LEFT)
                ttk.Label(file_row, text=file_info['Path'],
                         font=('Arial', 9), foreground='blue').pack(side=tk.LEFT, padx=5)
                if file_info['LastChange']:
                    ttk.Label(file_row, text=f"Modified: {file_info['LastChange']}",
                             font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=10)

    def populate_flat_list(self):
        """Populate all duplicates flat list tab"""
        # Clear existing widgets
        for widget in self.flat_list_frame.winfo_children():
            widget.destroy()

        if self.duplicate_files_df.empty:
            ttk.Label(self.flat_list_frame,
                     text="No duplicate files found",
                     font=('Arial', 12)).pack(pady=20)
            return

        # Prepare display dataframe
        display_df = self.duplicate_files_df[[
            'Name', 'Path', 'Size', 'Hash', 'DuplicateCount', 'LastChange'
        ]].copy()
        display_df.rename(columns={
            'DuplicateCount': 'Copies',
            'LastChange': 'Modified'
        }, inplace=True)

        # Create pandastable
        table = Table(self.flat_list_frame, dataframe=display_df,
                     showtoolbar=True, showstatusbar=True)
        table.show()

    def populate_largest(self):
        """Populate largest duplicates tab"""
        # Clear existing widgets
        for widget in self.largest_frame.winfo_children():
            widget.destroy()

        if len(self.duplicate_groups) == 0:
            ttk.Label(self.largest_frame,
                     text="No duplicate file groups found",
                     font=('Arial', 12)).pack(pady=20)
            return

        # Create DataFrame from groups (by total wasted space)
        largest_groups = []
        for group in self.duplicate_groups[:100]:  # Top 100
            largest_groups.append({
                'Copies': group['Count'],
                'FileSize': group['Size'],
                'WastedSpace': format_bytes(group['WastedKB'] * 1024),
                'FileName': group['Files'][0]['Name'],
                'FirstPath': group['Files'][0]['Path'],
                'Hash': group['Hash']
            })

        df = pd.DataFrame(largest_groups)

        # Create pandastable
        table = Table(self.largest_frame, dataframe=df,
                     showtoolbar=True, showstatusbar=True)
        table.show()

    def export_report(self):
        """Export duplicate detection report to CSV"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile="onedrive_duplicate_files.csv"
            )

            if file_path:
                if not self.duplicate_files_df.empty:
                    self.duplicate_files_df.to_csv(file_path, index=False)
                    self.status_label.config(
                        text=f"Exported {len(self.duplicate_files_df)} duplicate files to {file_path}"
                    )
                    log.info(f"Exported duplicates to {file_path}")
                else:
                    # Export summary even if no duplicates
                    summary_data = [{
                        'TotalFiles': self.stats['total_files'],
                        'FilesWithHash': self.stats['files_with_hash'],
                        'DuplicateGroups': self.stats['duplicate_groups'],
                        'TotalDuplicateFiles': self.stats['total_duplicate_files'],
                        'WastedSpaceKB': self.stats['wasted_space_kb'],
                        'HashAlgorithm': self.stats['hash_algorithm']
                    }]
                    df = pd.DataFrame(summary_data)
                    df.to_csv(file_path, index=False)
                    self.status_label.config(text=f"Exported summary to {file_path}")

        except Exception as e:
            log.error(f"Error exporting CSV: {e}")
            self.status_label.config(text=f"Error exporting CSV: {e}")
