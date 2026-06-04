import subprocess


def build_executable():
    subprocess.run([
        "pyinstaller",
        "--name=マニュアル検索",
        "--windowed",
        "--icon=assets/ManualSearch.ico",
        "--add-data", "utils/config.ini:.",
        "--add-data", "templates:templates",
        "main.py"
    ])

    print(f"Executable built successfully.")


if __name__ == "__main__":
    build_executable()
