from datetime import datetime
from typing import List, Optional

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QTextEdit, QGroupBox, QCheckBox, QMessageBox,
    QDialog, QDialogButtonBox
)

from service.search_indexer import SearchIndexer
from utils.config_manager import ConfigManager
from widgets.index_build_thread import IndexBuildThread


class IndexManagementWidget(QWidget):
    """インデックス管理UIウィジェット"""

    index_updated = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager

        index_file_path = self.config_manager.get_index_file_path()
        self.indexer = SearchIndexer(index_file_path)
        self.build_thread: Optional[IndexBuildThread] = None

        self._setup_ui()
        self._update_display()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(5000)  # 5秒間隔

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        stats_group = QGroupBox("インデックス統計情報")
        stats_layout = QVBoxLayout()

        self.stats_label = QLabel("統計情報を読み込み中...")
        stats_layout.addWidget(self.stats_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        operations_group = QGroupBox("インデックス操作")
        operations_layout = QVBoxLayout()

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

        self.auto_update_checkbox = QCheckBox("検索時にインデックスを毎回更新")
        self.auto_update_checkbox.setChecked(True)
        operations_layout.addWidget(self.auto_update_checkbox)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        operations_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        operations_layout.addWidget(self.status_label)

        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)

        log_group = QGroupBox("ログ")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def _update_display(self):
        try:
            stats = self.indexer.get_index_stats()

            stats_text = f"""
ファイル数: {stats['files_count']:,} 個
総サイズ: {stats['total_size_mb']:.1f} MB
インデックスファイルサイズ: {stats['index_file_size_mb']:.1f} MB
インデックスファイルパス: {self.indexer.index_file_path}
作成日時: {self._format_datetime(stats['created_at'])}
最終更新: {self._format_datetime(stats['last_updated'])}
            """.strip()

            self.stats_label.setText(stats_text)

        except Exception as e:
            self.stats_label.setText(f"統計情報の取得に失敗: {str(e)}")

    def _format_datetime(self, datetime_str: Optional[str]) -> str:
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
        directories = self.config_manager.get_directories()
        if not directories:
            QMessageBox.warning(self, "警告", "検索対象ディレクトリが設定されていません。")
            return

        self._start_index_operation("更新", directories)

    def _rebuild_index(self):
        reply = QMessageBox.question(
            self,
            "確認",
            "既存インデックスを削除して完全に再構築しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.indexer._initialize_new_index()
            self.indexer._save_index()

            directories = self.config_manager.get_directories()
            self._start_index_operation("再構築", directories)

    def _start_index_operation(self, operation_name: str, directories: List[str]):
        if self.build_thread and self.build_thread.isRunning():
            QMessageBox.information(self, "情報", "インデックス操作を実行中です。")
            return

        self._log(f"インデックス{operation_name}を開始します...")

        # UIの状態を更新
        self._set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        index_file_path = self.config_manager.get_index_file_path()
        self.build_thread = IndexBuildThread(directories, index_file_path)
        self.build_thread.progress_updated.connect(self._on_progress_updated)
        self.build_thread.status_updated.connect(self._on_status_updated)
        self.build_thread.completed.connect(self._on_operation_completed)
        self.build_thread.start()

    def _cleanup_index(self):
        try:
            removed_count = self.indexer.remove_missing_files()
            message = f"クリーンアップ完了: {removed_count} 個の存在しないファイルをインデックスから削除しました。"
            self._log(message)
            QMessageBox.information(self, "クリーンアップ完了", message)
            self._update_display()
            self.index_updated.emit()

        except Exception as e:
            error_msg = f"クリーンアップ中にエラーが発生しました: {str(e)}"
            self._log(error_msg)
            QMessageBox.critical(self, "エラー", error_msg)

    def _on_progress_updated(self, processed: int, total: int):
        if total > 0:
            progress = int((processed / total) * 100)
            self.progress_bar.setValue(progress)
            self.status_label.setText(f"処理中: {processed}/{total} ({progress}%)")

    def _on_status_updated(self, status: str):
        self.status_label.setText(status)
        self._log(status)

    def _on_operation_completed(self, success: bool):
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.status_label.setText("操作が正常に完了しました")
            self._update_display()
            self.index_updated.emit()
        else:
            self.status_label.setText("操作が失敗しました")

    def _set_buttons_enabled(self, enabled: bool):
        self.create_button.setEnabled(enabled)
        self.update_button.setEnabled(enabled)
        self.cleanup_button.setEnabled(enabled)
        self.rebuild_button.setEnabled(enabled)

    def _log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def is_auto_update_enabled(self) -> bool:
        """自動更新が有効かどうか"""
        return self.auto_update_checkbox.isChecked()

    def closeEvent(self, event):
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

        self.index_widget = IndexManagementWidget(config_manager, self)
        layout.addWidget(self.index_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

    def closeEvent(self, event):
        self.index_widget.closeEvent(event)
        super().closeEvent(event)
