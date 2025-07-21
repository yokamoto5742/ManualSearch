# -*- coding: utf-8 -*-
"""
定数管理ファイル
アプリケーション全体で使用される定数を一元管理します。
"""

# アプリケーション情報
APP_NAME = "マニュアル検索"

# ファイル拡張子
SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.txt', '.md']

# ファイル形式とハンドラーの対応
FILE_HANDLER_MAPPING = {
    '.pdf': '_open_pdf_file',
    '.txt': '_open_text_file',
    '.md': '_open_text_file'
}

# 検索関連の定数
SEARCH_METHODS_MAPPING = {
    '.pdf': 'search_pdf',
    '.txt': 'search_text',
    '.md': 'search_text'
}

MAX_SEARCH_RESULTS_PER_FILE = 100

# 検索タイプ
SEARCH_TYPE_AND = 'AND'
SEARCH_TYPE_OR = 'OR'

# デフォルト設定値
DEFAULT_WINDOW_WIDTH = 1150
DEFAULT_WINDOW_HEIGHT = 900
DEFAULT_WINDOW_X = 50
DEFAULT_WINDOW_Y = 50
DEFAULT_FONT_SIZE = 14
DEFAULT_HTML_FONT_SIZE = 16
DEFAULT_CONTEXT_LENGTH = 100
DEFAULT_PDF_TIMEOUT = 30
DEFAULT_MAX_TEMP_FILES = 10

# ウィンドウサイズの範囲
MIN_WINDOW_WIDTH = 800
MAX_WINDOW_WIDTH = 3840
MIN_WINDOW_HEIGHT = 600
MAX_WINDOW_HEIGHT = 2160

# フォントサイズの範囲
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 32

# タイムアウト値の範囲
MIN_PDF_TIMEOUT = 10
MAX_PDF_TIMEOUT = 120

# 最大一時ファイル数の範囲
MIN_MAX_TEMP_FILES = 1
MAX_MAX_TEMP_FILES = 50

# ネットワーク関連
NETWORK_TIMEOUT = 5
DNS_TEST_HOST = "8.8.8.8"
DNS_TEST_PORT = 53

# ハイライト色設定
HIGHLIGHT_COLORS = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']

# PDF処理用の色設定（RGB）
PDF_HIGHLIGHT_COLORS = [
    (1, 1, 0),      # 黄色
    (0.5, 1, 0.5),  # 薄緑
    (0.5, 0.7, 1),  # 薄青
    (1, 0.6, 0.4),  # オレンジ
    (1, 0.7, 0.7)   # ピンク
]

# PDF処理関連の定数
ACROBAT_WAIT_TIMEOUT = 30
ACROBAT_WAIT_INTERVAL = 0.5
PAGE_NAVIGATION_RETRY_COUNT = 3
PAGE_NAVIGATION_DELAY = 0.5

# プロセス終了関連
PROCESS_TERMINATE_TIMEOUT = 3
PROCESS_CLEANUP_DELAY = 1.0

# UI関連の定数
AUTO_CLOSE_MESSAGE_DURATION = 2000
CONFIRMATION_MESSAGE_DURATION = 5000
CURSOR_MOVE_DELAY = 100

# 設定ファイル関連
CONFIG_FILENAME = 'config.ini'

# デフォルトパス
DEFAULT_ACROBAT_PATH = r'C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe'

# 設定セクション名
CONFIG_SECTIONS = {
    'FILE_TYPES': 'FileTypes',
    'WINDOW_SETTINGS': 'WindowSettings',
    'SEARCH_SETTINGS': 'SearchSettings',
    'UI_SETTINGS': 'UISettings',
    'PATHS': 'Paths',
    'DIRECTORIES': 'Directories',
    'PDF_SETTINGS': 'PDFSettings',
    'INDEX_SETTINGS': 'IndexSettings'  # 新規追加
}

# 設定キー名
CONFIG_KEYS = {
    'EXTENSIONS': 'extensions',
    'WINDOW_WIDTH': 'window_width',
    'WINDOW_HEIGHT': 'window_height',
    'WINDOW_X': 'window_x',
    'WINDOW_Y': 'window_y',
    'FONT_SIZE': 'font_size',
    'ACROBAT_PATH': 'acrobat_path',
    'DIRECTORY_LIST': 'list',
    'LAST_DIRECTORY': 'last_directory',
    'CONTEXT_LENGTH': 'context_length',
    'FILENAME_FONT_SIZE': 'filename_font_size',
    'RESULT_DETAIL_FONT_SIZE': 'result_detail_font_size',
    'HTML_FONT_SIZE': 'html_font_size',
    'TIMEOUT': 'timeout',
    'CLEANUP_TEMP_FILES': 'cleanup_temp_files',
    'MAX_TEMP_FILES': 'max_temp_files',
    'INDEX_FILE_PATH': 'index_file_path',  # 新規追加
    'USE_INDEX_SEARCH': 'use_index_search'  # 新規追加
}

# エラーメッセージ
ERROR_MESSAGES = {
    'FILE_NOT_FOUND': 'ファイルが見つかりません',
    'FILE_NOT_ACCESSIBLE': 'ファイルにアクセスできません',
    'UNSUPPORTED_FORMAT': 'サポートされていないファイル形式です',
    'PDF_ACCESS_FAILED': 'PDFファイルにアクセスできません',
    'ACROBAT_NOT_FOUND': 'Adobe Acrobat Readerが見つかりません',
    'ACROBAT_START_FAILED': 'Acrobatの起動に失敗しました',
    'FOLDER_NOT_FOUND': '指定されたフォルダが見つかりません',
    'FOLDER_OPEN_FAILED': 'フォルダを開けませんでした',
    'ENCODING_DETECTION_FAILED': 'エンコーディングの検出に失敗しました',
    'FILE_DECODE_FAILED': 'ファイルのデコードに失敗しました'
}

# UI文字列
UI_LABELS = {
    'SEARCH_PLACEHOLDER': '検索語を入力 ( , または 、区切りで複数語検索)',
    'SEARCH_BUTTON': '検索',
    'CLOSE_BUTTON': '閉じる',
    'ADD_BUTTON': '追加',
    'EDIT_BUTTON': '編集',
    'DELETE_BUTTON': '削除',
    'INCLUDE_SUBDIRS': 'サブフォルダを含む',
    'OPEN_FOLDER': 'フォルダを開く',
    'AND_SEARCH_LABEL': 'AND検索(1ページに複数の検索語をすべて含む)',
    'OR_SEARCH_LABEL': 'OR検索(1ページに複数の検索語のいずれかを含む)',
    'YES_BUTTON': 'はい',
    'NO_BUTTON': 'いいえ',
    'CONFIRM_EXIT': '検索を終了しますか?',
    'SEARCHING': '検索中...',
    'CANCEL': 'キャンセル',
    'SEARCH_PROGRESS_TITLE': '検索の進行状況'
}

# テンプレート関連
TEMPLATE_DIRECTORY = 'templates'
TEXT_VIEWER_TEMPLATE = 'text_viewer.html'

# ファイルタイプ表示名
FILE_TYPE_DISPLAY_NAMES = {
    '.txt': 'テキストファイル',
    '.md': 'Markdownファイル',
    '.pdf': 'PDFファイル',
    '.html': 'HTMLファイル',
    '.css': 'CSSファイル'
}

# Markdown拡張
MARKDOWN_EXTENSIONS = ['nl2br']

# 正規表現パターン
SEARCH_TERM_SEPARATOR_PATTERN = r'[,、]'

# CSS関連
HIGHLIGHT_STYLE_TEMPLATE = 'background-color: {color}; padding: 2px; border-radius: 2px;'

# プロセス名検索パターン
ACROBAT_PROCESS_NAMES = [
    'acrobat',      # Adobe Acrobat (フルバージョン)
    'acrord32',     # Adobe Acrobat Reader DC (32ビット版)
    'acrord64',     # Adobe Acrobat Reader DC (64ビット版)
    'acrobat.exe',  # 拡張子付きのパターン
    'acrord32.exe', # 拡張子付きのパターン (32ビット版)
    'acrord64.exe', # 拡張子付きのパターン (64ビット版)
    'reader_sl',    # Reader起動用の一部プロセス
]

# インデックス関連
DEFAULT_INDEX_FILE = "search_index.json"
INDEX_UPDATE_THRESHOLD_DAYS = 7
DEFAULT_USE_INDEX_SEARCH = False
