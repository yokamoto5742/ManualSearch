import subprocess

from scripts.version_manager import update_version, update_version_py


def build_executable(increment_type="patch"):
    """
    実行ファイルをビルドする
    increment_type: "major", "minor", "patch" (デフォルト: "patch")
    """
    # バージョンを更新
    new_version = update_version(increment_type)

    # 後方互換性のためにscripts/version.pyも更新
    update_version_py(new_version)

    # PyInstallerでビルド
    subprocess.run([
        "pyinstaller",
        "--name=ManualSearch",
        "--windowed",
        "--icon=assets/ManualSearch.ico",
        "--add-data", "utils/config.ini:.",
        "--add-data", "templates:templates",
        "main.py"
    ])

    print(f"Executable built successfully. Version: {new_version}")
    return new_version


def build_major():
    """メジャーバージョンアップしてビルド"""
    return build_executable("major")


def build_minor():
    """マイナーバージョンアップしてビルド"""
    return build_executable("minor")


def build_patch():
    """パッチバージョンアップしてビルド"""
    return build_executable("patch")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        increment_type = sys.argv[1]
        if increment_type in ["major", "minor", "patch"]:
            build_executable(increment_type)
        else:
            print("使用方法: python build.py [major|minor|patch]")
            print("例:")
            print("  python build.py major   # 1.0.0 -> 2.0.0")
            print("  python build.py minor   # 1.0.0 -> 1.1.0")
            print("  python build.py patch   # 1.0.0 -> 1.0.1")
    else:
        # 引数がない場合はpatchバージョンでビルド
        build_executable("patch")
