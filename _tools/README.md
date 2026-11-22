# _tools/

検査と記録のスクリプト。すべて Python の標準ライブラリだけで動く。リポジトリのトップから実行する。

| スクリプト | 用途 | いつ使うか |
|---|---|---|
| `setup.py` | ヒアリングの答えを `_templates/` のひな形に入れ、仕様のファイル（SPEC.md／BRIEF.md／PLAYBOOK.md）、KICKOFF.md、PROGRESS.md、DECISIONS.md（知的作業は LEDGER.csv、専門作業は 05_evals/cases.csv も）を作る | 最初に 1 回 |
| `adopt.py` | 既存のプロジェクトに、テンプレートの仕組みだけを入れる（既存のファイルは上書きしない。既定は試し） | 後付けの最初に 1 回（テンプレートの側から実行） |
| `doctor.py` | 必要なファイル（ひな形を含む）、設定の形式、セットアップの状態を点検する | セットアップの後、再開のとき |
| `check_spec.py` | 合格条件の点検（未記入、個数、数値か確かめ方の有無、数えられない言葉） | 仕様を書いた後 |
| `check_ledger.py` | 証拠台帳と成果物の検査（引用の一致、ID の参照、網羅、断定の疑い） | 知的作業の成果物を書くたび |
| `check_cases.py` | 評価ケース表の検査（未実行・不合格・負例なし・証拠のパスの欠け） | 専門作業のマイルストーンごと（途中は `--allow-pending`） |
| `check_skill.py` | スキルの形の検査（frontmatter、name、description、参照の切れ、未記入） | スキルを作ったとき、直したとき |
| `seed_errors.py` | 仕込み検査（写しに誤りを入れ、審査が見つけた数を数える） | 最終の出力の前 |
| `conv.py` | 会話の記録の作成・追記・一覧・検索・表示（`04_logs/` に締めた記録も検索する） | 毎ターン（記録）、過去を参照するとき |
| `handoff.py` | 引き継ぎメモを `06_handoff/<MMDD-NN>_<話題>.md` に作る（`new`）・最新のメモを探す（`latest`） | セッションの区切り（`/handoff`） |
| `gitignore.py` | 成果物のフォルダ（`03_outputs/` の中）に最初の `.gitignore` を作る。複製元の `.gitignore` を優先、制作は github/gitignore の言語別 + 補完、それ以外はテンプレートのもの | セットアップ（自動）、成果物のフォルダを新しく作るとき |
| `cycle.py` | 版を締めて記録を `04_logs/<名前>/` に移し（既定は試し）、次の版の `PLAN.md` を作る | 版の区切り（`/next-cycle`） |
| `selftest.py` | テンプレートそのものの自己検査（12 通りのセットアップ、検査の正例・負例、サイクル、後付け、成果物の .gitignore） | テンプレートを直したとき |

## 例

```bash
python3 _tools/setup.py --answers _examples/answers/browser-game.json --out /tmp/try   # 試し書き
python3 _tools/check_spec.py SPEC.md
python3 _tools/check_ledger.py --doc 03_outputs/report.md --units 01_sources/units.txt
python3 _tools/seed_errors.py seed --in 03_outputs/report.md --out /tmp/seeded.md --key /tmp/key.json
python3 _tools/seed_errors.py score --key /tmp/key.json --report /tmp/review.md
python3 _tools/conv.py find 合格条件
python3 _tools/check_cases.py --allow-pending
python3 _tools/check_skill.py .claude/skills/*
python3 _tools/cycle.py close v0-0-1          # 試し。--apply で実行
python3 _tools/adopt.py --target ../my-app    # 試し。--apply で実行
python3 _tools/selftest.py
```

検査の見本は `_examples/ledger-sample/`（証拠台帳）と `_examples/craft-sample/`（評価ケースとスキル）にある。次で動きを確かめられる。

```bash
python3 _tools/check_ledger.py --ledger _examples/ledger-sample/LEDGER.csv \
  --doc _examples/ledger-sample/report.md --sources _examples/ledger-sample/sources \
  --units _examples/ledger-sample/units.txt
python3 _tools/check_cases.py _examples/craft-sample/cases.csv
python3 _tools/check_skill.py _examples/craft-sample/invoice-check
```

## 終了コード
どの検査も、不合格があれば 1、なければ 0 を返す。警告だけなら 0。

## 検査を足すとき
- 1 つのスクリプトは 1 つのことを確かめる。結果は「不合格」「警告」に分けて日本語で出す
- 追加のパッケージが要る検査は、このフォルダではなくプロジェクトのテストに置く
- 足したら、この表と、該当するスキル（`.claude/skills/verify/SKILL.md`）に 1 行足す
- 足した検査が、正例で合格し、負例（わざと壊した入力）で不合格になることを `selftest.py` に足す

## 限界
- `check_ledger.py` の引用の一致は、テキストの資料だけ。PDF や Word は、先にテキストにする
- `check_ledger.py` の「断定の疑い」「ID のない数値」は目安。警告として 1 件ずつ見る
- `seed_errors.py` が自動で入れるのは、数値の書き換えだけ。論理の誤りは手で足す
