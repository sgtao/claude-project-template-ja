#!/usr/bin/env python3
"""仕込み検査：資料や下書きの写しに、わざと誤りを入れて、審査が見つけるかを数える。

審査役（別エージェントや別の人）に写しを渡し、審査の報告に誤りがいくつ出てくるかで、
検査が本当に働いているかを確かめる。標準ライブラリのみで動く。

使い方:
  # 1. 誤りを仕込んだ写しと、答えのファイルを作る
  python3 _tools/seed_errors.py seed --in 03_outputs/report.md --out /tmp/seeded.md --key /tmp/key.json --n 5
  # 2. 審査役に /tmp/seeded.md を渡し、報告を review.md に保存する（答えのファイルは渡さない）
  # 3. 採点する
  python3 _tools/seed_errors.py score --key /tmp/key.json --report review.md

限界: 仕込めるのは数値の書き換えだけ。論理の誤りや引用の取り違えは、手で 1〜2 個足すとよい
（足した誤りは、答えのファイルの "manual" に目印の語を書けば採点に入る）。
"""
import argparse
import json
import random
import re
import sys
from pathlib import Path

NUM_RE = re.compile(r"(?<![\w.\-])\d[\d,]*(?:\.\d+)?(?![\w\-])")


def mutate(tok, rng):
    has_comma = "," in tok
    raw = tok.replace(",", "")
    if "." in raw:
        dec = len(raw.split(".")[1])
        v = float(raw)
        new = v * rng.choice((0.7, 0.8, 1.2, 1.3)) or 1.0
        s = f"{new:.{dec}f}"
    else:
        v = int(raw)
        delta = max(1, round(v * rng.choice((0.1, 0.2, 0.3))))
        new = v + delta if (rng.random() < 0.5 or v - delta < 1) else v - delta
        s = f"{new:,}" if has_comma else str(new)
    return s


def cmd_seed(a):
    rng = random.Random(a.seed)
    lines = Path(a.inp).read_text(encoding="utf-8").splitlines(keepends=True)
    cands = []
    for i, line in enumerate(lines):
        if line.lstrip().startswith(("#", "```", "|--", "http")):
            continue
        body_start = len(line) - len(re.sub(r"^\s*\d+[.)]\s+", "", line))  # 行頭の箇条番号は対象外
        for m in NUM_RE.finditer(line):
            if m.start() < body_start or "L-" in line[max(0, m.start() - 2):m.start()]:
                continue
            if len(m.group().replace(",", "")) == 4 and m.group().startswith(("19", "20")):
                continue  # 年らしい数は対象外
            cands.append((i, m.start(), m.end(), m.group()))
    if not cands:
        sys.exit("書き換えられる数値がありません。")
    picked, used_lines = [], set()
    for c in rng.sample(cands, len(cands)):
        if c[0] not in used_lines:
            picked.append(c)
            used_lines.add(c[0])
        if len(picked) == a.n:
            break
    key = []
    for n, (i, s, e, tok) in enumerate(sorted(picked), 1):
        new = mutate(tok, rng)
        if new == tok:
            new = str(int(float(tok.replace(",", ""))) + 1)
        lines[i] = lines[i][:s] + new + lines[i][e:]
        key.append({"id": n, "line": i + 1, "original": tok, "seeded": new,
                    "context": lines[i].strip()[:80]})
    Path(a.out).write_text("".join(lines), encoding="utf-8")
    Path(a.key).write_text(json.dumps({"seeded": key, "manual": []}, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"誤りを {len(key)} 個入れました: {a.out}（答え: {a.key}）")
    if len(key) < a.n:
        print(f"  注意: 数値が少なく、{a.n} 個は入れられませんでした。")


def cmd_score(a):
    key = json.loads(Path(a.key).read_text(encoding="utf-8"))
    report = Path(a.report).read_text(encoding="utf-8")
    flat = report.replace(",", "")
    found, total = 0, 0
    for k in key.get("seeded", []):
        total += 1
        hit = k["seeded"].replace(",", "") in flat or f"{k['line']}行" in report or f"行{k['line']}" in report
        found += hit
        print(f"  {'検出' if hit else '見逃し'}  {k['line']}行目  {k['original']} → {k['seeded']}")
    for word in key.get("manual", []):
        total += 1
        hit = word in report
        found += hit
        print(f"  {'検出' if hit else '見逃し'}  手で入れた誤り（目印: {word}）")
    rate = found / total if total else 0
    print(f"結果: {found}/{total} 個を検出（{rate:.0%}）")
    print("目安: 8 割未満なら、審査の指示か、渡す資料を見直す。")
    sys.exit(0 if rate >= a.threshold else 1)


def main():
    ap = argparse.ArgumentParser(description="仕込み検査")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed")
    s.add_argument("--in", dest="inp", required=True); s.add_argument("--out", required=True)
    s.add_argument("--key", required=True); s.add_argument("--n", type=int, default=5)
    s.add_argument("--seed", type=int, default=42); s.set_defaults(f=cmd_seed)
    s = sub.add_parser("score")
    s.add_argument("--key", required=True); s.add_argument("--report", required=True)
    s.add_argument("--threshold", type=float, default=0.8); s.set_defaults(f=cmd_score)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
