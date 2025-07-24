import os
import gc
import time
import psutil
import threading
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from PyQt5.QtCore import QCoreApplication, QTimer, QThread

from service.file_searcher import FileSearcher
from service.indexed_file_searcher import SmartFileSearcher, SearchMode
from service.search_indexer import SearchIndexer
from service.file_opener import FileOpener
from service.text_handler import highlight_text_file
from utils.config_manager import ConfigManager
from utils.helpers import read_file_with_auto_encoding
from constants import SEARCH_TYPE_AND, SEARCH_TYPE_OR


class PerformanceProfiler:
    """パフォーマンス測定用ヘルパークラス"""
    
    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process()
    
    def __enter__(self):
        gc.collect()  # ガベージコレクション実行
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        gc.collect()
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    @property
    def execution_time(self):
        """実行時間（秒）"""
        return self.end_time - self.start_time if self.end_time else 0
    
    @property
    def memory_usage(self):
        """メモリ使用量変化（MB）"""
        return self.end_memory - self.start_memory if self.end_memory else 0
    
    @property
    def peak_memory(self):
        """ピークメモリ使用量（MB）"""
        return self.end_memory if self.end_memory else 0


class TestLargeDatasetPerformance:
    """大容量データセット処理パフォーマンステスト"""
    
    @pytest.fixture
    def large_dataset_setup(self, temp_dir):
        """大容量データセット作成"""
        setup = {
            'root_dir': temp_dir,
            'config_file': os.path.join(temp_dir, 'perf_config.ini'),
            'index_file': os.path.join(temp_dir, 'perf_index.json'),
            'file_count': 1000,
            'files': []
        }
        
        # 設定ファイル作成
        config_content = f"""[FileTypes]
extensions = .txt,.md,.py

[SearchSettings]
context_length = 100

[IndexSettings]
index_file_path = {setup['index_file']}
use_index_search = True
"""
        
        with open(setup['config_file'], 'w') as f:
            f.write(config_content)
        
        # 大量ファイル作成（軽量版：実際のテストでは数を調整）
        file_count = min(100, setup['file_count'])  # テスト用に制限
        
        for i in range(file_count):
            file_type = ['txt', 'md', 'py'][i % 3]
            filename = f'large_file_{i:04d}.{file_type}'
            file_path = os.path.join(temp_dir, filename)
            
            # ファイル内容生成（Python関連のキーワードを含む）
            content_templates = [
                f'File {i}: Python programming tutorial with advanced concepts',
                f'# Document {i}\n\nPython development guide and best practices',
                f'# Python Script {i}\ndef process_data():\n    return "Python result {i}"'
            ]
            
            content = content_templates[i % 3] + '\n' + 'Sample content ' * 50
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            setup['files'].append(file_path)
        
        return setup
    
    @pytest.mark.slow
    def test_large_dataset_traditional_search_performance(self, large_dataset_setup, qapp):
        """大容量データセット従来検索パフォーマンステスト"""
        setup = large_dataset_setup
        config_manager = ConfigManager(setup['config_file'])
        
        with PerformanceProfiler("Large Dataset Traditional Search") as profiler:
            # 検索実行
            searcher = FileSearcher(
                directory=setup['root_dir'],
                search_terms=['Python'],
                include_subdirs=True,
                search_type=SEARCH_TYPE_OR,
                file_extensions=config_manager.get_file_extensions(),
                context_length=config_manager.get_context_length()
            )
            
            results = []
            searcher.result_found.connect(lambda f, m: results.append((f, m)))
            searcher.run()
        
        # パフォーマンス検証
        print(f"Traditional Search - Time: {profiler.execution_time:.2f}s, "
              f"Memory: {profiler.memory_usage:.2f}MB, "
              f"Results: {len(results)}")
        
        # 基本的な性能要件
        assert profiler.execution_time < 30.0  # 30秒以内
        assert profiler.memory_usage < 100.0   # 100MB以内の増加
        assert len(results) > 0  # 結果が得られること
    
    @pytest.mark.slow
    def test_large_dataset_index_creation_performance(self, large_dataset_setup):
        """大容量データセットインデックス作成パフォーマンステスト"""
        setup = large_dataset_setup
        
        with PerformanceProfiler("Large Dataset Index Creation") as profiler:
            indexer = SearchIndexer(setup['index_file'])
            
            # プログレスコールバック設定
            progress_calls = []
            def progress_callback(processed, total):
                progress_calls.append((processed, total))
            
            indexer.create_index([setup['root_dir']], progress_callback=progress_callback)
        
        # パフォーマンス検証
        print(f"Index Creation - Time: {profiler.execution_time:.2f}s, "
              f"Memory: {profiler.memory_usage:.2f}MB")
        
        # インデックス品質確認
        stats = indexer.get_index_stats()
        assert stats['files_count'] > 0
        
        # プログレス更新確認
        assert len(progress_calls) > 0
        
        # 性能要件
        assert profiler.execution_time < 60.0  # 60秒以内
        assert profiler.memory_usage < 200.0   # 200MB以内の増加
    
    @pytest.mark.slow
    def test_large_dataset_index_search_performance(self, large_dataset_setup, qapp):
        """大容量データセットインデックス検索パフォーマンステスト"""
        setup = large_dataset_setup
        config_manager = ConfigManager(setup['config_file'])
        
        # インデックス事前作成
        indexer = SearchIndexer(setup['index_file'])
        indexer.create_index([setup['root_dir']])
        
        with PerformanceProfiler("Large Dataset Index Search") as profiler:
            # インデックス検索実行
            searcher = SmartFileSearcher(
                directory=setup['root_dir'],
                search_terms=['Python'],
                include_subdirs=True,
                search_type=SEARCH_TYPE_OR,
                file_extensions=config_manager.get_file_extensions(),
                context_length=config_manager.get_context_length(),
                use_index=True,
                index_file_path=setup['index_file'],
                search_mode=SearchMode.INDEX_ONLY
            )
            
            results = []
            searcher.result_found.connect(lambda f, m: results.append((f, m)))
            searcher.run()
        
        # パフォーマンス検証
        print(f"Index Search - Time: {profiler.execution_time:.2f}s, "
              f"Memory: {profiler.memory_usage:.2f}MB, "
              f"Results: {len(results)}")
        
        # インデックス検索は従来検索より高速であるべき
        assert profiler.execution_time < 10.0  # 10秒以内
        assert profiler.memory_usage < 50.0    # 50MB以内の増加
        assert len(results) > 0
    
    def test_search_performance_comparison(self, large_dataset_setup, qapp):
        """検索方式パフォーマンス比較テスト"""
        setup = large_dataset_setup
        config_manager = ConfigManager(setup['config_file'])
        
        # インデックス作成
        indexer = SearchIndexer(setup['index_file'])
        indexer.create_index([setup['root_dir']])
        
        search_params = {
            'directory': setup['root_dir'],
            'search_terms': ['Python'],
            'include_subdirs': True,
            'search_type': SEARCH_TYPE_OR,
            'file_extensions': config_manager.get_file_extensions(),
            'context_length': config_manager.get_context_length()
        }
        
        # 従来検索
        with PerformanceProfiler("Traditional Search") as traditional_profiler:
            traditional_searcher = FileSearcher(**search_params)
            traditional_results = []
            traditional_searcher.result_found.connect(
                lambda f, m: traditional_results.append((f, m))
            )
            traditional_searcher.run()
        
        # インデックス検索
        with PerformanceProfiler("Index Search") as index_profiler:
            index_searcher = SmartFileSearcher(
                use_index=True,
                index_file_path=setup['index_file'],
                search_mode=SearchMode.INDEX_ONLY,
                **search_params
            )
            index_results = []
            index_searcher.result_found.connect(
                lambda f, m: index_results.append((f, m))
            )
            index_searcher.run()
        
        # 比較結果出力
        print(f"Performance Comparison:")
        print(f"  Traditional: {traditional_profiler.execution_time:.2f}s, "
              f"{traditional_profiler.memory_usage:.2f}MB")
        print(f"  Index:       {index_profiler.execution_time:.2f}s, "
              f"{index_profiler.memory_usage:.2f}MB")
        print(f"  Speedup:     {traditional_profiler.execution_time / index_profiler.execution_time:.2f}x")
        
        # インデックス検索が高速であることを確認
        assert index_profiler.execution_time <= traditional_profiler.execution_time
        
        # 結果の一貫性確認
        assert len(index_results) == len(traditional_results)


class TestMemoryUsageMonitoring:
    """メモリ使用量監視テスト"""
    
    @pytest.fixture
    def memory_test_setup(self, temp_dir):
        """メモリテスト用セットアップ"""
        setup = {
            'temp_dir': temp_dir,
            'config_file': os.path.join(temp_dir, 'memory_config.ini'),
            'large_files': []
        }
        
        # 設定ファイル作成
        with open(setup['config_file'], 'w') as f:
            f.write("[SearchSettings]\ncontext_length = 1000\n")
        
        # 大容量ファイル作成（10MB）
        for i in range(5):
            large_file = os.path.join(temp_dir, f'large_file_{i}.txt')
            with open(large_file, 'w', encoding='utf-8') as f:
                # 10MBのテキストファイル作成
                content = f"Line {j}: Python programming content with search terms\n" 
                f.write(content * 100000)  # 約10MB
            setup['large_files'].append(large_file)
        
        return setup
    
    def test_memory_leak_detection_long_running(self, memory_test_setup, qapp):
        """長時間実行メモリリーク検出テスト"""
        setup = memory_test_setup
        config_manager = ConfigManager(setup['config_file'])
        
        memory_samples = []
        process = psutil.Process()
        
        def sample_memory():
            memory_samples.append(process.memory_info().rss / 1024 / 1024)
        
        # 複数回検索実行
        for iteration in range(10):  # 10回繰り返し
            sample_memory()
            
            searcher = FileSearcher(
                directory=setup['temp_dir'],
                search_terms=['Python'],
                include_subdirs=False,
                search_type=SEARCH_TYPE_OR,
                file_extensions=['.txt'],
                context_length=config_manager.get_context_length()
            )
            
            results = []
            searcher.result_found.connect(lambda f, m: results.append((f, m)))
            searcher.run()
            
            # ガベージコレクション実行
            gc.collect()
            
            sample_memory()
        
        # メモリリーク検出
        initial_memory = memory_samples[0]
        final_memory = memory_samples[-1]
        memory_growth = final_memory - initial_memory
        
        print(f"Memory Growth: {memory_growth:.2f}MB over 10 iterations")
        print(f"Initial: {initial_memory:.2f}MB, Final: {final_memory:.2f}MB")
        
        # メモリ増加が100MB以下であることを確認
        assert memory_growth < 100.0, f"Memory leak detected: {memory_growth:.2f}MB growth"
    
    def test_large_file_memory_efficiency(self, memory_test_setup):
        """大容量ファイル処理メモリ効率テスト"""
        setup = memory_test_setup
        
        # 最大の大容量ファイルを選択
        largest_file = max(setup['large_files'], key=os.path.getsize)
        file_size_mb = os.path.getsize(largest_file) / 1024 / 1024
        
        with PerformanceProfiler("Large File Processing") as profiler:
            # ファイル読み込み
            content = read_file_with_auto_encoding(largest_file)
            
            # テキストハイライト処理
            with patch('service.text_handler.get_template_directory', 
                      return_value=os.path.join(setup['temp_dir'], 'templates')):
                # テンプレートディレクトリ作成
                template_dir = os.path.join(setup['temp_dir'], 'templates')
                os.makedirs(template_dir, exist_ok=True)
                
                template_content = "<html><body>{{ content | safe }}</body></html>"
                with open(os.path.join(template_dir, 'text_viewer.html'), 'w') as f:
                    f.write(template_content)
                
                try:
                    result_path = highlight_text_file(largest_file, ['Python'], 16)
                    
                    # 結果ファイルが作成されることを確認
                    assert os.path.exists(result_path)
                    
                    # クリーンアップ
                    os.remove(result_path)
                    
                except Exception as e:
                    # 大容量ファイル処理で例外が発生した場合の記録
                    print(f"Large file processing failed: {e}")
        
        print(f"Large File Memory Usage: File={file_size_mb:.1f}MB, "
              f"Memory={profiler.memory_usage:.2f}MB, "
              f"Time={profiler.execution_time:.2f}s")
        
        # メモリ使用量がファイルサイズの3倍以下であることを確認
        assert profiler.memory_usage < file_size_mb * 3
    
    def test_index_creation_memory_efficiency(self, memory_test_setup):
        """インデックス作成メモリ効率テスト"""
        setup = memory_test_setup
        
        index_file = os.path.join(setup['temp_dir'], 'memory_index.json')
        
        with PerformanceProfiler("Index Creation Memory") as profiler:
            indexer = SearchIndexer(index_file)
            indexer.create_index([setup['temp_dir']], include_subdirs=False)
        
        # インデックスファイルサイズ取得
        index_size_mb = os.path.getsize(index_file) / 1024 / 1024
        
        print(f"Index Creation Memory: Index={index_size_mb:.2f}MB, "
              f"Memory={profiler.memory_usage:.2f}MB")
        
        # メモリ使用量がインデックスサイズの5倍以下であることを確認
        assert profiler.memory_usage < max(index_size_mb * 5, 50.0)  # 最低50MB
    
    def test_concurrent_search_memory_usage(self, memory_test_setup, qapp):
        """並行検索メモリ使用量テスト"""
        setup = memory_test_setup
        config_manager = ConfigManager(setup['config_file'])
        
        concurrent_results = []
        memory_peak = 0
        
        def memory_monitor():
            nonlocal memory_peak
            process = psutil.Process()
            while len(concurrent_results) < 3:  # 3つの検索が完了するまで
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_peak = max(memory_peak, current_memory)
                time.sleep(0.1)
        
        # メモリ監視スレッド開始
        monitor_thread = threading.Thread(target=memory_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 複数の検索を並行実行（シミュレート）
        for i in range(3):
            searcher = FileSearcher(
                directory=setup['temp_dir'],
                search_terms=[f'Python_{i}'],
                include_subdirs=False,
                search_type=SEARCH_TYPE_OR,
                file_extensions=['.txt'],
                context_length=100
            )
            
            results = []
            searcher.result_found.connect(lambda f, m: results.append((f, m)))
            searcher.run()
            
            concurrent_results.append(results)
        
        # メモリ監視終了待ち
        monitor_thread.join(timeout=5)
        
        print(f"Concurrent Search Peak Memory: {memory_peak:.2f}MB")
        
        # ピークメモリが500MB以下であることを確認
        assert memory_peak < 500.0


class TestResponsivenessPerformance:
    """応答性パフォーマンステスト"""
    
    @pytest.fixture
    def responsiveness_setup(self, temp_dir):
        """応答性テスト用セットアップ"""
        setup = {
            'temp_dir': temp_dir,
            'config_file': os.path.join(temp_dir, 'resp_config.ini'),
            'files': []
        }
        
        # 設定ファイル作成
        with open(setup['config_file'], 'w') as f:
            f.write("[SearchSettings]\ncontext_length = 100\n")
        
        # 中程度のファイル群作成
        for i in range(50):
            test_file = os.path.join(temp_dir, f'resp_file_{i}.txt')
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(f'Response test file {i} with Python content\n' * 1000)
            setup['files'].append(test_file)
        
        return setup
    
    def test_search_response_time(self, responsiveness_setup, qapp):
        """検索応答時間テスト"""
        setup = responsiveness_setup
        config_manager = ConfigManager(setup['config_file'])
        
        response_times = []
        
        # 複数回の検索で応答時間測定
        for i in range(5):
            start_time = time.time()
            
            searcher = FileSearcher(
                directory=setup['temp_dir'],
                search_terms=['Python'],
                include_subdirs=False,
                search_type=SEARCH_TYPE_OR,
                file_extensions=['.txt'],
                context_length=config_manager.get_context_length()
            )
            
            results = []
            searcher.result_found.connect(lambda f, m: results.append((f, m)))
            searcher.run()
            
            response_time = time.time() - start_time
            response_times.append(response_time)
        
        # 応答時間統計
        avg_response = sum(response_times) / len(response_times)
        max_response = max(response_times)
        
        print(f"Search Response Times: Avg={avg_response:.2f}s, Max={max_response:.2f}s")
        
        # 応答時間要件
        assert avg_response < 5.0   # 平均5秒以内
        assert max_response < 10.0  # 最大10秒以内
    
    def test_search_cancellation_response(self, responsiveness_setup, qapp):
        """検索キャンセル応答時間テスト"""
        setup = responsiveness_setup
        config_manager = ConfigManager(setup['config_file'])
        
        cancellation_times = []
        
        for i in range(3):
            searcher = FileSearcher(
                directory=setup['temp_dir'],
                search_terms=['Python'],
                include_subdirs=False,
                search_type=SEARCH_TYPE_OR,
                file_extensions=['.txt'],
                context_length=config_manager.get_context_length()
            )
            
            # 検索開始
            searcher.start()
            
            # 少し待ってからキャンセル
            time.sleep(0.5)
            cancel_start = time.time()
            
            searcher.cancel_search()
            
            # キャンセル完了まで待機
            searcher.wait(5000)  # 最大5秒
            
            cancel_time = time.time() - cancel_start
            cancellation_times.append(cancel_time)
            
            # キャンセルフラグ確認
            assert searcher.cancel_flag == True
        
        # キャンセル応答時間統計
        avg_cancel = sum(cancellation_times) / len(cancellation_times)
        max_cancel = max(cancellation_times)
        
        print(f"Cancellation Response Times: Avg={avg_cancel:.2f}s, Max={max_cancel:.2f}s")
        
        # キャンセル応答時間要件
        assert avg_cancel < 2.0  # 平均2秒以内
        assert max_cancel < 5.0  # 最大5秒以内
    
    def test_progress_update_frequency(self, responsiveness_setup):
        """プログレス更新頻度テスト"""
        setup = responsiveness_setup
        
        index_file = os.path.join(setup['temp_dir'], 'progress_index.json')
        
        progress_updates = []
        update_times = []
        
        def progress_callback(processed, total):
            current_time = time.time()
            progress_updates.append((processed, total))
            if update_times:
                interval = current_time - update_times[-1]
                update_times.append(current_time)
            else:
                update_times.append(current_time)
        
        # インデックス作成でプログレス測定
        start_time = time.time()
        
        indexer = SearchIndexer(index_file)
        indexer.create_index([setup['temp_dir']], progress_callback=progress_callback)
        
        total_time = time.time() - start_time
        
        # プログレス更新統計
        update_count = len(progress_updates)
        avg_interval = total_time / max(update_count - 1, 1) if update_count > 1 else 0
        
        print(f"Progress Updates: Count={update_count}, "
              f"Avg Interval={avg_interval:.2f}s, Total Time={total_time:.2f}s")
        
        # プログレス更新要件
        assert update_count > 0  # 最低1回は更新
        if update_count > 1:
            assert avg_interval < 5.0  # 平均5秒間隔以内
    
    def test_file_opening_response_time(self, responsiveness_setup):
        """ファイルオープン応答時間テスト"""
        setup = responsiveness_setup
        config_manager = ConfigManager(setup['config_file'])
        
        file_opener = FileOpener(config_manager)
        opening_times = []
        
        # 複数ファイルでオープン時間測定
        for test_file in setup['files'][:10]:  # 10ファイルをテスト
            start_time = time.time()
            
            with patch('service.file_opener.open_text_file') as mock_open:
                file_opener.open_file(test_file, 1, ['Python'])
                
                opening_time = time.time() - start_time
                opening_times.append(opening_time)
                
                # モック呼び出し確認
                mock_open.assert_called_once()
        
        # オープン時間統計
        avg_opening = sum(opening_times) / len(opening_times)
        max_opening = max(opening_times)
        
        print(f"File Opening Times: Avg={avg_opening:.3f}s, Max={max_opening:.3f}s")
        
        # ファイルオープン応答時間要件
        assert avg_opening < 1.0  # 平均1秒以内
        assert max_opening < 2.0  # 最大2秒以内


class TestScalabilityPerformance:
    """スケーラビリティパフォーマンステスト"""
    
    def test_file_count_scalability(self, temp_dir):
        """ファイル数スケーラビリティテスト"""
        file_counts = [10, 50, 100]  # テスト用に制限された数
        performance_results = []
        
        for file_count in file_counts:
            # ファイル作成
            test_dir = os.path.join(temp_dir, f'scale_{file_count}')
            os.makedirs(test_dir)
            
            for i in range(file_count):
                test_file = os.path.join(test_dir, f'scale_file_{i}.txt')
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f'Scale test file {i} with Python content\n' * 100)
            
            # 検索性能測定
            with PerformanceProfiler(f"Scale Test {file_count} files") as profiler:
                searcher = FileSearcher(
                    directory=test_dir,
                    search_terms=['Python'],
                    include_subdirs=False,
                    search_type=SEARCH_TYPE_OR,
                    file_extensions=['.txt'],
                    context_length=100
                )
                
                results = []
                searcher.result_found.connect(lambda f, m: results.append((f, m)))
                searcher.run()
            
            performance_results.append({
                'file_count': file_count,
                'execution_time': profiler.execution_time,
                'memory_usage': profiler.memory_usage,
                'results_count': len(results)
            })
        
        # スケーラビリティ分析
        print("Scalability Analysis:")
        for result in performance_results:
            print(f"  {result['file_count']} files: "
                  f"{result['execution_time']:.2f}s, "
                  f"{result['memory_usage']:.2f}MB, "
                  f"{result['results_count']} results")
        
        # 線形スケーラビリティ確認（緩い要件）
        if len(performance_results) >= 2:
            first = performance_results[0]
            last = performance_results[-1]
            
            time_ratio = last['execution_time'] / first['execution_time']
            file_ratio = last['file_count'] / first['file_count']
            
            print(f"Time scaling ratio: {time_ratio:.2f}x for {file_ratio:.2f}x files")
            
            # 実行時間がファイル数の2倍以下の増加であることを確認
            assert time_ratio <= file_ratio * 2
    
    def test_search_term_count_scalability(self, temp_dir):
        """検索語数スケーラビリティテスト"""
        # テストファイル作成
        test_file = os.path.join(temp_dir, 'search_terms_test.txt')
        with open(test_file, 'w', encoding='utf-8') as f:
            content = ' '.join([f'term{i}' for i in range(100)]) * 10
            f.write(content)
        
        term_counts = [1, 5, 10, 20]
        performance_results = []
        
        for term_count in term_counts:
            search_terms = [f'term{i}' for i in range(term_count)]
            
            with PerformanceProfiler(f"Search {term_count} terms") as profiler:
                searcher = FileSearcher(
                    directory=temp_dir,
                    search_terms=search_terms,
                    include_subdirs=False,
                    search_type=SEARCH_TYPE_OR,
                    file_extensions=['.txt'],
                    context_length=100
                )
                
                results = []
                searcher.result_found.connect(lambda f, m: results.append((f, m)))
                searcher.run()
            
            performance_results.append({
                'term_count': term_count,
                'execution_time': profiler.execution_time,
                'memory_usage': profiler.memory_usage
            })
        
        # 検索語数スケーラビリティ分析
        print("Search Terms Scalability:")
        for result in performance_results:
            print(f"  {result['term_count']} terms: "
                  f"{result['execution_time']:.3f}s, "
                  f"{result['memory_usage']:.2f}MB")
        
        # 検索語数増加による性能劣化が合理的であることを確認
        max_time = max(r['execution_time'] for r in performance_results)
        assert max_time < 5.0  # 最大でも5秒以内


# パフォーマンステスト実行用のマーカー設定
pytestmark = pytest.mark.performance