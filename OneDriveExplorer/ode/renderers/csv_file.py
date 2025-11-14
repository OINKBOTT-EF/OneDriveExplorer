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
import json
import pandas as pd
import logging
from datetime import datetime

log = logging.getLogger(__name__)


def enrich_dataframe_with_activities(df):
    """
    Enrich dataframe with human-readable activity and status columns
    for better CSV/HTML export comprehension.
    """
    if df.empty:
        return df

    # Make a copy to avoid modifying the original
    df_enriched = df.copy()

    # File Status Interpretation (fileStatus codes 0-9)
    file_status_map = {
        0: 'Unknown',
        1: 'Folder Created',
        2: 'File Created',
        3: 'File Modified',
        4: 'File Renamed',
        5: 'File Moved',
        6: 'File Deleted (Synced)',
        7: 'Folder Synced',
        8: 'File Synced',
        9: 'Error/Pending'
    }

    if 'fileStatus' in df_enriched.columns:
        df_enriched['File Status Description'] = df_enriched['fileStatus'].apply(
            lambda x: file_status_map.get(x, 'Unknown') if pd.notna(x) else ''
        )

    # Hydration Status (Download Activity)
    if 'firstHydrationTime' in df_enriched.columns and 'lastHydrationTime' in df_enriched.columns:
        def get_hydration_status(row):
            first_hydration = row.get('firstHydrationTime', '')
            last_hydration = row.get('lastHydrationTime', '')
            hydration_count = row.get('hydrationCount', 0)
            hydration_type = row.get('lastHydrationType', '')

            if not first_hydration and not last_hydration:
                return 'Never Downloaded (Online-Only)'
            elif hydration_count > 1:
                return f'Downloaded {hydration_count} times (Last: {hydration_type})'
            elif hydration_type == 'active':
                return 'Downloaded (User-Initiated)'
            elif hydration_type == 'passive':
                return 'Downloaded (Automatic)'
            else:
                return 'Downloaded'

        df_enriched['Download Status'] = df_enriched.apply(get_hydration_status, axis=1)

    # Sharing Status
    if 'sharedItem' in df_enriched.columns:
        df_enriched['Sharing Status'] = df_enriched['sharedItem'].apply(
            lambda x: 'Shared' if x == 1 else 'Not Shared' if x == 0 else ''
        )

    # Activity Summary - determine primary activity based on available data
    def get_activity_summary(row):
        activities = []

        # Check for creation
        if row.get('fileStatus') in [1, 2]:
            activities.append('CREATED')

        # Check for modification
        if row.get('fileStatus') in [3]:
            activities.append('UPDATED')

        # Check for movement
        if row.get('fileStatus') in [4, 5]:
            activities.append('MOVED/RENAMED')

        # Check for deletion
        if row.get('fileStatus') == 6 or row.get('inRecycleBin') == 1:
            activities.append('DELETED')

        # Check for download
        if row.get('firstHydrationTime'):
            activities.append('DOWNLOADED')

        # Check for sharing
        if row.get('sharedItem') == 1:
            activities.append('SHARED')

        # Check for sync status
        if row.get('fileStatus') in [7, 8]:
            activities.append('SYNCED')

        return ' | '.join(activities) if activities else 'No Activity Detected'

    df_enriched['Activity Summary'] = df_enriched.apply(get_activity_summary, axis=1)

    # Folder Color Interpretation (if available)
    if 'folderColor' in df_enriched.columns:
        folder_color_map = {
            0: 'Default',
            1: 'Blue',
            2: 'Green',
            3: 'Yellow',
            4: 'Red',
            5: 'Purple'
        }
        df_enriched['Folder Color Name'] = df_enriched['folderColor'].apply(
            lambda x: folder_color_map.get(x, 'Default') if pd.notna(x) else ''
        )

    # Recycle Bin Status
    if 'inRecycleBin' in df_enriched.columns:
        df_enriched['Recycle Bin Status'] = df_enriched['inRecycleBin'].apply(
            lambda x: 'In Recycle Bin' if x == 1 else 'Active' if x == 0 else ''
        )

    # Permissions Summary (simplify spoPermissions array)
    if 'spoPermissions' in df_enriched.columns:
        def summarize_permissions(perms):
            if not perms or perms == '':
                return 'No Permissions Data'
            try:
                # Handle string representation of list
                if isinstance(perms, str):
                    perms = eval(perms)
                if isinstance(perms, list):
                    if 'FullControl' in perms or 'EditListItems' in perms:
                        return 'Full Control / Edit'
                    elif 'AddListItems' in perms and 'DeleteListItems' in perms:
                        return 'Read/Write/Delete'
                    elif 'ViewListItems' in perms:
                        return 'Read Only'
                return 'Custom Permissions'
            except:
                return 'Permissions Data Error'

        df_enriched['Permissions Summary'] = df_enriched['spoPermissions'].apply(summarize_permissions)

    return df_enriched


def print_csv(df, rbin_df, name, csv_path, comment, fus):
    log.info('Started writing CSV file with activity enrichment')
    data_dict = json.loads(comment)

    if not os.path.exists(csv_path):
        os.makedirs(csv_path)

    if not df.empty:
        # Enrich with activity-focused columns BEFORE sorting
        df = enrich_dataframe_with_activities(df)

        parent_col = 'parentResourceID' if 'parentResourceID' in df.columns else 'ParentFileSystemId'
        df = df.sort_values(by=['Level', parent_col, 'Type', 'FileSort', 'FolderSort', 'libraryType'],
                            ascending=[False, False, False, True, False, False])

        df = df.drop(['Level', 'FileSort', 'FolderSort'], axis=1)

    if not rbin_df.empty:
        # Enrich recycle bin data too
        rbin_df = enrich_dataframe_with_activities(rbin_df)
        df = pd.concat([df, rbin_df], ignore_index=True, axis=0)

    csv_file = os.path.basename(name).split('.')[0]+"_OneDrive.csv"
    fus_file = os.path.basename(name).split('.')[0]+"_FileUsageSync.csv"

    if data_dict["Name"] == 'Microsoft.ListSync.db':
        csv_file = os.path.basename(name).split('.')[0]+"_OneDrive_list_sync.csv"

    if data_dict["Name"] == 'Microsoft.FilesOnDemand.db':
        csv_file = os.path.basename(name).split('.')[0]+"_OneDrive_fod.csv"

    file_extension = os.path.splitext(name)[1][1:]

    if file_extension == 'previous':
        csv_file = os.path.basename(name).split('.')[0]+"_"+file_extension+"_OneDrive.csv"
        fus_file = os.path.basename(name).split('.')[0]+"_"+file_extension+"_FileUsageSync.csv"

    if not df.empty:
        with open(csv_path + '/' + csv_file, 'w', encoding='utf-8', newline='') as f:
            f.write(f'#{comment}\n')  # Add your comment here
            df.to_csv(f, index=False, encoding='utf-8')

    if not fus.empty:
        with open(csv_path + '/' + fus_file, 'w', encoding='utf-8', newline='') as f:
            fus.to_csv(f, index=False, encoding='utf-8')
