#!/usr/bin/env python3
"""会話履歴（02_conversations/）の作成・追記・検索ツール。標準ライブラリのみで動く。

toc・find・show は、締めたサイクルの記録（04_logs/*/conversations/）も見る。
new・add（番号の省略時）は、02_conversations/ だけを対象にする。

使い方:
  python3 _tools/conv.py new <kebab-case-topic> --title "題名"
  python3 _tools/conv.py add --q-title "短い題名" --q-file q.txt --a-file a.md [--changed PATH ...]
  python3 _tools/conv.py toc
  python3 _tools/conv.py find <語...>          # 語はすべて含む。"a|b" で「または」。新しい順
  python3 _tools/conv.py show <番号> <Q番号>   # 例: show 1117-01 2
  python3 _tools/conv.py where <パス>          # 記録にあるパスの今の場所を探す
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONV = ROOT / "02_conversations"
LOGS = ROOT / "04_logs"
END = "-----\n[toTop](#totoppage)\n"
NAME_RE = re.compile(r"^(\d{4})-(\d{2})_(.+)\.md$")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}


def conv_files(archive=True):
    """記録ファイルを新しい順（更新時刻）で返す。archive なら 04_logs/*/conversations/ も含める。"""
    fs = [p for p in CONV.glob("*.md") if NAME_RE.match(p.name)] if CONV.is_dir() else []
    if archive and LOGS.is_dir():
        fs += [p for p in LOGS.glob("*/conversations/*.md") if NAME_RE.match(p.name)]
    return sorted(fs, key=lambda p: (p.stat().st_mtime, p.name), reverse=True)


def where_label(path):
    """02_conversations 以外にある記録には、場所を添える。"""
    return "" if path.parent == CONV else f"  [{path.parent.relative_to(ROOT).as_posix()}]"


def number_of(path):
    m = NAME_RE.match(path.name)
    return f"{m.group(1)}-{m.group(2)}"


def title_of(text):
    m = re.search(r"^- `title`:\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else ""


def split_qas(text):
    """[(Q番号, 題名, 本文)] を返す。"""
    lines = text.splitlines()
    idx = [i for i, l in enumerate(lines) if l.startswith("## Q.")]
    out = []
    for n, start in enumerate(idx, 1):
        end = idx[n] if n < len(idx) else len(lines)
        block = lines[start:end]
        while block and block[-1].strip() in ("", "-----", "[toTop](#totoppage)"):
            block.pop()
        out.append((n, lines[start][5:].strip(), "\n".join(block)))
    return out


def resolve(ref, archive=True):
    fs = conv_files(archive)
    if not fs:
        sys.exit("記録ファイルがありません。先に `conv.py new` を実行してください。")
    if ref in (None, "latest"):
        return fs[0]
    for p in fs:
        if p.name.startswith(ref) or p.name == Path(ref).name:
            return p
    sys.exit(f"記録が見つかりません: {ref}")


def read_arg(text, file):
    if text is not None:
        return text
    if file == "-":
        return sys.stdin.read()
    if file:
        return Path(file).read_text(encoding="utf-8")
    return None


def cmd_new(a):
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.topic):
        sys.exit("話題は kebab-case（英小文字・数字・ハイフン）で指定してください。例: setup-spec")
    CONV.mkdir(exist_ok=True)
    mmdd = a.date or datetime.date.today().strftime("%m%d")
    nums = [int(m.group(2)) for p in conv_files()
            if (m := NAME_RE.match(p.name)) and m.group(1) == mmdd]
    name = f"{mmdd}-{max(nums, default=0) + 1:02d}_{a.topic}.md"
    head = (
        "###### [toTopPage](../README.md)\n"
        "###### [toREADME](./README.md)\n"
        f"# 02_conversations/{name}\n"
        f"- `title`: {a.title or a.topic}\n"
        "- `url`  : \n"
    )
    if a.output:
        head += f"- `output`: [{a.output}](../{a.output})\n"
    (CONV / name).write_text(head + "\n" + END, encoding="utf-8")
    print(f"02_conversations/{name}")


def cmd_add(a):
    path = resolve(a.file, archive=False)  # 締めたサイクルの記録には書き足さない
    q = read_arg(a.q, a.q_file)
    ans = read_arg(a.a, a.a_file)
    if q is None or ans is None:
        sys.exit("質問（--q か --q-file）と回答（--a か --a-file）が必要です。")
    text = path.read_text(encoding="utf-8")
    if not text.rstrip().endswith(END.strip()):
        text = text.rstrip() + "\n\n" + END
    block = f"## Q. {a.q_title}\n{q.strip()}\n\n---\n### Answer\n{ans.strip()}\n"
    if a.changed:
        block += "\n作成・更新したファイル:\n" + "".join(f"- [{c}](../{c})\n" for c in a.changed)
    path.write_text(text.rstrip() + "\n" + block + "\n" + END, encoding="utf-8")
    n = len(split_qas(path.read_text(encoding="utf-8")))
    print(f"02_conversations/{path.name} Q{n}")


def cmd_toc(a):
    for p in sorted(conv_files(), key=lambda p: p.name):
        text = p.read_text(encoding="utf-8")
        print(f"{number_of(p)}  {title_of(text)}  ({p.name}){where_label(p)}")
        for n, title, _ in split_qas(text):
            print(f"    Q{n}  {title}")


def cmd_find(a):
    groups = [[w.lower() for w in word.split("|")] for word in a.words]
    hits = 0
    for p in conv_files():
        for n, title, body in split_qas(p.read_text(encoding="utf-8")):
            low = body.lower()
            if all(any(alt in low for alt in g) for g in groups):
                first = next((l.strip() for l in body.splitlines()[1:]
                              if any(alt in l.lower() for alt in groups[0])), "")
                print(f"{number_of(p)} Q{n}  {title}\n    {first[:100]}")
                hits += 1
    if not hits:
        print("該当なし")


def cmd_show(a):
    p = resolve(a.number)
    qas = split_qas(p.read_text(encoding="utf-8"))
    n = int(str(a.q).lstrip("Qq"))
    if not 1 <= n <= len(qas):
        sys.exit(f"{number_of(p)} の Q は 1〜{len(qas)} です。")
    print(f"# {number_of(p)} Q{n}（{p.relative_to(ROOT).as_posix()}）\n{qas[n - 1][2]}")


def cmd_where(a):
    target = Path(a.path)
    if (ROOT / target).exists():
        print(f"そのままあります: {target}")
        return
    found = []
    for p in ROOT.rglob("*"):
        if SKIP_DIRS & set(p.parts):
            continue
        if p.name == target.name or (target.stem and p.stem == target.stem):
            found.append(p.relative_to(ROOT))
    if found:
        print("候補:")
        for f in sorted(found):
            print(f"  {f}")
    else:
        print("見つかりません。削除されたか、名前が変わっています。ユーザーに確認してください。")


def main():
    ap = argparse.ArgumentParser(description="会話履歴の作成・追記・検索")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new", help="記録ファイルを作る")
    s.add_argument("topic"); s.add_argument("--title"); s.add_argument("--date"); s.add_argument("--output")
    s.set_defaults(f=cmd_new)
    s = sub.add_parser("add", help="Q&A を追記する")
    s.add_argument("--file", help="番号（例 1117-01）。省略すると最新")
    s.add_argument("--q-title", required=True)
    s.add_argument("--q"); s.add_argument("--q-file")
    s.add_argument("--a"); s.add_argument("--a-file")
    s.add_argument("--changed", action="append", help="作成・更新したファイル（複数可）")
    s.set_defaults(f=cmd_add)
    s = sub.add_parser("toc", help="一覧"); s.set_defaults(f=cmd_toc)
    s = sub.add_parser("find", help="検索"); s.add_argument("words", nargs="+"); s.set_defaults(f=cmd_find)
    s = sub.add_parser("show", help="1 つの Q&A を表示")
    s.add_argument("number"); s.add_argument("q"); s.set_defaults(f=cmd_show)
    s = sub.add_parser("where", help="パスの今の場所を探す"); s.add_argument("path"); s.set_defaults(f=cmd_where)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
