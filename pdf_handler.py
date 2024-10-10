import subprocess
import tempfile
import time
import psutil
import pyautogui
import fitz

def open_pdf(file_path, acrobat_path, current_position, search_terms):
    try:
        highlighted_pdf_path = highlight_pdf(file_path, search_terms)

        process = subprocess.Popen([acrobat_path, highlighted_pdf_path])

        wait_for_acrobat(process.pid)

        navigate_to_page(current_position)

    except Exception as e:
        raise Exception(f"PDFを開けませんでした: {str(e)}")

def wait_for_acrobat(pid, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            process = psutil.Process(pid)
            if process.status() == psutil.STATUS_RUNNING:
                time.sleep(2)
                if "Acrobat" in pyautogui.getActiveWindowTitle():
                    return True
        except psutil.NoSuchProcess:
            return False
        time.sleep(0.5)
    return False

def navigate_to_page(page_number):
    if page_number == 1:
        return

    try:
        # Ctrl+Shift+Nを押してページ移動ダイアログを開く
        pyautogui.hotkey('ctrl', 'shift', 'n')
        time.sleep(0.5)

        # ページ番号を入力
        pyautogui.write(str(page_number))
        time.sleep(0.5)

        # Enterを押してページに移動
        pyautogui.press('enter')

    except Exception as e:
        print(f"ページ移動中にエラーが発生しました: {str(e)}")

def highlight_pdf(pdf_path, search_terms):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_path = tmp_file.name

    doc = fitz.open(pdf_path)
    colors = [
        (1, 1, 0),  # yellow
        (0.5, 1, 0.5),  # light green
        (0.5, 0.7, 1),  # light blue
        (1, 0.6, 0.4),  # light salmon
        (1, 0.7, 0.7)   # light pink
    ]

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
