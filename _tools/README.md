# _tools/

検査と記録のスクリプト。すべて Python の標準ライブラリだけで動く。リポジトリのトップから実行する。

| スクリプト | 用途 | いつ使うか |
|---|---|---|
| `setup.py` | ヒアリングの答えを `_templates/` のひな形に入れ、SPEC.md／BRIEF.md、KICKOFF.md、PROGRESS.md、DECISIONS.md（知的作業は LEDGER.csv も）を作る | 最初に 1 回 |
| `doctor.py` | 必要なファイル（ひな形を含む）、設定の形式、セットアップの状態を点検する | セットアップの後、再開のとき |
| `check_spec.py` | 合格条件の点検（未記入、個数、数値か確かめ方の有無、数えられない言葉） | 仕様を書いた後 |
| `check_ledger.py` | 証拠台帳と成果物の検査（引用の一致、ID の参照、網羅、断定の疑い） | 知的作業の成果物を書くたび |
| `seed_errors.py` | 仕込み検査（写しに誤りを入れ、審査が見つけた数を数える） | 最終の出力の前 |
| `conv.py` | 会話の記録の作成・追記・一覧・検索・表示 | 毎ターン（記録）、過去を参照するとき |

## 例

```bash
python3 _tools/setup.py --answers _examples/answers/browser-game.json --out /tmp/try   # 試し書き
python3 _tools/check_spec.py SPEC.md
python3 _tools/check_ledger.py --doc 03_outputs/report.md --units 01_sources/units.txt
python3 _tools/seed_errors.py seed --in 03_outputs/report.md --out /tmp/seeded.md --key /tmp/key.json
python3 _tools/seed_errors.py score --key /tmp/key.json --report /tmp/review.md
python3 _tools/conv.py find 合格条件
```

検査の見本は `_examples/ledger-sample/` にある。次で動きを確かめられる。

```bash
python3 _tools/check_ledger.py --ledger _examples/ledger-sample/LEDGER.csv \
  --doc _examples/ledger-sample/report.md --sources _examples/ledger-sample/sources \
  --units _examples/ledger-sample/units.txt
```

## 終了コード
どの検査も、不合格があれば 1、なければ 0 を返す。警告だけなら 0。

## 検査を足すとき
- 1 つのスクリプトは 1 つのことを確かめる。結果は「不合格」「警告」に分けて日本語で出す
- 追加のパッケージが要る検査は、このフォルダではなくプロジェクトのテストに置く
- 足したら、この表と、該当するスキル（`.claude/skills/verify/SKILL.md`）に 1 行足す

## 限界
- `check_ledger.py` の引用の一致は、テキストの資料だけ。PDF や Word は、先にテキストにする
- `check_ledger.py` の「断定の疑い」「ID のない数値」は目安。警告として 1 件ずつ見る
- `seed_errors.py` が自動で入れるのは、数値の書き換えだけ。論理の誤りは手で足す
