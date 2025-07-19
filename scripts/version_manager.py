import os
import re
from datetime import datetime
import sys

# プロジェクトルートディレクトリのパスを取得
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_INIT_PATH = os.path.join(PROJECT_ROOT, "app", "__init__.py")


def get_current_version():
    """app/__init__.pyから現在のバージョンを取得"""
    try:
        with open(APP_INIT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # __version__ = "x.x.x" の形式を検索
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
    """
    バージョンを増加させる
    increment_type: "major", "minor", "patch" (デフォルト: "patch")
    """
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
    """
    app/__init__.pyのバージョンを更新
    increment_type: "major", "minor", "patch" (デフォルト: "patch")
    """
    current_version = get_current_version()
    new_version = increment_version(current_version, increment_type)

    try:
        with open(APP_INIT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # __version__ = "x.x.x" を新しいバージョンに置換
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


def update_version_py(new_version):
    """scripts/version.pyファイルを更新する（後方互換性のため）"""
    version_py_path = os.path.join(os.path.dirname(__file__), "version.py")

    try:
        with open(version_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        # version.pyが存在しない場合は新規作成
        content = 'VERSION = "1.0.0"\nLAST_UPDATED = "2025/07/11"'

    # バージョン情報を更新
    content = re.sub(r'VERSION = "[0-9.]+"', f'VERSION = "{new_version}"', content)

    # 最終更新日を更新
    today = datetime.now().strftime("%Y/%m/%d")
    content = re.sub(r'LAST_UPDATED = "[0-9/]+"', f'LAST_UPDATED = "{today}"', content)

    with open(version_py_path, 'w', encoding='utf-8') as f:
        f.write(content)


def get_version_info():
    """バージョン情報の詳細を取得"""
    version = get_current_version()

    try:
        # app/__init__.pyからその他の情報も取得
        with open(APP_INIT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        author_match = re.search(r'__author__\s*=\s*["\']([^"\']+)["\']', content)
        email_match = re.search(r'__email__\s*=\s*["\']([^"\']+)["\']', content)

        return {
            'version': version,
            'author': author_match.group(1) if author_match else 'Unknown',
            'email': email_match.group(1) if email_match else 'Unknown'
        }
    except Exception as e:
        print(f"Error: バージョン情報取得中にエラーが発生しました: {e}")
        return {
            'version': version,
            'author': 'Unknown',
            'email': 'Unknown'
        }


# 後方互換性のための関数
def update_main_py(new_version):
    """非推奨: update_version_py を使用してください"""
    print("Warning: update_main_py は非推奨です。update_version_py を使用してください。")
    update_version_py(new_version)


if __name__ == "__main__":
    """コマンドライン実行時の処理"""
    if len(sys.argv) > 1:
        increment_type = sys.argv[1]
        if increment_type in ["major", "minor", "patch"]:
            update_version(increment_type)
        else:
            print("使用方法: python version_manager.py [major|minor|patch]")
    else:
        # 引数がない場合はpatchバージョンを更新
        update_version("patch")
