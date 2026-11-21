# 例 10：途中まで作ったアプリに、このテンプレートを後付けする（制作・後付け）

## 元の依頼
> 途中まで作った家計簿アプリを、この進め方で最後まで仕上げたい

## 始め方
1. テンプレートを手元に取り、既存のフォルダに仕組みだけを入れる（既存のファイルは上書きしない）
   ```bash
   python3 claude-project-template-ja/_tools/adopt.py --target ./kakeibo           # 試し
   python3 claude-project-template-ja/_tools/adopt.py --target ./kakeibo --apply --link
   ```
2. `./kakeibo` で Claude Code を開き、`/setup-project` で始め方に「後付け」を選ぶ

## ヒアリングでの答え方
答えの見本：[`answers/adopt-existing-app.json`](../answers/adopt-existing-app.json)

- 今の状態：動いている版、テストの件数、途中の作業を書く（基準として記録し、壊していないことを確かめる）
- 制約：もとの README と CLAUDE.md のルールを守る、と書く

## SPEC.md に足すとよい合格条件
```text
- 後付けの前のテスト 40 件が、後付けの後もすべて通る（確認：Jest。件数が一致）
- 検索が 1,000 件のデータで 1 秒以内（確認：計測スクリプト）
- 月ごとのグラフが 12 か月分出る（確認：スクリーンショット）
- もとの CLAUDE.md のルールと食い違う手順は、DECISIONS.md に書いてから変える
```

## 審査の役割
初めて触るユーザーに、もとからいる開発者の観点を足す（既存のルールやテストを壊していないか）。
