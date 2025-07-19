import os
import re
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_INIT_PATH = os.path.join(PROJECT_ROOT, "app", "__init__.py")


def get_current_version():
    try:
        with open(APP_INIT_PATH, encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        else:
            print("Warning: __version__ が見つかりません。デフォルトバージョンを返します。")
            return "0.0.0"
    except FileNotFoundError:
        print(f"Error: {APP_INIT_PATH} が見つかりません。")
        return "0.0.0"
    except Exception as e:
        print(f"Error: バージョン取得中にエラーが発生しました: {e}")
        return "0.0.0"


def get_current_date():
    try:
        with open(APP_INIT_PATH, encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'__date__\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        else:
            print("Warning: __date__ が見つかりません。現在の日付を返します。")
            return datetime.now().strftime("%Y-%m-%d")
    except FileNotFoundError:
        print(f"Error: {APP_INIT_PATH} が見つかりません。")
        return datetime.now().strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error: 日付取得中にエラーが発生しました: {e}")
        return datetime.now().strftime("%Y-%m-%d")


def increment_version(version, increment_type="patch"):
    try:
        major, minor, patch = map(int, version.split("."))
        return f"{major}.{minor}.{patch + 1}"
    except ValueError as e:
        print(f"Error: 無効なバージョン形式: {version}")
        return "0.0.0"


def update_version(increment_type="patch"):
    current_version = get_current_version()
    current_date = get_current_date()
    new_version = increment_version(current_version, increment_type)
    new_date = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(APP_INIT_PATH, encoding='utf-8') as f:
            content = f.read()

        new_content = re.sub(
            r'(__version__\s*=\s*["\'])[^"\']+(["\'])',
            rf'\g<1>{new_version}\g<2>',
            content
        )

        new_content = re.sub(
            r'(__date__\s*=\s*["\'])[^"\']+(["\'])',
            rf'\g<1>{new_date}\g<2>',
            new_content
        )

        with open(APP_INIT_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return new_version

    except Exception as e:
        print(f"Error: 更新中にエラーが発生しました: {e}")
        return current_version
