#!/usr/bin/env python3
"""評価ケース表（05_evals/cases.csv）の検査。標準ライブラリのみで動く。

専門作業（PLAYBOOK.md）で必ず、制作でも入出力の決まった処理があれば使う。
「検査が通った」が空振りでないことを、負例（失敗すべき入力）の有無で確かめる。

列: id, kind, input, expected, result, evidence, note
  kind   : 正例（ふつうの入力）／境界（判断の基準のきわ）／負例（止まるか警告を出すべき入力）
  result : 合格／不合格／未実行
  evidence: 結果の証拠（出力のファイル、ログ、コミット）。パスなら存在を確かめる

不合格にすること:
  列の不足、id の重複、kind・result の値の誤り、ケース 0 件、負例 0 件、
  不合格のケース、未実行のケース（--allow-pending のときは警告）、存在しない証拠のパス
警告にすること:
  合格なのに証拠が空、正例が 3 件未満、境界が 0 件

使い方:
  python3 _tools/check_cases.py                       # 05_evals/cases.csv
  python3 _tools/check_cases.py path/to/cases.csv --allow-pending   # 作業の途中
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLS = ["id", "kind", "input", "expected", "result", "evidence"]
KINDS = ("正例", "境界", "負例")
RESULTS = ("合格", "不合格", "未実行")


def looks_like_path(s):
    return "/" in s or s.endswith((".md", ".json", ".txt", ".log", ".csv", ".html", ".png"))


def check(path, allow_pending):
    fails, warns = [], []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)
    missing = [c for c in COLS if c not in header]
    if missing:
        fails.append(f"列がない: {', '.join(missing)}（必要な列: {', '.join(COLS)}）")
        return fails, warns, Counter(), Counter()
    if not rows:
        fails.append("ケースが 0 件（過去の実例から、正例・境界・負例を作る）")
    dup = [k for k, n in Counter(r["id"] for r in rows).items() if n > 1]
    if dup:
        fails.append(f"id の重複: {', '.join(dup)}")
    kinds, results = Counter(), Counter()
    for r in rows:
        rid = r["id"] or "(id なし)"
        k, res, ev = (r.get("kind") or "").strip(), (r.get("result") or "").strip(), (r.get("evidence") or "").strip()
        if k not in KINDS:
            fails.append(f"{rid}: kind「{k}」は {'・'.join(KINDS)} のどれでもない")
        if res not in RESULTS:
            fails.append(f"{rid}: result「{res}」は {'・'.join(RESULTS)} のどれでもない")
        kinds[k] += 1
        results[res] += 1
        if res == "不合格":
            fails.append(f"{rid}: 不合格（{r.get('note') or '理由の記載なし'}）")
        if res == "未実行":
            (warns if allow_pending else fails).append(f"{rid}: 未実行")
        if res == "合格" and not ev:
            warns.append(f"{rid}: 合格だが証拠（evidence）が空")
        for part in ev.replace("；", ";").split(";"):
            part = part.strip()
            if part and looks_like_path(part) and not part.startswith(("http://", "https://")):
                if not ((ROOT / part).exists() or (path.parent / part).exists()):
                    fails.append(f"{rid}: 証拠のパスがない: {part}")
    if rows and not kinds["負例"]:
        fails.append("負例が 0 件（失敗すべき入力で、止まるか警告が出ることを確かめるケースを足す）")
    if rows and kinds["正例"] < 3:
        warns.append(f"正例が {kinds['正例']} 件（3 件以上が目安）")
    if rows and not kinds["境界"]:
        warns.append("境界のケースが 0 件（判断の基準のきわを 1 件以上が目安）")
    return fails, warns, kinds, results


def main():
    ap = argparse.ArgumentParser(description="評価ケース表の検査")
    ap.add_argument("path", nargs="?", default="05_evals/cases.csv")
    ap.add_argument("--allow-pending", action="store_true", help="未実行を警告にとどめる（作業の途中）")
    a = ap.parse_args()
    p = Path(a.path) if Path(a.path).is_absolute() else ROOT / a.path
    if not p.is_file():
        sys.exit(f"ファイルがありません: {a.path}（ひな形は _templates/_cases.csv）")
    fails, warns, kinds, results = check(p, a.allow_pending)
    for w in warns:
        print(f"  警告  {w}")
    for x in fails:
        print(f"  不合格 {x}")
    summary = "、".join(f"{k} {kinds[k]}" for k in KINDS) + " ／ " + "、".join(f"{r} {results[r]}" for r in RESULTS)
    print(f"{p.name}: {summary} ／ 不合格 {len(fails)} 件、警告 {len(warns)} 件")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
