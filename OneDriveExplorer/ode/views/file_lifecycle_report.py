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
File Lifecycle & Activity Report

Comprehensive reporting on file activities throughout their lifecycle:
- WHERE files are located (OneDrive, SharePoint, Teams)
- WHAT actions occurred (create, modify, access, download, sync, share, delete)
- WHEN activities happened (complete timeline)
- WHO performed actions (creators, modifiers, sharers)
- HOW to interpret the data (explanations of OneDrive forensic artifacts)

This report combines data from:
- SyncEngineDatabase.db: File metadata, sync status, hydration
- SafeDelete.db: Deletion tracking
- GraphMetadata: User attribution
- FileUsageSync.db: Access patterns, sharing
- DAT files: File hashes, permissions, flags

Each section includes explanations of WHERE the data comes from and WHAT it means
for forensic investigations.
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


class FileLifecycleFrame(ttk.Frame):
    """
    File Lifecycle & Activity Report - Comprehensive activity tracking and forensic explanations
    """

    def __init__(self, master, cache_data, rbin_df, graphMetadata=None, fileusage_data=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.cache_data = cache_data
        self.rbin_df = rbin_df if rbin_df is not None else pd.DataFrame()
        self.graphMetadata = graphMetadata if graphMetadata is not None else pd.DataFrame()
        self.fileusage_data = fileusage_data

        self.setup_ui()
        self.analyze_activities()

    def setup_ui(self):
        """Create the UI components"""
        # Create notebook for different activity views
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Overview - Explains the forensic artifacts
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="📚 How to Read This Data")

        # Tab 2: File Locations (WHERE)
        self.locations_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.locations_frame, text="📍 WHERE: Locations")

        # Tab 3: Creation Activities (CREATING)
        self.creation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.creation_frame, text="🆕 CREATING")

        # Tab 4: Modification Activities (UPDATING)
        self.modification_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.modification_frame, text="✏️ UPDATING")

        # Tab 5: Access Activities (ACCESSING)
        self.access_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.access_frame, text="👁️ ACCESSING")

        # Tab 6: Download Activities (DOWNLOADING)
        self.download_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.download_frame, text="⬇️ DOWNLOADING")

        # Tab 7: Sync Activities (SYNCING)
        self.sync_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sync_frame, text="🔄 SYNCING")

        # Tab 8: Sharing Activities (SHARING)
        self.sharing_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sharing_frame, text="🔗 SHARING")

        # Tab 9: Deletion Activities (REMOVING)
        self.deletion_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.deletion_frame, text="🗑️ REMOVING")

        # Status bar
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.status_label = ttk.Label(self.status_frame, text="Analyzing file lifecycle activities...")
        self.status_label.pack(side=tk.LEFT)

        # Export button
        export_btn = ttk.Button(self.status_frame, text="Export Full Report (CSV)",
                               command=self.export_report)
        export_btn.pack(side=tk.RIGHT, padx=5)
        ToolTip(export_btn, "Export comprehensive activity report to CSV format")

    def analyze_activities(self):
        """Analyze all file activities"""
        try:
            # Initialize activity collections
            self.activities = {
                'created': [],
                'modified': [],
                'accessed': [],
                'downloaded': [],
                'synced': [],
                'shared': [],
                'deleted': []
            }

            self.locations = {
                'OneDrive Personal': 0,
                'OneDrive Business': 0,
                'SharePoint': 0,
                'Teams': 0,
                'Unknown': 0
            }

            # Process cache data
            if self.cache_data:
                for item_id, item_data in self.cache_data.items():
                    if not isinstance(item_data, dict):
                        continue

                    if item_data.get('Type') == 'File':
                        self.analyze_file_activity(item_data)

            # Process deletions
            if not self.rbin_df.empty:
                for _, row in self.rbin_df.iterrows():
                    self.activities['deleted'].append({
                        'Name': row.get('Name', 'Unknown'),
                        'Path': row.get('Path', ''),
                        'Timestamp': row.get('notificationTime', ''),
                        'Process': row.get('deletingProcess', 'Unknown'),
                        'Source': 'SafeDelete.db'
                    })

            # Create summary statistics
            self.stats = {
                'total_files': sum(len(v) for k, v in self.activities.items() if k != 'deleted'),
                'created_count': len(self.activities['created']),
                'modified_count': len(self.activities['modified']),
                'accessed_count': len(self.activities['accessed']),
                'downloaded_count': len(self.activities['downloaded']),
                'synced_count': len(self.activities['synced']),
                'shared_count': len(self.activities['shared']),
                'deleted_count': len(self.activities['deleted']),
                'locations': self.locations
            }

            # Populate all tabs
            self.populate_overview()
            self.populate_locations()
            self.populate_creation()
            self.populate_modification()
            self.populate_access()
            self.populate_download()
            self.populate_sync()
            self.populate_sharing()
            self.populate_deletion()

            # Update status
            total_activities = sum([
                self.stats['created_count'],
                self.stats['modified_count'],
                self.stats['accessed_count'],
                self.stats['downloaded_count'],
                self.stats['shared_count'],
                self.stats['deleted_count']
            ])
            self.status_label.config(text=f"Analyzed {total_activities} file lifecycle activities")

        except Exception as e:
            log.error(f"Error analyzing file lifecycle: {e}")
            self.status_label.config(text=f"Error: {e}")

    def analyze_file_activity(self, item_data):
        """Analyze individual file for all activities"""
        name = item_data.get('Name', 'Unknown')
        path = item_data.get('Path', '')

        # Determine location
        self.categorize_location(item_data)

        # CREATING: Track file creation
        disk_created = item_data.get('diskCreationTime')
        created_by = self.get_created_by(item_data)
        if disk_created and disk_created not in ['', 'NaT']:
            self.activities['created'].append({
                'Name': name,
                'Path': path,
                'Timestamp': disk_created,
                'CreatedBy': created_by,
                'Source': 'SyncEngineDatabase.db → diskCreationTime',
                'Explanation': 'When file was first created on local disk'
            })

        # UPDATING: Track modifications
        last_change = item_data.get('lastChange')
        modified_by = self.get_modified_by(item_data)
        if last_change and last_change not in ['', 'NaT']:
            self.activities['modified'].append({
                'Name': name,
                'Path': path,
                'Timestamp': last_change,
                'ModifiedBy': modified_by,
                'Source': 'DAT file → lastChange',
                'Explanation': 'Last time file content was modified'
            })

        # ACCESSING: Track access
        disk_accessed = item_data.get('diskLastAccessTime')
        if disk_accessed and disk_accessed not in ['', 'NaT']:
            self.activities['accessed'].append({
                'Name': name,
                'Path': path,
                'Timestamp': disk_accessed,
                'Source': 'SyncEngineDatabase.db → diskLastAccessTime',
                'Explanation': 'Last time file was opened or accessed'
            })

        # DOWNLOADING: Track hydration (downloads from cloud)
        first_hydration = item_data.get('firstHydrationTime')
        last_hydration = item_data.get('lastHydrationTime')
        hydration_type = item_data.get('lastHydrationType', 'Unknown')
        hydration_count = item_data.get('hydrationCount', 0)

        if first_hydration and first_hydration not in ['', 'NaT']:
            self.activities['downloaded'].append({
                'Name': name,
                'Path': path,
                'FirstDownload': first_hydration,
                'LastDownload': last_hydration if last_hydration else first_hydration,
                'DownloadType': hydration_type,
                'DownloadCount': hydration_count,
                'Source': 'SyncEngineDatabase.db → HydrationData',
                'Explanation': f"File downloaded from cloud ({hydration_type}: {'user-initiated' if hydration_type == 'active' else 'automatic'})"
            })

        # SYNCING: Track sync status
        file_status = item_data.get('fileStatus', 0)
        sync_status = self.decode_file_status(file_status)
        if file_status in [1, 2, 3, 4]:  # Synced or syncing states
            self.activities['synced'].append({
                'Name': name,
                'Path': path,
                'Status': sync_status,
                'StatusCode': file_status,
                'Source': 'DAT file → fileStatus',
                'Explanation': f'File sync state: {sync_status}'
            })

        # SHARING: Track sharing
        shared_item = item_data.get('sharedItem', 0)
        if shared_item and shared_item != 0:
            self.activities['shared'].append({
                'Name': name,
                'Path': path,
                'SharedFlag': shared_item,
                'Source': 'DAT file → bitMask bit 29',
                'Explanation': 'File is shared with other users'
            })

    def categorize_location(self, item_data):
        """Determine WHERE file is located"""
        path = item_data.get('Path', '')
        scope_id = item_data.get('scopeID', '')

        if 'Personal' in path or not scope_id:
            self.locations['OneDrive Personal'] += 1
        elif 'Teams' in path or 'teamID' in str(item_data):
            self.locations['Teams'] += 1
        elif scope_id:
            self.locations['SharePoint'] += 1
        else:
            self.locations['Unknown'] += 1

    def get_created_by(self, item_data):
        """Extract creator from GraphMetadata"""
        metadata = item_data.get('Metadata', {})
        if isinstance(metadata, dict):
            return metadata.get('createdBy', 'Unknown')
        return 'Unknown'

    def get_modified_by(self, item_data):
        """Extract modifier from GraphMetadata"""
        metadata = item_data.get('Metadata', {})
        if isinstance(metadata, dict):
            return metadata.get('modifiedBy', 'Unknown')
        return 'Unknown'

    def decode_file_status(self, status):
        """Decode fileStatus codes"""
        status_map = {
            0: 'Unknown',
            1: 'Synced',
            2: 'Synced (Available)',
            3: 'Syncing',
            4: 'Sync Pending',
            5: 'Sync Error',
            6: 'Online Only (Not Synced)',
            7: 'Not Linked',
            8: 'Excluded',
            9: 'Pinned'
        }
        return status_map.get(status, f'Unknown ({status})')

    def populate_overview(self):
        """Populate overview tab with forensic artifact explanations"""
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
        title = ttk.Label(scrollable_frame, text="How to Read OneDrive Forensic Data",
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10, padx=20)

        # Introduction
        intro_panel = InfoPanel(
            scrollable_frame,
            title="Understanding OneDrive Activity Data",
            message="This report analyzes OneDrive forensic artifacts to reconstruct file lifecycle activities.",
            type="info",
            details="Each tab shows a specific activity type (creating, updating, accessing, etc.) with explanations of WHERE the data comes from and WHAT it means for investigations."
        )
        intro_panel.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Data Sources Section
        sources_frame = ttk.LabelFrame(scrollable_frame, text="📁 Data Sources (WHERE data comes from)",
                                      padding=15)
        sources_frame.pack(fill=tk.X, padx=20, pady=10)

        sources_text = """
1. DAT Files (<UserCid>.dat)
   • Binary settings files containing file/folder metadata
   • Location: C:\\Users\\<user>\\AppData\\Local\\Microsoft\\OneDrive\\settings\\<account>
   • Contains: File names, paths, sizes, hashes, sync status, permissions, timestamps
   • Version: v29-v36 (hex 0x29-0x36)

2. SyncEngineDatabase.db
   • SQLite database with complete sync engine state
   • Location: C:\\Users\\<user>\\AppData\\Local\\Microsoft\\OneDrive\\settings\\<account>
   • Tables:
     - ClientFile_Records: File metadata with hydration (download) data
     - ClientFolder_Records: Folder metadata
     - GraphMetadata_Records: User attribution (who created/modified)
     - HydrationData: Download timestamps and types
   • Schema versions: 8-32+

3. SafeDelete.db
   • SQLite database tracking deleted files
   • Location: Same as SyncEngineDatabase.db
   • Tables:
     - items_moved_to_recycle_bin: Deleted file records
     - filter_delete_info: Deletion process tracking
   • Shows: What was deleted, when, by what process

4. Microsoft.FileUsageSync.db (if present)
   • SQLite database with usage patterns
   • Location: Nucleus folder for SharePoint/Teams
   • Contains: Recent files, quick access, collaborators, sharing history
   • Rich JSON data about file access patterns

5. Microsoft.ListSync.db (if present)
   • SharePoint/Teams list synchronization
   • Dynamic tables based on SharePoint lists
   • Contains: Full SharePoint metadata, sharing details, permissions
        """

        ttk.Label(sources_frame, text=sources_text, font=('Courier', 9),
                 justify=tk.LEFT).pack(anchor='w', padx=10, pady=5)

        # Activities Section
        activities_frame = ttk.LabelFrame(scrollable_frame, text="🔍 Activity Types (WHAT you can track)",
                                         padding=15)
        activities_frame.pack(fill=tk.X, padx=20, pady=10)

        activities_text = """
CREATING (🆕 tab):
• diskCreationTime: When file first created on local disk
• createdBy: User who created file (from GraphMetadata)
• Source: SyncEngineDatabase.db
• Forensic Value: File origin, timeline reconstruction

UPDATING (✏️ tab):
• lastChange: Last modification timestamp
• modifiedBy: User who last modified (from GraphMetadata)
• Source: DAT file, GraphMetadata
• Forensic Value: Track content changes, identify editors

ACCESSING (👁️ tab):
• diskLastAccessTime: Last time file was opened
• Source: SyncEngineDatabase.db
• Forensic Value: File usage patterns, user activity timeline
• Note: May update even for metadata reads

DOWNLOADING (⬇️ tab):
• firstHydrationTime: First download from cloud to disk
• lastHydrationTime: Most recent download
• hydrationType: 'active' (user-initiated) or 'passive' (automatic)
• hydrationCount: Number of times downloaded
• Source: SyncEngineDatabase.db → HydrationData
• Forensic Value: When files were accessed, user intent

SYNCING (🔄 tab):
• fileStatus: Current sync state (0-9)
  - 1: Synced
  - 3: Syncing (in progress)
  - 5: Sync Error
  - 6: Online Only (not downloaded)
• Source: DAT file
• Forensic Value: File availability, sync problems

SHARING (🔗 tab):
• sharedItem: Flag indicating file is shared (bitMask bit 29)
• SharedWithDetails: JSON with sharing information
• Source: DAT file, ListSync.db
• Forensic Value: Collaboration, data exfiltration detection

REMOVING (🗑️ tab):
• notificationTime: When file was deleted
• deletingProcess: Process that deleted file
• Source: SafeDelete.db
• Forensic Value: Deletion timeline, anti-forensics detection
        """

        ttk.Label(activities_frame, text=activities_text, font=('Courier', 9),
                 justify=tk.LEFT).pack(anchor='w', padx=10, pady=5)

        # Interpretation Guide
        interpret_frame = ttk.LabelFrame(scrollable_frame, text="💡 How to Interpret the Data",
                                        padding=15)
        interpret_frame.pack(fill=tk.X, padx=20, pady=10)

        interpret_text = """
Key Investigative Questions:

1. "When was this file last accessed?"
   → Check ACCESSING tab for diskLastAccessTime
   → Compare with UPDATING tab (lastChange) to see if file was modified

2. "Who created or modified this file?"
   → Check CREATING tab for createdBy
   → Check UPDATING tab for modifiedBy
   → Note: Requires GraphMetadata (SyncEngine schema v10+)

3. "Was this file downloaded to the local machine?"
   → Check DOWNLOADING tab for hydration data
   → 'active' = user opened file, 'passive' = automatic download
   → No hydration data = file never downloaded (online-only)

4. "Is this file being synced?"
   → Check SYNCING tab for fileStatus
   → Status 6 (Online Only) = not synced to disk
   → Status 5 (Error) = sync failed, investigate why

5. "Was this file shared with others?"
   → Check SHARING tab for sharedItem flag
   → Look for SharedWithDetails for specific users

6. "What files were deleted and when?"
   → Check REMOVING tab for deletion timeline
   → deletingProcess shows what deleted it (user, system, OneDrive)

7. "Where are my files stored?"
   → Check WHERE: Locations tab
   → OneDrive Personal vs Business vs SharePoint vs Teams

Timestamps Comparison:
• diskCreationTime < lastChange < diskLastAccessTime (typical sequence)
• firstHydrationTime after file cloud upload (download occurred)
• lastChange without diskLastAccessTime = modified but not opened recently
• diskLastAccessTime without lastChange = read but not modified
        """

        ttk.Label(interpret_frame, text=interpret_text, font=('Courier', 9),
                 justify=tk.LEFT).pack(anchor='w', padx=10, pady=5)

        # Important Notes
        notes_panel = InfoPanel(
            scrollable_frame,
            title="⚠️ Important Notes",
            message="Understanding data limitations and caveats",
            type="warning",
            details="""
• Timestamps are local time (system timezone at time of activity)
• diskLastAccessTime may be disabled by NTFS settings
• GraphMetadata (createdBy/modifiedBy) only in schema v10+ databases
• Hydration data only present for files that were downloaded
• Deleted files only tracked if SafeDelete.db is available
• Online-only files have no local timestamps (never on disk)
• Sharing data richness varies by account type (Personal/Business)
            """
        )
        notes_panel.pack(fill=tk.X, padx=20, pady=(0, 20))

    def populate_locations(self):
        """Populate WHERE: Locations tab"""
        for widget in self.locations_frame.winfo_children():
            widget.destroy()

        # Create scrollable canvas
        canvas = tk.Canvas(self.locations_frame)
        scrollbar = ttk.Scrollbar(self.locations_frame, orient="vertical", command=canvas.yview)
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
        title = ttk.Label(scrollable_frame, text="File Locations (WHERE)",
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Info panel
        info_panel = InfoPanel(
            scrollable_frame,
            title="Understanding OneDrive File Locations",
            message="Files can be stored in different OneDrive locations with different characteristics.",
            type="info",
            details="""
OneDrive Personal: Consumer accounts (@outlook.com, @hotmail.com)
OneDrive Business: Enterprise accounts (Office 365, SharePoint)
SharePoint: Team sites, document libraries
Teams: Microsoft Teams file storage (backed by SharePoint)

Detection Method:
- Path analysis (looks for 'Personal', 'Teams' in paths)
- scopeID presence (Business/SharePoint have scope IDs)
- teamID field (Teams integration)
            """
        )
        info_panel.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Location statistics
        stats_frame = ttk.LabelFrame(scrollable_frame, text="Location Distribution", padding=15)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)

        total_files = sum(self.stats['locations'].values())

        for idx, (location, count) in enumerate(self.stats['locations'].items()):
            if count == 0:
                continue

            pct = (count / max(total_files, 1)) * 100

            icon_map = {
                'OneDrive Personal': '👤',
                'OneDrive Business': '🏢',
                'SharePoint': '📚',
                'Teams': '👥',
                'Unknown': '❓'
            }

            card = StatisticCard(
                stats_grid,
                title=location,
                value=format_number(count),
                subtitle=f"{pct:.1f}% of files",
                icon=icon_map.get(location, '📁')
            )
            card.grid(row=idx // 2, column=idx % 2, padx=5, pady=5, sticky='ew')

        # Configure grid
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)

    def populate_creation(self):
        """Populate CREATING tab"""
        self._populate_activity_tab(
            self.creation_frame,
            self.activities['created'],
            "File Creation Activities",
            """Files created on local disk or synced from cloud.

Data Source: SyncEngineDatabase.db → diskCreationTime
Meaning: First time file appeared on this system

Important: This is LOCAL creation time, not necessarily when file
was originally created in the cloud. For cloud origin, check createdBy
metadata if available.

Columns:
- Timestamp: When file was created locally
- CreatedBy: User who created file (from GraphMetadata, if available)
- Name: Filename
- Path: Full OneDrive path
            """
        )

    def populate_modification(self):
        """Populate UPDATING tab"""
        self._populate_activity_tab(
            self.modification_frame,
            self.activities['modified'],
            "File Modification Activities",
            """Files that were modified (content changed).

Data Source: DAT file → lastChange
Meaning: Last time file CONTENT was modified

This shows actual content changes, not metadata updates.
Compare with diskLastAccessTime to see if file was accessed after modification.

Columns:
- Timestamp: Last modification time
- ModifiedBy: User who modified (from GraphMetadata, if available)
- Name: Filename
- Path: Full OneDrive path
            """
        )

    def populate_access(self):
        """Populate ACCESSING tab"""
        self._populate_activity_tab(
            self.access_frame,
            self.activities['accessed'],
            "File Access Activities",
            """Files that were accessed (opened or read).

Data Source: SyncEngineDatabase.db → diskLastAccessTime
Meaning: Last time file was accessed on local system

Note: NTFS access time updates can be disabled. If disabled,
this timestamp won't update. Check Windows NTFS settings.

Access time updates even for metadata operations (properties, thumbnails).

Columns:
- Timestamp: Last access time
- Name: Filename
- Path: Full OneDrive path
            """
        )

    def populate_download(self):
        """Populate DOWNLOADING tab"""
        self._populate_activity_tab(
            self.download_frame,
            self.activities['downloaded'],
            "File Download (Hydration) Activities",
            """Files downloaded from cloud to local disk.

Data Source: SyncEngineDatabase.db → HydrationData
Meaning: When files were "hydrated" (downloaded from OneDrive cloud)

Download Types:
- 'active': User-initiated download (opened file, selected "Always keep on device")
- 'passive': Automatic download (OneDrive decided to download)

Hydration Count: Number of times file was downloaded
- Count > 1: File was removed from disk and re-downloaded

No hydration data = File never downloaded (online-only)

Columns:
- FirstDownload: First time file was downloaded
- LastDownload: Most recent download
- DownloadType: active (user) or passive (automatic)
- DownloadCount: Total number of downloads
- Name: Filename
- Path: Full OneDrive path
            """
        )

    def populate_sync(self):
        """Populate SYNCING tab"""
        self._populate_activity_tab(
            self.sync_frame,
            self.activities['synced'],
            "File Sync Status",
            """Current sync state of files.

Data Source: DAT file → fileStatus
Meaning: Whether file is synced, syncing, or has issues

Status Codes:
0 = Unknown
1 = Synced (up to date)
2 = Synced (Available locally)
3 = Syncing (in progress)
4 = Sync Pending (queued)
5 = Sync Error (failed)
6 = Online Only (not downloaded to disk)
7 = Not Linked (not connected to OneDrive)
8 = Excluded (not syncing)
9 = Pinned (always keep on device)

Forensic Notes:
- Status 6 (Online Only): File exists in cloud but NOT on local disk
- Status 5 (Error): Investigate why sync failed
- Status 3 (Syncing): Was syncing when data captured

Columns:
- Status: Human-readable sync state
- StatusCode: Numeric code (0-9)
- Name: Filename
- Path: Full OneDrive path
            """
        )

    def populate_sharing(self):
        """Populate SHARING tab"""
        self._populate_activity_tab(
            self.sharing_frame,
            self.activities['shared'],
            "File Sharing Activities",
            """Files that are shared with other users.

Data Source: DAT file → bitMask bit 29
Meaning: File has been shared with others

This flag (bit 29 of 32-bit bitMask) indicates sharing status.
When set, file is shared via OneDrive/SharePoint sharing.

For detailed sharing information (who, when, permissions):
- Check FileUsageSync.db → SharedWithDetails (if available)
- Check ListSync.db → SharePoint metadata (if available)

Forensic Value:
- Data exfiltration detection (unexpected shares)
- Collaboration tracking
- Access control verification

Columns:
- SharedFlag: Sharing indicator value
- Name: Filename
- Path: Full OneDrive path

Note: Detailed sharing data (recipients, permissions, dates) requires
additional databases (FileUsageSync, ListSync) which may not always be present.
            """
        )

    def populate_deletion(self):
        """Populate REMOVING tab"""
        self._populate_activity_tab(
            self.deletion_frame,
            self.activities['deleted'],
            "File Deletion Activities",
            """Files that were deleted.

Data Source: SafeDelete.db → items_moved_to_recycle_bin
Meaning: Files moved to recycle bin by OneDrive

Deletion Tracking:
OneDrive maintains a separate database (SafeDelete.db) tracking
deletions before files are permanently removed.

Process Field:
Shows what deleted the file:
- 'OneDrive.exe': User deleted via OneDrive
- 'explorer.exe': User deleted via Windows Explorer
- Other: System or application deletion

Forensic Value:
- Anti-forensics detection (intentional deletions)
- Accidental deletion recovery
- Timeline reconstruction

Important: This only captures files deleted THROUGH OneDrive.
Files deleted by bypassing OneDrive (direct disk operations) won't appear here.

Columns:
- Timestamp: When file was deleted
- Process: What deleted the file
- Name: Filename
- Path: Original OneDrive path
            """
        )

    def _populate_activity_tab(self, parent_frame, activities, title, explanation):
        """Helper to populate activity tabs with consistent format"""
        for widget in parent_frame.winfo_children():
            widget.destroy()

        # Create scrollable canvas
        canvas = tk.Canvas(parent_frame)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
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
        ttk.Label(scrollable_frame, text=title, font=('Arial', 14, 'bold')).pack(pady=10)

        # Explanation panel
        info_panel = InfoPanel(
            scrollable_frame,
            title="How to Read This Data",
            message=explanation.split('\n\n')[0],  # First paragraph
            type="info",
            details='\n\n'.join(explanation.split('\n\n')[1:])  # Rest as details
        )
        info_panel.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Activity count
        count_card = StatisticCard(
            scrollable_frame,
            title="Total Activities",
            value=format_number(len(activities)),
            subtitle=f"Files with this activity type",
            icon="📊"
        )
        count_card.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Activity data
        if activities:
            df = pd.DataFrame(activities)

            # Create table frame
            table_frame = ttk.Frame(scrollable_frame)
            table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

            table = Table(table_frame, dataframe=df,
                         showtoolbar=True, showstatusbar=True)
            table.show()
        else:
            ttk.Label(scrollable_frame, text=f"No {title.lower()} found in this dataset",
                     font=('Arial', 12)).pack(pady=20)

    def export_report(self):
        """Export comprehensive activity report"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile="onedrive_file_lifecycle_report.csv"
            )

            if file_path:
                # Combine all activities into one export
                all_activities = []

                for activity_type, activities in self.activities.items():
                    for activity in activities:
                        activity['ActivityType'] = activity_type.upper()
                        all_activities.append(activity)

                if all_activities:
                    df = pd.DataFrame(all_activities)
                    df.to_csv(file_path, index=False)
                    self.status_label.config(
                        text=f"Exported {len(all_activities)} activities to {file_path}"
                    )
                    log.info(f"Exported lifecycle report to {file_path}")
                else:
                    self.status_label.config(text="No activities to export")

        except Exception as e:
            log.error(f"Error exporting report: {e}")
            self.status_label.config(text=f"Error exporting: {e}")
