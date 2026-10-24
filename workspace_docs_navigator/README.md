# Workspace Docs Navigator

An offline, dependency-free document navigator for this repository. It scans Markdown files below the repository root and makes their full text searchable in a browser.

## Start

Double-click `START_NAVIGATOR.bat`, or open a terminal here and run:

```powershell
python app.py
```

Open `http://127.0.0.1:8765`. Press `Ctrl+C` in the terminal to stop it.

## What it does

- finds workspace `.md` files dynamically
- excludes Git data, dependencies, virtual environments, caches, builds, and Obsidian metadata
- searches the title, path, headings, and full text (multiple words use AND matching)
- sorts by title, modified date, or path
- groups documents into collections and automatically inferred categories
- renders a local reader with a heading outline
- includes a Connections map for resolved Markdown links and Obsidian wikilinks
- includes a clickable folder tree for every indexed document, including unlinked notes
- keeps every document on `127.0.0.1`; it makes no network request and uploads nothing

Use **Refresh index** after creating, renaming, or editing Markdown files.
