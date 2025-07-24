import subprocess
import tempfile
import time
import os
import atexit
from typing import List, Tuple, Optional

import fitz
import psutil
import pyautogui

from constants import (
    PDF_HIGHLIGHT_COLORS,
    ACROBAT_WAIT_TIMEOUT,
    ACROBAT_WAIT_INTERVAL,
    PAGE_NAVIGATION_RETRY_COUNT,
    PAGE_NAVIGATION_DELAY,
    PROCESS_TERMINATE_TIMEOUT,
    PROCESS_CLEANUP_DELAY,
    ACROBAT_PROCESS_NAMES
)

_temp_files: List[str] = []


def cleanup_temp_files() -> None:
    global _temp_files
    for temp_file in _temp_files[:]:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            _temp_files.remove(temp_file)
        except (OSError, ValueError) as e:
            print(f"一時ファイルの削除に失敗: {temp_file} - {e}")


atexit.register(cleanup_temp_files)


def close_existing_acrobat_processes() -> None:
    try:
        acrobat_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            proc_name = proc.info['name'].lower()
            for acrobat_name in ACROBAT_PROCESS_NAMES:
                if proc_name == acrobat_name.lower() or proc_name == f"{acrobat_name.lower()}.exe":
                    acrobat_processes.append(proc)
                    break

        if acrobat_processes:
            print(f"既存のAcrobatプロセスが{len(acrobat_processes)}個見つかりました。すべて終了します。")

            for proc in acrobat_processes:
                try:
                    print(f"プロセス終了中: {proc.info['name']} (PID: {proc.pid})")
                    proc.terminate()

                    try:
                        proc.wait(timeout=PROCESS_TERMINATE_TIMEOUT)
                        print(f"Acrobatプロセス (PID: {proc.pid}) を正常に終了しました")
                    except psutil.TimeoutExpired:
                        proc.kill()
                        print(f"Acrobatプロセス (PID: {proc.pid}) を強制終了しました")

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    print(f"プロセス終了中にエラー: {e}")
                except Exception as e:
                    print(f"予期せぬエラー: {e}")

            time.sleep(PROCESS_CLEANUP_DELAY)

        else:
            print("既存のAcrobatプロセスは見つかりませんでした")

    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        print(f"プロセス確認中にエラー: {e}")
    except Exception as e:
        print(f"予期せぬエラー: {e}")


def open_pdf(file_path: str, acrobat_path: str, current_position: int, search_terms: List[str]) -> None:
    try:
        close_existing_acrobat_processes()
        highlighted_pdf_path = highlight_pdf(file_path, search_terms)
        process = subprocess.Popen([acrobat_path, highlighted_pdf_path])

        if wait_for_acrobat(process.pid):
            time.sleep(PROCESS_CLEANUP_DELAY)
            navigate_to_page(current_position)
        else:
            print("Acrobatの起動確認に失敗しました")

    except FileNotFoundError:
        raise FileNotFoundError(f"指定されたファイルが見つかりません: {file_path}")
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Acrobat Readerの起動に失敗しました: {e}")
    except Exception as e:
        raise RuntimeError(f"PDFを開く際に予期せぬエラーが発生しました: {str(e)}")


def wait_for_acrobat(pid: int, timeout: int = ACROBAT_WAIT_TIMEOUT) -> bool:
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            process = psutil.Process(pid)
            if process.status() == psutil.STATUS_RUNNING:
                time.sleep(ACROBAT_WAIT_INTERVAL)
                try:
                    active_window = pyautogui.getActiveWindowTitle()
                    if active_window and any(acrobat_name in active_window.lower() 
                                           for acrobat_name in ['acrobat', 'adobe']):
                        return True
                except Exception:
                    pass

        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            print(f"Acrobat待機中にエラー: {e}")

        time.sleep(ACROBAT_WAIT_INTERVAL)

    print(f"Acrobat起動のタイムアウト（{timeout}秒）")
    return False


def navigate_to_page(page_number: int) -> None:
    if page_number == 1:
        return

    try:
        for attempt in range(PAGE_NAVIGATION_RETRY_COUNT):
            try:
                pyautogui.hotkey('ctrl', 'shift', 'n')
                time.sleep(PAGE_NAVIGATION_DELAY)

                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)

                pyautogui.write(str(page_number))
                time.sleep(PAGE_NAVIGATION_DELAY)
                pyautogui.press('enter')

                break

            except Exception as e:
                print(f"ページ移動試行{attempt + 1}でエラー: {e}")
                if attempt < PAGE_NAVIGATION_RETRY_COUNT - 1:  # 最後の試行でなければ少し待つ
                    time.sleep(PROCESS_CLEANUP_DELAY)

    except Exception as e:
        print(f"ページ移動中にエラーが発生しました: {str(e)}")


def highlight_pdf(pdf_path: str, search_terms: List[str]) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_path = tmp_file.name

    global _temp_files
    _temp_files.append(tmp_path)

    doc = None
    try:
        doc = fitz.open(pdf_path)

        for page in doc:
            for i, term in enumerate(search_terms):
                if not term or not term.strip():
                    continue

                text_instances = page.search_for(term.strip())
                for inst in text_instances:
                    try:
                        highlight = page.add_highlight_annot(inst)
                        highlight.set_colors(stroke=PDF_HIGHLIGHT_COLORS[i % len(PDF_HIGHLIGHT_COLORS)])
                        highlight.update()
                    except Exception as e:
                        print(f"ハイライト追加エラー (term: {term}): {e}")
                        continue

        doc.save(tmp_path)
        return tmp_path

    except fitz.FileDataError:
        raise ValueError(f"無効なPDFファイル: {pdf_path}")
    except Exception as e:
        raise RuntimeError(f"PDFのハイライト処理中にエラーが発生しました: {str(e)}")
    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception as e:
                print(f"PDF document クローズ時にエラー: {e}")


def cleanup_single_temp_file(file_path: str) -> None:
    global _temp_files
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        if file_path in _temp_files:
            _temp_files.remove(file_path)
    except (OSError, ValueError) as e:
        print(f"一時ファイルの削除に失敗: {file_path} - {e}")
