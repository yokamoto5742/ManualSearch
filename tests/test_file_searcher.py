import pytest
import os
from PyQt5.QtCore import QCoreApplication
from file_searcher import FileSearcher


@pytest.fixture(scope="module")
def qapp():
    return QCoreApplication([])


@pytest.fixture
def temp_directory(tmpdir):
    # テスト用の一時ディレクトリとファイルを作成
    test_file1 = tmpdir.join("test1.txt")
    test_file1.write("This is a test file. It contains some test content.")

    test_file2 = tmpdir.join("test2.txt")
    test_file2.write("Another test file with different content.")

    subdir = tmpdir.mkdir("subdir")
    test_file3 = subdir.join("test3.txt")
    test_file3.write("This is a file in a subdirectory. It also contains test content.")

    return tmpdir


def test_temp_directory_setup(temp_directory):
    # テスト用ディレクトリの構造を確認
    assert os.path.isfile(os.path.join(str(temp_directory), "test1.txt"))
    assert os.path.isfile(os.path.join(str(temp_directory), "test2.txt"))
    assert os.path.isfile(os.path.join(str(temp_directory), "subdir", "test3.txt"))

    # ファイルの内容を確認
    with open(os.path.join(str(temp_directory), "test1.txt"), "r") as f:
        assert "This is a test file. It contains some test content." in f.read()
    with open(os.path.join(str(temp_directory), "test2.txt"), "r") as f:
        assert "Another test file with different content." in f.read()
    with open(os.path.join(str(temp_directory), "subdir", "test3.txt"), "r") as f:
        assert "This is a file in a subdirectory. It also contains test content." in f.read()


def test_file_searcher_basic(qapp, temp_directory):
    searcher = FileSearcher(str(temp_directory), ["test"], True, "OR", [".txt"], 10)

    results = []

    def on_result_found(file_path, matches):
        results.append((file_path, matches))
        print(f"Found in file: {file_path}")
        for match in matches:
            print(f"  Match: {match}")

    searcher.result_found.connect(on_result_found)
    searcher.run()

    print(f"Total results: {len(results)}")
    assert len(results) == 3  # 3つのファイルすべてにマッチするはず


def test_file_searcher_and_search(qapp, temp_directory):
    searcher = FileSearcher(str(temp_directory), ["test", "content"], True, "AND", [".txt"], 10)

    results = []

    def on_result_found(file_path, matches):
        results.append((file_path, matches))
        print(f"Found in file: {file_path}")
        for match in matches:
            print(f"  Match: {match}")

    searcher.result_found.connect(on_result_found)
    searcher.run()

    print(f"Total results: {len(results)}")
    assert len(results) == 3  # "test1.txt", "test2.txt", "subdir/test3.txt"がマッチするはず

    # 各ファイルが結果に含まれていることを確認
    file_names = [os.path.basename(result[0]) for result in results]
    assert "test1.txt" in file_names
    assert "test2.txt" in file_names
    assert "test3.txt" in file_names

    # 各ファイルの内容が期待通りであることを確認
    for file_path, matches in results:
        if "test1.txt" in file_path:
            assert any("test file" in match[1] for match in matches)
            assert any("test content" in match[1] for match in matches)
        elif "test2.txt" in file_path:
            assert any("test file" in match[1] for match in matches)
            assert any("content" in match[1] for match in matches)
        elif "test3.txt" in file_path:
            assert any("test content" in match[1] for match in matches)


def test_file_searcher_no_subdirs(qapp, temp_directory):
    searcher = FileSearcher(str(temp_directory), ["test"], False, "OR", [".txt"], 10)

    results = []

    def on_result_found(file_path, matches):
        results.append((file_path, matches))
        print(f"Found in file: {file_path}")

    searcher.result_found.connect(on_result_found)
    searcher.run()

    print(f"Total results: {len(results)}")
    assert len(results) == 2  # サブディレクトリを除外するので2つのファイルのみマッチするはず


def test_file_searcher_file_extensions(qapp, temp_directory):
    # 存在しない拡張子を指定
    searcher = FileSearcher(str(temp_directory), ["test"], True, "OR", [".pdf"], 10)

    results = []

    def on_result_found(file_path, matches):
        results.append((file_path, matches))
        print(f"Found in file: {file_path}")

    searcher.result_found.connect(on_result_found)
    searcher.run()

    print(f"Total results: {len(results)}")
    assert len(results) == 0  # マッチするファイルがないはず


def test_file_searcher_progress_update(qapp, temp_directory):
    searcher = FileSearcher(str(temp_directory), ["test"], True, "OR", [".txt"], 10)

    progress_values = []

    def on_progress_update(value):
        progress_values.append(value)
        print(f"Progress: {value}%")

    searcher.progress_update.connect(on_progress_update)
    searcher.run()

    print(f"Progress updates: {progress_values}")
    assert len(progress_values) > 0
    assert progress_values[-1] == 100  # 最後の進捗が100%であることを確認


def test_file_searcher_cancel(qapp, temp_directory):
    searcher = FileSearcher(str(temp_directory), ["test"], True, "OR", [".txt"], 10)

    results = []

    def on_result_found(file_path, matches):
        results.append((file_path, matches))
        print(f"Found in file: {file_path}")
        searcher.cancel_search()  # 最初の結果が見つかったらキャンセル

    searcher.result_found.connect(on_result_found)
    searcher.run()

    print(f"Total results: {len(results)}")
    assert len(results) <= 1  # キャンセルが機能していれば、最大1つの結果のみ


# モック関数を使用してPDFファイルの検索をテスト
def test_file_searcher_pdf(qapp, temp_directory, mocker):
    pdf_file = temp_directory.join("test.pdf")
    pdf_file.write("dummy content")  # 実際のPDFではありませんが、テストには十分です

    # PyPDF2.PdfReaderをモック
    mock_pdf_reader = mocker.patch('file_searcher.PyPDF2.PdfReader')
    mock_pdf_reader.return_value.pages = [mocker.Mock(extract_text=lambda: "This is a test PDF content.")]

    searcher = FileSearcher(str(temp_directory), ["test"], True, "OR", [".pdf"], 10)

    results = []

    def on_result_found(file_path, matches):
        results.append((file_path, matches))
        print(f"Found in file: {file_path}")
        for match in matches:
            print(f"  Match: {match}")

    searcher.result_found.connect(on_result_found)
    searcher.run()

    print(f"Total results: {len(results)}")
    assert len(results) == 1  # PDFファイルにマッチするはず
    assert results[0][0].endswith("test.pdf")


if __name__ == "__main__":
    pytest.main()
