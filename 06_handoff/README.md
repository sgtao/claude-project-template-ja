# 06_handoff/

セッションを区切るときの引き継ぎメモを置く場所。`/handoff` が作る。次のセッションは、最新のメモ 1 つから再開する。

- 1 回につき 1 ファイル：`<MMDD-NN>_<話題>.md`（番号は `python3 _tools/handoff.py new <話題>` が付ける）
- 最新のメモ：`python3 _tools/handoff.py latest`（パスを表示する）
- 前のメモは消さない（何を引き継いだかの履歴になる）。ひな形は `_templates/_HANDOFF.md`
- サイクルを締めると（`/next-cycle`）、メモは `04_logs/<名前>/handoff/` に移る
