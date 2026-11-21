#!/usr/bin/env python3
"""スキル（SKILL.md のあるフォルダ）の形の検査。標準ライブラリのみで動く。

専門作業をスキルにしたときと、このテンプレートの .claude/skills/ を直したときに使う。
中身の良し悪しではなく、読み込まれない・呼ばれない・参照が切れている、を見つける。

不合格にすること:
  SKILL.md がない、先頭の frontmatter（--- で囲む）がない、name か description がない、
  name が英小文字・数字・ハイフン以外か 64 字超、description が 1024 字超、
  本文から参照したファイル（リンクと scripts/・references/・assets/・templates/ で始まるパス）がない、
  未記入の印（[要記入、{{KEY}}、TODO。`…` の中は除く）が残っている
警告にすること:
  name とフォルダ名の違い、description が 40 字未満、呼び出しの言葉（「…」）が 0 個、本文が 500 行超

使い方:
  python3 _tools/check_skill.py 03_outputs/my-skill
  python3 _tools/check_skill.py .claude/skills/*        # 複数
"""
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
PATH_RE = re.compile(r"`((?:scripts|references|assets|templates)/[^`\s]+)`")
TODO_RE = re.compile(r"\[要記入|\{\{[A-Z_]+\}\}|\bTODO\b")


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    meta, key = {}, None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if km:
            key = km.group(1)
            meta[key] = km.group(2).strip().strip("\"'")
        elif key and line.startswith((" ", "\t")):  # 折り返した値
            meta[key] = (meta[key] + " " + line.strip()).strip()
    for k, v in meta.items():
        if v in (">", "|", ">-", "|-"):
            meta[k] = ""
    return meta, text[m.end():]


def check(folder):
    fails, warns = [], []
    skill = folder / "SKILL.md" if folder.is_dir() else folder
    folder = skill.parent
    if not skill.is_file():
        return [f"SKILL.md がない: {skill}"], warns
    text = skill.read_text(encoding="utf-8")
    meta, body = frontmatter(text)
    if meta is None:
        return ["先頭に frontmatter（--- で囲んだ name と description）がない"], warns
    name, desc = meta.get("name", ""), meta.get("description", "")
    if not name:
        fails.append("name がない")
    elif not NAME_RE.match(name) or len(name) > 64:
        fails.append(f"name「{name}」は英小文字・数字・ハイフンで 64 字以内にする")
    elif name != folder.name:
        warns.append(f"name「{name}」とフォルダ名「{folder.name}」が違う")
    if not desc:
        fails.append("description がない（何をするか、どんな言葉で呼ばれたら使うかを書く）")
    else:
        if len(desc) > 1024:
            fails.append(f"description が {len(desc)} 字（1024 字以内）")
        if len(desc) < 40:
            warns.append(f"description が {len(desc)} 字と短い（呼び出しの言葉を足す）")
        if not re.findall(r"「[^」]+」", desc) and "when" not in desc.lower():
            warns.append("description に呼び出しの言葉（「…」）がない")
    lines = body.count("\n") + 1
    if lines > 500:
        warns.append(f"本文が {lines} 行（500 行以内が目安。詳細は references/ に分ける）")
    refs = {m.group(1) for m in LINK_RE.finditer(body) if not m.group(1).startswith(("http://", "https://", "mailto:"))}
    refs |= {m.group(1) for m in PATH_RE.finditer(body)}
    for r in sorted(refs):
        if "<" in r or "*" in r:
            continue
        if not (folder / r).exists():
            fails.append(f"参照したファイルがない: {r}")
    todo = TODO_RE.findall(re.sub(r"`[^`\n]*`", "", text))  # コードとして書いた言及は数えない
    if todo:
        fails.append(f"未記入の印が {len(todo)} 箇所: {', '.join(sorted(set(todo))[:4])}")
    return fails, warns


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("使い方: python3 _tools/check_skill.py <SKILL.md のあるフォルダ> [...]")
    total = 0
    for a in args:
        fails, warns = check(Path(a))
        for w in warns:
            print(f"  警告  {w}")
        for x in fails:
            print(f"  不合格 {x}")
        print(f"{a}: 不合格 {len(fails)} 件、警告 {len(warns)} 件")
        total += len(fails)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
