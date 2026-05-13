import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QShortcut
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QKeySequence
from collections import defaultdict

from db import fetch_flagged_assets

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        super(MplCanvas, self).__init__(self.fig)
        
        # Apply initial theme
        theme = QSettings("GameAssetProfiler", "GameAssetProfiler").value("theme", "dark")
        self.apply_theme(theme == "dark")

    def apply_theme(self, is_dark):
        """Update canvas colors based on the application theme"""
        bg_color = '#1e1e2e' if is_dark else '#f5f5f5'
        text_color = '#cdd6f4' if is_dark else '#333333'
        
        self.fig.patch.set_facecolor(bg_color)
        self.axes.set_facecolor(bg_color)
        self.axes.spines['bottom'].set_color(text_color)
        self.axes.spines['top'].set_color('none') 
        self.axes.spines['right'].set_color('none')
        self.axes.spines['left'].set_color(text_color)
        self.axes.tick_params(axis='x', colors=text_color)
        self.axes.tick_params(axis='y', colors=text_color)


class VisualizationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.chart_mode = "severity"  # severity or trending
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        header_layout = QHBoxLayout()
        title = QLabel("Insights Visualization")
        # Removed hardcoded color so it respects the active theme
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # Chart type toggle buttons - using setMinimumWidth to fix clipping
        self.severity_btn = QPushButton("Severity Distribution")
        self.severity_btn.setMinimumWidth(180)
        self.severity_btn.clicked.connect(self.show_severity_chart)
        
        self.trending_btn = QPushButton("Insights Trending")
        self.trending_btn.setMinimumWidth(180)
        self.trending_btn.clicked.connect(self.show_trending_chart)
        
        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.setMinimumWidth(120)
        self.refresh_btn.clicked.connect(self.load_data)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.severity_btn)
        header_layout.addWidget(self.trending_btn)
        header_layout.addWidget(self.refresh_btn)

        self.layout.addLayout(header_layout)

        # Matplotlib canvas
        self.canvas = MplCanvas(self, width=8, height=6, dpi=100)
        
        # Matplotlib standard toolbar (Zoom, Pan, Save, etc)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: transparent; border: none;")
        
        # Layout to push the toolbar strictly to the top right of the canvas
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.toolbar)

        self.layout.addLayout(toolbar_layout)
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)
        
        # Initialize button styles
        self._update_button_styles()

        # ========================= Keyboard Shortcuts =========================
        # Ctrl+R: Refresh visualization data
        QShortcut(QKeySequence.Refresh, self).activated.connect(self.load_data)

    def apply_theme(self, theme_name):
        """Called externally by MainWindow to dynamically update theme."""
        is_dark = theme_name == "dark"
        self.canvas.apply_theme(is_dark)
        self._update_button_styles()
        self.load_data()  # Redraw the chart using the new color scheme

    def _update_button_styles(self):
        """Highlights the active chart mode button based on the current theme."""
        theme = QSettings("GameAssetProfiler", "GameAssetProfiler").value("theme", "dark")
        active_bg = "#45475a" if theme == "dark" else "#d0d0d0"
        inactive_bg = "#313244" if theme == "dark" else "#e0e0e0"
        
        if self.chart_mode == "severity":
            self.severity_btn.setStyleSheet(f"background-color: {active_bg};")
            self.trending_btn.setStyleSheet(f"background-color: {inactive_bg};")
        else:
            self.severity_btn.setStyleSheet(f"background-color: {inactive_bg};")
            self.trending_btn.setStyleSheet(f"background-color: {active_bg};")

    def show_severity_chart(self):
        """Switch to severity distribution chart"""
        self.chart_mode = "severity"
        self._update_button_styles()
        self.load_data()

    def show_trending_chart(self):
        """Switch to insights trending chart"""
        self.chart_mode = "trending"
        self._update_button_styles()
        self.load_data()

    def load_data(self):
        try:
            flagged = fetch_flagged_assets()
        except:
            flagged = []
        
        if self.chart_mode == "severity":
            self.load_severity_chart(flagged)
        else:
            self.load_trending_chart(flagged)

    def load_severity_chart(self, flagged):
        """Load and display severity distribution chart"""
        severity_counts = defaultdict(int)

        for _, insights_str in flagged:
            insights = insights_str.split(" | ")
            for insight in insights:
                insight = insight.strip()
                if not insight:
                    continue
                
                parts = insight.split(":", 1)
                severity = parts[0].strip() if len(parts) > 1 else "UNKNOWN"
                severity_counts[severity] += 1
                
        self.update_severity_chart(severity_counts)

    def load_trending_chart(self, flagged):
        """Load and display insights trending chart (top 10 most frequent insights)"""
        insight_counts = defaultdict(int)

        for _, insights_str in flagged:
            insights = insights_str.split(" | ")
            for insight in insights:
                insight = insight.strip()
                if not insight:
                    continue
                insight_counts[insight] += 1
        
        self.update_trending_chart(insight_counts)

    def update_severity_chart(self, severity_counts):
        """Update the severity distribution bar chart"""
        self.canvas.axes.clear()
        
        theme = QSettings("GameAssetProfiler", "GameAssetProfiler").value("theme", "dark")
        text_color = '#cdd6f4' if theme == "dark" else '#333333'
        empty_color = '#bac2de' if theme == "dark" else '#999999'
        
        if not severity_counts:
            # Display highly visible empty state
            self.canvas.axes.text(0.5, 0.5, 'No Insights Available', 
                                  horizontalalignment='center', 
                                  verticalalignment='center',
                                  color=empty_color, fontsize=14)
            self.canvas.axes.set_xticks([])
            self.canvas.axes.set_yticks([])
            self.canvas.draw()
            return
            
        categories = []
        counts = []
        colors = []
        
        # Consistent ordering for styling
        target_severities = ["CRITICAL", "WARNING", "INFO", "SUGGESTION", "UNKNOWN"]
        
        color_map = {
            "CRITICAL": "#f38ba8",   # catppuccin red
            "WARNING": "#f9e2af",    # catppuccin yellow
            "INFO": "#89b4fa",       # catppuccin blue
            "SUGGESTION": "#a6e3a1", # catppuccin green
            "UNKNOWN": "#6c7086"     # catppuccin overlay
        }

        # Include severities that have counts, following the ordered list
        for s in target_severities:
            if severity_counts[s] > 0:
                categories.append(s)
                counts.append(severity_counts[s])
                colors.append(color_map[s])
                
        # Catch any rogue severities
        for s, count in severity_counts.items():
            if s not in target_severities and count > 0:
                categories.append(s)
                counts.append(count)
                colors.append(color_map["UNKNOWN"])

        bars = self.canvas.axes.bar(categories, counts, color=colors)
        
        self.canvas.axes.set_title('Asset Insights by Severity', color=text_color, pad=20, fontsize=14)
        self.canvas.axes.set_ylabel('Number of Instances', color=text_color)
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            self.canvas.axes.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                  f'{int(height)}',
                                  ha='center', va='bottom', color=text_color, fontsize=11, fontweight='bold')

        self.canvas.draw()

    def update_trending_chart(self, insight_counts):
        """Update the insights trending chart (top 10 most frequent insights)"""
        self.canvas.axes.clear()
        
        theme = QSettings("GameAssetProfiler", "GameAssetProfiler").value("theme", "dark")
        text_color = '#cdd6f4' if theme == "dark" else '#333333'
        empty_color = '#bac2de' if theme == "dark" else '#999999'
        
        if not insight_counts:
            # Display highly visible empty state
            self.canvas.axes.text(0.5, 0.5, 'No Insights Available', 
                                  horizontalalignment='center', 
                                  verticalalignment='center',
                                  color=empty_color, fontsize=14)
            self.canvas.axes.set_xticks([])
            self.canvas.axes.set_yticks([])
            self.canvas.draw()
            return
        
        # Sort by count and get top 10
        sorted_insights = sorted(insight_counts.items(), key=lambda x: x[1], reverse=True)
        top_insights = sorted_insights[:10]
        
        # Handle "Other" bucket if there are more than 10
        if len(sorted_insights) > 10:
            other_count = sum(count for _, count in sorted_insights[10:])
            top_insights.append(("Other", other_count))
        
        labels = [label for label, _ in top_insights]
        counts = [count for _, count in top_insights]
        
        # Color by severity (extract from insight label)
        color_map = {
            "CRITICAL": "#f38ba8",
            "WARNING": "#f9e2af",
            "INFO": "#89b4fa",
            "SUGGESTION": "#a6e3a1",
        }
        
        colors = []
        for label in labels:
            if "CRITICAL" in label:
                colors.append(color_map["CRITICAL"])
            elif "WARNING" in label:
                colors.append(color_map["WARNING"])
            elif "SUGGESTION" in label:
                colors.append(color_map["SUGGESTION"])
            else:
                colors.append(color_map["INFO"])
        
        # Create horizontal bar chart
        y_positions = range(len(labels))
        bars = self.canvas.axes.barh(y_positions, counts, color=colors)
        
        self.canvas.axes.set_yticks(y_positions)
        self.canvas.axes.set_yticklabels(labels, fontsize=9, color=text_color)
        self.canvas.axes.set_xlabel('Occurrence Count', color=text_color)
        self.canvas.axes.set_title('Top Insights by Frequency', color=text_color, pad=20, fontsize=14)
        
        # Add values at the end of bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            width = bar.get_width()
            self.canvas.axes.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                                  f'{int(count)}',
                                  ha='left', va='center', color=text_color, fontsize=10, fontweight='bold')
        
        self.canvas.draw()