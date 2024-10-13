import os
import subprocess
import sys
from typing import List, Tuple


def run_monkeytype_command(command: List[str], cwd: str) -> Tuple[int, str, str]:
    print(f"実行コマンド: {' '.join(command)}")
    print(f"作業ディレクトリ: {cwd}")
    process = subprocess.Popen(command,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True, encoding='utf-8',
                               cwd=cwd)
    stdout, stderr = process.communicate()
    print(f"標準出力:\n{stdout}")
    print(f"標準エラー出力:\n{stderr}")
    return process.returncode, stdout, stderr


def add_type_hints(python_file: str) -> None:
    script_path = os.path.abspath(python_file)
    script_dir = os.path.dirname(script_path)
    module_name = os.path.splitext(os.path.basename(python_file))[0]

    print(f"1. MonkeyTypeを実行してスクリプトの実行情報を収集")
    run_command = [
        sys.executable,
        "-c",
        f"import sys; sys.path.insert(0, '{script_dir}'); "
        f"from monkeytype import trace; "
        f"trace('{module_name}');"
    ]
    returncode, stdout, stderr = run_monkeytype_command(run_command, script_dir)
    if returncode != 0:
        print(f"エラー: MonkeyType の実行中にエラーが発生しました。")
        return

    print(f"2. 収集した情報を基に型ヒントを適用")
    apply_command = [
        sys.executable,
        "-c",
        f"import sys; sys.path.insert(0, '{script_dir}'); "
        f"from monkeytype import cli; "
        f"cli.apply_stub_handler(cli.apply_stub_args('{module_name}'), sys.stdout, sys.stderr);"
    ]
    returncode, stdout, stderr = run_monkeytype_command(apply_command, script_dir)
    if returncode != 0:
        print(f"エラー: 型ヒントの適用中にエラーが発生しました。")
        return

    with open(script_path, 'r', encoding='utf-8') as file:
        updated_content = file.read()

    print(f"更新されたファイル内容:")
    print(updated_content[:500] + "..." if len(updated_content) > 500 else updated_content)

    print(f"型ヒントが {python_file} に追加されました。")


def get_target_script() -> str:
    while True:
        python_file = input("型ヒントを追加するPythonスクリプトのファイル名を入力してください: ")
        if os.path.isfile(python_file) and python_file.endswith('.py'):
            return python_file
        else:
            print("エラー: 指定されたファイルが存在しないか、Pythonスクリプト(.py)ではありません。")


if __name__ == "__main__":
    print("Pythonスクリプトに型ヒントを追加するツール")
    target_script = get_target_script()
    add_type_hints(target_script)
