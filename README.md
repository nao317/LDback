# リビングデザイン PoC バックエンド

見積もり支援PoCのバックエンドAPIです。FastAPIでAPIを提供し、将来的に
PostgreSQL + pgvectorを利用したRAG検索と見積もりロジックを実装します。

現在は、文書登録と文字列の部分一致検索をメモリ上で行う最小構成です。
PostgreSQLへの保存、Embedding生成、ベクトル検索はまだ接続していません。

## 必要な環境

- Python 3.10以上
- Docker
- Docker Compose v2（`docker compose` コマンド）
- curl

## ディレクトリ構成

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── api/
│       ├── __init__.py
│       └── rag.py
├── docker-compose.yml
├── pyrightconfig.json
├── requirements-dev.txt
├── requirements.txt
├── tests/
│   ├── test_health.py
│   └── test_rag.py
└── README.md
```

## 環境構築

`backend` ディレクトリで仮想環境を作成し、依存パッケージをインストールします。

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

仮想環境を有効化して作業する場合は、次を実行します。

```bash
source .venv/bin/activate
```

有効化後は、利用中のPythonを確認できます。

```bash
which python
python -c "import fastapi; print(fastapi.__version__)"
```

`which python` が `backend/.venv/bin/python` を指していれば正常です。

## ビルド相当の確認

現在はPythonパッケージやDockerイメージとして配布する構成ではないため、
専用のビルドコマンドはありません。依存関係とPythonコードを次のコマンドで確認します。

```bash
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q app
.venv/bin/python -c "from app.main import app; print(app.title)"
```

期待される出力は次のとおりです。

```text
Living Design PoC Backend
```

## FastAPIの起動

開発時は、自動リロードを有効にして起動します。

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

外部ホストから接続する必要がある場合は、ホストを明示します。

```bash
.venv/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000
```

起動後は次のURLを利用できます。

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## API

| Method | Path | 用途 |
| --- | --- | --- |
| GET | `/health` | APIの稼働確認 |
| POST | `/rag/documents` | 検索対象の文書をメモリへ登録 |
| POST | `/rag/query` | 登録済み文書を文字列の部分一致で検索 |

登録した文書はプロセスのメモリにだけ保存されます。サーバーを再起動すると消えます。

## curlによる動作確認

FastAPIを起動した状態で、別のターミナルから実行します。

### 1. ヘルスチェック

```bash
curl --fail --silent --show-error \
  http://127.0.0.1:8000/health
```

期待結果:

```json
{"status":"ok"}
```

### 2. 文書登録

```bash
curl --fail --silent --show-error \
  -X POST http://127.0.0.1:8000/rag/documents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "キッチン改修",
    "content": "キッチン交換と内装工事を実施しました"
  }'
```

期待結果:

```json
{
  "title": "キッチン改修",
  "content": "キッチン交換と内装工事を実施しました",
  "id": 1
}
```

### 3. 文書検索

文書登録と同じサーバープロセスに対して実行します。

```bash
curl --fail --silent --show-error \
  -X POST http://127.0.0.1:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query":"キッチン"}'
```

期待結果:

```json
{
  "query": "キッチン",
  "results": [
    {
      "title": "キッチン改修",
      "content": "キッチン交換と内装工事を実施しました",
      "id": 1
    }
  ],
  "answer": "キッチン交換と内装工事を実施しました"
}
```

### 4. 該当なしの検索

```bash
curl --fail --silent --show-error \
  -X POST http://127.0.0.1:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query":"浴室"}'
```

`results` が空配列になり、`answer` に該当情報がないことが返れば正常です。

## 自動テスト

開発用依存関係をインストールして、pytestとRuffを実行します。

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
```

現在は、ヘルスチェック、文書登録、検索一致、検索不一致をテストしています。

## PostgreSQL + pgvector

`docker-compose.yml` には、PostgreSQL 17とpgvectorを含むDBサービスを定義しています。
現在のFastAPIはまだDBへ接続していないため、APIのcurl確認だけならDBの起動は不要です。

### DBコンテナの起動

```bash
docker compose up -d db
docker compose ps
```

DBの準備完了を確認します。

```bash
docker compose exec db pg_isready -U postgres -d app
```

### ログの確認

```bash
docker compose logs -f db
```

ログ表示は `Ctrl+C` で終了できます。DBコンテナ自体は停止しません。

### PostgreSQLへの接続

```bash
docker compose exec db psql -U postgres -d app
```

psqlを終了する場合は `\q` を入力します。

### pgvector拡張の有効化

イメージにpgvectorは含まれていますが、利用するデータベースで拡張を有効化する必要があります。

```bash
docker compose exec db \
  psql -U postgres -d app \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

確認:

```bash
docker compose exec db \
  psql -U postgres -d app \
  -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

### DBコンテナの停止と再開

コンテナを残したまま停止します。

```bash
docker compose stop db
```

再開:

```bash
docker compose start db
```

### DBコンテナの削除

```bash
docker compose down
```

ボリュームも削除してDBデータを初期化する場合だけ、次を実行します。

```bash
docker compose down --volumes
```

`--volumes` を付けるとDBデータを復元できなくなるため注意してください。現在のCompose設定には
明示的な名前付きボリュームがないため、永続化が必要になる段階で追加します。

## トラブルシューティング

### `ModuleNotFoundError: No module named 'fastapi'`

実行に利用しているPythonと、FastAPIをインストールしたPythonが異なっています。
このリポジトリでは `.venv` のPythonを明示して実行してください。

```bash
.venv/bin/python -c "import fastapi; print(fastapi.__version__)"
.venv/bin/python -m uvicorn app.main:app --reload
```

### `Address already in use`

ポート8000が使用中です。別ポートで起動できます。

```bash
.venv/bin/python -m uvicorn app.main:app --reload --port 8001
```

### PostgreSQLのポートが使用中

ホスト側の5432番ポートが別のPostgreSQLで使用されています。使用状況を確認するか、
`docker-compose.yml` のポート割り当てを変更してください。

```yaml
ports:
  - "5433:5432"
```

## 現在の制約と次の実装候補

- 文書はメモリ保存のため、再起動すると消える
- 検索は文字列の部分一致で、意味検索ではない
- PostgreSQLとFastAPIは未接続
- pgvector用テーブルとマイグレーションは未作成
- Embedding生成とLLMによる回答生成は未実装
- DB接続とHTTPレベルの自動テストは未作成

次の段階では、文書とチャンクをPostgreSQLへ保存し、pgvectorによる類似度検索へ
置き換えます。
