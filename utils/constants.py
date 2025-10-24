"""
  1. アプリケーション基本情報
  2. ファイル・フォルダ関連
  3. UI関連（ウィンドウ、フォント）
  4. 検索機能関連
  5. PDF処理関連
  6. エラーメッセージ
  7. UIラベル
  8. その他の設定
"""

# ============================================================================
# 1. アプリケーション基本情報
# ============================================================================

APP_NAME = "マニュアル検索"


# ============================================================================
# 2. ファイル・フォルダ関連
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
# 3. UI関連（ウィンドウサイズ、フォント）
# ============================================================================

# --- ウィンドウサイズ（デフォルト） ---
DEFAULT_WINDOW_WIDTH = 1150
DEFAULT_WINDOW_HEIGHT = 900
DEFAULT_WINDOW_X = 50
DEFAULT_WINDOW_Y = 50

# --- ウィンドウサイズ（制限値） ---
MIN_WINDOW_WIDTH = 800
MAX_WINDOW_WIDTH = 3840
MIN_WINDOW_HEIGHT = 600
MAX_WINDOW_HEIGHT = 2160

# --- フォントサイズ（デフォルト） ---
DEFAULT_FONT_SIZE = 14
DEFAULT_HTML_FONT_SIZE = 16

# --- フォントサイズ（制限値） ---
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 32

# --- 色設定 ---
HIGHLIGHT_COLORS = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']

PDF_HIGHLIGHT_COLORS = [
    (1, 1, 0),      # 黄色
    (0.5, 1, 0.5),  # 薄緑
    (0.5, 0.7, 1),  # 薄青
    (1, 0.6, 0.4),  # オレンジ
    (1, 0.7, 0.7)   # ピンク
]

HIGHLIGHT_STYLE_TEMPLATE = 'background-color: {color}; padding: 2px; border-radius: 2px;'

# --- メッセージ表示時間（ミリ秒） ---
AUTO_CLOSE_MESSAGE_DURATION = 2000
CONFIRMATION_MESSAGE_DURATION = 5000
CURSOR_MOVE_DELAY = 100


# ============================================================================
# 4. 検索機能関連
# ============================================================================

# --- 検索タイプ ---
SEARCH_TYPE_AND = 'AND'
SEARCH_TYPE_OR = 'OR'

# --- 検索結果制限 ---
MAX_SEARCH_RESULTS_PER_FILE = 100

# --- デフォルト設定 ---
DEFAULT_CONTEXT_LENGTH = 100
DEFAULT_USE_INDEX_SEARCH = False

# --- インデックス設定 ---
INDEX_UPDATE_THRESHOLD_DAYS = 7

# --- 検索の正規表現パターン ---
SEARCH_TERM_SEPARATOR_PATTERN = r'[,、]'

# --- ネットワーク接続 ---
NETWORK_TIMEOUT = 5
DNS_TEST_HOST = "8.8.8.8"
DNS_TEST_PORT = 53


# ============================================================================
# 5. PDF処理関連
# ============================================================================

# --- デフォルト設定 ---
DEFAULT_ACROBAT_PATH = r'C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe'

# --- PDF処理のタイムアウト（秒） ---
DEFAULT_PDF_TIMEOUT = 30
MIN_PDF_TIMEOUT = 10
MAX_PDF_TIMEOUT = 120

# --- 一時ファイル管理 ---
DEFAULT_MAX_TEMP_FILES = 10
MIN_MAX_TEMP_FILES = 1
MAX_MAX_TEMP_FILES = 50

# --- Acrobatプロセス管理 ---
ACROBAT_PROCESS_NAMES = [
    'acrobat',      # Adobe Acrobat (フルバージョン)
    'acrord32',     # Adobe Acrobat Reader DC (32ビット版)
    'acrord64',     # Adobe Acrobat Reader DC (64ビット版)
    'acrobat.exe',  # 拡張子付きのパターン
    'acrord32.exe', # 拡張子付きのパターン (32ビット版)
    'acrord64.exe', # 拡張子付きのパターン (64ビット版)
    'reader_sl',    # Reader起動用の一部プロセス
]

ACROBAT_WAIT_TIMEOUT = 30
ACROBAT_WAIT_INTERVAL = 0.5

# --- ページナビゲーション ---
PAGE_NAVIGATION_RETRY_COUNT = 3
PAGE_NAVIGATION_DELAY = 0.5

# --- プロセス管理 ---
PROCESS_TERMINATE_TIMEOUT = 3
PROCESS_CLEANUP_DELAY = 1.0


# ============================================================================
# 6. ロギング関連
# ============================================================================

# --- デフォルト設定 ---
LOG_RETENTION_DAYS = 7


# ============================================================================
# 7. エラーメッセージ
# ============================================================================

ERROR_MESSAGES = {
    'FILE_NOT_FOUND': 'ファイルが見つかりません',
    'FILE_NOT_ACCESSIBLE': 'ファイルにアクセスできません',
    'UNSUPPORTED_FORMAT': 'サポートされていないファイル形式です',
    'PDF_ACCESS_FAILED': 'PDFファイルにアクセスできません',
    'ACROBAT_NOT_FOUND': 'Adobe Acrobat Readerが見つかりません',
    'ALL_ACROBAT_PATHS_NOT_FOUND': '設定されたパスをすべて確認しましたが、Adobe Acrobat/Readerの実行ファイルが見つかりませんでした。',
    'ACROBAT_START_FAILED': 'Acrobatの起動に失敗しました',
    'FOLDER_NOT_FOUND': '指定されたフォルダが見つかりません',
    'FOLDER_OPEN_FAILED': 'フォルダを開けませんでした',
    'ENCODING_DETECTION_FAILED': 'エンコーディングの検出に失敗しました',
    'FILE_DECODE_FAILED': 'ファイルのデコードに失敗しました'
}


# ============================================================================
# 8. UIラベル
# ============================================================================

UI_LABELS = {
    'SEARCH_PLACEHOLDER': '検索語を入力 ( , または 、区切りで複数語検索)',
    'SEARCH_BUTTON': '検索',
    'CLOSE_BUTTON': '閉じる',
    'ADD_BUTTON': '追加',
    'EDIT_BUTTON': '編集',
    'DELETE_BUTTON': '削除',
    'INCLUDE_SUBDIRS': 'サブフォルダ含む',
    'GLOBAL_SEARCH': 'フォルダ横断検索',
    'PDF_HIGHLIGHT': 'ハイライト付きPDF',
    'OPEN_FOLDER': 'フォルダを開く',
    'AND_SEARCH_LABEL': 'AND検索(複数の検索語をすべて含む)',
    'OR_SEARCH_LABEL': 'OR検索(複数の検索語のいずれかを含む)',
    'YES_BUTTON': 'はい',
    'NO_BUTTON': 'いいえ',
    'CONFIRM_EXIT': '検索を終了しますか?',
    'SEARCHING': '検索中...',
    'CANCEL': 'キャンセル',
    'SEARCH_PROGRESS_TITLE': '検索の進行状況'
}


# ============================================================================
# 9. 設定ファイル関連
# ============================================================================

CONFIG_SECTIONS = {
    'FILE_TYPES': 'FileTypes',
    'WINDOW_SETTINGS': 'WindowSettings',
    'SEARCH_SETTINGS': 'SearchSettings',
    'UI_SETTINGS': 'UISettings',
    'PATHS': 'Paths',
    'DIRECTORIES': 'Directories',
    'PDF_SETTINGS': 'PDFSettings',
    'INDEX_SETTINGS': 'IndexSettings'
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
    'USE_INDEX_SEARCH': 'use_index_search'
}


# ============================================================================
# 10. その他の設定
# ============================================================================

# --- Markdown拡張 ---
MARKDOWN_EXTENSIONS = ['nl2br']