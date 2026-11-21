#!/usr/bin/env python3
"""SPEC.md / BRIEF.md / PLAYBOOK.md の合格条件の点検。標準ライブラリのみで動く。

検査すること:
  1. 未記入の箇所（{{...}} と [要記入: ...]）が残っていないか
  2. 「## 合格条件」の項目が 1〜10 個か
  3. 各項目に、数値か「確認：」（確かめ方）が書かれているか
  4. 数えられない形容詞（きれい、自然、適切 など）だけで書かれていないか（警告）

使い方:
  python3 _tools/check_spec.py            # SPEC.md・BRIEF.md・PLAYBOOK.md のうち、あるものを検査
  python3 _tools/check_spec.py BRIEF.md
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAGUE = ("きれい", "綺麗", "滑らか", "自然", "適切", "十分", "リアル", "使いやすい", "分かりやすい",
         "わかりやすい", "高品質", "いい感じ", "なるべく", "できるだけ", "しっかり")


def criteria(text):
    m = re.search(r"^## 合格条件.*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return None
    return [l.strip() for l in m.group(1).splitlines() if re.match(r"\s*(\d+[.)]|- \[.\]|-)\s+\S", l)]


def check(path):
    text = path.read_text(encoding="utf-8")
    fails, warns = [], []
    todo = re.findall(r"\{\{[A-Z_]+\}\}|\[要記入[^\]]*\]", text)
    if todo:
        fails.append(f"未記入が {len(todo)} 箇所: {', '.join(sorted(set(todo))[:6])}")
    items = criteria(text)
    if items is None:
        fails.append("「## 合格条件」の見出しがない")
    else:
        if not 1 <= len(items) <= 10:
            fails.append(f"合格条件は 1〜10 個にする（現在 {len(items)} 個）")
        for it in items:
            body = re.sub(r"^(\d+[.)]|- \[.\]|-)\s+", "", it)
            if "要記入" in body:
                continue
            if not re.search(r"\d", body) and "確認：" not in body and "確認:" not in body:
                fails.append(f"数値も確かめ方もない: 「{body[:40]}」")
            hit = [v for v in VAGUE if v in body]
            if hit and not re.search(r"\d", body):
                warns.append(f"数えられない言葉（{'・'.join(hit)}）: 「{body[:40]}」")
    for w in warns:
        print(f"  警告  {w}")
    for x in fails:
        print(f"  不合格 {x}")
    print(f"{path.name}: 不合格 {len(fails)} 件、警告 {len(warns)} 件")
    return len(fails)


def main():
    names = sys.argv[1:] or ["SPEC.md", "BRIEF.md", "PLAYBOOK.md"]
    total, found = 0, 0
    for n in names:
        p = ROOT / n if not Path(n).is_absolute() else Path(n)
        if p.is_file():
            found += 1
            total += check(p)
        elif sys.argv[1:]:
            sys.exit(f"ファイルがありません: {n}")
    if not found:
        sys.exit("SPEC.md・BRIEF.md・PLAYBOOK.md のどれもありません（セットアップ前）。"
                 "python3 _tools/setup.py か /setup-project を実行してください。")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
