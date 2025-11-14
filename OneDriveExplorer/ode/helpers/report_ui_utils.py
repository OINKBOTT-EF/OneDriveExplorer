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
Enhanced UI Utilities for OneDriveExplorer Reporting Views
Provides reusable components for better UX, clarity, and visual appeal
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import logging

log = logging.getLogger(__name__)


class ToolTip:
    """
    Create a tooltip for a given widget with improved styling
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.showtip)
        self.widget.bind("<Leave>", self.hidetip)

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))

        # Styled tooltip
        frame = ttk.Frame(tw, relief='solid', borderwidth=1)
        frame.pack()
        label = ttk.Label(frame, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", foreground="black",
                         relief='flat', borderwidth=0,
                         font=("Arial", 9), padding=5)
        label.pack()

    def hidetip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class DateRangePicker(ttk.Frame):
    """
    Enhanced date range picker with preset options and validation
    """
    def __init__(self, master, callback=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.callback = callback
        self.setup_ui()

    def setup_ui(self):
        # Preset buttons row
        preset_frame = ttk.Frame(self)
        preset_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(preset_frame, text="Quick Presets:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))

        presets = [
            ("Last 24 Hours", 1),
            ("Last 7 Days", 7),
            ("Last 30 Days", 30),
            ("Last 90 Days", 90),
            ("All Time", 0)
        ]

        for label, days in presets:
            btn = ttk.Button(preset_frame, text=label,
                           command=lambda d=days: self.set_preset(d))
            btn.pack(side=tk.LEFT, padx=2)
            ToolTip(btn, f"Filter to show data from last {days} days" if days > 0 else "Show all available data")

        # Custom date entry row
        custom_frame = ttk.Frame(self)
        custom_frame.pack(fill=tk.X)

        ttk.Label(custom_frame, text="Custom Range:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(custom_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_from = ttk.Entry(custom_frame, width=20)
        self.date_from.pack(side=tk.LEFT, padx=(0, 10))
        self.date_from.insert(0, "YYYY-MM-DD HH:MM:SS")
        self.date_from.bind('<FocusIn>', lambda e: self.clear_placeholder(self.date_from, "YYYY-MM-DD HH:MM:SS"))
        ToolTip(self.date_from, "Enter start date/time\nFormat: YYYY-MM-DD HH:MM:SS\nExample: 2025-01-01 00:00:00")

        ttk.Label(custom_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_to = ttk.Entry(custom_frame, width=20)
        self.date_to.pack(side=tk.LEFT, padx=(0, 10))
        self.date_to.insert(0, "YYYY-MM-DD HH:MM:SS")
        self.date_to.bind('<FocusIn>', lambda e: self.clear_placeholder(self.date_to, "YYYY-MM-DD HH:MM:SS"))
        ToolTip(self.date_to, "Enter end date/time\nFormat: YYYY-MM-DD HH:MM:SS\nExample: 2025-12-31 23:59:59")

        ttk.Button(custom_frame, text="Apply", command=self.apply_custom).pack(side=tk.LEFT, padx=5)
        ttk.Button(custom_frame, text="Clear", command=self.clear_dates).pack(side=tk.LEFT, padx=5)

    def clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.configure(foreground='black')

    def set_preset(self, days):
        if days == 0:
            # All time
            self.date_from.delete(0, tk.END)
            self.date_to.delete(0, tk.END)
            self.date_from.insert(0, "YYYY-MM-DD HH:MM:SS")
            self.date_to.insert(0, "YYYY-MM-DD HH:MM:SS")
        else:
            now = datetime.now()
            past = now - timedelta(days=days)
            self.date_from.delete(0, tk.END)
            self.date_to.delete(0, tk.END)
            self.date_from.insert(0, past.strftime("%Y-%m-%d 00:00:00"))
            self.date_to.insert(0, now.strftime("%Y-%m-%d 23:59:59"))

        if self.callback:
            self.callback()

    def apply_custom(self):
        if self.callback:
            self.callback()

    def clear_dates(self):
        self.date_from.delete(0, tk.END)
        self.date_to.delete(0, tk.END)
        self.date_from.insert(0, "YYYY-MM-DD HH:MM:SS")
        self.date_to.insert(0, "YYYY-MM-DD HH:MM:SS")
        if self.callback:
            self.callback()

    def get_dates(self):
        """Return tuple of (from_date, to_date) or (None, None) if invalid"""
        from_str = self.date_from.get()
        to_str = self.date_to.get()

        if from_str == "YYYY-MM-DD HH:MM:SS":
            from_str = None
        if to_str == "YYYY-MM-DD HH:MM:SS":
            to_str = None

        return (from_str, to_str)


class ProgressBar(ttk.Frame):
    """
    Visual progress bar with percentage and color coding
    """
    def __init__(self, master, value=0, maximum=100, label="", show_percentage=True, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.value = value
        self.maximum = maximum
        self.show_percentage = show_percentage

        # Container
        container = ttk.Frame(self)
        container.pack(fill=tk.X, expand=True)

        # Label
        if label:
            ttk.Label(container, text=label, font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 10))

        # Progress bar
        self.progressbar = ttk.Progressbar(container, orient='horizontal',
                                          length=200, mode='determinate',
                                          maximum=maximum, value=value)
        self.progressbar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Percentage label
        if show_percentage:
            percentage = (value / maximum * 100) if maximum > 0 else 0
            self.pct_label = ttk.Label(container, text=f"{percentage:.1f}%",
                                       font=('Arial', 9, 'bold'))
            self.pct_label.pack(side=tk.LEFT, padx=(10, 0))

        # Color code based on percentage
        self.update_color()

    def update_color(self):
        """Update progress bar color based on value"""
        if self.maximum == 0:
            return

        percentage = (self.value / self.maximum) * 100

        # Note: ttk.Progressbar styling is theme-dependent
        # This is a visual indicator only
        if percentage >= 90:
            color = 'green'
        elif percentage >= 70:
            color = 'blue'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'

    def set_value(self, value):
        """Update progress bar value"""
        self.value = value
        self.progressbar['value'] = value
        if self.show_percentage:
            percentage = (value / self.maximum * 100) if self.maximum > 0 else 0
            self.pct_label.config(text=f"{percentage:.1f}%")
        self.update_color()


class StatisticCard(ttk.Frame):
    """
    Styled statistic card for displaying key metrics
    """
    def __init__(self, master, title, value, subtitle="", icon="", trend=None, *args, **kwargs):
        super().__init__(master, relief='groove', borderwidth=1, *args, **kwargs)
        self.setup_ui(title, value, subtitle, icon, trend)

    def setup_ui(self, title, value, subtitle, icon, trend):
        # Main container with padding
        container = ttk.Frame(self, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        # Title row with icon
        title_row = ttk.Frame(container)
        title_row.pack(fill=tk.X)

        if icon:
            ttk.Label(title_row, text=icon, font=('Arial', 16)).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(title_row, text=title, font=('Arial', 10)).pack(side=tk.LEFT)

        if trend:
            # Trend indicator (↑ up, ↓ down, → stable)
            trend_symbol = "↑" if trend > 0 else ("↓" if trend < 0 else "→")
            trend_color = "green" if trend > 0 else ("red" if trend < 0 else "gray")
            ttk.Label(title_row, text=trend_symbol, font=('Arial', 14),
                     foreground=trend_color).pack(side=tk.RIGHT)

        # Value (large text)
        ttk.Label(container, text=str(value), font=('Arial', 20, 'bold')).pack(anchor='w', pady=(5, 0))

        # Subtitle (if provided)
        if subtitle:
            ttk.Label(container, text=subtitle, font=('Arial', 8),
                     foreground='gray').pack(anchor='w')


class InfoPanel(ttk.Frame):
    """
    Informational panel with icon and expandable details
    """
    def __init__(self, master, title, message, type="info", details=None, *args, **kwargs):
        super().__init__(master, relief='solid', borderwidth=1, *args, **kwargs)
        self.details = details
        self.details_visible = False
        self.setup_ui(title, message, type)

    def setup_ui(self, title, message, type):
        # Icon mapping
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅',
            'tip': '💡'
        }

        # Color mapping
        colors = {
            'info': '#e7f3ff',
            'warning': '#fff3cd',
            'error': '#f8d7da',
            'success': '#d4edda',
            'tip': '#d1ecf1'
        }

        icon = icons.get(type, 'ℹ️')
        bg_color = colors.get(type, '#e7f3ff')

        # Main container
        container = ttk.Frame(self, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        # Header row
        header = ttk.Frame(container)
        header.pack(fill=tk.X)

        ttk.Label(header, text=icon, font=('Arial', 14)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(header, text=title, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)

        if self.details:
            self.expand_btn = ttk.Button(header, text="Show Details",
                                        command=self.toggle_details)
            self.expand_btn.pack(side=tk.RIGHT)

        # Message
        ttk.Label(container, text=message, font=('Arial', 9),
                 wraplength=600).pack(anchor='w', pady=(5, 0))

        # Details (hidden by default)
        if self.details:
            self.details_frame = ttk.Frame(container)
            self.details_label = ttk.Label(self.details_frame, text=self.details,
                                          font=('Arial', 8), wraplength=600,
                                          foreground='gray')
            self.details_label.pack(anchor='w', pady=(5, 0))

    def toggle_details(self):
        if self.details_visible:
            self.details_frame.pack_forget()
            self.expand_btn.config(text="Show Details")
            self.details_visible = False
        else:
            self.details_frame.pack(fill=tk.X, pady=(5, 0))
            self.expand_btn.config(text="Hide Details")
            self.details_visible = True


class SearchBox(ttk.Frame):
    """
    Enhanced search box with clear button and search icon
    """
    def __init__(self, master, callback=None, placeholder="Search...", width=40, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.callback = callback
        self.placeholder = placeholder
        self.search_var = tk.StringVar()
        self.setup_ui(width)

    def setup_ui(self, width):
        # Search icon (optional, using emoji)
        ttk.Label(self, text="🔍", font=('Arial', 12)).pack(side=tk.LEFT, padx=(0, 5))

        # Entry field
        self.entry = ttk.Entry(self, textvariable=self.search_var, width=width)
        self.entry.pack(side=tk.LEFT)
        self.entry.insert(0, self.placeholder)
        self.entry.bind('<FocusIn>', self.on_focus_in)
        self.entry.bind('<FocusOut>', self.on_focus_out)
        self.entry.configure(foreground='gray')

        # Bind search callback
        if self.callback:
            self.search_var.trace('w', lambda *args: self.callback(self.get_search_text()))

        # Clear button
        clear_btn = ttk.Button(self, text="✕", width=3, command=self.clear)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        ToolTip(clear_btn, "Clear search")

    def on_focus_in(self, event):
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.configure(foreground='black')

    def on_focus_out(self, event):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.configure(foreground='gray')

    def get_search_text(self):
        text = self.search_var.get()
        return text if text != self.placeholder else ""

    def clear(self):
        self.search_var.set("")
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.placeholder)
        self.entry.configure(foreground='gray')


class FilterCheckboxGroup(ttk.Frame):
    """
    Group of checkboxes with Select All/None functionality
    """
    def __init__(self, master, title, options, callback=None, columns=3, *args, **kwargs):
        """
        options: dict like {'key': 'Display Label'}
        """
        super().__init__(master, *args, **kwargs)
        self.options = options
        self.callback = callback
        self.vars = {}
        self.setup_ui(title, columns)

    def setup_ui(self, title, columns):
        # Title and controls row
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(header, text=title, font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Button(header, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(header, text="Select None", command=self.select_none).pack(side=tk.LEFT, padx=2)

        # Checkboxes in grid
        cb_frame = ttk.Frame(self)
        cb_frame.pack(fill=tk.X)

        row = 0
        col = 0
        for key, label in self.options.items():
            var = tk.BooleanVar(value=True)
            self.vars[key] = var

            cb = ttk.Checkbutton(cb_frame, text=label, variable=var,
                                command=self.on_change)
            cb.grid(row=row, column=col, sticky='w', padx=5, pady=2)

            col += 1
            if col >= columns:
                col = 0
                row += 1

    def select_all(self):
        for var in self.vars.values():
            var.set(True)
        self.on_change()

    def select_none(self):
        for var in self.vars.values():
            var.set(False)
        self.on_change()

    def on_change(self):
        if self.callback:
            self.callback()

    def get_selected(self):
        """Returns list of selected keys"""
        return [key for key, var in self.vars.items() if var.get()]


def format_number(value, decimals=0):
    """Format number with thousands separators"""
    if isinstance(value, (int, float)):
        if decimals > 0:
            return f"{value:,.{decimals}f}"
        return f"{value:,}"
    return str(value)


def format_bytes(bytes_value, precision=2):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.{precision}f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.{precision}f} PB"


def format_percentage(value, total, decimals=1):
    """Format as percentage with color coding"""
    if total == 0:
        return "0.0%"
    pct = (value / total) * 100
    return f"{pct:.{decimals}f}%"


def get_health_color(percentage):
    """Return color based on health percentage"""
    if percentage >= 90:
        return 'green'
    elif percentage >= 70:
        return 'blue'
    elif percentage >= 50:
        return 'orange'
    else:
        return 'red'


def get_health_status(percentage):
    """Return status text based on percentage"""
    if percentage >= 90:
        return "Excellent"
    elif percentage >= 70:
        return "Good"
    elif percentage >= 50:
        return "Fair"
    else:
        return "Poor"
