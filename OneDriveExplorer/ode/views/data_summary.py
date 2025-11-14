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

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import pandas as pd
import logging
from ode.helpers.report_ui_utils import (
    ToolTip, InfoPanel, StatisticCard, ProgressBar,
    format_number, format_bytes, format_percentage
)

log = logging.getLogger(__name__)


class DataSummaryFrame(ttk.Frame):
    """
    Data Summary Dashboard - Shows what data was loaded and provides an overview
    of the OneDrive analysis results.
    """

    def __init__(self, master, cache_data, rbin_df, df_scope, account, data_sources=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.cache_data = cache_data
        self.rbin_df = rbin_df
        self.df_scope = df_scope
        self.account = account
        self.data_sources = data_sources or {}

        self.setup_ui()
        self.populate_summary()

    def setup_ui(self):
        """Create the UI components"""
        # Create a canvas with scrollbar for the entire summary
        canvas = tk.Canvas(self, borderwidth=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Title
        title_frame = ttk.Frame(self.scrollable_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=10)

        title_label = ttk.Label(title_frame, text="OneDrive Data Summary Report",
                               font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)

        timestamp_label = ttk.Label(title_frame,
                                    text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                    font=('Arial', 10))
        timestamp_label.pack(side=tk.RIGHT)

        # Info panel
        info_panel = InfoPanel(
            self.scrollable_frame,
            title="Data Summary Dashboard",
            message="This dashboard provides an overview of all loaded OneDrive data sources, account information, and key statistics.",
            type="info",
            details="The dashboard shows which databases were successfully loaded, account scope information, file/folder counts, storage usage, and data completeness indicators. Use this to verify your forensic data is complete before analysis."
        )
        info_panel.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Create sections
        self.create_data_sources_section()
        self.create_account_section()
        self.create_statistics_section()
        self.create_completeness_section()

    def create_section(self, title, icon=""):
        """Create a collapsible section frame"""
        section_frame = ttk.LabelFrame(self.scrollable_frame, text=f"{icon} {title}",
                                       padding=15)
        section_frame.pack(fill=tk.X, padx=20, pady=10)
        return section_frame

    def create_data_sources_section(self):
        """Create Data Sources section"""
        section = self.create_section("Data Sources Loaded", "📁")

        # Create table-like layout
        headers_frame = ttk.Frame(section)
        headers_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(headers_frame, text="Data Source", font=('Arial', 10, 'bold'),
                 width=30).grid(row=0, column=0, sticky='w', padx=5)
        ttk.Label(headers_frame, text="Status", font=('Arial', 10, 'bold'),
                 width=15).grid(row=0, column=1, sticky='w', padx=5)
        ttk.Label(headers_frame, text="Details", font=('Arial', 10, 'bold'),
                 width=40).grid(row=0, column=2, sticky='w', padx=5)

        # Separator
        ttk.Separator(section, orient='horizontal').pack(fill=tk.X, pady=5)

        # Data sources content (will be populated later)
        self.data_sources_content = ttk.Frame(section)
        self.data_sources_content.pack(fill=tk.X)

    def create_account_section(self):
        """Create Account Information section"""
        section = self.create_section("Account Information", "👤")
        self.account_content = ttk.Frame(section)
        self.account_content.pack(fill=tk.X)

    def create_statistics_section(self):
        """Create Statistics section"""
        section = self.create_section("Data Statistics", "📊")
        self.stats_content = ttk.Frame(section)
        self.stats_content.pack(fill=tk.X)

    def create_completeness_section(self):
        """Create Data Completeness section"""
        section = self.create_section("Data Completeness Indicators", "✓")
        self.completeness_content = ttk.Frame(section)
        self.completeness_content.pack(fill=tk.X)

    def add_data_source_row(self, source_name, status, details, row):
        """Add a data source row"""
        status_color = "green" if status == "✓ Loaded" else "red"
        status_icon = "✓" if status == "✓ Loaded" else "✗"

        ttk.Label(self.data_sources_content, text=source_name,
                 font=('Arial', 9)).grid(row=row, column=0, sticky='w', padx=5, pady=3)

        status_label = ttk.Label(self.data_sources_content, text=f"{status_icon} {status.replace('✓ ', '').replace('✗ ', '')}",
                                font=('Arial', 9))
        status_label.grid(row=row, column=1, sticky='w', padx=5, pady=3)

        ttk.Label(self.data_sources_content, text=details,
                 font=('Arial', 9)).grid(row=row, column=2, sticky='w', padx=5, pady=3)

    def populate_summary(self):
        """Populate the summary with actual data"""
        try:
            # Data Sources
            row = 0

            # Check what data sources were loaded
            sources_info = [
                ("SyncEngineDatabase.db", self.data_sources.get('sync_engine', False),
                 "Main OneDrive sync database"),
                ("SafeDelete.db", self.data_sources.get('safe_delete', False),
                 "Deleted files tracking"),
                ("DAT File", self.data_sources.get('dat_file', False),
                 "OneDrive settings and metadata"),
                ("FileUsageSync.db", self.data_sources.get('file_usage', False),
                 "File usage and collaboration data"),
                ("ODL Logs", self.data_sources.get('odl_logs', False),
                 "OneDrive debug logs"),
                ("Registry Hive", self.data_sources.get('registry', False),
                 "Windows registry data"),
                ("Recycle Bin", not self.rbin_df.empty,
                 f"{len(self.rbin_df)} deleted items" if not self.rbin_df.empty else "No data")
            ]

            for source_name, loaded, details in sources_info:
                status = "✓ Loaded" if loaded else "✗ Not Loaded"
                self.add_data_source_row(source_name, status, details, row)
                row += 1

            # Account Information
            if self.account:
                ttk.Label(self.account_content, text=f"Account: {self.account}",
                         font=('Arial', 11, 'bold')).pack(anchor='w', pady=3)

            if not self.df_scope.empty:
                for _, scope in self.df_scope.iterrows():
                    scope_id = scope.get('scopeID', 'Unknown')
                    scope_name = scope.get('Name', 'Unknown')
                    ttk.Label(self.account_content, text=f"Scope: {scope_name} (ID: {scope_id})",
                             font=('Arial', 10)).pack(anchor='w', pady=2, padx=10)

            # Count files and folders
            total_items = 0
            total_files = 0
            total_folders = 0
            total_size_kb = 0
            hydrated_files = 0
            shared_items = 0

            if self.cache_data:
                for item_id, item_data in self.cache_data.items():
                    if not isinstance(item_data, dict):
                        continue

                    total_items += 1
                    item_type = item_data.get('Type', '')

                    if item_type == 'File':
                        total_files += 1

                        # Parse size (format: "123 KB")
                        size_str = item_data.get('size', '0 KB')
                        if isinstance(size_str, str) and 'KB' in size_str:
                            try:
                                size_kb = int(size_str.replace('KB', '').replace(',', '').strip())
                                total_size_kb += size_kb
                            except:
                                pass

                        # Check if hydrated
                        if item_data.get('firstHydrationTime'):
                            hydrated_files += 1

                    elif item_type == 'Folder':
                        total_folders += 1

                    # Check if shared
                    if item_data.get('sharedItem', 0) != 0:
                        shared_items += 1

            deleted_items = len(self.rbin_df) if not self.rbin_df.empty else 0

            # Statistics using StatisticCard components
            stats_grid = ttk.Frame(self.stats_content)
            stats_grid.pack(fill=tk.X, expand=True)

            # Row 1: Total items, files, folders
            card1 = StatisticCard(
                stats_grid,
                title="Total Items",
                value=format_number(total_items),
                subtitle="Files and Folders",
                icon="📦"
            )
            card1.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
            ToolTip(card1, "Total number of files and folders in loaded data")

            card2 = StatisticCard(
                stats_grid,
                title="Files",
                value=format_number(total_files),
                subtitle=format_percentage(total_files, total_items, 1) + " of items" if total_items > 0 else "0% of items",
                icon="📄"
            )
            card2.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
            ToolTip(card2, "Number of files found in OneDrive data")

            card3 = StatisticCard(
                stats_grid,
                title="Folders",
                value=format_number(total_folders),
                subtitle=format_percentage(total_folders, total_items, 1) + " of items" if total_items > 0 else "0% of items",
                icon="📁"
            )
            card3.grid(row=0, column=2, padx=5, pady=5, sticky='ew')
            ToolTip(card3, "Number of folders found in OneDrive data")

            # Row 2: Storage, hydrated, shared
            total_size_bytes = total_size_kb * 1024
            card4 = StatisticCard(
                stats_grid,
                title="Total Storage",
                value=format_bytes(total_size_bytes),
                subtitle=f"{format_number(total_size_kb)} KB",
                icon="💾"
            )
            card4.grid(row=1, column=0, padx=5, pady=5, sticky='ew')
            ToolTip(card4, "Total storage used by all files")

            hydration_pct = format_percentage(hydrated_files, total_files, 1) if total_files > 0 else "0.0%"
            card5 = StatisticCard(
                stats_grid,
                title="Hydrated Files",
                value=format_number(hydrated_files),
                subtitle=f"{hydration_pct} downloaded",
                icon="⬇️"
            )
            card5.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
            ToolTip(card5, "Files that were downloaded to local disk (hydrated)")

            card6 = StatisticCard(
                stats_grid,
                title="Shared Items",
                value=format_number(shared_items),
                subtitle=format_percentage(shared_items, total_items, 1) + " of items" if total_items > 0 else "0% of items",
                icon="🔗"
            )
            card6.grid(row=1, column=2, padx=5, pady=5, sticky='ew')
            ToolTip(card6, "Items shared with other users")

            # Row 3: Deleted items
            card7 = StatisticCard(
                stats_grid,
                title="Deleted Items",
                value=format_number(deleted_items),
                subtitle="From SafeDelete.db",
                icon="🗑️"
            )
            card7.grid(row=2, column=0, padx=5, pady=5, sticky='ew')
            ToolTip(card7, "Items found in deletion history (SafeDelete database)")

            # Configure column weights for even distribution
            for i in range(3):
                stats_grid.grid_columnconfigure(i, weight=1)

            # Add hydration progress bar
            if total_files > 0:
                hydration_frame = ttk.Frame(self.stats_content)
                hydration_frame.pack(fill=tk.X, pady=(15, 0))

                ttk.Label(hydration_frame, text="Hydration Progress:",
                         font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

                progress = ProgressBar(
                    hydration_frame,
                    value=hydrated_files,
                    maximum=total_files,
                    label="Downloaded Files:",
                    show_percentage=True
                )
                progress.pack(fill=tk.X)
                ToolTip(progress, f"{hydrated_files} of {total_files} files were downloaded to disk")

            # Data Completeness using InfoPanel
            has_timestamps = self.check_timestamp_completeness()
            has_deletions = not self.rbin_df.empty
            has_hydration = hydrated_files > 0
            has_sharing = shared_items > 0

            completeness_grid = ttk.Frame(self.completeness_content)
            completeness_grid.pack(fill=tk.X)

            # Calculate overall completeness score
            completeness_score = sum([has_timestamps, has_deletions, has_hydration, has_sharing])
            total_checks = 4
            completeness_pct = (completeness_score / total_checks) * 100

            # Completeness summary card
            completeness_card = StatisticCard(
                completeness_grid,
                title="Overall Data Completeness",
                value=f"{completeness_score}/{total_checks}",
                subtitle=f"{completeness_pct:.0f}% complete",
                icon="✓"
            )
            completeness_card.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
            ToolTip(completeness_card, "Number of data categories available out of 4 total categories")

            # Individual completeness indicators
            completeness_items = [
                ("Timestamp Data", has_timestamps, "File modification, creation, and access timestamps"),
                ("Deletion History", has_deletions, "SafeDelete.db with deletion tracking"),
                ("Hydration Data", has_hydration, "Download history (firstHydrationTime)"),
                ("Sharing Information", has_sharing, "Files shared with other users")
            ]

            row = 1
            for item, complete, tooltip_text in completeness_items:
                icon = "✓" if complete else "⚠"
                status_text = "Available" if complete else "Limited/Unavailable"
                panel_type = "success" if complete else "warning"

                panel = InfoPanel(
                    completeness_grid,
                    title=f"{icon} {item}",
                    message=status_text,
                    type=panel_type
                )
                panel.grid(row=row, column=0, columnspan=2, padx=5, pady=3, sticky='ew')
                ToolTip(panel, tooltip_text)
                row += 1

            # Configure column weights
            completeness_grid.grid_columnconfigure(0, weight=1)
            completeness_grid.grid_columnconfigure(1, weight=1)

        except Exception as e:
            log.error(f"Error populating summary: {e}")

    def check_timestamp_completeness(self):
        """Check if timestamp data is available"""
        if not self.cache_data:
            return False

        # Check if at least some items have timestamp data
        has_timestamps = False
        for item_id, item_data in self.cache_data.items():
            if not isinstance(item_data, dict):
                continue

            if (item_data.get('lastChange') or
                item_data.get('diskCreationTime') or
                item_data.get('diskLastAccessTime')):
                has_timestamps = True
                break

        return has_timestamps
