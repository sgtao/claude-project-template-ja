# claude-project-template

Claude Code で、長い制作や知的作業を最後までやり切るためのテンプレートリポジトリ。
Opus や Sonnet でも結果が安定するように、計画・記憶・検査をファイルとスクリプトに出してある。

- **制作**（アプリ、ゲーム、映像、音楽、絵）は `SPEC.md` を使う
- **知的作業**（調査、分析、レビュー、執筆、意思決定）は `BRIEF.md` と証拠台帳 `LEDGER.csv` を使う
- 会話は毎ターン `02_conversations/` に記録し、振り返ってルールに戻す

## 始め方（5 分）

```bash
# 1. このテンプレートを新しいフォルダに写して、git を初期化する
cp -r claude-project-template my-project && cd my-project
git init && git add -A && git commit -m "init from template"

# 2. ヒアリングに答える（どちらか）
python3 _tools/setup.py          # 端末で答える
#   または Claude Code を開いて  /setup-project  と入力する（選択式で聞かれる）

# 3. 点検する（「合格条件の点検」だけ NG なのは、この時点では正常）
python3 _tools/doctor.py

# 4. Claude Code を開き、KICKOFF.md の枠の中を最初のメッセージとして渡す
```

その後の流れは次のとおり。人が確かめるのは ★ の 3 点。

| 段階 | やること | 使うもの |
|---|---|---|
| 1. 仕様 | SPEC.md／BRIEF.md の [要記入] を埋める → ★確認 | `KICKOFF.md` |
| 2. 最小版 | 粗くても最後まで通す（知的作業は対象 1 件を仕上げる）→ ★確認 | `/milestone` |
| 3. 反復 | マイルストーンを 1 つずつ。検査 → 記録 → コミット | `/milestone` |
| 4. 検証 | 機械検査、独立した審査、仕込み検査 | `/verify` |
| 5. 出力 | ★承認の後、最終の出力 | |
| 随時 | 履歴からルールを見直す | `/retro` |

## ファイルの地図

| ファイル | 役割 |
|---|---|
| `CLAUDE.md` | Claude の既定ルール（進め方、承認、検査、モデルの使い分け） |
| `HISTORY.md` | 会話の記録・参照・改善のルール（CLAUDE.md から読み込まれる） |
| `SPEC.md` | 制作の仕様と合格条件。セットアップで記入される |
| `BRIEF.md` | 知的作業の依頼書と合格条件。セットアップで記入される |
| `PROGRESS.md` | 現在地、チェックリスト、次の一手。セッションをまたぐ記憶 |
| `DECISIONS.md` | 決めたことと、失敗から決めたルールの台帳 |
| `LEDGER.csv` | 証拠台帳（知的作業で、資料から拾った事実と出所） |
| `KICKOFF.md` | 最初のプロンプト。セットアップで作られる |
| `01_sources/` | 資料や素材を置く |
| `02_conversations/` | 会話の記録 |
| `03_outputs/` | 成果物を置く |
| `_tools/` | 検査と記録のスクリプト（Python の標準ライブラリだけで動く）→ [一覧](_tools/README.md) |
| `_examples/` | ヒアリングの質問、ひな形、プロンプト例、検査の見本 → [説明](_examples/README.md) |
| `.claude/skills/` | スキル：`setup-project`、`milestone`、`verify`、`retro` |
| `.claude/agents/` | サブエージェント：`reviewer`（Opus、審査）、`implementer`（Sonnet、実装） |
| `.claude/settings.json` | 権限の初期設定 |
| `.mcp.json.example` | MCP の設定例（有効化は手動）→ [手順](docs/setup-mcp-and-skills.md) |

`SPEC.md` と `BRIEF.md` のうち、使わないほうは消してよい。

## 考え方

1. **完成を数えられる形にする**：合格条件は 10 個以内で、スクリプトか画像で確かめられるものにする
2. **最初に最後まで通す**：粗い最小版で、出力までの道を先に確かめる
3. **記憶をファイルに出す**：1 マイルストーン 1 セッション。次は `PROGRESS.md` から再開する
4. **検査を機械にする**：制作はテストと画像、知的作業は証拠台帳。通るまで次へ進まない
5. **別の目で見る**：制作の経緯を知らない審査役に見せ、仕込み検査で審査そのものを確かめる
6. **履歴をルールに戻す**：同じ指摘が 2 回出たら、検査かルールにする

## モデルの使い分け（目安）

| 工程 | モデル |
|---|---|
| 仕様づくり、統合、判断、審査、立て直し | Opus |
| 範囲の決まった実装、抽出、執筆、検査の実行 | Sonnet |

effort は、Opus は medium、Sonnet は high から始め、検査で落ちる工程だけ上げる。
この割り当ては出発点で、自分の課題で確かめて調整する。

## 必要なもの
- Claude Code
- Python 3.9 以上（追加のパッケージは不要）
- git
- MCP を使う場合だけ Node.js（`npx`）

## テンプレートを育てる
プロジェクトで `/retro` から生まれたルールや検査のうち、ほかのプロジェクトでも使えるものは、
このテンプレートに戻す。質問を足すときは `_examples/hearing/questions.json` と
`_examples/templates/` のひな形に、同じ名前の `{{KEY}}` を置く。
