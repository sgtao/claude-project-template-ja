# craft-sample/ — 専門作業の見本（架空の請求書の突き合わせ）

専門作業（`PLAYBOOK.md`）で作る成果物と、評価ケース表の見本。検査の動きを確かめるのに使う。

| 場所 | 中身 |
|---|---|
| `invoice-check/` | 手順をスキルにした見本（`SKILL.md` と、判断の基準 `references/criteria.md`） |
| `cases.csv` | 評価ケース表の見本（正例 3・境界 1・負例 1。すべて合格） |
| `evals/` | ケースの証拠（実行の記録）の見本 |

```bash
python3 _tools/check_skill.py _examples/craft-sample/invoice-check
python3 _tools/check_cases.py _examples/craft-sample/cases.csv
```
