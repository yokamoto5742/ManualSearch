import subprocess

from scripts.version_manager import update_version, update_main_py


def build_executable():
    new_version = update_version()
    update_main_py(new_version)

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


if __name__ == "__main__":
    build_executable()
