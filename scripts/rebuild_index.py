import argparse
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from service.search_indexer import SearchIndexer
from utils.config_manager import ConfigManager


def parse_arguments():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description="インデックスの完全再構築を行います",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python scripts/rebuild_index.py
  python scripts/rebuild_index.py --index-file my_index.json
  python scripts/rebuild_index.py --config-file /path/to/config.ini
        """
    )
    
    parser.add_argument(
        '--index-file', 
        type=str, 
        help='インデックスファイルのパス（デフォルト: 設定ファイルから取得）'
    )
    
    parser.add_argument(
        '--config-file',
        type=str,
        help='設定ファイルのパス（デフォルト: 標準設定ファイル）'
    )
    
    parser.add_argument(
        '--no-subdirs',
        action='store_true',
        help='サブディレクトリを含めない（デフォルトは含める）'
    )
    
    
    return parser.parse_args()




def print_progress(current: int, total: int):
    """進捗表示"""
    percentage = (current / total) * 100 if total > 0 else 0
    bar_length = 50
    filled_length = int(bar_length * current // total) if total > 0 else 0
    
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r[{bar}] {current}/{total} ({percentage:.1f}%)', end='', flush=True)
    
    if current == total:
        print()  # 改行


def main():
    """メイン処理"""
    args = parse_arguments()
    
    try:
        # 設定管理の初期化
        if args.config_file:
            config_manager = ConfigManager(args.config_file)
        else:
            config_manager = ConfigManager()
        
        # インデックスファイルパスの決定
        if args.index_file:
            index_file_path = args.index_file
        else:
            index_file_path = config_manager.get_index_file_path()
        
        print(f"インデックス再構築スクリプト")
        print(f"インデックスファイル: {index_file_path}")
        print(f"設定ファイル: {config_manager.config_file}")
        print("-" * 50)
        
        # ディレクトリ設定の取得
        directories = config_manager.get_directories()
        if not directories:
            print("エラー: 検索対象ディレクトリが設定されていません。")
            print("アプリケーションで検索ディレクトリを設定してから再実行してください。")
            return 1
        
        print(f"検索対象ディレクトリ ({len(directories)}個):")
        for i, directory in enumerate(directories, 1):
            if os.path.exists(directory):
                print(f"  {i}. {directory} ✓")
            else:
                print(f"  {i}. {directory} ✗ (存在しません)")
        
        include_subdirs = not args.no_subdirs
        print(f"サブディレクトリを含む: {'はい' if include_subdirs else 'いいえ'}")
        print()
        
        # インデックス再構築の開始
        if os.path.exists(index_file_path):
            print(f"既存のインデックスファイルが見つかりました: {index_file_path}")
            print("既存のインデックスを削除して再構築します。")
        else:
            print("新しいインデックスを作成します。")
        
        # 既存インデックスの削除
        if os.path.exists(index_file_path):
            try:
                os.remove(index_file_path)
                print(f"既存のインデックスファイルを削除しました: {index_file_path}")
            except OSError as e:
                print(f"エラー: インデックスファイルの削除に失敗しました: {e}")
                return 1
        
        # インデックスの再構築
        print("インデックスの再構築を開始します...")
        print()
        
        indexer = SearchIndexer(index_file_path)
        
        try:
            indexer.create_index(
                directories=directories,
                include_subdirs=include_subdirs,
                progress_callback=print_progress
            )
            
            print("\nインデックス再構築が完了しました！")
            
            # 統計情報の表示
            stats = indexer.get_index_stats()
            print(f"\n=== インデックス統計 ===")
            print(f"インデックス化されたファイル数: {stats['files_count']}")
            print(f"総ファイルサイズ: {stats['total_size_mb']:.2f} MB")
            print(f"インデックスファイルサイズ: {stats['index_file_size_mb']:.2f} MB")
            print(f"作成日時: {stats['created_at']}")
            print(f"最終更新: {stats['last_updated']}")
            
            return 0
            
        except Exception as e:
            print(f"\nエラー: インデックス再構築中にエラーが発生しました: {e}")
            return 1
            
    except Exception as e:
        print(f"エラー: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)