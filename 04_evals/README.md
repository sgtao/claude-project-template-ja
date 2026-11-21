# 04_evals/

評価の実行記録を置く場所。実物の入力を実際の手順で通したときの、入力・出力・結果を残す。

- 1 回の実行につき 1 フォルダ：`<MMDD-NN>_<話題>/`（中に `README.md`：何を、どの手順で、どの版で通し、何が分かったか）
- 専門作業の評価ケース表は `cases.csv`（ひな形は `_templates/_cases.csv`。検査は `python3 _tools/check_cases.py`）
- 大きな出力や、別の git リポジトリを含む出力は、`.gitignore` に足してよい（`README.md` だけは残す）
- サイクルを締めると（`/next-cycle`）、実行記録は `05_logs/<名前>/evals/` に移る。`cases.csv` は写しを残して続けて使う
