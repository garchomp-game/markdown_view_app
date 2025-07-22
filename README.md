# 📖 Markdown Reader

プロフェッショナルなMarkdownドキュメントビューアー。個別表示と一枚綴り表示の両方に対応し、ダークテーマ、検索機能、リアルタイムナビゲーションを提供します。

## ✨ 特徴

### � 柔軟な表示モード
- **📄 個別表示**: ファイルごとに集中して読める（`/file/<filename>`）
- **📜 一枚綴り表示**: 全ドキュメントを連続で読める（`/all`）
- **🏠 ホーム表示**: ファイル一覧とキーボードショートカット（`/`）

### 🎨 モダンなUI/UX
- **🌗 ダークテーマ対応**: 目に優しい表示切り替え
- **📱 レスポンシブデザイン**: モバイル・デスクトップ両対応
- **🔄 リアルタイムテーマ切り替え**: CSS変数による高速切り替え
- **📊 プログレスバー**: 読書進捗の視覚化

### � パフォーマンスと機能
- **🔍 高速検索**: ファイル名とコンテンツ内リアルタイム検索
- **⌨️ キーボードショートカット**: 効率的なナビゲーション
- **🖨️ 印刷最適化**: きれいに印刷できるスタイル
- **📈 統計情報**: 推定読書時間・文字数・ファイルサイズ表示

### 💻 技術的特徴
- **🔄 動的SCSSコンパイル**: リアルタイムスタイル更新
- **⚡ Flask動的ルーティング**: 柔軟なファイルパス対応
- **🎯 モジュラー設計**: 保守しやすいコード構造

## 🛠️ 技術スタック

- **バックエンド**: Flask 3.0.0 (Python)
- **スタイリング**: SCSS + CSS Variables
- **JavaScript**: Vanilla ES6+ (モジュラー設計)
- **Markdown処理**: Python-Markdown 3.5.1 + 豊富な拡張
- **コンパイル**: libsass 0.22.0 + Node.js sass

## 🚀 インストール・起動

### 📋 必要な環境
- Python 3.8+
- Node.js 16+ (SCSS コンパイル用)
- pip

### 🔧 セットアップ

**1. リポジトリのクローン**
```bash
git clone <repository-url>
cd markdown-reader
```

**2. Python仮想環境の作成と有効化**
```bash
# 仮想環境を作成
python3 -m venv .venv

# 仮想環境を有効化
# Linux/macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

**3. 依存関係のインストール**
```bash
# Python パッケージをインストール
pip install -r requirements.txt

# Node.js パッケージをインストール（SCSS コンパイル用）
npm install
```

**4. SCSS コンパイル**
```bash
# 初回ビルド
npm run build-css

# 開発時（ファイル監視）
npm run watch-css
```

**5. アプリケーション起動**
```bash
python app.py
```

### 🌐 アクセス方法
- **ホーム**: http://localhost:5000/
- **個別ファイル**: http://localhost:5000/file/docs/1_hoge.md
- **一枚綴り**: http://localhost:5000/all
- **API ファイル一覧**: http://localhost:5000/api/files
- **API 検索**: http://localhost:5000/api/search?q=keyword

## 📁 プロジェクト構造

```
markdown-reader/
├── 📄 app.py                    # メインFlaskアプリケーション
├── 📄 requirements.txt          # Python依存関係
├── 📄 package.json             # Node.js依存関係
├── 📄 .gitignore               # Git除外設定
├── 📁 docs/                    # Markdownファイル置き場
│   ├── 📄 1_hoge.md           #   番号付きファイル
│   ├── 📁 2_myFolder/         #   サブフォルダ対応
│   │   ├── 📄 1_huga.md
│   │   ├── 📄 2_hogera.md
│   │   └── 📄 ...
│   └── 📄 3_hogerahogera.md
├── 📁 static/                  # 静的ファイル
│   ├── 📁 css/                #   コンパイル済みCSS
│   ├── 📁 js/                 #   JavaScript モジュール
│   └── 📁 scss/               #   SCSS ソースファイル
├── 📁 templates/               # Jinja2 テンプレート
│   └── 📄 index.html          #   メインテンプレート
└── 📁 .venv/                   # Python仮想環境
```

## 使用方法

### Markdownファイルの配置
`docs/`フォルダに番号付きのMarkdownファイルを配置してください：
- `01_introduction.md`
- `02_getting_started.md`
- `03_advanced_topics.md`
- など

### 機能説明

#### 個別表示モード
- ファイルごとに集中して読める
- 前/次のファイルにナビゲーション
- サイドバーで全ファイル一覧表示

#### 全体表示モード  
- 全ドキュメントを1ページで表示
- スクロールで連続読書
- 目次から任意のセクションにジャンプ

## ⌨️ キーボードショートカット

### 🔍 検索
- `Ctrl + K`: 検索ボックスにフォーカス
- `Escape`: 検索をクリア

### 🧭 ナビゲーション  
- `↑ / ↓`: 検索結果の移動
- `Enter`: 選択したファイルを開く
- `Tab`: UI要素間の移動

### 🎨 表示制御
- `Ctrl + D`: ダークテーマ切り替え
- `Ctrl + \`: サイドバー開閉

## 📖 使い方

### 基本的な操作

1. **ファイルの配置**
   - `docs/` フォルダにMarkdownファイルを配置
   - ファイル名は `1_example.md` のように番号付きにすると自動ソート
   - サブフォルダも対応（`docs/subfolder/1_file.md`）

2. **個別表示**
   - サイドバーからファイルをクリック
   - 目次から見出しにジャンプ可能
   - ファイル統計情報を表示

3. **一枚綴り表示**
   - トップナビゲーションから「All Docs」をクリック
   - 全ドキュメントを連続表示
   - 長文の読書に最適

4. **検索機能**
   - ファイル名やコンテンツをリアルタイム検索
   - マッチした部分をハイライト表示
   - 検索結果をキーボードで選択

### 📁 ファイル命名規則

効率的なナビゲーションのため、以下の命名規則を推奨：

```
docs/
├── 1_introduction.md        # 番号付きでソート
├── 2_getting-started.md     # ハイフン区切り
├── 3_advanced-topics.md
├── chapter1/                # サブフォルダ対応
│   ├── 1_basics.md
│   ├── 2_examples.md
│   └── 3_exercises.md
└── appendix/
    ├── 1_references.md
    └── 2_glossary.md
```

### 🎨 テーマカスタマイズ

SCSS変数を編集してテーマをカスタマイズ可能：

```scss
// static/scss/_variables.scss
$primary-color: #3b82f6;     // メインカラー
$sidebar-width: 300px;       // サイドバー幅
$font-family: 'Inter', sans-serif; // フォント
```

変更後は再コンパイルが必要：
```bash
npm run build-css
```

## 🔧 開発・カスタマイズ

### 📝 新機能の追加

1. **新しいルートの追加**
   ```python
   # app.py
   @app.route('/new-feature')
   def new_feature():
       return render_template('index.html', ...)
   ```

2. **JavaScript機能の拡張**
   ```javascript
   // static/js/new-feature.js
   export class NewFeature {
       constructor() { /* ... */ }
   }
   ```

3. **スタイルの追加**
   ```scss
   // static/scss/_components.scss
   .new-component {
       /* カスタムスタイル */
   }
   ```

### 🧪 デバッグモード

開発時はデバッグモードを有効化：

```python
# app.py の最後
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### 📦 デプロイメント

**本番環境への推奨設定:**

```python
# app.py
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

```bash
# 本番用依存関係
pip install gunicorn

# Gunicornで起動
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🤝 トラブルシューティング

### よくある問題と解決法

**❌ SCSSがコンパイルされない**
```bash
# Node.js依存関係を再インストール
npm install
npm run build-css
```

**❌ テーマが切り替わらない**
```bash
# libsassが正しくインストールされているか確認
pip install libsass
python -c "import sass; print('✓ libsass OK')"
```

**❌ ファイルが見つからない**
- `docs/` フォルダの存在を確認
- ファイルパスに日本語が含まれていないか確認
- ファイル権限を確認

**❌ ポートが使用中**
```bash
# 別のポートで起動
python app.py --port 5001
```

### 📊 ログとデバッグ

デバッグ情報の確認：
```bash
# Flask ログレベル設定
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

ブラウザの開発者ツールでJavaScriptエラーも確認してください。

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 👥 コントリビューション

プルリクエストやイシューの報告を歓迎します！

### 開発に参加するには

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

---

**📖 Happy Reading! 🚀**
