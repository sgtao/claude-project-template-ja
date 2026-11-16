# _templates/

セットアップで直下に作るファイルのひな形。`_tools/setup.py`（と `/setup-project`）だけが読む。
`{{KEY}}` にヒアリングの答えが入り、答えのない `{{KEY}}` は `[要記入: KEY]` になる。

| ひな形 | 直下に作るファイル | 作られる型 |
|---|---|---|
| `_SPEC.md` | `SPEC.md` | 制作 |
| `_BRIEF.md` | `BRIEF.md` | 知的作業 |
| `_LEDGER.csv` | `LEDGER.csv` | 知的作業 |
| `_PROGRESS.md` | `PROGRESS.md` | 両方 |
| `_DECISIONS.md` | `DECISIONS.md` | 両方 |
| `_KICKOFF.build.md` | `KICKOFF.md` | 制作 |
| `_KICKOFF.knowledge.md` | `KICKOFF.md` | 知的作業 |

## 守ること
- プロジェクトの作業中は、ここではなく直下に作られたファイルを編集する
- ひな形を直すのは、テンプレートそのものを育てるとき（README の「テンプレートを育てる」）。
  `{{KEY}}` を足したら `_examples/hearing/questions.json` に同じ `key` の質問を足す
- 直したら、次の試し書きで出力を確かめる

```bash
python3 _tools/setup.py --answers _examples/answers/browser-game.json --out /tmp/try-build
python3 _tools/setup.py --answers _examples/answers/contract-review.json --out /tmp/try-knowledge
```
