import subprocess

def build_executable():
    subprocess.run([
        "pyinstaller",
        "--windowed",
        "rebuild_index.py"
    ])

    print(f"Executable built successfully.")


if __name__ == "__main__":
    build_executable()
