# app.py - Modular Flask Application for Markdown Reader
# ======================================================

import os
import re
from datetime import datetime
from flask import Flask, render_template, abort, jsonify, request, url_for
import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions import codehilite, fenced_code, tables

# Flaskアプリケーションを作成します
app = Flask(__name__)

# 設定
DOCS_DIR = '.'
READING_SPEED_CJK = 400  # 日本語読書速度（文字/分）
READING_SPEED_LATIN = 200  # 英語読書速度（語/分）

class FileInfo:
    """ファイル情報を保持するクラス"""
    def __init__(self, path, name, content='', size='', modified=''):
        self.path = path
        self.name = name
        self.content = content
        self.size = size
        self.modified = modified
        self.stats = {
            'size': size,
            'modified': modified
        } if size or modified else None

def format_file_size(size_bytes):
    """ファイルサイズを人間が読みやすい形式に変換"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024} KB"
    else:
        return f"{size_bytes // (1024 * 1024)} MB"

def format_datetime(timestamp):
    """タイムスタンプを人間が読みやすい形式に変換"""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M')

def get_md_files_structure():
    """
    ディレクトリを再帰的に探索し、.mdファイルの情報をリストで取得します。
    ファイル名のプレフィックスはソートにのみ使用し、表示用の名前からは除去します。
    """
    md_files_info = []
    
    for root, dirs, files in os.walk(DOCS_DIR, topdown=True):
        # 除外するディレクトリ
        excluded_dirs = ['.venv', '__pycache__', '.git', 'node_modules', 'static', 'templates']
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        dirs.sort()
        files.sort()
        
        depth = root.count(os.sep) if root != '.' else 0
        
        for filename in files:
            if filename.endswith('.md'):
                # 接頭辞に番号がついていない場合はスキップ
                match = re.match(r'^\d+_', filename)
                if not match:
                    continue
                    
                full_path = os.path.join(root, filename)
                
                try:
                    # ファイル情報を取得
                    stat_info = os.stat(full_path)
                    file_size = format_file_size(stat_info.st_size)
                    modified_time = format_datetime(stat_info.st_mtime)
                    
                    # ファイル内容を読み込み
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 表示用のファイル名（接頭辞を除去）
                    clean_name = filename[len(match.group(0)):].replace('.md', '')
                    
                    # ソート用のキーを生成
                    sort_key = []
                    path_parts = full_path.replace(DOCS_DIR, '').strip('/').split('/')
                    for part in path_parts:
                        if part.endswith('.md'):
                            match = re.match(r'^(\d+)_', part)
                            sort_key.append(int(match.group(1)) if match else 999)
                        else:
                            match = re.match(r'^(\d+)_', part)
                            sort_key.append(int(match.group(1)) if match else 999)
                    
                    file_info = FileInfo(
                        path=full_path,
                        name=clean_name,
                        content=content,
                        size=file_size,
                        modified=modified_time
                    )
                    
                    md_files_info.append({
                        'file_info': file_info,
                        'sort_key': sort_key,
                        'depth': depth
                    })
                    
                except (IOError, OSError) as e:
                    print(f"Warning: Could not read file {full_path}: {e}")
                    continue
    
    # ソート
    md_files_info.sort(key=lambda x: x['sort_key'])
    
    # FileInfoオブジェクトのみを返す
    return [item['file_info'] for item in md_files_info]

def calculate_reading_time(content):
    """コンテンツの推定読書時間を計算"""
    # CJK文字（中国語、日本語、韓国語）をカウント
    cjk_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u309f\u30a0-\u30ff]', content))
    
    # 英語の単語をカウント
    latin_words = len(re.findall(r'\b[a-zA-Z]+\b', content))
    
    # 読書時間を計算（分）
    cjk_time = cjk_chars / READING_SPEED_CJK
    latin_time = latin_words / READING_SPEED_LATIN
    
    total_time = cjk_time + latin_time
    return max(1, round(total_time))

def count_words(content):
    """コンテンツの単語数をカウント"""
    # CJK文字をカウント
    cjk_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u309f\u30a0-\u30ff]', content))
    
    # 英語の単語をカウント  
    latin_words = len(re.findall(r'\b[a-zA-Z]+\b', content))
    
    # CJK文字は1文字を1語として計算
    return cjk_chars + latin_words

def process_markdown(content):
    """Markdownコンテンツを処理してHTMLに変換"""
    # Markdown拡張機能を設定
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.attr_list',
        'markdown.extensions.def_list',
        'markdown.extensions.abbr',
        'markdown.extensions.footnotes',
        'markdown.extensions.md_in_html'
    ]
    
    extension_configs = {
        'markdown.extensions.codehilite': {
            'css_class': 'highlight',
            'use_pygments': True
        },
        'markdown.extensions.toc': {
            'permalink': True,
            'permalink_class': 'toc-link',
            'permalink_title': 'Permalink to this heading'
        }
    }
    
    md = markdown.Markdown(
        extensions=extensions,
        extension_configs=extension_configs
    )
    
    html_content = md.convert(content)
    return html_content

@app.route('/')
def index():
    """インデックスページ"""
    files = get_md_files_structure()
    total_files = len(files)
    
    context = {
        'files': files,
        'total_files': total_files,
        'current_file': None,
        'content': None,
        'current_index': None,
        'progress_percentage': 0,
        'prev_file': None,
        'next_file': None,
        'word_count': None,
        'reading_time': None
    }
    
    return render_template('index.html', **context)

@app.route('/all')
def view_all():
    """すべてのMarkdownファイルを一枚綴りで表示"""
    files = get_md_files_structure()
    
    if not files:
        return render_template('index.html', **{
            'files': [],
            'total_files': 0,
            'current_file': None,
            'content': '<p>No markdown files found.</p>',
            'current_index': None,
            'progress_percentage': 0,
            'prev_file': None,
            'next_file': None,
            'word_count': 0,
            'reading_time': 0,
            'view_mode': 'all'
        })
    
    # すべてのファイルの内容を結合
    combined_content = []
    total_word_count = 0
    total_reading_time = 0
    
    for i, file in enumerate(files, 1):
        try:
            # ファイル内容を読み込み
            file_path = os.path.join(DOCS_DIR, file.path)
            
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # セクション区切りを追加
            section_header = f'<div class="document-section" data-file="{file.path}">'
            section_header += f'<h1 class="section-title">{i}. {file.name}</h1>'
            section_header += f'<div class="section-meta">File: {file.path}</div>'
            
            # MarkdownをHTMLに変換
            html_content = process_markdown(content)
            
            # 統計情報を計算
            word_count = count_words(content)
            reading_time = calculate_reading_time(content)
            
            total_word_count += word_count
            total_reading_time += reading_time
            
            # セクションとして追加
            combined_content.append(section_header)
            combined_content.append(html_content)
            combined_content.append('</div>')
            
            # セクション間の区切り
            if i < len(files):
                combined_content.append('<hr class="section-divider">')
                
        except Exception as e:
            # エラーハンドリング
            error_content = f'<div class="error-section"><p>Error loading {file.name}: {str(e)}</p></div>'
            combined_content.append(error_content)
    
    # 結合されたコンテンツ
    final_content = '\n'.join(combined_content)
    
    # 仮想ファイル情報を作成
    virtual_file = FileInfo(
        path='all',
        name='All Documents (Combined View)',
        content=final_content
    )
    
    context = {
        'files': files,
        'total_files': len(files),
        'current_file': virtual_file,
        'content': final_content,
        'current_index': 'ALL',
        'progress_percentage': 100,
        'prev_file': None,
        'next_file': None,
        'word_count': total_word_count,
        'reading_time': total_reading_time,
        'view_mode': 'all'
    }
    
    return render_template('index.html', **context)

@app.route('/file/<path:file_path>')
def view_file(file_path):
    """特定のMarkdownファイルを表示"""
    files = get_md_files_structure()
    
    # 現在のファイルを検索
    current_file = None
    current_index = None
    
    for i, file_info in enumerate(files):
        if file_info.path == file_path:
            current_file = file_info
            current_index = i + 1
            break
    
    if not current_file:
        abort(404)
    
    # 前後のファイルを取得
    prev_file = files[current_index - 2] if current_index > 1 else None
    next_file = files[current_index] if current_index < len(files) else None
    
    # Markdownを処理
    html_content = process_markdown(current_file.content)
    
    # 統計情報を計算
    word_count = count_words(current_file.content)
    reading_time = calculate_reading_time(current_file.content)
    
    # 進捗を計算
    progress_percentage = (current_index / len(files)) * 100 if files else 0
    
    context = {
        'files': files,
        'total_files': len(files),
        'current_file': current_file,
        'content': html_content,
        'current_index': current_index,
        'progress_percentage': progress_percentage,
        'prev_file': prev_file,
        'next_file': next_file,
        'word_count': word_count,
        'reading_time': reading_time,
        'document_id': file_path
    }
    
    return render_template('index.html', **context)

@app.route('/api/files')
def api_files():
    """ファイル一覧をJSONで返すAPI"""
    files = get_md_files_structure()
    
    files_data = []
    for i, file_info in enumerate(files):
        files_data.append({
            'path': file_info.path,
            'name': file_info.name,
            'index': i + 1,
            'size': file_info.size,
            'modified': file_info.modified,
            'url': url_for('view_file', file_path=file_info.path)
        })
    
    return jsonify({
        'files': files_data,
        'total': len(files)
    })

@app.route('/api/search')
def api_search():
    """検索API"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []})
    
    files = get_md_files_structure()
    results = []
    
    for file_info in files:
        # ファイル名での検索
        if query.lower() in file_info.name.lower():
            results.append({
                'type': 'filename',
                'file_path': file_info.path,
                'file_name': file_info.name,
                'match': file_info.name,
                'url': url_for('view_file', file_path=file_info.path)
            })
        
        # コンテンツでの検索
        lines = file_info.content.split('\n')
        for line_num, line in enumerate(lines, 1):
            if query.lower() in line.lower():
                # コンテキストを抽出
                start_pos = max(0, line.lower().find(query.lower()) - 50)
                end_pos = min(len(line), start_pos + 100)
                context = line[start_pos:end_pos]
                
                if start_pos > 0:
                    context = '...' + context
                if end_pos < len(line):
                    context = context + '...'
                
                results.append({
                    'type': 'content',
                    'file_path': file_info.path,
                    'file_name': file_info.name,
                    'line_number': line_num,
                    'match': context,
                    'url': url_for('view_file', file_path=file_info.path) + f'#line-{line_num}'
                })
    
    return jsonify({'results': results[:20]})  # 最大20件まで

@app.errorhandler(404)
def not_found_error(error):
    """404エラーハンドラ"""
    files = get_md_files_structure()
    
    context = {
        'files': files,
        'total_files': len(files),
        'current_file': None,
        'content': '<h1>Page Not Found</h1><p>The requested file could not be found.</p>',
        'current_index': None,
        'progress_percentage': 0,
        'prev_file': None,
        'next_file': None,
        'word_count': None,
        'reading_time': None
    }
    
    return render_template('index.html', **context), 404

@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラ"""
    files = get_md_files_structure()
    
    context = {
        'files': files,
        'total_files': len(files),
        'current_file': None,
        'content': '<h1>Internal Server Error</h1><p>An error occurred while processing your request.</p>',
        'current_index': None,
        'progress_percentage': 0,
        'prev_file': None,
        'next_file': None,
        'word_count': None,
        'reading_time': None
    }
    
    return render_template('index.html', **context), 500

# SCSS compilation route for development
@app.route('/static/css/main.css')
def compile_scss():
    """SCSS to CSS compilation endpoint for development"""
    try:
        import sass
        
        # Compile SCSS to CSS
        css_content = sass.compile(
            filename=os.path.join(app.static_folder, 'scss', 'main.scss'),
            output_style='expanded',
            include_paths=[os.path.join(app.static_folder, 'scss')]
        )
        
        from flask import Response
        return Response(css_content, mimetype='text/css')
        
    except ImportError:
        # Fallback: serve a basic CSS file if sass is not installed
        basic_css = """
        /* Basic fallback styles */
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .app-container { display: flex; min-height: 100vh; }
        .sidebar { width: 300px; background: #f8f9fa; padding: 1rem; }
        .main-content { flex: 1; padding: 1rem; }
        .markdown-content { max-width: 800px; margin: 0 auto; }
        """
        from flask import Response
        return Response(basic_css, mimetype='text/css')
    except Exception as e:
        # Error handling
        error_css = f"/* SCSS compilation error: {str(e)} */"
        from flask import Response
        return Response(error_css, mimetype='text/css')

if __name__ == '__main__':
    # 開発用の設定
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
