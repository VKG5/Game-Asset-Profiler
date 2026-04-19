import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QShortcut
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from collections import defaultdict

from db import fetch_flagged_assets

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # Apply strict dark theme colors
        self.fig.patch.set_facecolor('#1e1e2e')
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#1e1e2e')
        self.axes.spines['bottom'].set_color('#cdd6f4')
        self.axes.spines['top'].set_color('none') 
        self.axes.spines['right'].set_color('none')
        self.axes.spines['left'].set_color('#cdd6f4')
        self.axes.tick_params(axis='x', colors='#cdd6f4')
        self.axes.tick_params(axis='y', colors='#cdd6f4')
        
        super(MplCanvas, self).__init__(self.fig)


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
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #cdd6f4;")
        
        # Chart type toggle buttons
        self.severity_btn = QPushButton("Severity Distribution")
        self.severity_btn.setFixedWidth(150)
        self.severity_btn.clicked.connect(self.show_severity_chart)
        self.severity_btn.setStyleSheet("background-color: #45475a;")
        
        self.trending_btn = QPushButton("Insights Trending")
        self.trending_btn.setFixedWidth(150)
        self.trending_btn.clicked.connect(self.show_trending_chart)
        
        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.setFixedWidth(120)
        self.refresh_btn.clicked.connect(self.load_data)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.severity_btn)
        header_layout.addWidget(self.trending_btn)
        header_layout.addWidget(self.refresh_btn)

        self.layout.addLayout(header_layout)

        # Matplotlib canvas
        self.canvas = MplCanvas(self, width=8, height=6, dpi=100)
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)

        # ========================= Keyboard Shortcuts =========================
        # Ctrl+R: Refresh visualization data
        QShortcut(QKeySequence.Refresh, self).activated.connect(self.load_data)

    def show_severity_chart(self):
        """Switch to severity distribution chart"""
        self.chart_mode = "severity"
        self.severity_btn.setStyleSheet("background-color: #45475a;")
        self.trending_btn.setStyleSheet("")
        self.load_data()

    def show_trending_chart(self):
        """Switch to insights trending chart"""
        self.chart_mode = "trending"
        self.severity_btn.setStyleSheet("")
        self.trending_btn.setStyleSheet("background-color: #45475a;")
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
        
        if not severity_counts:
            # Display highly visible empty state
            self.canvas.axes.text(0.5, 0.5, 'No Insights Available', 
                                  horizontalalignment='center', 
                                  verticalalignment='center',
                                  color='#bac2de', fontsize=14)
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
        
        self.canvas.axes.set_title('Asset Insights by Severity', color='#cdd6f4', pad=20, fontsize=14)
        self.canvas.axes.set_ylabel('Number of Instances', color='#cdd6f4')
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            self.canvas.axes.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                  f'{int(height)}',
                                  ha='center', va='bottom', color='#cdd6f4', fontsize=11, fontweight='bold')

        self.canvas.draw()

    def update_trending_chart(self, insight_counts):
        """Update the insights trending chart (top 10 most frequent insights)"""
        self.canvas.axes.clear()
        
        if not insight_counts:
            # Display highly visible empty state
            self.canvas.axes.text(0.5, 0.5, 'No Insights Available', 
                                  horizontalalignment='center', 
                                  verticalalignment='center',
                                  color='#bac2de', fontsize=14)
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
        self.canvas.axes.set_yticklabels(labels, fontsize=9)
        self.canvas.axes.set_xlabel('Occurrence Count', color='#cdd6f4')
        self.canvas.axes.set_title('Top Insights by Frequency', color='#cdd6f4', pad=20, fontsize=14)
        
        # Add values at the end of bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            width = bar.get_width()
            self.canvas.axes.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                                  f'{int(count)}',
                                  ha='left', va='center', color='#cdd6f4', fontsize=10, fontweight='bold')
        
        self.canvas.draw()
