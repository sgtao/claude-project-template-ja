# 使い方の型：対象 3 つ × 始め方 4 つ

このテンプレートは、**何を作るか（対象）** と **どこから始めるか（始め方）** の 2 つで形を決める。
どちらもセットアップ（`/setup-project` か `python3 _tools/setup.py`）の質問で選ぶ。

## 対象

| 対象 | 正本のファイル | 向いている仕事 | 主な検査 |
|---|---|---|---|
| 制作（build） | `SPEC.md` | アプリ、ゲーム、映像、音楽、絵、ツール | テスト、計測、スクリーンショット |
| 知的作業（knowledge） | `BRIEF.md` ＋ `LEDGER.csv` | 調査、分析、レビュー、執筆、意思決定 | `check_ledger.py`（証拠台帳） |
| 専門作業（craft） | `PLAYBOOK.md` ＋ `05_evals/cases.csv` | 繰り返す作業の手順書・チェックリスト化、スキル・スクリプトでの自動化 | `check_cases.py`（評価ケース）、`check_skill.py` |

専門作業の進め方：
1. 過去の実例（入力・出力・作業メモ）を `01_sources/` に置く
2. 今の手順と、判断の基準（暗黙知）を書き出す
3. 手順ごとに自動化の水準を決める（手作業／チェックリスト／スクリプト／スキル。迷ったら低いほう）
4. 実例から評価ケース（正例・境界・負例）を作り、手順書やスキルがそれを通るまで直す
5. 熟練者と、初めてその作業をする人の 2 つの役割で審査する

見本：[`_examples/craft-sample/`](../_examples/craft-sample/README.md)、[例 7](../_examples/prompts/07_expense-check-skill.md)

## 始め方

| 始め方 | こんなとき | 仕様のファイルに足される節 | 最初のマイルストーン | 例 |
|---|---|---|---|---|
| 新規（new） | 何もないところから作る | なし | 粗くても最後まで通る版（専門作業は実例 1 件を通す） | 例 1〜7 |
| 後付け（adopt） | 進行中のプロジェクトを、この進め方で続ける | 今の状態（後付け） | 今の状態の把握と、基準のテストの記録 | [例 10](../_examples/prompts/10_adopt-existing-app.md) |
| 移行（migrate） | 別の技術・新しい版・新しい形へ移す | 移行元と移行先（同等性の基準、切り戻し） | 基準の検査と、最小の 1 か所の移行 | [例 8](../_examples/prompts/08_migrate-frontend.md) |
| 複製して改造（fork） | 他のリポジトリ・スキル・OSS を写して作り替える | 複製元（時点、ライセンス、同期の方針、変える点・変えない点） | 複製をそのまま動かし、元のテストを通す | [例 9](../_examples/prompts/09_fork-skill-plugin.md) |

### 新規・移行・複製して改造の始め方
テンプレートを新しいフォルダに写してから、セットアップする。

```bash
cp -r claude-project-template-ja my-project && cd my-project
git init && git add -A && git commit -m "init from template"
python3 _tools/setup.py        # または Claude Code で /setup-project
```

- 移行：移行元が別のリポジトリなら、`01_sources/` に置く（読むだけ）か、`TARGET_DIR` に移行先の作業場所を書く
- 複製して改造：複製元は `01_sources/` に置き（読むだけ）、作り替える写しは `03_outputs/<名前>/` に置く。
  写しを独立したリポジトリにするなら、このリポジトリの `.gitignore` に `03_outputs/<名前>/` を足す
- `.gitignore`：セットアップが、成果物のフォルダ（`TARGET_DIR`。未指定なら `03_outputs/`）に最初の 1 つを作る。
  複製して改造は複製元の `.gitignore` を優先、新規・後付け・移行の制作は github/gitignore の言語別 + テンプレートの補完（ネットが使えなければ同梱の写し）、
  知的作業・専門作業はテンプレートのもの。作り直しは `python3 _tools/gitignore.py --dir <フォルダ> --langs <言語> --force`

### 後付けの始め方
既存のフォルダに、このテンプレートの仕組みだけを入れる。既存の CLAUDE.md・README.md・settings.json・同名のスキルは上書きしない。

```bash
python3 claude-project-template-ja/_tools/adopt.py --target ../my-app            # 試し（予定だけ出す）
python3 claude-project-template-ja/_tools/adopt.py --target ../my-app --apply --link
cd ../my-app && python3 _tools/doctor.py
```

その後、`../my-app` で Claude Code を開き、`/setup-project` で始め方に「後付け」を選ぶ。
`../my-app` に、もとから `SPEC.md`・`PROGRESS.md`・`DECISIONS.md` などがあると、セットアップは止まる。
`--force` で作り直すと、上書きする前のファイルを `04_logs/pre-setup-<日付>/` に写すので、その中身を新しい仕様の
「今の状態（後付け）」に移す。

古い版のこのテンプレートで始めたプロジェクトを新しくするときは `--update` を付ける。`_tools/`・`_templates/`・
`_examples/hearing/` の中の同じ名前のファイルを新しくし、足りないスキルやフォルダを足す（ファイルは消さない）。
プロジェクトで直したスキルと CLAUDE.md は上書きせず、違いを表示するので、見比べて手で取り込む。

```bash
python3 claude-project-template-ja/_tools/adopt.py --target ../old-project --update          # 試し
python3 claude-project-template-ja/_tools/adopt.py --target ../old-project --update --apply
```
`--link` は、既存の CLAUDE.md の末尾に `@CLAUDE.template.md` の 1 行を足す（ルールが食い違うときは、既存のほうを優先する）。

## 成果物を別の git リポジトリに置く形
プラグインやライブラリのように、成果物だけを公開するときに使う。

```
my-project/                 ← 作業台（仕様、記録、評価。このテンプレート）
├── 01_sources/             ← 複製元・参考（読むだけ）
├── 03_outputs/my-plugin/   ← 成果物のリポジトリ（独自の .git。作業台の .gitignore に入れる）
├── 05_evals/               ← 実物の入力を通した記録
└── 04_logs/v0-0-1/         ← 締めた版の記録
```

- コミットは、それぞれのリポジトリで行う。報告や `DECISIONS.md` には、どちらのリポジトリのコミットかを書く
- 成果物のリポジトリの README に、作業台の内部の事情（承認待ちの操作など）を書かない

## 版を重ねる（サイクル）
1 つのプロジェクトで改修を重ねるときは、版ごとに記録を締める。

```
/setup-project → KICKOFF → /milestone … → /verify → （公開）
   → /next-cycle（04_logs/<版>/ に締めて、PLAN.md を作る）→ 承認 → /milestone … → /verify → …
セッションの区切りごとに /handoff、マイルストーン 3 つごとか版の区切りで /retro
```

| 道具 | 役割 |
|---|---|
| `/handoff` | `06_handoff/` に引き継ぎメモを作り、次のセッションの最初のメッセージを示す |
| `/next-cycle` | `cycle.py close` で記録を `04_logs/<版>/` に締め、`cycle.py start` で次の `PLAN.md` を作る。版の途中から `04_logs/<版>/` に計画を置いていたときは `close --merge` |
| `conv.py toc・find・show` | `02_conversations/` と `04_logs/*/conversations/` の両方を調べる |
