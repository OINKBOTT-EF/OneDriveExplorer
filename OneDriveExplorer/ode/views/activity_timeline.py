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
from tkinter import filedialog
from datetime import datetime
import pandas as pd
from pandastable import Table, TableModel
import logging
from ode.helpers.report_ui_utils import (
    ToolTip, DateRangePicker, SearchBox, FilterCheckboxGroup,
    InfoPanel, StatisticCard, format_number
)

log = logging.getLogger(__name__)


class ActivityTimelineFrame(ttk.Frame):
    """
    Activity Timeline View - Shows chronological history of OneDrive activities
    including sync, download, deletion, and access events.
    """

    def __init__(self, master, cache_data, rbin_df, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.cache_data = cache_data
        self.rbin_df = rbin_df
        self.timeline_df = pd.DataFrame()
        self.filtered_df = pd.DataFrame()

        # Activity type icons/labels
        self.activity_types = {
            'MODIFIED': '🔄 MODIFIED',
            'CREATED': '📁 CREATED',
            'ACCESSED': '👁️ ACCESSED',
            'DOWNLOADED': '⬇️ DOWNLOADED',
            'DELETED': '🗑️ DELETED',
            'SHARED': '🔗 SHARED'
        }

        self.setup_ui()
        self.build_timeline()

    def setup_ui(self):
        """Create the UI components"""
        # Main container with paned window
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Info panel at top
        info_panel = InfoPanel(
            self.paned,
            title="Activity Timeline",
            message="View chronological history of all OneDrive activities including syncs, downloads, deletions, and access events.",
            type="tip",
            details="Use the filters below to narrow down activities by type, date range, or search text. Click on preset date ranges for quick filtering. Export your filtered results to CSV or HTML format."
        )
        self.paned.add(info_panel, weight=0)

        # Top frame for filters and controls
        self.filter_frame = ttk.LabelFrame(self.paned, text="Filters & Controls", padding=10)
        self.paned.add(self.filter_frame, weight=0)

        # Filter controls
        self.create_filter_controls()

        # Middle frame for statistics
        self.stats_frame = ttk.LabelFrame(self.paned, text="Activity Statistics", padding=10)
        self.paned.add(self.stats_frame, weight=0)

        # Bottom frame for timeline table
        self.table_frame = ttk.Frame(self.paned)
        self.paned.add(self.table_frame, weight=1)

        # Status bar
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.status_label = ttk.Label(self.status_frame, text="Loading timeline...")
        self.status_label.pack(side=tk.LEFT)

    def create_filter_controls(self):
        """Create filter controls"""
        # Row 1: Activity type filters using FilterCheckboxGroup
        filter_row1 = ttk.Frame(self.filter_frame)
        filter_row1.pack(fill=tk.X, pady=(0, 10))

        self.activity_filter = FilterCheckboxGroup(
            filter_row1,
            title="Activity Types:",
            options=self.activity_types,
            callback=self.apply_filters,
            columns=6
        )
        self.activity_filter.pack(fill=tk.X)

        # Row 2: Date range filters using DateRangePicker
        filter_row2 = ttk.Frame(self.filter_frame)
        filter_row2.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_row2, text="Date Range:", font=('Arial', 9, 'bold')).pack(anchor='w', pady=(0, 5))
        self.date_picker = DateRangePicker(filter_row2, callback=self.apply_filters)
        self.date_picker.pack(fill=tk.X)

        # Row 3: Search and export using SearchBox
        filter_row3 = ttk.Frame(self.filter_frame)
        filter_row3.pack(fill=tk.X, pady=(0, 10))

        self.search_box = SearchBox(
            filter_row3,
            callback=self.on_search,
            placeholder="Search by name, path, or details...",
            width=50
        )
        self.search_box.pack(side=tk.LEFT, padx=(0, 20))

        clear_btn = ttk.Button(filter_row3, text="Clear All Filters", command=self.clear_filters)
        clear_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(clear_btn, "Reset all filters and show all timeline events")

        # Row 4: Export buttons
        filter_row4 = ttk.Frame(self.filter_frame)
        filter_row4.pack(fill=tk.X)

        ttk.Label(filter_row4, text="Export:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))

        csv_btn = ttk.Button(filter_row4, text="Export to CSV", command=self.export_csv)
        csv_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(csv_btn, "Export filtered timeline to CSV format for spreadsheet analysis")

        html_btn = ttk.Button(filter_row4, text="Export to HTML", command=self.export_html)
        html_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(html_btn, "Export filtered timeline to HTML format for web viewing")

    def on_search(self, search_text):
        """Handle search callback"""
        self.apply_filters()

    def build_timeline(self):
        """Build the chronological timeline from all data sources"""
        timeline_events = []

        try:
            # Process main cache data for file/folder activities
            if self.cache_data:
                for item_id, item_data in self.cache_data.items():
                    if not isinstance(item_data, dict):
                        continue

                    name = item_data.get('Name', 'Unknown')
                    path = item_data.get('Path', '')
                    item_type = item_data.get('Type', 'Unknown')

                    # Modified events (lastChange)
                    last_change = item_data.get('lastChange')
                    if last_change and last_change != '' and last_change != 'NaT':
                        timeline_events.append({
                            'Timestamp': last_change,
                            'ActivityType': 'MODIFIED',
                            'Name': name,
                            'Path': path,
                            'Type': item_type,
                            'Details': f"File size: {item_data.get('size', 'Unknown')}"
                        })

                    # Created events (diskCreationTime)
                    disk_created = item_data.get('diskCreationTime')
                    if disk_created and disk_created != '' and disk_created != 'NaT':
                        timeline_events.append({
                            'Timestamp': disk_created,
                            'ActivityType': 'CREATED',
                            'Name': name,
                            'Path': path,
                            'Type': item_type,
                            'Details': f"Created on disk"
                        })

                    # Accessed events (diskLastAccessTime)
                    disk_accessed = item_data.get('diskLastAccessTime')
                    if disk_accessed and disk_accessed != '' and disk_accessed != 'NaT':
                        timeline_events.append({
                            'Timestamp': disk_accessed,
                            'ActivityType': 'ACCESSED',
                            'Name': name,
                            'Path': path,
                            'Type': item_type,
                            'Details': f"Last accessed"
                        })

                    # Download events (firstHydrationTime, lastHydrationTime)
                    first_hydration = item_data.get('firstHydrationTime')
                    if first_hydration and first_hydration != '' and first_hydration != 'NaT':
                        hydration_type = item_data.get('lastHydrationType', 'Unknown')
                        timeline_events.append({
                            'Timestamp': first_hydration,
                            'ActivityType': 'DOWNLOADED',
                            'Name': name,
                            'Path': path,
                            'Type': item_type,
                            'Details': f"First download ({hydration_type})"
                        })

                    last_hydration = item_data.get('lastHydrationTime')
                    if last_hydration and last_hydration != '' and last_hydration != 'NaT' and last_hydration != first_hydration:
                        hydration_count = item_data.get('hydrationCount', 1)
                        hydration_type = item_data.get('lastHydrationType', 'Unknown')
                        timeline_events.append({
                            'Timestamp': last_hydration,
                            'ActivityType': 'DOWNLOADED',
                            'Name': name,
                            'Path': path,
                            'Type': item_type,
                            'Details': f"Downloaded (count: {hydration_count}, type: {hydration_type})"
                        })

                    # Shared events
                    shared_item = item_data.get('sharedItem', 0)
                    if shared_item and shared_item != 0:
                        # Use lastChange as approximation for share time if available
                        if last_change and last_change != '' and last_change != 'NaT':
                            timeline_events.append({
                                'Timestamp': last_change,
                                'ActivityType': 'SHARED',
                                'Name': name,
                                'Path': path,
                                'Type': item_type,
                                'Details': f"Shared item (sharedItem: {shared_item})"
                            })

            # Process recycle bin data for deletions
            if not self.rbin_df.empty:
                for _, row in self.rbin_df.iterrows():
                    notification_time = row.get('notificationTime', '')
                    if notification_time and notification_time != '' and notification_time != 'NaT':
                        timeline_events.append({
                            'Timestamp': notification_time,
                            'ActivityType': 'DELETED',
                            'Name': row.get('Name', 'Unknown'),
                            'Path': row.get('Path', ''),
                            'Type': row.get('Type', 'File'),
                            'Details': f"Deleted (Process: {row.get('deletingProcess', 'Unknown')})"
                        })

            # Create DataFrame from events
            if timeline_events:
                self.timeline_df = pd.DataFrame(timeline_events)

                # Convert timestamp to datetime for proper sorting
                self.timeline_df['Timestamp'] = pd.to_datetime(self.timeline_df['Timestamp'], errors='coerce')

                # Remove any rows with invalid timestamps
                self.timeline_df = self.timeline_df.dropna(subset=['Timestamp'])

                # Sort by timestamp (most recent first)
                self.timeline_df = self.timeline_df.sort_values('Timestamp', ascending=False)

                # Convert timestamp back to string for display
                self.timeline_df['Timestamp_Display'] = self.timeline_df['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

                # Reorder columns for display
                display_columns = ['Timestamp_Display', 'ActivityType', 'Name', 'Path', 'Type', 'Details']
                self.timeline_df = self.timeline_df[['Timestamp'] + display_columns]

                log.info(f"Built timeline with {len(self.timeline_df)} events")
            else:
                self.timeline_df = pd.DataFrame(columns=['Timestamp', 'Timestamp_Display', 'ActivityType', 'Name', 'Path', 'Type', 'Details'])
                log.warning("No timeline events found")

            # Initially show all data
            self.filtered_df = self.timeline_df.copy()

            # Update UI
            self.update_statistics()
            self.update_table()
            self.update_status()

        except Exception as e:
            log.error(f"Error building timeline: {e}")
            self.status_label.config(text=f"Error building timeline: {e}")

    def apply_filters(self):
        """Apply filters to the timeline"""
        try:
            filtered = self.timeline_df.copy()

            # Filter by activity type using FilterCheckboxGroup
            selected_types = self.activity_filter.get_selected()
            if selected_types:
                filtered = filtered[filtered['ActivityType'].isin(selected_types)]

            # Filter by date range using DateRangePicker
            date_from_str, date_to_str = self.date_picker.get_dates()

            if date_from_str:
                try:
                    date_from = pd.to_datetime(date_from_str)
                    filtered = filtered[filtered['Timestamp'] >= date_from]
                except:
                    pass

            if date_to_str:
                try:
                    date_to = pd.to_datetime(date_to_str)
                    filtered = filtered[filtered['Timestamp'] <= date_to]
                except:
                    pass

            # Filter by search term using SearchBox
            search_term = self.search_box.get_search_text().lower()
            if search_term:
                mask = (
                    filtered['Name'].str.lower().str.contains(search_term, na=False) |
                    filtered['Path'].str.lower().str.contains(search_term, na=False) |
                    filtered['Details'].str.lower().str.contains(search_term, na=False)
                )
                filtered = filtered[mask]

            self.filtered_df = filtered
            self.update_table()
            self.update_statistics()
            self.update_status()

        except Exception as e:
            log.error(f"Error applying filters: {e}")

    def clear_filters(self):
        """Clear all filters"""
        # Reset activity type filters
        self.activity_filter.select_all()

        # Clear date range
        self.date_picker.clear_dates()

        # Clear search
        self.search_box.clear()

        # Reset to full dataset
        self.filtered_df = self.timeline_df.copy()
        self.update_table()
        self.update_statistics()
        self.update_status()

    def update_table(self):
        """Update the timeline table with filtered data"""
        # Clear existing table if any
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        if not self.filtered_df.empty:
            # Prepare display dataframe (without internal Timestamp column)
            display_df = self.filtered_df.drop(columns=['Timestamp']).copy()
            display_df.rename(columns={'Timestamp_Display': 'Timestamp'}, inplace=True)

            # Create pandastable
            self.table = Table(self.table_frame, dataframe=display_df,
                             showtoolbar=True, showstatusbar=True)
            self.table.show()
        else:
            ttk.Label(self.table_frame, text="No timeline events to display",
                     font=('Arial', 12)).pack(pady=20)

    def update_statistics(self):
        """Update the statistics panel using StatisticCard components"""
        # Clear existing stats
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        if not self.filtered_df.empty:
            # Calculate statistics
            stats = self.filtered_df['ActivityType'].value_counts()

            # Create grid for statistic cards
            cards_container = ttk.Frame(self.stats_frame)
            cards_container.pack(fill=tk.X, expand=True)

            # Total events card
            total_card = StatisticCard(
                cards_container,
                title="Total Events",
                value=format_number(len(self.filtered_df)),
                subtitle="Filtered timeline events",
                icon="📊"
            )
            total_card.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

            # Activity type cards
            activity_icons = {
                'MODIFIED': '🔄',
                'CREATED': '📁',
                'ACCESSED': '👁️',
                'DOWNLOADED': '⬇️',
                'DELETED': '🗑️',
                'SHARED': '🔗'
            }

            col = 1
            for activity_type, count in stats.items():
                label = self.activity_types.get(activity_type, activity_type).replace(activity_icons.get(activity_type, ''), '').strip()
                icon = activity_icons.get(activity_type, '')

                card = StatisticCard(
                    cards_container,
                    title=label,
                    value=format_number(count),
                    subtitle=f"{(count/len(self.filtered_df)*100):.1f}% of events",
                    icon=icon
                )
                card.grid(row=0, column=col, padx=5, pady=5, sticky='ew')
                col += 1

            # Configure column weights for even distribution
            for i in range(col):
                cards_container.grid_columnconfigure(i, weight=1)

            # Date range info
            if len(self.filtered_df) > 0:
                earliest = self.filtered_df['Timestamp'].min()
                latest = self.filtered_df['Timestamp'].max()

                date_frame = ttk.Frame(self.stats_frame)
                date_frame.pack(fill=tk.X, pady=(10, 0))

                date_card = StatisticCard(
                    date_frame,
                    title="Date Range",
                    value=f"{earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}",
                    subtitle=f"{(latest - earliest).days} days of activity",
                    icon="📅"
                )
                date_card.pack(fill=tk.X, padx=5)
        else:
            ttk.Label(self.stats_frame, text="No statistics available",
                     font=('Arial', 10)).pack()

    def update_status(self):
        """Update status bar"""
        if not self.filtered_df.empty:
            total = len(self.timeline_df)
            showing = len(self.filtered_df)
            self.status_label.config(text=f"Showing {showing} of {total} events")
        else:
            self.status_label.config(text="No events to display")

    def export_csv(self):
        """Export timeline to CSV"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile="onedrive_activity_timeline.csv"
            )

            if file_path:
                # Prepare export dataframe
                export_df = self.filtered_df.drop(columns=['Timestamp']).copy()
                export_df.rename(columns={'Timestamp_Display': 'Timestamp'}, inplace=True)
                export_df.to_csv(file_path, index=False)
                self.status_label.config(text=f"Exported {len(export_df)} events to {file_path}")
                log.info(f"Exported timeline to {file_path}")
        except Exception as e:
            log.error(f"Error exporting CSV: {e}")
            self.status_label.config(text=f"Error exporting CSV: {e}")

    def export_html(self):
        """Export timeline to HTML"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
                initialfile="onedrive_activity_timeline.html"
            )

            if file_path:
                # Prepare export dataframe
                export_df = self.filtered_df.drop(columns=['Timestamp']).copy()
                export_df.rename(columns={'Timestamp_Display': 'Timestamp'}, inplace=True)

                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OneDrive Activity Timeline</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #0078d4; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th {{ background-color: #0078d4; color: white; padding: 10px; text-align: left; }}
        td {{ border: 1px solid #ddd; padding: 8px; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .stats {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>OneDrive Activity Timeline Report</h1>
    <div class="stats">
        <h2>Summary</h2>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Events: {len(export_df)}</p>
    </div>
    {export_df.to_html(index=False, classes='timeline-table')}
</body>
</html>
"""

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                self.status_label.config(text=f"Exported {len(export_df)} events to {file_path}")
                log.info(f"Exported timeline to {file_path}")
        except Exception as e:
            log.error(f"Error exporting HTML: {e}")
            self.status_label.config(text=f"Error exporting HTML: {e}")
