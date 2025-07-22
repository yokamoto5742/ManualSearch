from typing import List, Optional
from datetime import datetime

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QTextEdit, QGroupBox, QCheckBox, QMessageBox,
    QDialog, QDialogButtonBox
)

from service.search_indexer import SearchIndexer
from utils.config_manager import ConfigManager


class IndexBuildThread(QThread):
    """インデックス作成用スレッド"""

    progress_updated = pyqtSignal(int, int)  # processed, total
    status_updated = pyqtSignal(str)
    completed = pyqtSignal(bool)  # success

    def __init__(self, directories: List[str], index_file_path: str = "search_index.json"):
        super().__init__()
        self.directories = directories
        self.indexer = SearchIndexer(index_file_path)
        self.should_cancel = False

    def run(self):
        try:
            self.status_updated.emit("インデックス作成を開始...")

            def progress_callback(processed: int, total: int):
                if not self.should_cancel:
                    self.progress_updated.emit(processed, total)

            self.indexer.create_index(
                self.directories,
                include_subdirs=True,
                progress_callback=progress_callback
            )

            if not self.should_cancel:
                self.status_updated.emit("インデックス作成完了")
                self.completed.emit(True)
            else:
                self.status_updated.emit("インデックス作成がキャンセルされました")
                self.completed.emit(False)

        except Exception as e:
            self.status_updated.emit(f"エラー: {str(e)}")
            self.completed.emit(False)

    def cancel(self):
        self.should_cancel = True


class IndexManagementWidget(QWidget):
    """インデックス管理用ウィジェット"""

    index_updated = pyqtSignal()  # インデックスが更新された時のシグナル

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.indexer = SearchIndexer()
        self.build_thread: Optional[IndexBuildThread] = None

        self._setup_ui()
        self._update_display()

        # 定期的に統計情報を更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(5000)  # 5秒間隔

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # インデックス統計情報グループ
        stats_group = QGroupBox("インデックス統計")
        stats_layout = QVBoxLayout()

        self.stats_label = QLabel("統計情報を読み込み中...")
        stats_layout.addWidget(self.stats_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # インデックス操作グループ
        operations_group = QGroupBox("インデックス操作")
        operations_layout = QVBoxLayout()

        # ボタンレイアウト
        button_layout = QHBoxLayout()

        self.create_button = QPushButton("インデックス作成")
        self.create_button.clicked.connect(self._create_index)
        button_layout.addWidget(self.create_button)

        self.update_button = QPushButton("インデックス更新")
        self.update_button.clicked.connect(self._update_index)
        button_layout.addWidget(self.update_button)

        self.cleanup_button = QPushButton("クリーンアップ")
        self.cleanup_button.clicked.connect(self._cleanup_index)
        button_layout.addWidget(self.cleanup_button)

        self.rebuild_button = QPushButton("完全再構築")
        self.rebuild_button.clicked.connect(self._rebuild_index)
        button_layout.addWidget(self.rebuild_button)

        operations_layout.addLayout(button_layout)

        # 設定
        self.auto_update_checkbox = QCheckBox("検索時に自動的にインデックスを更新")
        self.auto_update_checkbox.setChecked(True)
        operations_layout.addWidget(self.auto_update_checkbox)

        # 進行状況
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        operations_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        operations_layout.addWidget(self.status_label)

        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)

        # ログ表示
        log_group = QGroupBox("ログ")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def _update_display(self):
        """表示内容を更新"""
        try:
            stats = self.indexer.get_index_stats()

            stats_text = f"""
ファイル数: {stats['files_count']:,} 個
総サイズ: {stats['total_size_mb']:.1f} MB
インデックスファイルサイズ: {stats['index_file_size_mb']:.1f} MB
作成日時: {self._format_datetime(stats['created_at'])}
最終更新: {self._format_datetime(stats['last_updated'])}
            """.strip()

            self.stats_label.setText(stats_text)

        except Exception as e:
            self.stats_label.setText(f"統計情報の取得に失敗: {str(e)}")

    def _format_datetime(self, datetime_str: Optional[str]) -> str:
        """日時文字列をフォーマット"""
        if not datetime_str:
            return "未設定"

        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return datetime_str

    def _create_index(self):
        """インデックスを作成"""
        directories = self.config_manager.get_directories()
        if not directories:
            QMessageBox.warning(self, "警告", "検索対象ディレクトリが設定されていません。")
            return

        self._start_index_operation("作成", directories)

    def _update_index(self):
        """インデックスを更新"""
        directories = self.config_manager.get_directories()
        if not directories:
            QMessageBox.warning(self, "警告", "検索対象ディレクトリが設定されていません。")
            return

        self._start_index_operation("更新", directories)

    def _rebuild_index(self):
        """インデックスを完全再構築"""
        reply = QMessageBox.question(
            self,
            "確認",
            "インデックスを完全に再構築しますか？\n既存のインデックスは削除されます。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 既存のインデックスをクリア
            self.indexer._initialize_new_index()
            self.indexer._save_index()

            directories = self.config_manager.get_directories()
            self._start_index_operation("再構築", directories)

    def _start_index_operation(self, operation_name: str, directories: List[str]):
        """インデックス操作を開始"""
        if self.build_thread and self.build_thread.isRunning():
            QMessageBox.information(self, "情報", "インデックス操作が既に実行中です。")
            return

        self._log(f"インデックス{operation_name}を開始します...")

        # UIの状態を更新
        self._set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # スレッドを開始
        self.build_thread = IndexBuildThread(directories)
        self.build_thread.progress_updated.connect(self._on_progress_updated)
        self.build_thread.status_updated.connect(self._on_status_updated)
        self.build_thread.completed.connect(self._on_operation_completed)
        self.build_thread.start()

    def _cleanup_index(self):
        """インデックスをクリーンアップ"""
        try:
            removed_count = self.indexer.remove_missing_files()
            message = f"クリーンアップ完了: {removed_count} 個のファイルを削除しました。"
            self._log(message)
            QMessageBox.information(self, "クリーンアップ完了", message)
            self._update_display()
            self.index_updated.emit()

        except Exception as e:
            error_msg = f"クリーンアップ中にエラーが発生しました: {str(e)}"
            self._log(error_msg)
            QMessageBox.critical(self, "エラー", error_msg)

    def _on_progress_updated(self, processed: int, total: int):
        """進行状況の更新"""
        if total > 0:
            progress = int((processed / total) * 100)
            self.progress_bar.setValue(progress)
            self.status_label.setText(f"処理中: {processed}/{total} ({progress}%)")

    def _on_status_updated(self, status: str):
        """ステータスの更新"""
        self.status_label.setText(status)
        self._log(status)

    def _on_operation_completed(self, success: bool):
        """操作完了時の処理"""
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.status_label.setText("操作が正常に完了しました")
            self._update_display()
            self.index_updated.emit()
        else:
            self.status_label.setText("操作が失敗しました")

    def _set_buttons_enabled(self, enabled: bool):
        """ボタンの有効/無効を設定"""
        self.create_button.setEnabled(enabled)
        self.update_button.setEnabled(enabled)
        self.cleanup_button.setEnabled(enabled)
        self.rebuild_button.setEnabled(enabled)

    def _log(self, message: str):
        """ログメッセージを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def is_auto_update_enabled(self) -> bool:
        """自動更新が有効かどうか"""
        return self.auto_update_checkbox.isChecked()

    def closeEvent(self, event):
        """ウィジェット終了時の処理"""
        if self.build_thread and self.build_thread.isRunning():
            self.build_thread.cancel()
            self.build_thread.wait(3000)  # 3秒待機

        if self.update_timer:
            self.update_timer.stop()

        super().closeEvent(event)


class IndexManagementDialog(QDialog):
    """インデックス管理ダイアログ"""

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("インデックス管理")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # インデックス管理ウィジェット
        self.index_widget = IndexManagementWidget(config_manager, self)
        layout.addWidget(self.index_widget)

        # ボタン
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

    def closeEvent(self, event):
        """ダイアログ終了時の処理"""
        self.index_widget.closeEvent(event)
        super().closeEvent(event)