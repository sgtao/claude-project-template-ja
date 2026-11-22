# _templates/gitignore/

[github/gitignore](https://github.com/github/gitignore)（CC0）の主要な言語の写し。
`_tools/gitignore.py` が、ネットから取れないとき（オフライン、取得の失敗）に代わりに使う。
ふだんは実行時に最新を取るので、ここは「取れないときの控え」。

- 写した日：2026-11-22（github/gitignore の main、コミット eeb775f7cb）
- 入っている言語：Python／Node／Go／Rust／Java／Swift／Ruby／C／C++／Dart／Android／Unity／Terraform／VisualStudio
- 足したい言語があれば、`<名前>.gitignore`（github/gitignore のファイル名のまま）を置く。
  別名（typescript → Node など）は `_tools/gitignore.py` の `ALIASES` に足す
- 更新するときは、同じ名前で取り直して置き換える。ここは手で書き換えない
