# _examples/

セットアップの材料と見本。

| 場所 | 中身 |
|---|---|
| `hearing/questions.json` | ヒアリングの質問の正本。`_tools/setup.py` と `/setup-project` が使う |
| `templates/` | SPEC.md、BRIEF.md、PROGRESS.md、KICKOFF.md のひな形（`{{KEY}}` に答えが入る） |
| `answers/` | 答えの見本（JSON）。セットアップを実行すると、実際の答えが `current.json` に残る |
| `prompts/` | 一文の依頼を、このテンプレートの形に直した例 |
| `ledger-sample/` | 証拠台帳と検査の見本（架空の契約書） |

## ヒアリングの流れ

```
一文の依頼
   │  /setup-project（Claude が選択式で聞く）または python3 _tools/setup.py（端末で答える）
   ▼
answers/current.json ──▶ SPEC.md か BRIEF.md（下書き）＋ KICKOFF.md ＋ PROGRESS.md
   │  KICKOFF.md を Claude に渡す
   ▼
[要記入] が埋まった SPEC.md／BRIEF.md ──▶ ユーザーが確認 ──▶ /milestone
```

ヒアリングは「ユーザーしか知らないこと」だけを聞く。数値の合格条件、技術の選定、マイルストーンは、
KICKOFF の段階で Claude が案を作り、ユーザーが確かめる。

## 試す

```bash
python3 _tools/setup.py --answers _examples/answers/browser-game.json --out /tmp/try-build
python3 _tools/setup.py --answers _examples/answers/contract-review.json --out /tmp/try-knowledge
```

## 質問を変える
1. `hearing/questions.json` に質問を足す（`key`、`ask`、必要なら `choices`、`when`、`default`）
2. `templates/` のひな形の、答えを入れたい場所に `{{KEY}}` を書く
3. 上の「試す」のコマンドで、出力を確かめる

## プロンプト例の読み方
`prompts/` の各ファイルは、次の 3 つを並べている。
- 元の一文の依頼
- ヒアリングでの答え方
- その分野で SPEC.md／BRIEF.md に足すとよい合格条件

合格条件の数値は出発点で、題材に合わせて変える。
