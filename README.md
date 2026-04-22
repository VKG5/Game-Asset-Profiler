# Game Asset Profiler

[![GitHub Repository](https://img.shields.io/badge/GitHub-Open%20Source-blue?logo=github)](https://github.com/VKG5/Game-Asset-Profiler)
[![Python](https://img.shields.io/badge/Python-3.8%2B-yellow?logo=python)](https://python.org)
[![PyQt5](https://img.shields.io/badge/UI-PyQt5-green)](https://pypi.org/project/PyQt5/)

**Game Asset Profiler** is a diagnostic and optimization tool for monitoring, analyzing, and visualizing the memory footprint of game assets. By scanning project directories and generating comprehensive per-file insights, it helps artists, developers, and technical directors identify asset bloat, unoptimized textures, and VRAM budget overruns.

This tool is specifically tailored towards the optimization of 2D Game Assets (such as PNGs, JPGs, and DDS textures) which are critical for high-fidelity 2D-heavy titles. It generates accurate, byte-level VRAM requirement metrics and offers severity-based visualizations to assist studios in maintaining performant experiences without sacrificing visual quality.

---

## Table of Contents

- [Game Asset Profiler](#game-asset-profiler)
  - [Table of Contents](#table-of-contents)
  - [Features Overview](#features-overview)
  - [VRAM Calculation Methodology](#vram-calculation-methodology)
    - [Standard Formats (PNG, JPG, TGA, BMP, etc.)](#standard-formats-png-jpg-tga-bmp-etc)
    - [DDS Format (GPU-Compressed Textures)](#dds-format-gpu-compressed-textures)
  - [Insight Engine \& Severity System](#insight-engine--severity-system)
    - [Numbered Sequence Detection](#numbered-sequence-detection)
    - [Disk Compression Heuristic](#disk-compression-heuristic)
  - [UI Tabs Reference](#ui-tabs-reference)
    - [Overview Tab](#overview-tab)
    - [Database Tab](#database-tab)
    - [Visualization Tab](#visualization-tab)
      - [1. Severity Distribution (Bar Chart)](#1-severity-distribution-bar-chart)
      - [2. Insights Trending (Horizontal Bar Chart)](#2-insights-trending-horizontal-bar-chart)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
    - [Global](#global)
    - [Overview Tab](#overview-tab-1)
    - [Database Tab](#database-tab-1)
    - [Visualization Tab](#visualization-tab-1)
  - [Right-Click Context Menus](#right-click-context-menus)
  - [Asset Starring \& Favorites](#asset-starring--favorites)
  - [Database Management (Load / Save / Export)](#database-management-load--save--export)
  - [Project Structure](#project-structure)
  - [Installation \& Usage](#installation--usage)

---

## Features Overview

| Feature | Description |
|---|---|
| **Multi-threaded Scanning** | Scans large project directories without blocking the UI using a `QThread`-based worker |
| **Byte-Level VRAM Metrics** | Calculates exact uncompressed in-memory texture size (IrfanView-aligned formula) |
| **DDS Format Support** | Treats DDS disk size as VRAM footprint (GPU-compressed, no decode overhead) |
| **Power-of-Two Detection** | Flags NPOT textures that waste GPU memory due to padding |
| **Numbered Sequence Detection** | Detects frame sequences (e.g. `anim_001.png`) and suggests texture atlas packing |
| **Severity-Coded Insights** | CRITICAL / WARNING / INFO / SUGGESTION tiers for every flagged asset |
| **Asset Starring** | Bookmark specific assets as Favorites — persists across sessions |
| **Regex Search** | Live search with optional full regex pattern matching |
| **Folder Tree View** | Hierarchical folder view with aggregated VRAM totals per folder |
| **Asset Thumbnails** | In-line 80×80 px image previews in the database table |
| **Dark & Light Themes** | Persistent theme preference saved between sessions |
| **Log Export** | Export insights log to `.txt` (categorized by severity) |
| **CSV Export** | Export selected database rows to `.csv` |
| **Database Load / Save** | Load external `.db` files or export the current scan state |

---

## VRAM Calculation Methodology

The profiler uses a **byte-accurate, IrfanView-aligned formula** to compute the uncompressed in-memory (VRAM) size for each texture. This is the same figure a GPU driver would need to allocate when a texture is fully decoded and uploaded.

### Standard Formats (PNG, JPG, TGA, BMP, etc.)

1. **Pixel loading via PIL** — The file is opened and `img.load()` is called to force full pixel decoding.
2. **`img.tobytes()` measurement** — The length of the raw byte buffer is taken. This is the **most authoritative** measure because it accounts for actual bit depth, colour mode padding, and any PIL-internal alignment — exactly matching what IrfanView reports as uncompressed size.
3. **Fallback formula** — For modes not fully supported by `tobytes()`, the fallback is:
   ```
   VRAM (bytes) = Width × Height × Bytes-Per-Pixel
   ```
   where BPP is determined by colour mode:

   | PIL Mode | BPP | Description |
   |---|---|---|
   | `1` | 1/8 | 1-bit bitmap |
   | `L` | 1 | 8-bit grayscale |
   | `P` | 1 | 8-bit palette |
   | `RGB` | 3 | 24-bit colour |
   | `RGBA` | 4 | 32-bit colour + alpha |
   | `CMYK` | 4 | CMYK print format |
   | `YCbCr` | 3 | Video colour format |
   | `I` / `F` | 4 | 32-bit integer/float |
   | `I;16` | 2 | 16-bit integer |

4. **Final conversion** — The byte count is divided by `1024 × 1024` to produce the VRAM figure in **MB**.

### DDS Format (GPU-Compressed Textures)

DDS files (DXT1, DXT5, BC7, etc.) are already GPU-compressed and uploaded to VRAM at their disk size without CPU-side decompression. Therefore:

```
VRAM (MB) = File Size on Disk (bytes) / 1024 / 1024
```

The compression block factors are documented for informational reference:

| Format | Bits/Pixel | Notes |
|---|---|---|
| DXT1 | 4 | ~0.5× uncompressed RGBA |
| DXT5 | 8 | ~1.0× equivalent (with alpha) |
| BC7 | 8 | High-quality, ~1.0× equivalent |

---

## Insight Engine & Severity System

After calculating metrics, every image asset is passed through the **Insight Engine** (`insights.py`) which generates zero or more tagged insight strings grouped by severity:

| Severity | Colour | Trigger Conditions |
|---|---|---|
| `CRITICAL` | 🔴 Red | VRAM ≥ 100 MB **or** resolution 4096+ px |
| `WARNING` | 🟡 Yellow | VRAM ≥ 50 MB **or** non-power-of-two dimensions |
| `INFO` | 🔵 Blue | RGBA texture (flag potential alpha waste), grayscale texture, 2K resolution |
| `SUGGESTION` | 🟢 Green | PNG/TGA with VRAM ≥ 50 MB (suggest BC/DXT GPU compression), numbered sequences detected (suggest atlas packing) |

### Numbered Sequence Detection

The engine uses a regex pattern to detect numbered frame animation sequences such as:

```
explosion_001.png, explosion_002.png, explosion_003.png ...
```

If **3 or more** consecutive files share the same base name, it recommends **Texture Atlas Packing** with tools like _TexturePacker_ to dramatically reduce draw calls and VRAM overhead.

### Disk Compression Heuristic

If `disk size / pixel count < 0.5`, the asset is flagged as **"Highly compressed on disk"** — a useful signal that the on-disk format may not reflect the true VRAM cost after decoding.

All insights are stored in the SQLite database as pipe-delimited strings:

```
CRITICAL: >100MB VRAM texture | WARNING: Non power-of-two texture | INFO: RGBA texture (check alpha usage)
```

---

## UI Tabs Reference

The application is organized into **three tabs**, each serving a distinct purpose in the asset profiling workflow.

### Overview Tab

The primary landing tab. Use this to begin a new scan or review existing insights.

**Sections:**

- **Folder Selection** — Click **Browse Project** to choose a root directory. The scanner recursively walks the entire folder tree.
- **Scan Controls** — **Start Scan** launches the background worker thread. **Stop Scan** gracefully halts mid-scan (already-processed assets are retained in the database).
- **Database Statistics Panel** — Always-visible live summary showing:
  - Total Assets scanned
  - Total VRAM across all assets (MB)
  - Average VRAM per asset (MB)
  - Type breakdown (images vs. other files)
- **Progress Bar** — Real-time scan progress (0–100%).
- **Generated Insights & Logs Table** — A filterable table of all flagged assets with columns: **Path**, **Severity**, **Message**.
  - **Filter dropdown** — Narrow down to `CRITICAL`, `WARNING`, `INFO`, `SUGGESTION`, or `All`.
  - **Insight count badge** — Shows the number of currently visible insights.
  - **Export Logs** — Exports the current filtered view to a `.txt` file, sorted by severity.

---

### Database Tab

Full searchable, sortable asset explorer backed by the SQLite database.

**Search & Filter Bar:**

| Control | Function |
|---|---|
| Search box | Live path search with 300ms debounce to avoid excess queries |
| **Regex Mode** checkbox | Enables full regular expression matching in the search box |
| Type filter | Filter by `All`, `image`, or `other` |
| VRAM filter | Filter by `> 10 MB`, `> 50 MB`, `> 100 MB` |
| **Clear Filters** button | Resets all filters to default |
| Asset count badge | Live count of currently displayed assets |

**Asset View (Table):**

The table contains the following columns:

| Column | Description |
|---|---|
| `★` | Favorite / Star indicator — click to toggle |
| Thumbnail | 80×80 px inline image preview (cached after first load) |
| Path | Full file path |
| Type | `image` or `other` |
| Size | Disk size in bytes |
| Width / Height | Image dimensions in pixels |
| Channels | Number of colour channels |
| VRAM (MB) | Uncompressed in-memory size — **red** if > 100 MB, **yellow** if > 50 MB |
| Insights | Severity-tagged insight string(s) for the asset |

- **Sortable** — Click any column header to sort ascending/descending.
- **Multi-select** — Hold `Ctrl` or `Shift` to select multiple rows.
- **Double-click** — Opens the file directly in your default application.

**Folder View (Tree):**

Toggle to a hierarchical folder tree that aggregates **total VRAM per folder**. Folders exceeding **1,000 MB** are highlighted red; folders exceeding **500 MB** are highlighted yellow. This makes it trivial to spot which sub-directories in a project are the biggest VRAM consumers.

**Bulk Actions Toolbar** (appears on multi-select):

- **★ Mark Favorite** — Stars all selected rows.
- **☆ Unmark Favorite** — Removes stars from all selected rows.
- **📊 Export Selected** — Exports selected rows to a `.csv` file.

---

### Visualization Tab

An interactive chart dashboard powered by **Matplotlib** embedded in the Qt window.

**Two Chart Modes:**

#### 1. Severity Distribution (Bar Chart)

Shows a vertical bar chart breaking down the total count of insight instances by severity level. Each bar is colour-coded:

| Severity | Chart Colour |
|---|---|
| CRITICAL | `#f38ba8` (red) |
| WARNING | `#f9e2af` (yellow) |
| INFO | `#89b4fa` (blue) |
| SUGGESTION | `#a6e3a1` (green) |

Value labels are rendered on top of each bar for immediate readability.

#### 2. Insights Trending (Horizontal Bar Chart)

Shows the **Top 10 most frequently occurring** individual insight messages ranked by occurrence count. If there are more than 10 unique insight types, the remaining are collapsed into an **"Other"** bucket. Each bar is colour-coded by the severity of its insight. This view is useful for identifying systemic issues (e.g. "NPOT textures" appearing across hundreds of files) that require a batch fix rather than individual remediation.

**Controls:**

- **Severity Distribution** / **Insights Trending** buttons — Switch between chart modes.
- **Refresh Data** button — Manually reload chart data from the database.
- `Ctrl+R` — Keyboard shortcut for refreshing.

---

## Keyboard Shortcuts

Press `Ctrl+?` at any time to view the in-app keyboard shortcuts reference dialog.

### Global

| Shortcut | Action |
|---|---|
| `Ctrl+?` | Show Keyboard Shortcuts dialog |
| `Ctrl+1` | Switch to Overview tab |
| `Ctrl+2` | Switch to Database tab |
| `Ctrl+3` | Switch to Visualization tab |
| `Ctrl+R` | Refresh all tabs |
| `Ctrl+O` | Load database file |
| `Ctrl+Shift+S` | Save database as… |
| `Ctrl+Q` | Exit application |

### Overview Tab

| Shortcut | Action |
|---|---|
| `Ctrl+N` | Start a new scan |
| `Ctrl+E` | Export current insights log to `.txt` |
| `Ctrl+C` | Copy selected log row's file path to clipboard |

### Database Tab

| Shortcut | Action |
|---|---|
| `Ctrl+F` | Focus the search box |
| `Ctrl+C` | Copy selected asset's file path to clipboard |
| `Ctrl+E` | Export selected assets to `.csv` |
| `Ctrl+R` | Refresh database view |

### Visualization Tab

| Shortcut | Action |
|---|---|
| `Ctrl+R` | Refresh visualization charts |

---

## Right-Click Context Menus

Right-clicking on any row in the **Overview Tab** or **Database Tab** opens a context menu with the following options:

| Menu Item | Action |
|---|---|
| **Open File** | Opens the asset file directly using the system default application |
| **Open Folder Location** | Opens the folder containing the file in the system file explorer |
| **Copy Path** | Copies the full absolute file path to the clipboard |
| **Toggle Favorite** *(Database Tab only)* | Stars/unstars the selected asset |

> **Tip:** In the Database Tab, clicking directly on the `★` column of any row also instantly toggles the favorite status without needing the context menu.

Additionally, **double-clicking** any row opens the file directly via the OS default application.

---

## Asset Starring & Favorites

The starring system allows you to bookmark specific assets for follow-up:

- Click the `★` / `☆` cell in the Database Tab, or use **right-click → Toggle Favorite**.
- Use **"★ Mark Favorite"** or **"☆ Unmark Favorite"** in the Bulk Actions toolbar to star/unstar multiple selected assets at once.
- Favorite status is stored persistently in the SQLite database — stars survive application restarts.
- Use the search and filter controls to isolate your starred assets for focused review.

---

## Database Management (Load / Save / Export)

All profiling results are stored in a local **SQLite database** (`assets.db`). The application provides full database management via the **File** menu:

| Action | Shortcut | Description |
|---|---|---|
| **Load Database...** | `Ctrl+O` | Opens a file browser to load any external `.db` file. All tabs refresh automatically to reflect the loaded database |
| **Save Database As...** | `Ctrl+Shift+S` | Copies the current live database to a new file path of your choice |
| **Export Database...** | `Ctrl+E` | Exports the current database state to a shareable `.db` file |
| **Clear Database...** | *(menu only)* | Wipes all records from the database with a confirmation dialog showing the asset count to be deleted |
| **Refresh** | `Ctrl+R` | Forces all three tabs to reload their data from the current database |

> **Workflow tip:** You can maintain separate `.db` files per project or milestone (e.g. `project_alpha_v1.db`, `project_alpha_v2.db`) and switch between them via **Load Database** to compare profiling results over time.

---

## Project Structure

```
Game_Asset_Profiler_v1.0.0/
│
├── __init__.py          # Application entry point — initialises PyQt5, applies QSS theme
├── scanner.py           # QThread-based multi-threaded directory scanner
├── metrics.py           # Byte-level VRAM calculation engine (IrfanView-aligned)
├── insights.py          # Insight Engine — severity tagging and sequence detection
├── db.py                # SQLite database layer (CRUD, search, stats, favorites)
├── utils.py             # Helpers (thumbnail generation, formatting)
├── assets.db            # SQLite database (created/maintained at runtime)
├── requirements.txt     # Python dependencies
│
└── ui/
    ├── __init__.py      # MainWindow, menu bar, theme switching, shortcuts dialog
    ├── main_window.py   # MainWindow alias/entry reference
    ├── style.qss        # Base Qt stylesheet (dark theme)
    ├── themes.py        # Dark and light theme stylesheets
    └── tabs/
        ├── overview_tab.py       # Scan controls, stats panel, insights log table
        ├── database_tab.py       # Asset explorer, folder tree, starring, CSV export
        ├── visualization_tab.py  # Matplotlib severity + trending charts
        └── folder_view_tab.py    # Standalone folder view component
```

---

## Installation & Usage

1. **Install Dependencies**

   Ensure you have Python 3.8+ installed. Install required libraries:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Profiler**

   Launch the application:
   ```bash
   python main.py
   ```
   *(Or use whichever entry point your environment is configured for)*

3. **Scan a Project**

   - Navigate to the **Overview** tab.
   - Click **Browse Project** and select your game assets root folder.
   - Click **Start Scan**. Results populate in real time.
   - Switch to **Database** or **Visualization** tabs to analyse results.
