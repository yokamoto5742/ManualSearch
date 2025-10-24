from datetime import datetime
from typing import List, Optional

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel,
    QMessageBox, QProgressBar, QPushButton, QTextEdit, QVBoxLayout, QWidget
)

from service.search_indexer import SearchIndexer
from utils.config_manager import ConfigManager
from widgets.index_build_thread import IndexBuildThread


class IndexManagementWidget(QWidget):
    """インデックス統計情報と操作を管理するウィジェット"""
    # インデックス更新シグナル
    index_updated = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        """初期化

        Args:
            config_manager: 設定管理オブジェクト
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.config_manager = config_manager

        index_file_path = self.config_manager.get_index_file_path()
        self.indexer = SearchIndexer(index_file_path)
        self.build_thread: Optional[IndexBuildThread] = None

        self._setup_ui()
        self._update_display()

        # 定期的に統計情報を更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(5000)

    def _setup_ui(self) -> None:
        """UIレイアウトを構築"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # インデックス統計情報セクション
        stats_group = QGroupBox("インデックス統計情報")
        stats_layout = QVBoxLayout()

        self.stats_label = QLabel("統計情報を読み込み中...")
        stats_layout.addWidget(self.stats_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # インデックス操作セクション
        operations_group = QGroupBox("インデックス操作")
        operations_layout = QVBoxLayout()

        button_layout = QHBoxLayout()

        # 各種操作ボタン
        self.create_button = QPushButton("初回作成")
        self.create_button.clicked.connect(self._create_index)
        button_layout.addWidget(self.create_button)

        self.update_button = QPushButton("ファイル追加更新")
        self.update_button.clicked.connect(self._update_index)
        button_layout.addWidget(self.update_button)

        self.cleanup_button = QPushButton("ファイル削除更新")
        self.cleanup_button.clicked.connect(self._cleanup_index)
        button_layout.addWidget(self.cleanup_button)

        self.rebuild_button = QPushButton("完全再構築")
        self.rebuild_button.clicked.connect(self._rebuild_index)
        button_layout.addWidget(self.rebuild_button)

        operations_layout.addLayout(button_layout)

        # 進捗表示
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        operations_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        operations_layout.addWidget(self.status_label)

        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)

        # ログセクション
        log_group = QGroupBox("ログ")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def _update_display(self) -> None:
        """インデックス統計情報を表示に反映"""
        try:
            stats = self.indexer.get_index_stats()

            stats_text = f"""
ファイル数: {stats['files_count']:,} 個
総サイズ: {stats['total_size_mb']:.1f} MB
インデックスファイルサイズ: {stats['index_file_size_mb']:.1f} MB
インデックスファイルパス: {self.indexer.storage.index_file_path}
作成日時: {self._format_datetime(stats['created_at'])}
最終更新: {self._format_datetime(stats['last_updated'])}
            """.strip()

            self.stats_label.setText(stats_text)

        except Exception as e:
            self.stats_label.setText(f"統計情報の取得に失敗: {str(e)}")

    def _format_datetime(self, datetime_str: Optional[str]) -> str:
        """ISO形式の日時文字列を表示形式に変換

        Args:
            datetime_str: ISO形式の日時文字列

        Returns:
            フォーマット済みの日時文字列
        """
        if not datetime_str:
            return "未設定"

        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return datetime_str

    def _create_index(self) -> None:
        """インデックスを初回作成"""
        directories = self.config_manager.get_directories()
        if not directories:
            QMessageBox.warning(self, "警告", "検索対象ディレクトリが設定されていません。")
            return

        self._start_index_operation("作成", directories)

    def _update_index(self) -> None:
        """インデックスにファイルを追加して更新"""
        directories = self.config_manager.get_directories()
        if not directories:
            QMessageBox.warning(self, "警告", "検索対象ディレクトリが設定されていません。")
            return

        self._start_index_operation("更新", directories)

    def _rebuild_index(self) -> None:
        """インデックスを完全に再構築"""
        reply = QMessageBox.question(
            self,
            "確認",
            "既存インデックスを削除して完全に再構築しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # インデックスをリセット
            self.indexer.index_data = self.indexer.storage._create_new_index()
            self.indexer.storage.save(self.indexer.index_data)

            directories = self.config_manager.get_directories()
            self._start_index_operation("再構築", directories)

    def _start_index_operation(self, operation_name: str, directories: List[str]) -> None:
        """インデックス操作をスレッドで開始

        Args:
            operation_name: 操作名（作成、更新など）
            directories: インデックス対象のディレクトリリスト
        """
        if self.build_thread and self.build_thread.isRunning():
            QMessageBox.information(self, "情報", "インデックス操作を実行中です。")
            return

        self._log(f"インデックス{operation_name}を開始します...")

        self._set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # インデックス作成スレッドを開始
        index_file_path = self.config_manager.get_index_file_path()
        self.build_thread = IndexBuildThread(directories, index_file_path)
        self.build_thread.progress_updated.connect(self._on_progress_updated)
        self.build_thread.status_updated.connect(self._on_status_updated)
        self.build_thread.completed.connect(self._on_operation_completed)
        self.build_thread.start()

    def _cleanup_index(self) -> None:
        """削除されたファイルをインデックスから削除"""
        try:
            removed_count = self.indexer.remove_missing_files()
            message = f"クリーンアップ完了: {removed_count} 個の現在存在しないファイルをインデックスから削除しました。"
            self._log(message)
            QMessageBox.information(self, "クリーンアップ完了", message)
            self._update_display()
            self.index_updated.emit()

        except Exception as e:
            error_msg = f"クリーンアップ中にエラーが発生しました: {str(e)}"
            self._log(error_msg)
            QMessageBox.critical(self, "エラー", error_msg)

    def _on_progress_updated(self, processed: int, total: int) -> None:
        """スレッドから進捗更新を受け取る

        Args:
            processed: 処理済みファイル数
            total: 総ファイル数
        """
        if total > 0:
            progress = int((processed / total) * 100)
            self.progress_bar.setValue(progress)
            self.status_label.setText(f"処理中: {processed}/{total} ({progress}%)")

    def _on_status_updated(self, status: str) -> None:
        """スレッドからステータス更新を受け取る

        Args:
            status: ステータスメッセージ
        """
        self.status_label.setText(status)
        self._log(status)

    def _on_operation_completed(self, success: bool) -> None:
        """スレッドから完了シグナルを受け取る

        Args:
            success: 成功した場合True
        """
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.status_label.setText("操作が正常に完了しました")
            self._update_display()
            self.index_updated.emit()
        else:
            self.status_label.setText("操作が失敗しました")

    def _set_buttons_enabled(self, enabled: bool) -> None:
        """操作ボタンの有効無効を設定

        Args:
            enabled: 有効にする場合True
        """
        self.create_button.setEnabled(enabled)
        self.update_button.setEnabled(enabled)
        self.cleanup_button.setEnabled(enabled)
        self.rebuild_button.setEnabled(enabled)

    def _log(self, message: str) -> None:
        """ログテキストにメッセージを追加

        Args:
            message: ログメッセージ
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def closeEvent(self, a0) -> None:
        """ウィジェットを閉じるときの処理"""
        # 実行中のスレッドをキャンセルして終了を待機
        if self.build_thread and self.build_thread.isRunning():
            self.build_thread.cancel()
            self.build_thread.wait(3000)

        # タイマーを停止
        if self.update_timer:
            self.update_timer.stop()

        super().closeEvent(a0)


class IndexManagementDialog(QDialog):
    """インデックス管理ダイアログ"""

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        """初期化

        Args:
            config_manager: 設定管理オブジェクト
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setWindowTitle("インデックス管理")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # インデックス管理ウィジェットを追加
        self.index_widget = IndexManagementWidget(config_manager, self)
        layout.addWidget(self.index_widget)

        # クローズボタンを追加
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

    def closeEvent(self, a0) -> None:
        """ダイアログを閉じるときの処理"""
        self.index_widget.closeEvent(a0)
        super().closeEvent(a0)
