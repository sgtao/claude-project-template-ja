# claude-project-template-ja

Claude Code で、長い制作・知的作業・専門作業を最後までやり切るためのテンプレートリポジトリ。
Opus や Sonnet でも結果が安定するように、計画・記憶・検査をファイルとスクリプトに出してある。

- **制作**（アプリ、ゲーム、映像、音楽、絵、ツール）は `SPEC.md` を使う
- **知的作業**（調査、分析、レビュー、執筆、意思決定）は `BRIEF.md` と証拠台帳 `LEDGER.csv` を使う
- **専門作業**（繰り返す作業を、手順書・チェックリスト・スキル・スクリプトにする）は `PLAYBOOK.md` と評価ケース表 `05_evals/cases.csv` を使う
- 始め方は 4 つ：**新規**、進行中のプロジェクトへの**後付け**、別の技術や版への**移行**、他のリポジトリを**複製して改造**
- 会話は毎ターン `02_conversations/` に記録し、振り返ってルールに戻す。版を重ねるときは `04_logs/` に版ごとに締める

型の選び方と、始め方ごとの手順は [docs/usecases.md](docs/usecases.md) にある。

## 始め方（5 分）

```bash
# 1. このテンプレートを新しいフォルダに写して、git を初期化する
cp -r claude-project-template-ja my-project && cd my-project
git init && git add -A && git commit -m "init from template"

# 2. ヒアリングに答える（どちらか）
python3 _tools/setup.py          # 端末で答える
#   または Claude Code を開いて  /setup-project  と入力する（選択式で聞かれる）

# 3. 点検する（「合格条件の点検」だけ NG なのは、この時点では正常）
python3 _tools/doctor.py

# 4. Claude Code を開き、KICKOFF.md の枠の中を最初のメッセージとして渡す
```

進行中の既存プロジェクトに入れるときは、手順 1 の代わりに、テンプレートの親フォルダで次を実行する
（既存のファイルは上書きしない。詳しくは [docs/usecases.md](docs/usecases.md) の「後付けの始め方」）。

```bash
python3 claude-project-template-ja/_tools/adopt.py --target my-app            # 試し
python3 claude-project-template-ja/_tools/adopt.py --target my-app --apply --link
```

ヒアリングの答えは `_examples/answers/current.json` に残る（やり直しや `--answers` での再実行に使う）。
個人情報や秘密を答えに書いたときは、コミットの前に消すか `.gitignore` に入れる。

テンプレートの直下には、仕様や記憶のファイルはまだない。ひな形は `_templates/` にあり、
ヒアリングの後で、選んだ型に必要なものだけが直下に作られる。

| 対象 | セットアップで直下に作られるファイル |
|---|---|
| 制作 | `SPEC.md`、`PROGRESS.md`、`DECISIONS.md`、`KICKOFF.md` |
| 知的作業 | `BRIEF.md`、`LEDGER.csv`、`PROGRESS.md`、`DECISIONS.md`、`KICKOFF.md` |
| 専門作業 | `PLAYBOOK.md`、`05_evals/cases.csv`、`PROGRESS.md`、`DECISIONS.md`、`KICKOFF.md` |

始め方（後付け・移行・複製して改造）を選ぶと、仕様のファイルに「今の状態」「移行元と移行先」「複製元」の節と、
それに合う最初のマイルストーンが入る。

その後の流れは次のとおり。人が確かめるのは ★ の 3 点。

| 段階 | やること | 使うもの |
|---|---|---|
| 1. 仕様 | 仕様のファイルの [要記入] を埋める → ★確認 | `KICKOFF.md` |
| 2. 最小版 | 粗くても最後まで通す（知的作業は対象 1 件、専門作業は実例 1 件）→ ★確認 | `/milestone` |
| 3. 反復 | マイルストーンを 1 つずつ。検査 → 計画と差分の突き合わせ → 記録 → コミット | `/milestone` |
| 4. 検証 | 機械検査、実物の通し、独立した審査、仕込み検査 | `/verify` |
| 5. 出力 | ★承認の後、最終の出力 | |
| 区切り | セッションを終える・別セッションに渡す | `/handoff` |
| 次の版 | 版の記録を `04_logs/` に締め、次の版の計画（`PLAN.md`）を作る | `/next-cycle` |
| 随時 | 履歴からルールを見直す | `/retro` |

## ファイルの地図

最初から入っているもの：

| ファイル | 役割 |
|---|---|
| `CLAUDE.md` | Claude の既定ルール（進め方、承認、始め方ごとの注意、検査、モデルの使い分け） |
| `HISTORY.md` | 会話の記録・参照・改善のルール（CLAUDE.md から読み込まれる） |
| `_templates/` | セットアップで作られるファイルと、途中で作る文書のひな形 → [説明](_templates/README.md) |
| `01_sources/` | 資料、素材、過去の実例、複製元を置く |
| `02_conversations/` | 会話の記録 |
| `03_outputs/` | 成果物を置く（別の git リポジトリにしてもよい → [docs/usecases.md](docs/usecases.md)） |
| `05_evals/` | 評価の実行記録（実物の入力を通した入出力）と、評価ケース表 |
| `04_logs/` | 締めた版の記録（仕様の写し、計画、引き継ぎ、会話、評価） |
| `06_handoff/` | 引き継ぎメモ（セッションの区切りごと） |
| `_tools/` | 検査・記録・セットアップのスクリプト（Python の標準ライブラリだけで動く）→ [一覧](_tools/README.md) |
| `_examples/` | ヒアリングの質問、答えとプロンプトの見本、検査の見本 → [説明](_examples/README.md) |
| `.claude/skills/` | スキル：`setup-project`、`milestone`、`verify`、`handoff`、`next-cycle`、`retro` |
| `.claude/agents/` | サブエージェント：`reviewer`（Opus、審査）、`implementer`（Sonnet、実装） |
| `.claude/settings.json` | 権限の初期設定 |
| `.mcp.json.example` | MCP の設定例（有効化は手動）→ [手順](docs/setup-mcp-and-skills.md) |

セットアップや作業の途中で作られるもの（ひな形は `_templates/_<ファイル名>`）：

| ファイル | 役割 | いつ |
|---|---|---|
| `SPEC.md`／`BRIEF.md`／`PLAYBOOK.md` | 仕様と合格条件の正本（対象ごとに 1 つ） | セットアップ |
| `LEDGER.csv` | 証拠台帳（資料から拾った事実と出所） | セットアップ（知的作業） |
| `05_evals/cases.csv` | 評価ケース表（正例・境界・負例） | セットアップ（専門作業） |
| `PROGRESS.md` | 現在地、チェックリスト、次の一手。セッションをまたぐ記憶 | セットアップ |
| `DECISIONS.md` | 決めたことと、失敗から決めたルールの台帳 | セットアップ |
| `KICKOFF.md` | 最初のプロンプト（対象と始め方で中身が違う） | セットアップ |
| `06_handoff/` | 引き継ぎメモ（日付と連番のファイル） | `/handoff` |
| `MANUAL-CHECK.md` | 対話でしか確かめられない動作を、人が確かめる手順 | `/verify` |
| `PLAN.md` | 次の版の改修計画（承認の後、仕様のファイルに反映する） | `/next-cycle` |

セットアップをやり直すときは `python3 _tools/setup.py --force`。`DECISIONS.md`・`LEDGER.csv`・`05_evals/cases.csv` は
書き足していく台帳なので、`--force` でも上書きしない。

## 考え方

1. **完成を数えられる形にする**：合格条件は 10 個以内で、スクリプトか画像で確かめられるものにする
2. **最初に最後まで通す**：粗い最小版で、出力までの道を先に確かめる
3. **記憶をファイルに出す**：1 マイルストーン 1 セッション。次は `PROGRESS.md` と最新の引き継ぎメモ（`python3 _tools/handoff.py latest`）から再開する
4. **検査を機械にする**：制作はテストと画像、知的作業は証拠台帳、専門作業は評価ケース。通るまで次へ進まない
5. **検査そのものを疑う**：新しい検査は、わざと壊した入力で落ちることを確かめる。完成の前に、実物の入力を実際の手順で通す
6. **別の目で見る**：制作の経緯を知らない審査役に見せ、仕込み検査で審査そのものを確かめる
7. **履歴をルールに戻す**：同じ指摘が 2 回出たら、検査かルールにする。版の区切りで `04_logs/` に締めて読み返す

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
プロジェクトで `/retro` や `/next-cycle` から生まれたルールや検査のうち、ほかのプロジェクトでも使えるものは、
このテンプレートに戻す。質問を足すときは `_examples/hearing/questions.json` と
`_templates/` のひな形に、同じ名前の `{{KEY}}` を置く。ひな形を直したら、直下の `SPEC.md` などではなく
`_templates/` のほうを直す（直下のファイルは、テンプレートには入れない）。

直したら、テンプレートの自己検査を通す（12 通りのセットアップ、検査の正例と負例、サイクル、後付けを一時フォルダで試す）。

```bash
python3 _tools/selftest.py
```


---

🤖 Built with [Claude.ai](https://claude.ai/)
