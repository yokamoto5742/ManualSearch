import subprocess
import tempfile
import time
import os
import atexit
from typing import List, Tuple, Optional

import fitz
import psutil
import pyautogui

# 一時ファイルを追跡するためのリスト
_temp_files: List[str] = []


def cleanup_temp_files() -> None:
    """アプリケーション終了時に一時ファイルをクリーンアップ"""
    global _temp_files
    for temp_file in _temp_files[:]:  # コピーを作成してイテレート
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            _temp_files.remove(temp_file)
        except (OSError, ValueError) as e:
            print(f"一時ファイルの削除に失敗: {temp_file} - {e}")


# アプリケーション終了時のクリーンアップを登録
atexit.register(cleanup_temp_files)


def close_existing_acrobat_processes() -> None:
    """既存のAcrobatプロセスを確認し、必要に応じて警告"""
    try:
        acrobat_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            if 'acrobat' in proc.info['name'].lower():
                acrobat_processes.append(proc)

        if acrobat_processes:
            print(f"既存のAcrobatプロセスが{len(acrobat_processes)}個見つかりました")
            # 必要に応じてここでユーザーに選択を求めることも可能

    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        print(f"プロセス確認中にエラー: {e}")


def open_pdf(file_path: str, acrobat_path: str, current_position: int, search_terms: List[str]) -> None:
    """PDFファイルを開く（改良版）"""
    try:
        # 既存のAcrobatプロセスをチェック
        close_existing_acrobat_processes()

        # ハイライト付きPDFを作成
        highlighted_pdf_path = highlight_pdf(file_path, search_terms)

        # Acrobat Readerで開く
        process = subprocess.Popen([acrobat_path, highlighted_pdf_path])

        # Acrobatの起動を待機
        if wait_for_acrobat(process.pid):
            # 少し待ってからページ移動
            time.sleep(1.0)
            navigate_to_page(current_position)
        else:
            print("Acrobatの起動確認に失敗しました")

    except FileNotFoundError:
        raise FileNotFoundError(f"指定されたファイルが見つかりません: {file_path}")
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Acrobat Readerの起動に失敗しました: {e}")
    except Exception as e:
        raise RuntimeError(f"PDFを開く際に予期せぬエラーが発生しました: {str(e)}")


def wait_for_acrobat(pid: int, timeout: int = 30) -> bool:
    """Acrobatの起動を待機（タイムアウト延長）"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # プロセスの存在確認
            process = psutil.Process(pid)
            if process.status() == psutil.STATUS_RUNNING:
                # Acrobatのウィンドウが表示されるまで少し待つ
                time.sleep(0.5)
                try:
                    active_window = pyautogui.getActiveWindowTitle()
                    if active_window and ("acrobat" in active_window.lower() or "adobe" in active_window.lower()):
                        return True
                except Exception:
                    # ウィンドウタイトル取得に失敗しても継続
                    pass

        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            print(f"Acrobat待機中にエラー: {e}")

        time.sleep(0.5)

    print(f"Acrobat起動のタイムアウト（{timeout}秒）")
    return False


def navigate_to_page(page_number: int) -> None:
    """指定ページに移動"""
    if page_number == 1:
        return

    try:
        # より確実なページ移動のため、複数回試行
        for attempt in range(3):
            try:
                pyautogui.hotkey('ctrl', 'shift', 'n')
                time.sleep(0.8)  # 待機時間を延長

                # 既存のテキストをクリア
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)

                pyautogui.write(str(page_number))
                time.sleep(0.5)
                pyautogui.press('enter')

                # 成功したらループを抜ける
                break

            except Exception as e:
                print(f"ページ移動試行{attempt + 1}でエラー: {e}")
                if attempt < 2:  # 最後の試行でなければ少し待つ
                    time.sleep(1.0)

    except Exception as e:
        print(f"ページ移動中にエラーが発生しました: {str(e)}")


def highlight_pdf(pdf_path: str, search_terms: List[str]) -> str:
    """PDFにハイライトを追加（改良版）"""
    colors: List[Tuple[float, float, float]] = [
        (1, 1, 0), (0.5, 1, 0.5), (0.5, 0.7, 1), (1, 0.6, 0.4), (1, 0.7, 0.7)
    ]

    # 一時ファイルを作成
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_path = tmp_file.name

    # グローバルリストに追加して後でクリーンアップできるようにする
    global _temp_files
    _temp_files.append(tmp_path)

    doc = None
    try:
        doc = fitz.open(pdf_path)

        for page in doc:
            for i, term in enumerate(search_terms):
                if not term.strip():  # 空の検索語をスキップ
                    continue

                text_instances = page.search_for(term.strip())
                for inst in text_instances:
                    try:
                        highlight = page.add_highlight_annot(inst)
                        highlight.set_colors(stroke=colors[i % len(colors)])
                        highlight.update()
                    except Exception as e:
                        print(f"ハイライト追加エラー (term: {term}): {e}")
                        continue

        # PDFを保存
        doc.save(tmp_path)
        return tmp_path

    except fitz.FileDataError:
        raise ValueError(f"無効なPDFファイル: {pdf_path}")
    except Exception as e:
        raise RuntimeError(f"PDFのハイライト処理中にエラーが発生しました: {str(e)}")
    finally:
        # documentオブジェクトを確実に解放
        if doc is not None:
            try:
                doc.close()
            except Exception as e:
                print(f"PDF document クローズ時にエラー: {e}")


def cleanup_single_temp_file(file_path: str) -> None:
    """単一の一時ファイルをクリーンアップ"""
    global _temp_files
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        if file_path in _temp_files:
            _temp_files.remove(file_path)
    except (OSError, ValueError) as e:
        print(f"一時ファイルの削除に失敗: {file_path} - {e}")


def get_temp_files_count() -> int:
    """現在の一時ファイル数を取得（デバッグ用）"""
    global _temp_files
    return len(_temp_files)