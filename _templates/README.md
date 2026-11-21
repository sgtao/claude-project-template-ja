# _templates/

セットアップで直下に作るファイルのひな形。`_tools/setup.py`（と `/setup-project`）だけが読む。
`{{KEY}}` にヒアリングの答えが入り、答えのない `{{KEY}}` は `[要記入: KEY]` になる。

| ひな形 | 直下に作るファイル | 作られる型 |
|---|---|---|
| `_SPEC.md` | `SPEC.md` | 制作 |
| `_BRIEF.md` | `BRIEF.md` | 知的作業 |
| `_PLAYBOOK.md` | `PLAYBOOK.md` | 専門作業 |
| `_LEDGER.csv` | `LEDGER.csv` | 知的作業 |
| `_cases.csv` | `05_evals/cases.csv` | 専門作業 |
| `_PROGRESS.md` | `PROGRESS.md` | すべて |
| `_DECISIONS.md` | `DECISIONS.md` | すべて |
| `_KICKOFF.build.md`／`_KICKOFF.knowledge.md`／`_KICKOFF.craft.md` | `KICKOFF.md` | 対象ごと |
| `_MODE.md` | （仕様のファイルに取り込む）始め方ごとの節 | すべて |
| `_KICKOFF.mode.md` | （KICKOFF に取り込む）始め方ごとの最初の指示 | すべて |

途中で作る文書のひな形（セットアップでは作らない）：

| ひな形 | 作るファイル | 作るとき |
|---|---|---|
| `_HANDOFF.md` | `HANDOFF.md` | `/handoff` |
| `_MANUAL-CHECK.md` | `MANUAL-CHECK.md` | `/verify` の実物の通しで、対話でしか確かめられない動作があるとき |
| `_PLAN.md` | `PLAN.md` | `/next-cycle`（`cycle.py start`） |

## 書き方
- `{{KEY}}`：ヒアリングの答えを入れる。`{{KEY_LABEL}}` は選択肢の表示名
- `{{> _MODE.md}}`：ほかのひな形をその場所に取り込む
- `<!-- when KIND=craft MODE=fork,migrate -->` 〜 `<!-- end -->`：条件に合うときだけ残す
  （空白区切りはすべて満たす、カンマは「または」。入れ子にしない）

## 守ること
- プロジェクトの作業中は、ここではなく直下に作られたファイルを編集する
- ひな形を直すのは、テンプレートそのものを育てるとき（README の「テンプレートを育てる」）。
  `{{KEY}}` を足したら `_examples/hearing/questions.json` に同じ `key` の質問を足す
- 直したら、次の試し書きで出力を確かめる

```bash
python3 _tools/setup.py --answers _examples/answers/browser-game.json --out /tmp/try-build
python3 _tools/setup.py --answers _examples/answers/contract-review.json --out /tmp/try-knowledge
python3 _tools/setup.py --answers _examples/answers/fork-skill-plugin.json --out /tmp/try-craft
python3 _tools/selftest.py setup    # 全部の見本と 12 通りの組み合わせを一度に試す
```
