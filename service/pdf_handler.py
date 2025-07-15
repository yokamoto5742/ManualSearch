import subprocess
import tempfile
import time
from typing import List, Tuple

import fitz
import psutil
import pyautogui


def open_pdf(file_path: str, acrobat_path: str, current_position: int, search_terms: List[str]) -> None:
    try:
        highlighted_pdf_path = highlight_pdf(file_path, search_terms)
        process = subprocess.Popen([acrobat_path, highlighted_pdf_path])
        if wait_for_acrobat(process.pid):
            navigate_to_page(current_position)
    except FileNotFoundError:
        raise FileNotFoundError(f"指定されたファイルが見つかりません: {file_path}")
    except subprocess.SubprocessError:
        raise RuntimeError("Acrobat Readerの起動に失敗しました")
    except Exception as e:
        raise RuntimeError(f"PDFを開く際に予期せぬエラーが発生しました: {str(e)}")


def wait_for_acrobat(pid: int, timeout: int = 20) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            process = psutil.Process(pid)
            if process.status() == psutil.STATUS_RUNNING and "Acrobat" in pyautogui.getActiveWindowTitle():
                return True
        except psutil.NoSuchProcess:
            return False
        time.sleep(0.5)
    return False


def navigate_to_page(page_number: int) -> None:
    if page_number == 1:
        return

    try:
        pyautogui.hotkey('ctrl', 'shift', 'n')
        time.sleep(0.5)
        pyautogui.write(str(page_number))
        time.sleep(0.5)
        pyautogui.press('enter')
    except Exception as e:
        print(f"ページ移動中にエラーが発生しました: {str(e)}")


def highlight_pdf(pdf_path: str, search_terms: List[str]) -> str:
    colors: List[Tuple[float, float, float]] = [
        (1, 1, 0), (0.5, 1, 0.5), (0.5, 0.7, 1), (1, 0.6, 0.4), (1, 0.7, 0.7)
    ]

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_path = tmp_file.name

    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            for i, term in enumerate(search_terms):
                text_instances = page.search_for(term.strip())
                for inst in text_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=colors[i % len(colors)])
                    highlight.update()
        doc.save(tmp_path)
        doc.close()
        return tmp_path
    except fitz.FileDataError:
        raise ValueError(f"無効なPDFファイル: {pdf_path}")
    except Exception as e:
        raise RuntimeError(f"PDFのハイライト処理中にエラーが発生しました: {str(e)}")
