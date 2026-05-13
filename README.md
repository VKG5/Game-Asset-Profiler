# Game Asset Profiler (Godot Auditor Branch)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Open%20Source-blue?logo=github)](https://github.com/VKG5/Game-Asset-Profiler/tree/godot-migrator)
[![Python](https://img.shields.io/badge/Python-3.9%2B-yellow?logo=python)](https://python.org)
[![PyQt5](https://img.shields.io/badge/UI-PyQt5-green)](https://pypi.org/project/PyQt5/)

**Godot Auditor Branch** of the Game Asset Profiler. This specialized branch transforms the core profiler into a powerful dependency tracking and safe-migration tool built explicitly for Godot Engine developers.

It introduces a native, high-performance reference auditor that recursively maps out dependencies across your entire Godot project without relying on heavy external math libraries.

---

## Table of Contents

- [Game Asset Profiler](#game-asset-profiler-godot-auditor-branch)
  - [Table of Contents](#table-of-contents)
  - [Godot-Specific Features](#-godot-specific-features)
    - [Native Dependencies](#1-native-dependency-graphing-no-external-libraries)
    - [Hierarchy](#2-interactive-reference-hierarchy)
    - [Safe Migrator](#3-safe-migrator)
    - [Asset Categorization](#4-expanded-asset-categorization)
    - [Architecture](#5-ephemeral-and-fast-architecture)
  - [UI Tabs Reference](#️-ui-tabs-reference)
  - [Keyboard Shortcuts](#️-keyboard-shortcuts)
  - [Installation \& Usage](#-installation--usage)

---

## 🌟 Godot-Specific Features

### 1. Native Dependency Graphing (No External Libraries)

Instead of using heavy graph libraries like NetworkX or SciPy, this branch utilizes optimized Python dictionaries (Adjacency Lists) to calculate the mathematical graph of your project. 
  - **Fast & Lightweight:** Processes thousands of files in seconds.
  - **Regex-Powered Parsing:** Scans `.tscn`, `.tres`, `.gd`, `.material`, `.anim`, and `.shader` files for `ext_resource` definitions and `preload()` calls to accurately map both Godot 3.x and Godot 4.x dependencies.

### 2. Interactive Reference Hierarchy

The new References Tab offers a dual-pane view:
  - **Left Pane (Folder View):** A clean, hierarchical view of your project files.
  - **Right Pane (Reference Tree):** Select any file on the left to instantly visualize its entire dependency chain. It recursively expands sub-dependencies and features **automatic circular-loop detection** (highlighted in red) to prevent infinite loops.

### 3. Safe Migrator

Refactoring or extracting a system from a monolithic Godot project is notoriously difficult due to broken res:// paths.
  - The **Safe Migrator** allows you to select a target file (e.g., `Player.tscn`), automatically gather all required sub-dependencies (scripts, textures, hitboxes, audio), and securely copy them to a new, empty directory.
  - **Zero Broken Links:** It reconstructs the exact relative `res://` folder hierarchy from the original project, ensuring no paths break when imported into a new Godot project.

### 4. Expanded Asset Categorization

The core scanner and Database Tab have been upgraded to recognize and filter specific game dev formats with custom UI emojis:
- **Code & Nodes:** `tscn` (📦), `tres` (📝), `gd` (📜), `shader`/`gdshader` (🖌️)
- **Audio:** `wav`, `ogg`, `mp3` (🎵)
- **Video:** `mp4`, `webm`, `ks9` (🎬)

### 5. Ephemeral and Fast Architecture

To keep the application highly responsive, the SQLite database is automatically wiped on both application startup and exit. This prevents stale data from slowing down the boot process, ensuring a snappy, fresh session every time you open the tool.

---

## 🖥️ UI Tabs Reference

| Tab | Purpose |
|---|---|
| Overview | Select your project folder and hit "Start Scan". The background `QThread` worker parses dependencies, saves the `project_root` to settings, and populates the database dynamically. |
| Database | Explore your assets with advanced filters. Easily filter by `tscn`, `gd`, `video`, etc. Double-click any file to open it in your system's default editor. |
| Visualization | Review VRAM and severity metrics via Matplotlib charts (from the core profiler). |
| References | *New!* Automatically loads the dependency graph of your scanned project. View hierarchical trees and trigger the Safe Migrator. |

---

## ⌨️ Keyboard Shortcuts

Press `Ctrl+?` at any time to view the in-app keyboard shortcuts reference dialog. This branch introduces new quality-of-life shortcuts, including a persistent theme toggler.

| Shortcut | Action |
|---|---|
| `Ctrl+T` | **Toggle Theme** (Instantly switch between Dark/Light modes) |
| `Ctrl+1` | Switch to Overview tab |
| `Ctrl+2` | Switch to Database tab |
| `Ctrl+3` | Switch to Visualization tab |
| `Ctrl+4` | Switch to **References tab** |
| `Ctrl+R` | Refresh all tabs / Reload database data |
| `Ctrl+F` | Focus the search box (Database tab) |
| `Ctrl+E` | Export selected assets to CSV |

---

## 🚀 Installation & Usage

1. **Install Dependencies**

   Ensure you have Python 3.9+ installed. Install required libraries:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Profiler**

   Launch the application:
   ```bash
   python main.py
   ```

3. **Workflow**
  - Go to the **Overview Tab**, click **Browse Project**, select your Godot project folder, and click **Start Scan.**
  - Switch to the **References Tab** (`Ctrl + 4`).
  - Click on a file in the Left Pane to view its dependencies in the Right Pane.
  - Click **Migrate Selected File & Dependencies** to extract the file safely.