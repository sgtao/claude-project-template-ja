#!/usr/bin/env python3
"""証拠台帳（LEDGER.csv）と成果物の機械検査。標準ライブラリのみで動く。

検査すること:
  1. 引用の一致   : 種別「記載」の引用が、出所のファイルにその通りあるか（空白の違いは無視）
  2. 参照の完全性 : 成果物の [L-001] の形の ID が、すべて台帳にあるか
  3. ID のない数値: 数値を含むのに ID がない文（警告）
  4. 網羅         : --units のファイルに書いた単位（条項、論文、選択肢など）が、すべて台帳にあるか
  5. 出所の区別   : 種別「解釈」「推測」の ID を使う文に、断定を避ける言葉があるか（警告）

使い方:
  python3 _tools/check_ledger.py --doc 03_outputs/report.md
  python3 _tools/check_ledger.py --ledger LEDGER.csv --doc out.md --sources 01_sources --units units.txt

終了コード: 不合格があれば 1、なければ 0（警告だけなら 0）。
"""
import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = ("記載", "計算", "解釈", "推測")
HEDGES = ("可能性", "推測", "考えられ", "とみられ", "解釈", "確認が必要", "かもしれ", "おそれ", "仮定", "想定")
ID_RE = re.compile(r"\[(L-\d+)\]")
TEXT_EXT = {".md", ".txt", ".csv", ".json", ".html", ".htm", ".tsv", ".yaml", ".yml"}


def squash(s):
    return re.sub(r"\s+", "", s)


def sentences(text):
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "|", "```")):
            continue
        line = re.sub(r"^(\d+[.)]|[-*・])\s*", "", line)
        for s in re.split(r"(?<=[。．!?！？])", line):
            if s.strip():
                yield s.strip()


def main():
    ap = argparse.ArgumentParser(description="証拠台帳と成果物の機械検査")
    ap.add_argument("--ledger", default="LEDGER.csv")
    ap.add_argument("--doc", help="成果物（Markdown かテキスト）。省略すると台帳だけ検査する")
    ap.add_argument("--sources", default="01_sources", help="出所ファイルの置き場所")
    ap.add_argument("--units", help="扱うべき単位を 1 行に 1 つ書いたファイル")
    a = ap.parse_args()

    fails, warns = [], []
    ledger_path = ROOT / a.ledger if not Path(a.ledger).is_absolute() else Path(a.ledger)
    src_dir = ROOT / a.sources if not Path(a.sources).is_absolute() else Path(a.sources)
    with open(ledger_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    need = {"id", "claim", "source", "locator", "quote", "kind", "unit"}
    if rows and not need <= set(rows[0].keys()):
        sys.exit(f"台帳の列が足りません。必要な列: {', '.join(sorted(need))}")

    ids, cache = {}, {}
    for r in rows:
        rid = (r["id"] or "").strip()
        if not re.fullmatch(r"L-\d+", rid):
            fails.append(f"ID の形が不正（L-001 の形にする）: {rid!r}")
            continue
        if rid in ids:
            fails.append(f"ID の重複: {rid}")
        ids[rid] = r
        kind = (r["kind"] or "").strip()
        if kind not in KINDS:
            fails.append(f"{rid}: 種別は {'・'.join(KINDS)} のどれかにする（現在: {kind!r}）")
        if not (r["claim"] or "").strip():
            fails.append(f"{rid}: 主張が空")
        if kind != "記載":
            continue
        src, quote = (r["source"] or "").strip(), (r["quote"] or "").strip()
        if not src or not quote:
            fails.append(f"{rid}: 種別「記載」には出所と引用が必要")
            continue
        if src.startswith(("http://", "https://")):
            warns.append(f"{rid}: 出所が URL のため、引用の一致は確かめていない（未検証）")
            continue
        p = src_dir / src
        if not p.is_file():
            fails.append(f"{rid}: 出所のファイルがない: {a.sources}/{src}")
            continue
        if p.suffix.lower() not in TEXT_EXT:
            warns.append(f"{rid}: {src} はテキストでないため未検証。テキストにしてから再検査する")
            continue
        if src not in cache:
            cache[src] = squash(p.read_text(encoding="utf-8", errors="replace"))
        if squash(quote) not in cache[src]:
            fails.append(f"{rid}: 引用が出所にない: 「{quote[:40]}」（{src}）")

    if a.units:
        have = {(r["unit"] or "").strip() for r in rows}
        for u in Path(a.units).read_text(encoding="utf-8").splitlines():
            u = u.strip()
            if u and not u.startswith("#") and u not in have:
                fails.append(f"網羅: 単位「{u}」が台帳にない")

    used = set()
    if a.doc:
        doc_path = ROOT / a.doc if not Path(a.doc).is_absolute() else Path(a.doc)
        for s in sentences(doc_path.read_text(encoding="utf-8")):
            found = ID_RE.findall(s)
            used.update(found)
            for rid in found:
                if rid not in ids:
                    fails.append(f"参照: 台帳にない ID {rid}: 「{s[:40]}」")
                elif ids[rid]["kind"].strip() in ("解釈", "推測") and not any(h in s for h in HEDGES):
                    warns.append(f"断定の疑い（{rid} は{ids[rid]['kind'].strip()}）: 「{s[:50]}」")
            if not found and re.search(r"\d", ID_RE.sub("", s)):
                warns.append(f"ID のない数値: 「{s[:50]}」")
        unused = sorted(set(ids) - used)
        if unused:
            warns.append(f"成果物で使っていない台帳の行: {', '.join(unused[:10])}"
                         + (" ほか" if len(unused) > 10 else ""))

    print(f"台帳 {len(rows)} 行 / 成果物で参照した ID {len(used)} 個")
    for w in warns:
        print(f"  警告  {w}")
    for x in fails:
        print(f"  不合格 {x}")
    print(f"結果: 不合格 {len(fails)} 件、警告 {len(warns)} 件")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
