# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返す。
- 変更範囲は最小限に抑える。
- コードの修正は直接適用する。
- コーディング規約はPEP8に従う。コメントは必要最小限にする。
- 可読性を優先する。一度読んだだけで理解できるコードが最高です。
- Pythonコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## Automatic Notifications (Hooks)
自動通知は`.claude/settings.local.json` で設定：
- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## Development Commands

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test types
python -m pytest -m unit -v               # Unit tests only
python -m pytest -m integration -v        # Integration tests only
python -m pytest -m gui -v                # GUI tests only (requires display)

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run single test
python -m pytest tests/test_file_searcher.py::TestFileSearcher::test_search_functionality -v
```

### Running the Application
```bash
# Run the main application
python main.py

# Build executable (if needed)
python build.py
```

## Architecture Overview

### Core Design Patterns
- **MVC Pattern**: Model (Service layer), View (Widgets), Controller (MainWindow)
- **Qt Signal System**: Decoupled communication between components using PyQt5 signals
- **Thread-based Processing**: File searching and indexing run in separate QThread instances
- **Plugin-like File Handlers**: Extensible file type support via handler mapping

### Directory Structure
```
ManualSearch/
├── main.py                     # Application entry point
├── constants.py                # Global constants and configuration mappings
├── app/
│   └── main_window.py          # Main UI controller and component orchestration
├── service/                    # Core business logic
│   ├── file_searcher.py        # Multi-threaded file searching engine
│   ├── indexed_file_searcher.py # Smart indexer-based search with fallback
│   ├── search_indexer.py       # Full-text index creation and management
│   ├── file_opener.py          # Cross-platform file opening with Adobe integration
│   ├── pdf_handler.py          # PDF processing and highlighting
│   └── text_handler.py         # Text file processing
├── widgets/                    # UI components
│   ├── search_widget.py        # Search input and controls
│   ├── results_widget.py       # Search results display with highlighting
│   ├── directory_widget.py     # Directory selection and management
│   └── index_management_widget.py # Index building and maintenance UI
└── utils/
    ├── config_manager.py       # INI-based configuration persistence
    └── helpers.py              # Shared utility functions
```

### Key Architecture Components

#### Search System
- **FileSearcher**: Multi-threaded search engine that processes files in parallel using ThreadPoolExecutor
- **SmartFileSearcher**: Intelligent search router that uses index when available, falls back to direct file search
- **SearchIndexer**: Creates and maintains full-text search indexes with file modification tracking

#### File Processing Pipeline
1. File discovery via os.walk() with extension filtering
2. Content extraction using format-specific handlers (PDF via PyMuPDF, text via encoding detection)
3. Search term matching with configurable AND/OR logic
4. Context extraction with highlighting markup
5. Result aggregation and UI display

#### Configuration System
- INI file-based configuration (`utils/config.ini`)
- Hierarchical settings with validation and defaults
- Runtime setting updates with immediate persistence
- Window geometry, fonts, search behavior, and Adobe Acrobat integration paths

### File Format Support
Extensible via `constants.py` mappings:
- **PDF**: PyMuPDF (fitz) for text extraction, Adobe integration for viewing with highlights
- **Text/Markdown**: Auto-encoding detection, HTML template rendering with search highlighting
- **Add new formats**: Update `SUPPORTED_FILE_EXTENSIONS`, `FILE_HANDLER_MAPPING`, and `SEARCH_METHODS_MAPPING`

### Threading Model
- **UI Thread**: Main application and widget interactions
- **FileSearcher Thread**: Parallel file processing with progress signals
- **Index Building**: Background index creation with progress tracking
- All threads communicate via Qt signals to maintain thread safety

### Adobe Acrobat Integration
- Process management and PDF highlighting via temporary files
- Configurable Acrobat executable path
- Network folder path translation for UNC paths
- Cleanup of temporary highlighted PDF files

## Key Development Notes

### Configuration Management
- Settings are stored in `utils/config.ini` with automatic creation on first run
- ConfigManager handles validation, defaults, and type conversion
- Window geometry and UI state are automatically persisted

### Search Performance
- Index-based search provides significant performance improvement for large document collections
- Incremental index updates based on file modification time
- Configurable index file location and usage toggle

### Error Handling
- Comprehensive file accessibility checks before processing  
- Graceful encoding detection with fallbacks for text files
- Process cleanup for Adobe Acrobat integration failures

### Testing Strategy
- Pytest configuration in `pytest.ini` with multiple test markers
- GUI testing support via pytest-qt
- Coverage reporting with HTML output to `htmlcov/`
- Integration tests for file processing pipelines