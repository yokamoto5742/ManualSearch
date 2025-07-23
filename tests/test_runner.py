#!/usr/bin/env python
"""
テスト実行スクリプト
すべてのユニットテストを実行し、カバレッジレポートを生成します。
"""

import sys
import os
import pytest

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def run_tests():
    """テストを実行"""
    args = [
        '-v',  # 詳細出力
        '--tb=short',  # トレースバックを短く
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
    
    # テスト実行
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n✅ すべてのテストが成功しました！")
        print("📊 カバレッジレポート: htmlcov/index.html")
    else:
        print("\n❌ テストが失敗しました。")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(run_tests())
