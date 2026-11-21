# 05_logs/

締めたサイクル（版）の記録を置く場所。`python3 _tools/cycle.py close <名前> --apply`（`/next-cycle`）が作る。

- `05_logs/<名前>/`：その版の仕様・進み具合・台帳の写し、計画（PLAN.md）、引き継ぎメモ、会話、評価
- 中身は**読み取り専用の記録**として扱い、書き換えない。直すことがあれば、今のサイクルの記録に書く
- 会話は `python3 _tools/conv.py toc`・`find`・`show` で、02_conversations/ と一緒に調べられる
