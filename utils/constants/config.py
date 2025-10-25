"""
アプリケーション設定関連の定数
"""

# ============================================================================
# アプリケーション基本情報
# ============================================================================

APP_NAME = "マニュアル検索"


# ============================================================================
# ファイル・フォルダ関連
# ============================================================================

SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.txt', '.md']

FILE_HANDLER_MAPPING = {
    '.pdf': '_open_pdf_file',
    '.txt': '_open_text_file',
    '.md': '_open_text_file'
}

SEARCH_METHODS_MAPPING = {
    '.pdf': 'search_pdf',
    '.txt': 'search_text',
    '.md': 'search_text'
}

TEMPLATE_DIRECTORY = 'templates'
TEXT_VIEWER_TEMPLATE = 'text_viewer.html'

FILE_TYPE_DISPLAY_NAMES = {
    '.txt': 'テキストファイル',
    '.md': 'Markdownファイル',
    '.pdf': 'PDFファイル',
    '.html': 'HTMLファイル',
    '.css': 'CSSファイル'
}

CONFIG_FILENAME = 'config.ini'
DEFAULT_INDEX_FILE = "search_index.json"


# ============================================================================
# 検索機能関連
# ============================================================================

SEARCH_TYPE_AND = 'AND'
SEARCH_TYPE_OR = 'OR'

MAX_SEARCH_RESULTS_PER_FILE = 100

DEFAULT_CONTEXT_LENGTH = 100
DEFAULT_USE_INDEX_SEARCH = False

INDEX_UPDATE_THRESHOLD_DAYS = 7

SEARCH_TERM_SEPARATOR_PATTERN = r'[,、]'


# ============================================================================
# PDF処理関連
# ============================================================================

DEFAULT_PDF_TIMEOUT = 30
MIN_PDF_TIMEOUT = 10
MAX_PDF_TIMEOUT = 120

DEFAULT_MAX_TEMP_FILES = 10
MIN_MAX_TEMP_FILES = 1
MAX_MAX_TEMP_FILES = 50


# ============================================================================
# ログ関連
# ============================================================================

LOG_RETENTION_DAYS = 7


# ============================================================================
# 設定ファイル関連
# ============================================================================

CONFIG_SECTIONS = {
    'FILE_TYPES': 'FileTypes',
    'WINDOW_SETTINGS': 'WindowSettings',
    'SEARCH_SETTINGS': 'SearchSettings',
    'UI_SETTINGS': 'UISettings',
    'PATHS': 'Paths',
    'DIRECTORIES': 'Directories',
    'PDF_SETTINGS': 'PDFSettings',
    'INDEX_SETTINGS': 'IndexSettings',
    'SEARCH': 'search'
}

CONFIG_KEYS = {
    'EXTENSIONS': 'extensions',
    'WINDOW_WIDTH': 'window_width',
    'WINDOW_HEIGHT': 'window_height',
    'WINDOW_X': 'window_x',
    'WINDOW_Y': 'window_y',
    'FONT_SIZE': 'font_size',
    'ACROBAT_PATH': 'acrobat_path',
    'ACROBAT_READER_PATH': 'acrobat_reader_path',
    'ACROBAT_READER_X86_PATH': 'acrobat_reader_x86_path',
    'DIRECTORY_LIST': 'list',
    'LAST_DIRECTORY': 'last_directory',
    'CONTEXT_LENGTH': 'context_length',
    'FILENAME_FONT_SIZE': 'filename_font_size',
    'RESULT_DETAIL_FONT_SIZE': 'result_detail_font_size',
    'HTML_FONT_SIZE': 'html_font_size',
    'TIMEOUT': 'timeout',
    'CLEANUP_TEMP_FILES': 'cleanup_temp_files',
    'MAX_TEMP_FILES': 'max_temp_files',
    'INDEX_FILE_PATH': 'index_file_path',
    'USE_INDEX_SEARCH': 'use_index_search',
    'USE_PDF_HIGHLIGHT': 'use_pdf_highlight'
}


# ============================================================================
# ファイル処理：マジックナンバー・拡張子パターン
# ============================================================================

PDF_MAGIC_NUMBER = b'%PDF'

FILE_EXTENSION_PDF = '.pdf'
FILE_EXTENSION_TXT = '.txt'
FILE_EXTENSION_MD = '.md'
FILE_EXTENSION_HTML = '.html'

FILE_TYPES = {
    'PDF': FILE_EXTENSION_PDF,
    'TEXT': FILE_EXTENSION_TXT,
    'MARKDOWN': FILE_EXTENSION_MD,
    'HTML': FILE_EXTENSION_HTML
}


# ============================================================================
# テキストファイル処理：エンコーディング設定
# ============================================================================

ENCODING_CANDIDATES = ['utf-8', 'cp1252', 'latin-1']
ENCODING_FALLBACK = 'latin-1'

PDF_TEXT_PAGE_SEPARATOR = '\n\n'
TEXT_LINE_SEPARATOR = '\n'


# ============================================================================
# その他の設定
# ============================================================================

MARKDOWN_EXTENSIONS = ['nl2br']

INDEX_DEFAULT_CONTEXT_LENGTH = 100
INDEX_MAX_RESULTS = 200
INDEX_HASH_READ_CHUNK_SIZE = 8192
INDEX_PROGRESS_LOG_INTERVAL = 10
