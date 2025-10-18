import sys
import os
import warnings
import pytest

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# ワーニングの抑制
warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*_bootstrap.*")
warnings.filterwarnings("ignore", "builtin type.*has no __module__ attribute", DeprecationWarning)


def run_tests():
    """テストを実行"""
    args = [
        '-v',  # 詳細出力
        '--tb=short',  # トレースバックを短く
        '--disable-warnings',  # ワーニングを無効化
        '--cov=app',  # appモジュールのカバレッジ
        '--cov=service',  # serviceモジュールのカバレッジ
        '--cov=utils',  # utilsモジュールのカバレッジ
        '--cov=widgets',  # widgetsモジュールのカバレッジ
        '--cov-report=html',  # HTMLカバレッジレポート
        '--cov-report=term-missing',  # ターミナルにカバレッジ表示
        '--cov-config=.coveragerc',  # カバレッジ設定ファイル
    ]
    
    # 特定のテストファイルが指定された場合
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    
    # PyQt5のイベントループ関連の警告を抑制
    os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'
    
    # Python警告の設定
    os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'
    
    print("🚀 テスト実行を開始します...")
    print(f"📁 プロジェクトルート: {project_root}")
    print(f"🐍 Python バージョン: {sys.version}")
    print()
    
    # テスト実行
    exit_code = pytest.main(args)
    
    print()
    if exit_code == 0:
        print("✅ すべてのテストが成功しました！")
        print("📊 カバレッジレポート: htmlcov/index.html")
    else:
        print("❌ テストが失敗しました。")
        print(f"🔢 終了コード: {exit_code}")
    
    return exit_code


def run_specific_test(test_name: str):
    """特定のテストのみを実行"""
    args = [
        f"tests/{test_name}",
        '-v',
        '--disable-warnings',
        '--tb=short'
    ]
    return pytest.main(args)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].startswith('test_'):
        # 特定のテストファイルを実行
        sys.exit(run_specific_test(sys.argv[1]))
    else:
        # 全テストを実行
        sys.exit(run_tests())
