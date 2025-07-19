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


def increment_version(version, increment_type="patch"):
    try:
        major, minor, patch = map(int, version.split("."))

        if increment_type == "major":
            return f"{major + 1}.0.0"
        elif increment_type == "minor":
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"
    except ValueError as e:
        print(f"Error: 無効なバージョン形式: {version}")
        return "0.0.1"


def update_version(increment_type="patch"):
    current_version = get_current_version()
    new_version = increment_version(current_version, increment_type)

    try:
        with open(APP_INIT_PATH, encoding='utf-8') as f:
            content = f.read()

        new_content = re.sub(
            r'(__version__\s*=\s*["\'])[^"\']+(["\'])',
            rf'\g<1>{new_version}\g<2>',
            content
        )

        with open(APP_INIT_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"バージョンを {current_version} から {new_version} に更新しました。")
        return new_version

    except Exception as e:
        print(f"Error: バージョン更新中にエラーが発生しました: {e}")
        return current_version

