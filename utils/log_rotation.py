import logging
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def setup_logging(log_directory: str = 'logs', log_retention_days: int = 7, log_name: str = 'ManualSearch', log_level: str = 'INFO'):
    project_root = get_project_root()
    log_dir_path = project_root / log_directory

    if not log_dir_path.exists():
        log_dir_path.mkdir(parents=True, exist_ok=True)

    log_file = log_dir_path / f'{log_name}.log'

    log_level_enum = getattr(logging, log_level.upper(), logging.INFO)

    file_handler = TimedRotatingFileHandler(filename=str(log_file), when='midnight', backupCount=log_retention_days,
                                            encoding='utf-8')
    file_handler.suffix = "%Y-%m-%d.log"
    file_handler.setLevel(log_level_enum)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level_enum)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logging.basicConfig(
        level=log_level_enum,
        handlers=[file_handler, console_handler]
    )

    cleanup_old_logs(log_dir_path, log_retention_days, log_name)
    logging.info(f"ログシステムを初期化しました: {log_file}")
    logging.info(f"ログレベル: {log_level}")


def cleanup_old_logs(log_directory: Path, retention_days: int, log_name: str):
    now = datetime.now()
    main_log_file = f'{log_name}.log'

    for file_path in log_directory.glob('*.log'):
        if file_path.name != main_log_file:
            file_modification_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if now - file_modification_time > timedelta(days=retention_days):
                try:
                    file_path.unlink()
                    logging.info(f"古いログファイルを削除しました: {file_path.name}")
                except OSError as e:
                    logging.error(f"ログファイルの削除中にエラーが発生しました {file_path.name}: {str(e)}")
