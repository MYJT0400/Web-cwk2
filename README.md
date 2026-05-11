# Coursework 2 - Search Engine Tool

## Project Overview and Purpose

This project is a Python command-line search tool for the `quotes.toscrape.com` website.

Its purpose is to:

- crawl pages from the target website,
- build an inverted index while crawling,
- store the compiled index in the file system,
- load the saved index later,
- print the postings list for a word,
- find pages that contain one or more query terms.

The current implementation performs full in-domain crawling, uses case-insensitive token normalization, and stores per-page word statistics including frequency and positions.

## Installation and Setup

### Requirements

- Python 3.12 or later recommended

### Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### Install dependencies

```powershell
pip install -r requirements.txt
```

## Dependencies

The project uses the following packages:

- `requests` for HTTP requests
- `beautifulsoup4` for HTML parsing
- `pytest` for automated testing

These dependencies can be installed with:

```powershell
pip install -r requirements.txt
```

## Usage Examples

The program supports both:

- interactive shell mode
- one-command execution mode

### Start the interactive shell

```powershell
python src/main.py
```

Inside the shell, you can run the four required commands directly.

### 1. Build

Build crawls the website, creates the inverted index during crawling, and saves output files.

Interactive shell example:

```text
build
```

One-command example:

```powershell
python src/main.py --mode once build
```

### 2. Load

Load reads a previously saved index from the file system.

Interactive shell example:

```text
load
```

One-command example:

```powershell
python src/main.py --mode once load --index-path data/inverted_index.json
```

### 3. Print

Print shows the inverted index entry for a single word.

Interactive shell example:

```text
print nonsense
```

One-command example:

```powershell
python src/main.py --mode once print nonsense --index-path data/inverted_index.json
```

### 4. Find

Find returns pages containing the query term or query terms.

Single-word example:

```text
find indifference
```

Multi-word example:

```text
find good friends
```

One-command example:

```powershell
python src/main.py --mode once find good friends --index-path data/inverted_index.json
```

## Output Files

By default, the build command writes:

- `data/crawl_pages.txt`
- `data/inverted_index.json`

The index file stores:

- `metadata`
- `index`

Each indexed word maps to one or more pages, and each page stores:

- `frequency`
- `positions`

## Testing Instructions

Run the automated test suite with:

```powershell
python -m pytest -q
```

The tests cover:

- crawler behavior,
- inverted index construction,
- index saving and loading,
- search behavior,
- invalid and edge-case inputs.

