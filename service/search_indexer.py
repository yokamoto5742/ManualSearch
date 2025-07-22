import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz

from constants import SUPPORTED_FILE_EXTENSIONS
from utils.helpers import read_file_with_auto_encoding


class SearchIndexer:
    def __init__(self, index_file_path: str = "search_index.json"):
        self.index_file_path = index_file_path
        self.index_data = {
            "version": "1.0",
            "created_at": None,
            "last_updated": None,
            "files": {}  # file_path: {content, mtime, size, hash}
        }
        self._load_existing_index()
    
    def _load_existing_index(self) -> None:
        if os.path.exists(self.index_file_path):
            try:
                with open(self.index_file_path, encoding='utf-8') as f:
                    self.index_data = json.load(f)
                print(f"既存のインデックスを読み込みました: {len(self.index_data.get('files', {}))} ファイル")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"インデックスファイルの読み込みに失敗: {e}")
                self._initialize_new_index()
        else:
            self._initialize_new_index()
    
    def _initialize_new_index(self) -> None:
        """新しいインデックスを初期化"""
        self.index_data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": None,
            "files": {}
        }
    
    def create_index(self, directories: List[str], include_subdirs: bool = True, 
                    progress_callback: Optional[callable] = None) -> None:

        file_list = self._get_file_list(directories, include_subdirs)
        total_files = len(file_list)
        print(f"対象ファイル数: {total_files}")
        
        processed = 0
        updated_files = 0
        
        for file_path in file_list:
            try:
                if self._should_update_file(file_path):
                    self._process_file(file_path)
                    updated_files += 1
                
                processed += 1
                
                if progress_callback:
                    progress_callback(processed, total_files)

                if processed % max(1, total_files // 10) == 0:
                    print(f"進行状況: {processed}/{total_files} ({(processed/total_files)*100:.1f}%)")
                    
            except Exception as e:
                print(f"ファイル処理エラー: {file_path} - {e}")

        self._save_index()
        
        print(f"インデックス作成完了: {updated_files} ファイルを更新")
    
    def _get_file_list(self, directories: List[str], include_subdirs: bool) -> List[str]:
        file_list = []
        
        for directory in directories:
            if not os.path.exists(directory):
                print(f"ディレクトリが見つかりません: {directory}")
                continue
            
            if include_subdirs:
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._is_supported_file(file_path):
                            file_list.append(file_path)
            else:
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path) and self._is_supported_file(file_path):
                        file_list.append(file_path)
        
        return file_list
    
    def _is_supported_file(self, file_path: str) -> bool:
        return any(file_path.lower().endswith(ext) for ext in SUPPORTED_FILE_EXTENSIONS)
    
    def _should_update_file(self, file_path: str) -> bool:
        try:
            current_mtime = os.path.getmtime(file_path)
            current_size = os.path.getsize(file_path)
            
            if file_path not in self.index_data["files"]:
                return True
            
            stored_info = self.index_data["files"][file_path]

            return (stored_info.get("mtime", 0) != current_mtime or 
                   stored_info.get("size", 0) != current_size)
        
        except OSError:
            return False
    
    def _process_file(self, file_path: str) -> None:
        try:
            content = self._extract_text_content(file_path)
            if content:
                file_stats = os.stat(file_path)

                file_hash = self._calculate_file_hash(file_path)
                
                self.index_data["files"][file_path] = {
                    "content": content,
                    "mtime": file_stats.st_mtime,
                    "size": file_stats.st_size,
                    "hash": file_hash,
                    "indexed_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"ファイル処理エラー: {file_path} - {e}")
    
    def _extract_text_content(self, file_path: str) -> str:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self._extract_pdf_content(file_path)
        else:
            return self._extract_text_file_content(file_path)
    
    def _extract_pdf_content(self, file_path: str) -> str:
        content = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                content += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            print(f"PDF読み込みエラー: {file_path} - {e}")
        
        return content
    
    def _extract_text_file_content(self, file_path: str) -> str:
        try:
            return read_file_with_auto_encoding(file_path)
        except Exception as e:
            print(f"テキストファイル読み込みエラー: {file_path} - {e}")
            return ""
    
    def _calculate_file_hash(self, file_path: str) -> str:
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                hash_md5.update(chunk)
        except Exception:
            return ""
        
        return hash_md5.hexdigest()
    
    def _save_index(self) -> None:
        """インデックスをファイルに保存"""
        self.index_data["last_updated"] = datetime.now().isoformat()
        
        try:
            with open(self.index_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.index_data, f, ensure_ascii=False, indent=2)
            print(f"インデックスを保存しました: {self.index_file_path}")
        except Exception as e:
            print(f"インデックス保存エラー: {e}")
    
    def search_in_index(self, search_terms: List[str], search_type: str = "AND") -> List[Tuple[str, List[Tuple[int, str]]]]:
        results = []
        
        for file_path, file_info in self.index_data["files"].items():
            content = file_info.get("content", "")
            
            if self._match_search_terms(content, search_terms, search_type):
                matches = self._find_matches_in_content(content, search_terms, file_path)
                if matches:
                    results.append((file_path, matches))
        
        return results
    
    def _match_search_terms(self, content: str, search_terms: List[str], search_type: str) -> bool:
        content_lower = content.lower()
        
        if search_type == "AND":
            return all(term.lower() in content_lower for term in search_terms)
        else:  # OR
            return any(term.lower() in content_lower for term in search_terms)
    
    def _find_matches_in_content(self, content: str, search_terms: List[str], 
                               file_path: str, context_length: int = 100) -> List[Tuple[int, str]]:
        matches = []
        
        if file_path.lower().endswith('.pdf'):
            pages = content.split('\n\n')
            for page_num, page_content in enumerate(pages, 1):
                for term in search_terms:
                    if term.lower() in page_content.lower():
                        context = self._extract_context(page_content, term, context_length)
                        matches.append((page_num, context))
                        break  # ページごとに1つのマッチのみ
        else:
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                for term in search_terms:
                    if term.lower() in line.lower():
                        context = self._extract_context(line, term, context_length)
                        matches.append((line_num, context))
                        break  # 行ごとに1つのマッチのみ

        return matches[:200]
    
    def _extract_context(self, text: str, search_term: str, context_length: int) -> str:
        term_index = text.lower().find(search_term.lower())
        if term_index == -1:
            return text[:context_length * 2]
        
        start = max(0, term_index - context_length)
        end = min(len(text), term_index + len(search_term) + context_length)
        
        return text[start:end]
    
    def get_index_stats(self) -> Dict:
        files_count = len(self.index_data.get("files", {}))
        total_size = sum(info.get("size", 0) for info in self.index_data.get("files", {}).values())
        
        return {
            "files_count": files_count,
            "total_size_mb": total_size / (1024 * 1024),
            "created_at": self.index_data.get("created_at"),
            "last_updated": self.index_data.get("last_updated"),
            "index_file_size_mb": os.path.getsize(self.index_file_path) / (1024 * 1024) if os.path.exists(self.index_file_path) else 0
        }
    
    def remove_missing_files(self) -> int:
        missing_files = []
        
        for file_path in self.index_data["files"]:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        for file_path in missing_files:
            del self.index_data["files"][file_path]
        
        if missing_files:
            self._save_index()
            print(f"{len(missing_files)} 個の存在しないファイルをインデックスから削除しました")
        
        return len(missing_files)
