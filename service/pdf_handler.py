import atexit
import logging
import os
import subprocess
import tempfile
import time
from typing import List, cast

import fitz
import psutil
import pyautogui

from utils.constants import (
    ACROBAT_KEYBINDS,
    ACROBAT_KEYSTROKE_DELAY,
    ACROBAT_PROCESS_NAMES,
    ACROBAT_WAIT_INTERVAL,
    ACROBAT_WAIT_TIMEOUT,
    DIALOG_MESSAGES,
    LOG_MESSAGE_TEMPLATES,
    PAGE_NAVIGATION_DELAY,
    PAGE_NAVIGATION_RETRY_COUNT,
    PDF_HIGHLIGHT_COLORS,
    PROCESS_CLEANUP_DELAY,
    PROCESS_TERMINATE_TIMEOUT,
)

logger = logging.getLogger(__name__)


class TempFileManager:
    """PDFの一時ファイル管理クラス"""
    
    def __init__(self):
        self._temp_files: List[str] = []
        atexit.register(self.cleanup_all)
    
    def add(self, file_path: str) -> None:
        """一時ファイルを追加"""
        self._temp_files.append(file_path)
    
    def cleanup_all(self) -> None:
        """すべての一時ファイルを削除"""
        for temp_file in self._temp_files[:]:
            self._cleanup_file(temp_file)
    
    def cleanup_single(self, file_path: str) -> None:
        """特定の一時ファイルを削除"""
        self._cleanup_file(file_path)
    
    def _cleanup_file(self, file_path: str) -> None:
        """ファイルを削除"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if file_path in self._temp_files:
                self._temp_files.remove(file_path)
        except (OSError, ValueError) as e:
            logger.warning(f"一時ファイルの削除に失敗: {file_path} - {e}")


temp_file_manager = TempFileManager()


class AcrobatProcessManager:
    @staticmethod
    def close_all_processes() -> None:
        try:
            acrobat_processes = AcrobatProcessManager._find_processes()
            
            if not acrobat_processes:
                logger.debug(LOG_MESSAGE_TEMPLATES['NO_ACROBAT_PROCESSES'])
                return

            logger.info(LOG_MESSAGE_TEMPLATES['FOUND_ACROBAT_PROCESSES'].format(count=len(acrobat_processes)))
            
            for proc in acrobat_processes:
                AcrobatProcessManager._terminate_process(proc)
            
            time.sleep(PROCESS_CLEANUP_DELAY)
            
        except Exception as e:
            logger.error(f"プロセス確認中にエラー: {e}")
    
    @staticmethod
    def _find_processes() -> List[psutil.Process]:
        acrobat_processes = []
        
        for proc in psutil.process_iter(['pid', 'name']):
            proc_name = proc.info['name'].lower()
            
            if AcrobatProcessManager._is_acrobat_process(proc_name):
                acrobat_processes.append(proc)
        
        return acrobat_processes
    
    @staticmethod
    def _is_acrobat_process(process_name: str) -> bool:
        return any(
            process_name in [name.lower(), f"{name.lower()}.exe"]
            for name in ACROBAT_PROCESS_NAMES
        )
    
    @staticmethod
    def _terminate_process(proc: psutil.Process) -> None:
        try:
            logger.info(LOG_MESSAGE_TEMPLATES['PROCESS_TERMINATING'].format(
                process_name=proc.info['name'], pid=proc.pid
            ))
            proc.terminate()

            try:
                proc.wait(timeout=PROCESS_TERMINATE_TIMEOUT)
                logger.info(LOG_MESSAGE_TEMPLATES['PROCESS_TERMINATED'].format(pid=proc.pid))
            except psutil.TimeoutExpired:
                proc.kill()
                logger.warning(LOG_MESSAGE_TEMPLATES['PROCESS_FORCE_KILLED'].format(pid=proc.pid))
                
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"プロセス終了中にエラー: {e}")
    
    @staticmethod
    def wait_for_startup(pid: int, timeout: int = ACROBAT_WAIT_TIMEOUT) -> bool:
        """Acrobatの起動を待機"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                process = psutil.Process(pid)
                
                if process.status() != psutil.STATUS_RUNNING:
                    time.sleep(ACROBAT_WAIT_INTERVAL)
                    continue

                time.sleep(ACROBAT_WAIT_INTERVAL)
                
                try:
                    return True
                except Exception:
                    pass
                
            except psutil.NoSuchProcess:
                return False
            except Exception as e:
                logger.error(LOG_MESSAGE_TEMPLATES['ACROBAT_WAIT_ERROR'].format(error=e))

            time.sleep(ACROBAT_WAIT_INTERVAL)

        logger.warning(LOG_MESSAGE_TEMPLATES['ACROBAT_TIMEOUT'].format(timeout=timeout))
        return False
    
    @staticmethod
    def _is_acrobat_window(window_title: str) -> bool:
        window_lower = window_title.lower()
        return any(keyword in window_lower for keyword in ['acrobat', 'adobe'])


class PDFNavigator:
    @staticmethod
    def navigate_to_page(page_number: int) -> None:
        if page_number == 1:
            return
        
        for attempt in range(PAGE_NAVIGATION_RETRY_COUNT):
            try:
                PDFNavigator._execute_navigation(page_number)
                break
            except Exception as e:
                logger.warning(f"ページ移動試行{attempt + 1}でエラー: {e}")
                if attempt < PAGE_NAVIGATION_RETRY_COUNT - 1:
                    time.sleep(PROCESS_CLEANUP_DELAY)
    
    @staticmethod
    def _execute_navigation(page_number: int) -> None:
        pyautogui.hotkey(*ACROBAT_KEYBINDS['FIND_AND_REPLACE'])
        time.sleep(PAGE_NAVIGATION_DELAY)

        pyautogui.hotkey(*ACROBAT_KEYBINDS['SELECT_ALL'])
        time.sleep(ACROBAT_KEYSTROKE_DELAY)

        pyautogui.write(str(page_number))
        time.sleep(PAGE_NAVIGATION_DELAY)

        pyautogui.press(ACROBAT_KEYBINDS['CONFIRM'][0])


class PDFHighlighter:
    @staticmethod
    def highlight_pdf(pdf_path: str, search_terms: List[str]) -> str:
        temp_path = PDFHighlighter._create_temp_file()
        
        try:
            with fitz.open(pdf_path) as doc:
                PDFHighlighter._add_highlights(doc, search_terms)
                doc.save(temp_path)
            
            return temp_path
        
        except fitz.FileDataError as e:
            raise ValueError(DIALOG_MESSAGES['INVALID_PDF'].format(pdf_path=pdf_path)) from e
        except Exception as e:
            raise RuntimeError(f"PDFのハイライト処理中にエラー: {e}") from e
    
    @staticmethod
    def _create_temp_file() -> str:
        """一時ファイルを作成"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name
        
        temp_file_manager.add(tmp_path)
        return tmp_path
    
    @staticmethod
    def _add_highlights(doc: fitz.Document, search_terms: List[str]) -> None:
        for page in doc:
            for i, term in enumerate(search_terms):
                if not term or not term.strip():
                    continue
                
                PDFHighlighter._highlight_term_in_page(page, term, i)
    
    @staticmethod
    def _highlight_term_in_page(page: fitz.Page, term: str, color_index: int) -> None:
        text_instances = []
        try:
            text_instances = cast(list, page.search_for(term.strip()))  # type: ignore[attr-defined]
        except AttributeError:
            try:
                text_instances = cast(list, page.get_text("blocks"))  # type: ignore[attr-defined]
            except Exception:
                pass

        for inst in text_instances:
            try:
                highlight = page.add_highlight_annot(inst)
                color = PDF_HIGHLIGHT_COLORS[color_index % len(PDF_HIGHLIGHT_COLORS)]
                highlight.set_colors(stroke=color)
                highlight.update()
            except Exception as e:
                logger.warning(f"ハイライト追加エラー (term: {term}): {e}")


def open_pdf(
    file_path: str, 
    acrobat_path: str, 
    current_position: int, 
    search_terms: List[str],
    use_highlight: bool = True
) -> None:
    try:
        # 既存のAcrobatプロセスを終了
        AcrobatProcessManager.close_all_processes()
        
        # ハイライトの有無に応じてPDFパスを決定
        if use_highlight:
            pdf_path = PDFHighlighter.highlight_pdf(file_path, search_terms)
        else:
            pdf_path = file_path
        
        # Acrobatで開く
        process = subprocess.Popen([acrobat_path, pdf_path])
        
        # 起動を待機
        if AcrobatProcessManager.wait_for_startup(process.pid):
            time.sleep(PROCESS_CLEANUP_DELAY)
            PDFNavigator.navigate_to_page(current_position)
        else:
            logger.warning("Acrobatの起動確認に失敗しました")
    
    except FileNotFoundError as e:
        raise FileNotFoundError(f"指定されたファイルが見つかりません: {file_path}") from e
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Acrobat Readerの起動に失敗しました: {e}") from e
    except Exception as e:
        raise RuntimeError(f"PDFを開く際に予期せぬエラーが発生しました: {e}") from e
