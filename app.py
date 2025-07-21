# app.py
# 必要なライブラリをインポートします
import os
import re
import json
import unicodedata
from flask import Flask, render_template_string, abort, jsonify, request
import markdown
from markdown.extensions.toc import TocExtension

# Flaskアプリケーションを作成します
app = Flask(__name__)

# Markdownファイルが置かれているディレクトリを指定します
DOCS_DIR = '.'

# --- ヘルパー関数 ---

def get_md_files_structure():
    """
    ディレクトリを再帰的に探索し、.mdファイルの情報をリストで取得します。
    ファイル名のプレフィックスはソートにのみ使用し、表示用の名前からは除去します。
    階層構造を保持して正しい順序でファイルを並べます。
    """
    md_files_info = []
    
    # まずすべてのファイル情報を収集
    for root, dirs, files in os.walk(DOCS_DIR, topdown=True):
        if '.venv' in dirs: dirs.remove('.venv')
        if 'app.py' in files: files.remove('app.py')

        dirs.sort()  # ディレクトリを番号順でソート
        files.sort()  # ファイルを番号順でソート
        
        depth = root.count(os.sep) if root != '.' else 0
        
        for filename in files:
            if filename.endswith('.md'):
                # 接頭辞に番号がついていない場合はスキップ
                match = re.match(r'^\d+_', filename)
                if not match:
                    continue
                    
                full_path = os.path.join(root, filename)
                
                # ファイル内容を読み込んで統計情報を取得
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 文字数と推定読書時間を計算（日本語400文字/分として計算）
                char_count = len(content)
                estimated_reading_time = max(1, char_count // 400)
                
                clean_name_with_ext = filename[len(match.group(0)):]
                
                # ソート用のキーを生成（パス全体を使用して階層順序を保持）
                sort_key = []
                path_parts = full_path.replace(DOCS_DIR, '').strip('/').split('/')
                for part in path_parts:
                    if part.endswith('.md'):
                        # ファイルの場合
                        match = re.match(r'^(\d+)_', part)
                        sort_key.append(int(match.group(1)) if match else 999)
                    else:
                        # ディレクトリの場合
                        match = re.match(r'^(\d+)_', part)
                        sort_key.append(int(match.group(1)) if match else 999)
                
                md_files_info.append({
                    'path': full_path,
                    'depth': depth,
                    'clean_name': clean_name_with_ext.replace('.md', ''),
                    'char_count': char_count,
                    'estimated_reading_time': estimated_reading_time,
                    'content': content,
                    'sort_key': sort_key  # ソート用キー
                })
    
    # ソートキーを使用して正しい階層順序でソート
    md_files_info.sort(key=lambda x: x['sort_key'])
    
    # インデックスを再割り当て
    for i, file_info in enumerate(md_files_info):
        file_info['index'] = i
        # ソートキーは不要なので削除
        del file_info['sort_key']
    
    return md_files_info

def extract_headings(content):
    """Markdownコンテンツからヘッダーを抽出して目次を生成"""
    import unicodedata
    headings = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('#').strip()
            
            # カスタムslugify関数と同じロジックを使用
            anchor_id = slugify_heading(title, '-')
                
            headings.append({
                'level': level,
                'title': title,
                'anchor': anchor_id,
                'line': i + 1
            })
    return headings

def slugify_heading(value, separator='-'):
    """見出しテキストからアンカーIDを生成（TocExtension対応）"""
    import unicodedata
    import re
    
    # Unicode正規化
    value = unicodedata.normalize('NFKD', value)
    # 英数字、ひらがな、カタカナ、漢字、ハイフン、アンダースコア以外を削除
    value = re.sub(r'[^\w\s\-_ぁ-んァ-ヶ一-龯]', '', value)
    # スペースをセパレータに変換
    value = re.sub(r'[\s_]+', separator, value)
    # 連続するセパレータを単一に
    value = re.sub(f'{re.escape(separator)}+', separator, value)
    # 先頭末尾のセパレータを削除
    value = value.strip(separator).lower()
    
    return value if value else 'heading'

# --- HTMLテンプレート & スタイル ---

# Markdownコンテンツの表示スタイル
MARKDOWN_STYLE = """
<style>
    /* 基本的なMarkdownスタイル */
    .markdown-content h1, .markdown-content h2, .markdown-content h3 {
        padding-bottom: 0.3em; margin-top: 1.5em; margin-bottom: 1em;
        border-bottom: 1px solid #e5e7eb; 
        scroll-margin-top: 120px; /* ヘッダーやプログレスバーのオフセット */
    }
    .dark .markdown-content h1, .dark .markdown-content h2, .dark .markdown-content h3 {
        border-bottom-color: #374151;
    }
    .markdown-content h1 { font-size: 2.25rem; } 
    .markdown-content h2 { font-size: 1.875rem; } 
    .markdown-content h3 { font-size: 1.5rem; }
    .markdown-content h4, .markdown-content h5, .markdown-content h6 { 
        scroll-margin-top: 120px; 
        margin-top: 1.25em; 
        margin-bottom: 0.75em; 
    }
    .markdown-content p { margin-bottom: 1em; line-height: 1.7; }
    .markdown-content a { color: #3b82f6; text-decoration: underline; }
    .markdown-content pre {
        background-color: #f3f4f6; color: #111827;
        padding: 1rem; border-radius: 0.5rem; overflow-x: auto; margin-bottom: 1em;
    }
    .dark .markdown-content pre { background-color: #1f2937; color: #d1d5db; }
    .markdown-content code { 
        font-family: 'Fira Code', 'Monaco', 'Consolas', monospace; 
        background-color: #e5e7eb; padding: 0.2em 0.4em; border-radius: 0.25rem; 
    }
    .dark .markdown-content code { background-color: #374151; }
    .markdown-content pre > code { background-color: transparent; padding: 0; }
    .markdown-content ul, .markdown-content ol { padding-left: 2em; margin-bottom: 1em; }
    .markdown-content li { margin-bottom: 0.5em; }
    .markdown-content hr { border-top: 1px solid #e5e7eb; margin: 3rem 0; }
    .dark .markdown-content hr { border-top-color: #374151; }
    
    /* 目次スタイル */
    .toc {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 2rem 0;
        max-height: 400px;
        overflow-y: auto;
    }
    .dark .toc {
        background-color: #1e293b;
        border-color: #475569;
    }
    .toc ul {
        list-style: none;
        padding-left: 0;
        margin: 0;
    }
    .toc ul ul {
        padding-left: 1.5rem;
        margin-top: 0.25rem;
    }
    .toc li {
        margin: 0.25rem 0;
    }
    .toc a {
        color: #475569;
        text-decoration: none;
        display: block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        transition: all 0.2s;
    }
    .dark .toc a {
        color: #94a3b8;
    }
    .toc a:hover {
        background-color: #e2e8f0;
        color: #1e293b;
    }
    .dark .toc a:hover {
        background-color: #334155;
        color: #f1f5f9;
    }
    
    /* アンカーリンクスタイル - 完全に非表示にして、見出し自体をクリック可能にする */
    .anchor-link {
        display: none;
    }
    
    /* 見出しに直接リンク機能を追加 */
    .markdown-content h1,
    .markdown-content h2,
    .markdown-content h3,
    .markdown-content h4,
    .markdown-content h5,
    .markdown-content h6 {
        position: relative;
        cursor: pointer;
    }
    
    .markdown-content h1:hover,
    .markdown-content h2:hover,
    .markdown-content h3:hover,
    .markdown-content h4:hover,
    .markdown-content h5:hover,
    .markdown-content h6:hover {
        color: #3b82f6;
    }
    
    .dark .markdown-content h1:hover,
    .dark .markdown-content h2:hover,
    .dark .markdown-content h3:hover,
    .dark .markdown-content h4:hover,
    .dark .markdown-content h5:hover,
    .dark .markdown-content h6:hover {
        color: #60a5fa;
    }
    
    /* プログレスバー */
    .progress-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background-color: #e2e8f0;
        z-index: 1000;
    }
    .dark .progress-container {
        background-color: #475569;
    }
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #3b82f6, #06b6d4);
        width: 0%;
        transition: width 0.3s ease;
    }
    
    /* 統計情報 */
    .reading-stats {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
        padding: 1rem;
        background-color: #f1f5f9;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        color: #64748b;
    }
    .dark .reading-stats {
        background-color: #1e293b;
        color: #94a3b8;
    }
    .reading-stat {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    /* 印刷スタイル */
    @media print {
        .no-print { display: none !important; }
        .markdown-content { 
            font-size: 12pt; 
            line-height: 1.5;
            color: #000 !important;
        }
        .markdown-content pre {
            background-color: #f5f5f5 !important;
            color: #000 !important;
            border: 1px solid #ccc;
        }
        .toc { 
            break-inside: avoid;
            page-break-inside: avoid;
        }
    }
    
    /* アニメーション */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .animate-fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* サイドバー固定スタイル */
    .sidebar-fixed {
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        z-index: 30;
    }
</style>
"""

# JavaScriptをPythonのf-stringから分離し、パースエラーを回避
HEAD_SCRIPT = """
<script>
    // ダークモード設定の読み込み
    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    
    // プログレスバー初期化
    window.addEventListener('load', function() {
        const progressContainer = document.createElement('div');
        progressContainer.className = 'progress-container no-print';
        progressContainer.innerHTML = '<div class="progress-bar" id="progress-bar"></div>';
        document.body.insertBefore(progressContainer, document.body.firstChild);
        updateProgress();
    });
    
    function updateProgress() {
        window.addEventListener('scroll', function() {
            const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = (window.scrollY / totalHeight) * 100;
            document.getElementById('progress-bar').style.width = Math.min(progress, 100) + '%';
        });
    }
</script>
"""

BODY_SCRIPT = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // テーマトグル
    const themeToggle = document.getElementById('theme-toggle');
    const htmlEl = document.documentElement;
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            htmlEl.classList.toggle('dark');
            localStorage.theme = htmlEl.classList.contains('dark') ? 'dark' : 'light';
        });
    }

    // サイドバー制御
    const sidebar = document.getElementById('sidebar');
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    if (sidebar && mobileMenuButton) {
        mobileMenuButton.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('-translate-x-full');
        });
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !mobileMenuButton.contains(e.target)) {
                sidebar.classList.add('-translate-x-full');
            }
        });
    }

    // 検索機能
    const searchInput = document.getElementById('search-docs');
    const docLinks = document.querySelectorAll('#doc-list a');
    if (searchInput && docLinks.length > 0) {
        searchInput.addEventListener('keyup', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            docLinks.forEach(link => {
                const isVisible = link.textContent.toLowerCase().includes(searchTerm);
                link.style.display = isVisible ? 'flex' : 'none';
            });
        });
    }

    // コンテンツ内検索
    const contentSearchInput = document.getElementById('content-search');
    if (contentSearchInput) {
        contentSearchInput.addEventListener('keyup', debounce(function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const content = document.querySelector('.markdown-content');
            if (!content) return;
            
            // 既存のハイライトを削除
            removeHighlights(content);
            
            if (searchTerm.length > 2) {
                highlightText(content, searchTerm);
            }
        }, 300));
    }

    // ブックマーク機能
    initBookmarks();

    // スムーズスクロール - より確実な実装
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const target = document.getElementById(targetId);
            if (target) {
                // プログレスバーとヘッダーの高さを考慮してオフセットを設定
                const offsetTop = target.offsetTop - 120;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // URLを更新
                if (history.pushState) {
                    history.pushState(null, null, '#' + targetId);
                }
                
                // フォーカスを設定
                target.focus({ preventScroll: true });
            } else {
                console.warn('Target not found:', targetId);
            }
        });
    });

    // 見出しをクリックしてもジャンプできるようにする
    document.querySelectorAll('.markdown-content h1, .markdown-content h2, .markdown-content h3, .markdown-content h4, .markdown-content h5, .markdown-content h6').forEach(heading => {
        heading.addEventListener('click', function() {
            const id = this.getAttribute('id');
            if (id) {
                if (history.pushState) {
                    history.pushState(null, null, '#' + id);
                }
                this.focus({ preventScroll: true });
            }
        });
    });

    // ページ読み込み時のハッシュ処理
    if (window.location.hash) {
        setTimeout(() => {
            const target = document.querySelector(window.location.hash);
            if (target) {
                const offsetTop = target.offsetTop - 120;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        }, 100);
    }

    // 読書進捗の保存
    saveReadingProgress();
    
    // デバッグ用: 目次のリンクとヘッダーのIDを確認
    console.log('=== DEBUG INFO ===');
    console.log('TOC links:');
    document.querySelectorAll('.toc a').forEach((link, index) => {
        console.log(`  ${index}: href="${link.href}", text="${link.textContent}"`);
    });
    console.log('Headers with IDs:');
    document.querySelectorAll('.markdown-content h1[id], .markdown-content h2[id], .markdown-content h3[id], .markdown-content h4[id], .markdown-content h5[id], .markdown-content h6[id]').forEach((header, index) => {
        console.log(`  ${index}: id="${header.id}", text="${header.textContent}"`);
    });
    console.log('All headers (with or without IDs):');
    document.querySelectorAll('.markdown-content h1, .markdown-content h2, .markdown-content h3, .markdown-content h4, .markdown-content h5, .markdown-content h6').forEach((header, index) => {
        console.log(`  ${index}: id="${header.id || 'NO_ID'}", text="${header.textContent}"`);
    });
    console.log('=================');
});

// デバウンス関数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// テキストハイライト機能
function highlightText(container, searchTerm) {
    const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );

    const textNodes = [];
    let node;
    while (node = walker.nextNode()) {
        textNodes.push(node);
    }

    textNodes.forEach(textNode => {
        const text = textNode.textContent;
        const regex = new RegExp(searchTerm, 'gi');
        if (regex.test(text)) {
            const highlightedText = text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800">$&</mark>');
            const wrapper = document.createElement('span');
            wrapper.innerHTML = highlightedText;
            textNode.parentNode.replaceChild(wrapper, textNode);
        }
    });
}

function removeHighlights(container) {
    const highlights = container.querySelectorAll('mark');
    highlights.forEach(highlight => {
        const parent = highlight.parentNode;
        parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
        parent.normalize();
    });
}

// ブックマーク機能
function initBookmarks() {
    const bookmarkButton = document.getElementById('bookmark-toggle');
    if (bookmarkButton) {
        const currentPath = window.location.pathname;
        const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
        const isBookmarked = bookmarks.includes(currentPath);
        
        updateBookmarkButton(bookmarkButton, isBookmarked);
        
        bookmarkButton.addEventListener('click', () => {
            toggleBookmark(currentPath);
            const newIsBookmarked = JSON.parse(localStorage.getItem('bookmarks') || '[]').includes(currentPath);
            updateBookmarkButton(bookmarkButton, newIsBookmarked);
        });
    }
}

function updateBookmarkButton(button, isBookmarked) {
    button.innerHTML = isBookmarked ? 
        '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M3 4a2 2 0 012-2h10a2 2 0 012 2v12l-5-3-5 3V4z"></path></svg>' :
        '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path></svg>';
    button.title = isBookmarked ? 'ブックマークを削除' : 'ブックマークに追加';
}

function toggleBookmark(path) {
    const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
    const index = bookmarks.indexOf(path);
    
    if (index > -1) {
        bookmarks.splice(index, 1);
    } else {
        bookmarks.push(path);
    }
    
    localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
}

// 読書進捗の保存
function saveReadingProgress() {
    let progressTimer;
    window.addEventListener('scroll', () => {
        clearTimeout(progressTimer);
        progressTimer = setTimeout(() => {
            const currentPath = window.location.pathname;
            const progress = Math.round((window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100);
            localStorage.setItem(`progress-${currentPath}`, progress);
        }, 1000);
    });
    
    // ページ読み込み時に進捗を自動復元
    const currentPath = window.location.pathname;
    const savedProgress = localStorage.getItem(`progress-${currentPath}`);
    if (savedProgress && savedProgress > 10) {
        // 自動的に復元（確認なし）
        setTimeout(() => {
            window.scrollTo({
                top: (document.documentElement.scrollHeight - window.innerHeight) * (savedProgress / 100),
                behavior: 'smooth'
            });
        }, 500);
    }
}
</script>
"""


# --- ルート（URLのパス）ごとの処理 ---

@app.route('/api/search')
def api_search():
    """コンテンツ内検索API"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    files = get_md_files_structure()
    results = []
    
    for file_info in files:
        content = file_info['content']
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines):
            if query in line.lower():
                # 前後の文脈を含める
                context_start = max(0, line_num - 2)
                context_end = min(len(lines), line_num + 3)
                context = '\n'.join(lines[context_start:context_end])
                
                results.append({
                    'file_index': file_info['index'],
                    'file_name': file_info['clean_name'],
                    'line_number': line_num + 1,
                    'content': context,
                    'highlight_line': line
                })
    
    return jsonify(results[:20])  # 最大20件まで

@app.route('/api/bookmarks')
def api_bookmarks():
    """ブックマーク一覧取得API"""
    files = get_md_files_structure()
    bookmarks_data = []
    
    for file_info in files:
        bookmarks_data.append({
            'path': f'/view/{file_info["index"]}',
            'title': file_info['clean_name'],
            'index': file_info['index']
        })
    
    return jsonify(bookmarks_data)

@app.route('/')
def show_all():
    """全てのMarkdownファイルを連結して表示するページ"""
    files = get_md_files_structure()
    full_content = ""
    total_chars = 0
    total_reading_time = 0
    
    for file_info in files:
        full_content += f"## <span class='text-lg font-semibold text-sky-600 dark:text-sky-400 mr-2'>{file_info['index'] + 1}.</span> {file_info['clean_name']}\n"
        full_content += f"<span class='text-sm text-gray-500 dark:text-gray-400'>Path: {file_info['path']}</span>\n\n"
        with open(file_info['path'], 'r', encoding='utf-8') as f: 
            content = f.read()
            full_content += content + "\n\n<hr>\n\n"
        total_chars += file_info['char_count']
        total_reading_time += file_info['estimated_reading_time']
    
    html_content = markdown.markdown(full_content, extensions=['fenced_code', 
        TocExtension(anchorlink=False, slugify=slugify_heading)])
        
    # 見出しに手動でアンカーIDを追加
    import re
    def add_heading_ids(html):
        def replace_heading(match):
            tag = match.group(1)
            heading_content = match.group(2)
            anchor_id = slugify_heading(heading_content, '-')
            return f'<{tag} id="{anchor_id}">{heading_content}</{tag}>'
        
        # h1からh6タグにIDを追加（より柔軟なパターン）
        pattern = r'<(h[1-6])[^>]*>([^<]+)</h[1-6]>'
        result = re.sub(pattern, replace_heading, html)
        return result
    
    html_content = add_heading_ids(html_content)
    
    template = f"""
    <!DOCTYPE html>
    <html lang="ja" class="">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>All Documents</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
        {MARKDOWN_STYLE}
        {HEAD_SCRIPT}
    </head>
    <body class="bg-slate-50 text-slate-800 dark:bg-slate-900 dark:text-slate-200">
        <div class="max-w-6xl mx-auto p-4 sm:p-8">
            <header class="mb-8 no-print">
                <div class="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-6">
                    <div class="flex-1">
                        <h1 class="text-4xl font-bold text-slate-900 dark:text-white animate-fade-in-up mb-4">📚 All Documents</h1>
                        <div class="reading-stats">
                            <div class="reading-stat">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                                <span>推定読書時間: {total_reading_time}分</span>
                            </div>
                            <div class="reading-stat">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>
                                <span>文字数: {total_chars:,}文字</span>
                            </div>
                            <div class="reading-stat">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>
                                <span>ファイル数: {len(files)}個</span>
                            </div>
                        </div>
                        <p class="text-slate-600 dark:text-slate-400 mt-4 flex flex-wrap items-center gap-4">
                            <a href="/view/0" class="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/70 transition-colors font-medium">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                                </svg>
                                個別表示で読む
                            </a>
                            <button onclick="window.print()" class="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors font-medium">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path>
                                </svg>
                                印刷する
                            </button>
                        </p>
                    </div>
                    
                    <div class="flex flex-col sm:flex-row gap-3">
                        <input id="content-search" type="text" placeholder="コンテンツを検索..." 
                               class="px-4 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:ring-2 focus:ring-sky-500 focus:outline-none shadow-sm min-w-[240px]">
                        <button id="theme-toggle" class="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                            <svg class="w-6 h-6 hidden dark:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>
                            </svg>
                            <svg class="w-6 h-6 dark:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            </header>
            <main class="bg-white dark:bg-slate-800 p-6 sm:p-8 rounded-lg shadow-sm max-w-4xl mx-auto">
                <div class="markdown-content animate-fade-in-up">{html_content}</div>
            </main>
        </div>
        {BODY_SCRIPT}
    </body>
    </html>
    """
    return render_template_string(template)

@app.route('/view/<int:current_index>')
def show_one(current_index):
    """指定されたインデックスのファイルを個別に表示するページ"""
    files = get_md_files_structure()
    if not 0 <= current_index < len(files): abort(404)

    current_file = files[current_index]
    content = current_file['content']
    
    # 目次を生成
    headings = extract_headings(content)
    toc_html = ""
    if headings:
        toc_html = "<div class='toc'><h4 class='font-semibold mb-3 text-slate-700 dark:text-slate-300'>📖 目次</h4><ul>"
        current_level = 0
        for heading in headings:
            if heading['level'] > current_level:
                toc_html += "<ul>" * (heading['level'] - current_level - 1)
            elif heading['level'] < current_level:
                toc_html += "</ul>" * (current_level - heading['level'])
            
            toc_html += f"<li><a href='#{heading['anchor']}'>{heading['title']}</a></li>"
            current_level = heading['level']
        
        toc_html += "</ul>" * current_level + "</div>"

    # Markdownをヘッダーにアンカーを追加してHTMLに変換
    html_content = markdown.markdown(content, extensions=[
        'fenced_code', 
        TocExtension(anchorlink=False, slugify=slugify_heading)
    ])
    
    # 見出しに手動でアンカーIDを追加
    import re
    def add_heading_ids(html):
        def replace_heading(match):
            tag = match.group(1)
            heading_content = match.group(2)
            anchor_id = slugify_heading(heading_content, '-')
            return f'<{tag} id="{anchor_id}">{heading_content}</{tag}>'
        
        # h1からh6タグにIDを追加（より柔軟なパターン）
        pattern = r'<(h[1-6])[^>]*>([^<]+)</h[1-6]>'
        result = re.sub(pattern, replace_heading, html)
        return result
    
    html_content = add_heading_ids(html_content)
    
    # プログレス表示のためのファイル統計
    total_files = len(files)
    progress_percent = ((current_index + 1) / total_files) * 100
    
    sidebar_html = ""
    for file_info in files:
        is_current = file_info['index'] == current_index
        bg_class = "bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300" if is_current else "hover:bg-slate-100 dark:hover:bg-slate-700"
        link_class = "font-semibold" if is_current else "text-slate-700 dark:text-slate-300"
        indent_style = f"margin-left: {file_info['depth'] * 1.25}rem;"

        # ブックマークアイコンの表示
        bookmark_icon = '<svg class="w-3 h-3 text-amber-500" fill="currentColor" viewBox="0 0 20 20"><path d="M3 4a2 2 0 012-2h10a2 2 0 012 2v12l-5-3-5 3V4z"></path></svg>' if is_current else ''

        sidebar_html += f"""
        <a href="/view/{file_info['index']}" class="flex items-center p-2 rounded-md {bg_class} transition-colors duration-150" style="{indent_style}">
            <span class="text-slate-400 dark:text-slate-500 w-8 text-center mr-1 font-mono flex-shrink-0">{file_info['index'] + 1}</span>
            <span class="{link_class} flex-1">{file_info['clean_name']}</span>
            <div class="flex items-center gap-1 text-xs text-slate-400">
                <span>{file_info['estimated_reading_time']}分</span>
                {bookmark_icon}
            </div>
        </a>
        """
    
    prev_link = f'<a href="/view/{current_index - 1}" class="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors font-medium">← 前へ</a>' if current_index > 0 else '<div class="w-20"></div>'
    next_link = f'<a href="/view/{current_index + 1}" class="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors font-medium">次へ →</a>' if current_index < len(files) - 1 else '<div class="w-20"></div>'

    template = f"""
    <!DOCTYPE html>
    <html lang="ja" class="">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{current_file['clean_name']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
        {MARKDOWN_STYLE}
        {HEAD_SCRIPT}
    </head>
    <body class="bg-slate-50 text-slate-800 dark:bg-slate-900 dark:text-slate-200">
        <div class="flex min-h-screen">
            <aside id="sidebar" class="sidebar-fixed w-80 h-screen bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 p-4 flex flex-col transform -translate-x-full lg:translate-x-0 transition-transform duration-300 ease-in-out">
                <div class="mb-4 flex-shrink-0">
                    <h2 class="text-lg font-bold mb-2 px-2 text-slate-900 dark:text-white">📚 Documents</h2>
                    <div class="text-sm text-slate-500 dark:text-slate-400 px-2 mb-2">
                        進捗: {current_index + 1}/{total_files} ({progress_percent:.1f}%)
                    </div>
                    <div class="bg-slate-200 dark:bg-slate-600 rounded-full h-2 mb-3">
                        <div class="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full transition-all duration-500" style="width: {progress_percent}%"></div>
                    </div>
                </div>
                
                <div class="p-2 mb-2 flex-shrink-0">
                    <input id="search-docs" type="text" placeholder="ファイルを検索..." 
                           class="w-full px-3 py-2 text-sm rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:ring-2 focus:ring-sky-500 focus:outline-none">
                </div>
                
                <!-- スクロール可能なナビゲーション領域 -->
                <nav id="doc-list" class="space-y-1 overflow-y-auto flex-1 min-h-0">{sidebar_html}</nav>
                
                <!-- 固定ボタン領域 -->
                <div class="p-3 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/50 rounded-b-lg flex-shrink-0 mt-4">
                    <div class="space-y-3">
                        <a href="/" class="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-600 rounded-lg transition-colors group">
                            <svg class="w-4 h-4 text-slate-400 group-hover:text-blue-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                            </svg>
                            <span>全体表示で読む</span>
                        </a>
                        <button onclick="window.print()" class="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-600 rounded-lg transition-colors group">
                            <svg class="w-4 h-4 text-slate-400 group-hover:text-green-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path>
                            </svg>
                            <span>このページを印刷</span>
                        </button>
                    </div>
                </div>
            </aside>

            <main class="flex-1 lg:ml-0">
                <div class="p-4 sm:p-6 lg:p-8">
                    <div class="max-w-4xl mx-auto">
                        <header class="flex justify-between items-center mb-6 no-print">
                            <button id="mobile-menu-button" class="lg:hidden p-2 rounded-md text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
                            </button>
                            
                            <div class="flex-1 mx-4">
                                <input id="content-search" type="text" placeholder="このページ内を検索..." 
                                       class="w-full max-w-md px-3 py-2 text-sm rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:ring-2 focus:ring-sky-500 focus:outline-none">
                            </div>
                            
                            <div class="flex gap-2">
                                <button id="bookmark-toggle" class="p-2 rounded-md text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
                                    </svg>
                                </button>
                                <button id="theme-toggle" class="p-2 rounded-md text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                                    <svg class="w-6 h-6 hidden dark:block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                                    <svg class="w-6 h-6 dark:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path></svg>
                                </button>
                            </div>
                        </header>
                        
                        <article class="bg-white dark:bg-slate-800 rounded-lg shadow-sm animate-fade-in-up">
                            <div class="p-6 sm:p-8">
                                <h1 class="text-4xl font-bold text-slate-900 dark:text-white flex items-center">
                                   <span class="text-3xl text-slate-400 dark:text-slate-500 mr-4">{current_file['index'] + 1}.</span>
                                   <span>{current_file['clean_name']}</span>
                                </h1>
                                <div class="reading-stats">
                                    <div class="reading-stat">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        <span>約{current_file['estimated_reading_time']}分</span>
                                    </div>
                                    <div class="reading-stat">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                        </svg>
                                        <span>{current_file['char_count']:,}文字</span>
                                    </div>
                                    <div class="reading-stat">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                                        </svg>
                                        <span>{current_file['path']}</span>
                                    </div>
                                </div>
                            </div>
                            
                            {toc_html}
                            
                            <div class="markdown-content p-6 sm:p-8 pt-0">{html_content}</div>
                            
                            <footer class="flex justify-between items-center p-6 text-slate-700 dark:text-slate-300 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/50 no-print">
                                {prev_link}
                                <div class="text-sm font-medium bg-slate-200 dark:bg-slate-600 px-3 py-1 rounded-full">
                                    {current_index + 1} / {total_files}
                                </div>
                                {next_link}
                            </footer>
                        </article>
                    </div>
                </div>
            </main>
        </div>
        {BODY_SCRIPT}
    </body>
    </html>
    """
    return render_template_string(template)

if __name__ == '__main__':
    print("Starting Markdown viewer server...")
    print(" * Combined view: http://127.0.0.1:5000/")
    print(" * Individual view: http://127.0.0.1:5000/view/0")
    print("Press CTRL+C to quit")
    app.run(host='0.0.0.0', port=5000)
