#!/usr/bin/env python3
"""引き継ぎメモの作成と、最新のメモの検索。標準ライブラリのみで動く。

  new <話題> [--date MMDD] : 06_handoff/<MMDD-NN>_<話題>.md を _templates/_HANDOFF.md から作る。
                             NN は同じ日の連番（締めた版の 04_logs/*/handoff/ のメモも数える）
  latest                   : 最新のメモのパスを表示する（なければ終了コード 1）

使い方:
  python3 _tools/handoff.py new v0-0-2-m3
  python3 _tools/handoff.py latest
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "06_handoff"
NAME_RE = re.compile(r"^(\d{4})-(\d{2})_(.+)\.md$")
SLUG_RE = re.compile(r"^[a-z0-9]+([.\-][a-z0-9]+)*$")


def memos(archive=True):
    files = [p for p in DIR.glob("*.md") if NAME_RE.match(p.name)] if DIR.is_dir() else []
    if archive:
        files += [p for p in (ROOT / "04_logs").glob("*/handoff/*.md") if NAME_RE.match(p.name)]
    return files


def cmd_new(a):
    if not SLUG_RE.match(a.topic):
        sys.exit("話題は英小文字・数字と . - で書いてください。例: v0-0-2-m3")
    date = a.date or datetime.date.today().strftime("%m%d")
    if not re.fullmatch(r"\d{4}", date):
        sys.exit("--date は MMDD（4 桁）で書いてください")
    tpl = ROOT / "_templates" / "_HANDOFF.md"
    if not tpl.exists():
        sys.exit("ひな形がありません: _templates/_HANDOFF.md")
    n = 1 + max([int(m.group(2)) for p in memos() if (m := NAME_RE.match(p.name)).group(1) == date], default=0)
    out = DIR / f"{date}-{n:02d}_{a.topic}.md"
    DIR.mkdir(exist_ok=True)
    out.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")
    print(out.relative_to(ROOT).as_posix())


def cmd_latest(a):
    files = memos(archive=False)
    if not files:
        print("引き継ぎメモはありません（06_handoff/ が空。/handoff で作る）", file=sys.stderr)
        sys.exit(1)
    print(max(files, key=lambda p: (NAME_RE.match(p.name).group(1, 2), p.stat().st_mtime)).relative_to(ROOT).as_posix())


def main():
    ap = argparse.ArgumentParser(description="引き継ぎメモ")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new"); s.add_argument("topic"); s.add_argument("--date"); s.set_defaults(f=cmd_new)
    s = sub.add_parser("latest"); s.set_defaults(f=cmd_latest)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
