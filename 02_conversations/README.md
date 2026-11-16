###### [toTopPage](../README.md)
# 02_conversations/

会話の記録を置く場所。1 チャットにつき 1 ファイル。記録のルールは [HISTORY.md](../HISTORY.md) にある。

## ファイル名
`MMDD-NN_<kebab-case の話題>.md`（`MMDD` はチャット開始日、`NN` は同日内の連番）

## 記録を作る・足す
```bash
python3 _tools/conv.py new setup-spec --title "仕様づくり"
python3 _tools/conv.py add --q-title "合格条件の案" --q-file /tmp/q.txt --a-file /tmp/a.md --changed SPEC.md
```

## 記録を調べる（使い方）
記録ファイルを丸ごと読まず、一覧 → 検索 → 1 つの Q&A だけ、の順に絞る。

```bash
python3 _tools/conv.py toc                    # 一覧（番号、題名、Q の題名）
python3 _tools/conv.py find 合格条件 "検査|テスト"   # 語はすべて含む。| は「または」。新しい順
python3 _tools/conv.py show 1117-01 2         # 1117-01 の Q2 だけを表示
python3 _tools/conv.py where 03_outputs/report.md   # 記録にあるパスの今の場所を探す
```

## 書式（スクリプトを使えないとき）
```markdown
###### [toTopPage](../README.md)
###### [toREADME](./README.md)
# 02_conversations/<ファイル名>.md
- `title`: <チャットの題名>
- `url`  : 
- `output`: [<成果物の相対パス>](../<成果物の相対パス>)   ← 成果物がある場合のみ

-----
[toTop](#totoppage)
## Q. <質問の短い題名>
<ユーザーの質問本文（原文のまま）>

---
### Answer
<回答の内容>

-----
[toTop](#totoppage)
```

## 守ること
- 過去の記録ファイルは書き換えない（パスが変わっていても、リンクを直さない）
- パスワードや API キー、個人情報の原文は書かない
