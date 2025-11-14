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

    # Timestamp Age Categorization
    def categorize_timestamp_age(timestamp_str):
        """Categorize timestamps into age buckets for forensic analysis"""
        if not timestamp_str or timestamp_str == '':
            return 'No Timestamp'

        try:
            from datetime import datetime
            if isinstance(timestamp_str, str):
                # Parse timestamp (format: YYYY-MM-DD HH:MM:SS)
                ts = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            else:
                ts = timestamp_str

            now = datetime.now()
            age_days = (now - ts).days

            if age_days < 0:
                return 'Future Date (Suspicious)'
            elif age_days == 0:
                return 'Today'
            elif age_days == 1:
                return 'Yesterday'
            elif age_days <= 7:
                return 'Last 7 Days'
            elif age_days <= 30:
                return 'Last 30 Days'
            elif age_days <= 90:
                return 'Last 90 Days'
            elif age_days <= 180:
                return 'Last 6 Months'
            elif age_days <= 365:
                return 'Last Year'
            elif age_days <= 730:
                return '1-2 Years Ago'
            else:
                return f'{age_days // 365} Years Ago'
        except:
            return 'Invalid Date'

    # Apply timestamp categorization to lastChange
    if 'lastChange' in df_enriched.columns:
        df_enriched['File Age Category'] = df_enriched['lastChange'].apply(categorize_timestamp_age)

    # Apply timestamp categorization to firstHydrationTime
    if 'firstHydrationTime' in df_enriched.columns:
        df_enriched['First Download Age'] = df_enriched['firstHydrationTime'].apply(categorize_timestamp_age)

    # File Size Categorization
    if 'size' in df_enriched.columns:
        def categorize_file_size(size_str):
            """Categorize file sizes into forensic buckets"""
            try:
                if isinstance(size_str, str):
                    # Remove ' KB' and commas, convert to float
                    size_kb = float(size_str.replace(' KB', '').replace(',', ''))
                else:
                    size_kb = float(size_str) if pd.notna(size_str) else 0

                if size_kb == 0:
                    return 'Empty (0 KB)'
                elif size_kb < 1:
                    return 'Tiny (<1 KB)'
                elif size_kb < 100:
                    return 'Small (<100 KB)'
                elif size_kb < 1024:  # 1 MB
                    return 'Medium (100 KB - 1 MB)'
                elif size_kb < 10240:  # 10 MB
                    return 'Large (1-10 MB)'
                elif size_kb < 102400:  # 100 MB
                    return 'Very Large (10-100 MB)'
                elif size_kb < 1048576:  # 1 GB
                    return 'Huge (100 MB - 1 GB)'
                else:
                    return f'Massive (>{size_kb/1048576:.1f} GB)'
            except:
                return 'Unknown Size'

        df_enriched['Size Category'] = df_enriched['size'].apply(categorize_file_size)

    # Media Metadata Interpretation
    if 'mediaDateTaken' in df_enriched.columns:
        def interpret_media_metadata(row):
            """Interpret media file metadata"""
            date_taken = row.get('mediaDateTaken', '')
            width = row.get('mediaWidth', 0)
            height = row.get('mediaHeight', 0)
            duration = row.get('mediaDuration', 0)

            # Check if media metadata exists
            if date_taken and date_taken != '1970-01-01 00:00:00':
                media_type = 'Video' if duration > 0 else 'Photo'

                if width and height:
                    # Categorize resolution
                    pixels = width * height
                    if pixels >= 3840 * 2160:
                        resolution = '4K or Higher'
                    elif pixels >= 1920 * 1080:
                        resolution = 'Full HD (1080p)'
                    elif pixels >= 1280 * 720:
                        resolution = 'HD (720p)'
                    elif pixels >= 640 * 480:
                        resolution = 'SD'
                    else:
                        resolution = 'Low Resolution'

                    return f'{media_type} - {resolution} ({width}x{height})'
                else:
                    return media_type

            return 'No Media Metadata'

        df_enriched['Media Info'] = df_enriched.apply(interpret_media_metadata, axis=1)

    # Library Type Interpretation
    if 'libraryType' in df_enriched.columns:
        library_type_map = {
            0: 'Unknown Library',
            1: 'Personal OneDrive',
            2: 'SharePoint Document Library',
            3: 'SharePoint MySite',
            4: 'Teams',
            5: 'SharePoint List',
            6: 'External Share'
        }
        df_enriched['Library Type Description'] = df_enriched['libraryType'].apply(
            lambda x: library_type_map.get(x, f'Unknown ({x})') if pd.notna(x) else 'No Library Info'
        )

    # Path Depth Analysis
    if 'Path' in df_enriched.columns:
        def analyze_path_depth(path):
            """Analyze path depth for organizational insights"""
            if not path or path == '':
                return 'No Path'

            try:
                # Count backslashes to determine depth
                depth = path.count('\\')

                if depth == 0:
                    return 'Root Level'
                elif depth == 1:
                    return '1 Level Deep'
                elif depth == 2:
                    return '2 Levels Deep'
                elif depth == 3:
                    return '3 Levels Deep'
                elif depth <= 5:
                    return f'{depth} Levels Deep (Normal)'
                elif depth <= 10:
                    return f'{depth} Levels Deep (Deep)'
                else:
                    return f'{depth} Levels Deep (Very Deep - Potential Issue)'
            except:
                return 'Invalid Path'

        df_enriched['Path Depth'] = df_enriched['Path'].apply(analyze_path_depth)

    # eTag Version Analysis
    if 'eTag' in df_enriched.columns:
        def interpret_etag(etag):
            """Interpret eTag for version tracking"""
            if not etag or etag == '':
                return 'No Version Info'

            try:
                # eTag format is typically: "{GUID},version"
                if ',' in str(etag):
                    parts = str(etag).split(',')
                    version = parts[-1].strip('"}')
                    return f'Version {version}'
                return 'Version 1 (Initial)'
            except:
                return 'Unknown Version'

        df_enriched['File Version'] = df_enriched['eTag'].apply(interpret_etag)

    # Volume and Item Index Forensic Info
    if 'volumeID' in df_enriched.columns and 'itemIndex' in df_enriched.columns:
        def format_file_reference(row):
            """Format volumeID and itemIndex as File Reference Number"""
            volume = row.get('volumeID', '')
            item = row.get('itemIndex', '')

            if volume and item and volume != '' and str(item) != '0':
                return f'{volume}:{item}'
            return 'No File Reference'

        df_enriched['File Reference'] = df_enriched.apply(format_file_reference, axis=1)

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

    # File Extension and Type Categorization
    if 'Name' in df_enriched.columns:
        def categorize_file_type(filename):
            """Categorize files by extension for forensic analysis"""
            if not filename or filename == '':
                return 'No Filename'

            try:
                # Extract extension
                if '.' in filename:
                    ext = filename.rsplit('.', 1)[-1].lower()

                    # Document types
                    if ext in ['doc', 'docx', 'docm', 'dot', 'dotx', 'dotm']:
                        return 'Document - Word'
                    elif ext in ['xls', 'xlsx', 'xlsm', 'xlsb', 'xlt', 'xltx', 'xltm']:
                        return 'Document - Excel'
                    elif ext in ['ppt', 'pptx', 'pptm', 'pot', 'potx', 'potm', 'pps', 'ppsx', 'ppsm']:
                        return 'Document - PowerPoint'
                    elif ext in ['pdf']:
                        return 'Document - PDF'
                    elif ext in ['txt', 'rtf', 'odt', 'ods', 'odp']:
                        return 'Document - Other'

                    # Media types
                    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'heic']:
                        return 'Media - Image'
                    elif ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'm4v']:
                        return 'Media - Video'
                    elif ext in ['mp3', 'wav', 'wma', 'aac', 'flac', 'm4a', 'ogg']:
                        return 'Media - Audio'

                    # Archives
                    elif ext in ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'cab', 'iso']:
                        return 'Archive - Compressed'

                    # Executables and Scripts (potentially suspicious)
                    elif ext in ['exe', 'dll', 'sys', 'bat', 'cmd', 'com', 'scr']:
                        return 'Executable - Windows'
                    elif ext in ['ps1', 'psm1', 'psd1']:
                        return 'Executable - PowerShell'
                    elif ext in ['vbs', 'vbe', 'js', 'jse', 'wsf', 'wsh']:
                        return 'Executable - Script'
                    elif ext in ['msi', 'msp', 'msu']:
                        return 'Executable - Installer'

                    # Code and Development
                    elif ext in ['py', 'java', 'c', 'cpp', 'cs', 'js', 'ts', 'rb', 'go', 'rs']:
                        return 'Code - Source'
                    elif ext in ['html', 'htm', 'css', 'xml', 'json', 'yaml', 'yml']:
                        return 'Code - Markup'

                    # Database
                    elif ext in ['db', 'sqlite', 'mdb', 'accdb', 'sql']:
                        return 'Database'

                    # Email
                    elif ext in ['msg', 'eml', 'pst', 'ost']:
                        return 'Email'

                    # Virtual Machines
                    elif ext in ['vhd', 'vhdx', 'vmdk', 'ova', 'ovf']:
                        return 'Virtual Machine'

                    else:
                        return f'Other - .{ext}'
                else:
                    return 'No Extension'
            except:
                return 'Unknown Type'

        df_enriched['File Type Category'] = df_enriched['Name'].apply(categorize_file_type)

    # Suspicious Pattern Detection
    def detect_suspicious_patterns(row):
        """Flag potentially suspicious file patterns for investigation"""
        flags = []

        # Check file type
        file_type = row.get('File Type Category', '')
        if 'Executable' in file_type or 'Script' in file_type:
            flags.append('EXECUTABLE')

        # Check for empty files
        size_cat = row.get('Size Category', '')
        if 'Empty' in size_cat:
            flags.append('EMPTY_FILE')

        # Check for future dates (clock tampering)
        age_cat = row.get('File Age Category', '')
        if 'Future Date' in age_cat:
            flags.append('FUTURE_DATE')

        # Check for very deep paths (possible evasion)
        path_depth = row.get('Path Depth', '')
        if 'Very Deep' in path_depth:
            flags.append('DEEP_PATH')

        # Check for very old files that were recently downloaded (possible persistence)
        file_age = row.get('File Age Category', '')
        download_age = row.get('First Download Age', '')
        if download_age and 'Years Ago' in file_age and 'Days' in download_age:
            flags.append('OLD_FILE_RECENT_ACCESS')

        # Check for hidden file extensions (double extension)
        name = row.get('Name', '')
        if name:
            # Count dots in filename
            dot_count = name.count('.')
            if dot_count >= 2:
                flags.append('DOUBLE_EXTENSION')

        return ' | '.join(flags) if flags else 'No Suspicious Patterns'

    df_enriched['Suspicious Indicators'] = df_enriched.apply(detect_suspicious_patterns, axis=1)

    # Hash Algorithm Interpretation
    if 'localHashAlgorithm' in df_enriched.columns:
        def interpret_hash_algorithm(algo):
            """Interpret hash algorithm for integrity verification"""
            if not algo or algo == '':
                return 'No Hash'

            algo_str = str(algo).lower()

            if 'sha1' in algo_str:
                return 'SHA1 (Strong - Industry Standard)'
            elif 'quickxor' in algo_str:
                return 'quickXor (Fast - Microsoft Proprietary)'
            elif 'md5' in algo_str:
                return 'MD5 (Weak - Legacy)'
            elif 'sha256' in algo_str:
                return 'SHA256 (Very Strong)'
            else:
                return f'Unknown Algorithm ({algo})'

        df_enriched['Hash Algorithm Type'] = df_enriched['localHashAlgorithm'].apply(interpret_hash_algorithm)

    # Folder Status Interpretation
    if 'folderStatus' in df_enriched.columns:
        folder_status_map = {
            0: 'Unknown Folder Status',
            1: 'Folder Created',
            2: 'Folder Modified',
            3: 'Folder Renamed',
            4: 'Folder Moved',
            5: 'Folder Deleted',
            6: 'Folder Excluded',
            7: 'Folder Synced',
            8: 'Folder Error',
            9: 'Folder Pending'
        }
        df_enriched['Folder Status Description'] = df_enriched['folderStatus'].apply(
            lambda x: folder_status_map.get(x, f'Unknown Status ({x})') if pd.notna(x) else ''
        )

    # Notification/Deletion Time Age (for SafeDelete data)
    if 'notificationTime' in df_enriched.columns:
        df_enriched['Deletion Age'] = df_enriched['notificationTime'].apply(categorize_timestamp_age)

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
