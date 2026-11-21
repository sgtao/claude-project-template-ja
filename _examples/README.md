# _examples/

セットアップの材料と見本。ひな形（SPEC.md などの元）は [`_templates/`](../_templates/README.md) にある。

| 場所 | 中身 |
|---|---|
| `hearing/questions.json` | ヒアリングの質問の正本。`_tools/setup.py` と `/setup-project` が使う |
| `answers/` | 答えの見本（JSON）。セットアップを実行すると、実際の答えが `current.json` に残る |
| `prompts/` | 一文の依頼を、このテンプレートの形に直した例（下の表） |
| `ledger-sample/` | 証拠台帳と検査の見本（架空の契約書） |
| `craft-sample/` | 専門作業の見本：スキルと評価ケース表（架空の請求書の突き合わせ） |

| 例 | 対象 | 始め方 |
|---|---|---|
| 01 ブラウザゲーム／02 Three.js の映像／03 Blender・音楽・絵 | 制作 | 新規 |
| 04 契約書レビュー／05 意思決定の分析／06 記事と授業 | 知的作業 | 新規 |
| 07 経費精算のチェックを手順書とスキルに | 専門作業 | 新規 |
| 08 Vue 2 から Vue 3 への移行 | 制作 | 移行 |
| 09 手元のスキルを複製して 1 つのプラグインに | 専門作業 | 複製して改造 |
| 10 途中まで作ったアプリに後付け | 制作 | 後付け |

## ヒアリングの流れ

```
一文の依頼
   │  /setup-project（Claude が選択式で聞く）または python3 _tools/setup.py（端末で答える）
   ▼
answers/current.json ＋ _templates/ のひな形
   ▼
SPEC.md／BRIEF.md／PLAYBOOK.md（下書き）＋ KICKOFF.md ＋ PROGRESS.md ＋ DECISIONS.md
（＋ 知的作業は LEDGER.csv、専門作業は 04_evals/cases.csv）
   │  KICKOFF.md を Claude に渡す
   ▼
[要記入] が埋まった仕様のファイル ──▶ ユーザーが確認 ──▶ /milestone
```

ヒアリングは「ユーザーしか知らないこと」だけを聞く。数値の合格条件、技術の選定、マイルストーンは、
KICKOFF の段階で Claude が案を作り、ユーザーが確かめる。

## 試す

```bash
python3 _tools/setup.py --answers _examples/answers/browser-game.json --out /tmp/try-build
python3 _tools/setup.py --answers _examples/answers/contract-review.json --out /tmp/try-knowledge
python3 _tools/selftest.py setup   # すべての見本を一度に
```

## 質問を変える
1. `hearing/questions.json` に質問を足す（`key`、`ask`、必要なら `choices`、`when`、`default`）
2. `_templates/` のひな形の、答えを入れたい場所に `{{KEY}}` を書く
3. 上の「試す」のコマンドで、出力を確かめる。始め方や対象ごとに分けたいときは、ひな形の中で `<!-- when ... -->` を使う
4. `python3 _tools/selftest.py` を通す

## プロンプト例の読み方
`prompts/` の各ファイルは、次の 3 つを並べている。
- 元の一文の依頼
- ヒアリングでの答え方
- その分野で仕様のファイル（SPEC.md／BRIEF.md／PLAYBOOK.md）に足すとよい合格条件

合格条件の数値は出発点で、題材に合わせて変える。
