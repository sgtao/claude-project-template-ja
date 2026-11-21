#!/usr/bin/env python3
"""既存のプロジェクト（進行中のリポジトリや作業フォルダ）に、このテンプレートの仕組みだけを入れる。標準ライブラリのみで動く。

始め方の「後付け」（adopt）で使う。既存のファイルは上書きしない。既定は試し（予定だけ出す）で、--apply で実行する。

  置くもの      : _tools/、_templates/、_examples/hearing/、HISTORY.md、.claude/skills/*、.claude/agents/*、
                  02_conversations/・04_evals/・05_logs/ の README.md
  既存があれば  : そのファイル・フォルダは置かない（「既存のまま」と表示する）
  CLAUDE.md     : なければ置く。あれば CLAUDE.template.md として置き、--link のときだけ、既存の CLAUDE.md の末尾に
                  取り込みの 1 行（@CLAUDE.template.md）を足す
  settings.json : なければ置く。あれば .claude/settings.template.json として置き、足りない権限を表示する（書き換えない）
  .gitignore    : 足りない行だけを末尾に足す
  README.md     : 触らない

使い方:
  python3 _tools/adopt.py --target ../my-app            # 試し
  python3 _tools/adopt.py --target ../my-app --apply --link
その後、対象のフォルダで Claude Code を開き、/setup-project で始め方に「後付け」を選ぶ。
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TREES = ["_tools", "_templates", "_examples/hearing"]
FILES = ["HISTORY.md", "02_conversations/README.md", "04_evals/README.md", "05_logs/README.md"]
MARK = "# --- claude-project-template-ja ---"
SKIP = {"__pycache__", ".DS_Store"}


def ignore(_, names):
    return [n for n in names if n in SKIP or n.endswith(".pyc")]


def plan(target, link):
    acts, notes = [], []  # acts: (種類, 元, 先, 説明)
    for t in TREES:
        dst = target / t
        acts.append(("既存のまま" if dst.exists() else "置く", ROOT / t, dst, "フォルダ"))
    for f in FILES:
        dst = target / f
        acts.append(("既存のまま" if dst.exists() else "置く", ROOT / f, dst, ""))
    for kind in ("skills", "agents"):
        for src in sorted((ROOT / ".claude" / kind).iterdir()):
            if src.name in SKIP:
                continue
            dst = target / ".claude" / kind / src.name
            acts.append(("既存のまま" if dst.exists() else "置く", src, dst, f"{kind} の同名あり" if dst.exists() else ""))
    claude = target / "CLAUDE.md"
    if not claude.exists():
        acts.append(("置く", ROOT / "CLAUDE.md", claude, ""))
    else:
        acts.append(("置く", ROOT / "CLAUDE.md", target / "CLAUDE.template.md", "既存の CLAUDE.md は変えない"))
        if link:
            if "@CLAUDE.template.md" in claude.read_text(encoding="utf-8"):
                notes.append("CLAUDE.md はすでに @CLAUDE.template.md を取り込んでいる")
            else:
                acts.append(("末尾に足す", None, claude, "@CLAUDE.template.md の 1 行"))
        else:
            notes.append("既存の CLAUDE.md に、このテンプレートのルールを読ませるには、末尾に「@CLAUDE.template.md」を"
                         "1 行足す（--link で自動）。食い違うルールは、既存のほうを優先する")
    st = target / ".claude" / "settings.json"
    if not st.exists():
        acts.append(("置く", ROOT / ".claude" / "settings.json", st, ""))
    else:
        acts.append(("置く", ROOT / ".claude" / "settings.json", target / ".claude" / "settings.template.json",
                     "既存の settings.json は変えない"))
        try:
            have = json.loads(st.read_text(encoding="utf-8")).get("permissions", {})
            want = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["permissions"]
            for k, vals in want.items():
                miss = [v for v in vals if v not in have.get(k, [])]
                if miss:
                    notes.append(f"settings.json の permissions.{k} に足りないもの: {', '.join(miss)}")
        except (ValueError, KeyError) as e:
            notes.append(f"既存の settings.json を読めない（{e}）。手で見比べる")
    gi = target / ".gitignore"
    have = set(gi.read_text(encoding="utf-8").splitlines()) if gi.exists() else set()
    src = (ROOT / ".gitignore").read_text(encoding="utf-8").split("# local settings")[0]  # 以降はテンプレートの手元だけの行
    want = [l for l in src.splitlines() if l.strip() and not l.startswith("#") and l not in have]
    if want:
        acts.append(("末尾に足す", None, gi, f"{len(want)} 行（{', '.join(want[:4])}{' …' if len(want) > 4 else ''}）"))
    return acts, notes, want


def main():
    ap = argparse.ArgumentParser(description="既存のプロジェクトに、テンプレートの仕組みを入れる")
    ap.add_argument("--target", required=True, help="既存のプロジェクトのフォルダ")
    ap.add_argument("--apply", action="store_true", help="実行する（既定は試し）")
    ap.add_argument("--link", action="store_true", help="既存の CLAUDE.md の末尾に @CLAUDE.template.md を足す")
    a = ap.parse_args()
    target = Path(a.target).resolve()
    if not target.is_dir():
        sys.exit(f"フォルダがありません: {a.target}")
    if target == ROOT:
        sys.exit("テンプレートそのものには入れられません。")
    if (target / "_tools" / "adopt.py").exists() and (target / "_templates").exists():
        print("注意: すでにテンプレートの仕組みが入っているようです。既存のものは上書きしません。")
    acts, notes, gi_lines = plan(target, a.link)
    print(f"{target} に入れます（{'実行' if a.apply else '試し。何も変えていません'}）")
    for kind, _, dst, note in acts:
        print(f"  {kind:　<5} {dst.relative_to(target)}" + (f"  — {note}" if note else ""))
    for n in notes:
        print(f"  注意  {n}")
    if not a.apply:
        print("\n実行するには --apply を付けてください。")
        return
    for kind, src, dst, _ in acts:
        if kind == "置く":
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, ignore=ignore)
            else:
                shutil.copy2(src, dst)
        elif kind == "末尾に足す" and dst.name == "CLAUDE.md":
            text = dst.read_text(encoding="utf-8").rstrip("\n")
            dst.write_text(text + "\n\n## プロジェクトの進め方（テンプレート）\n@CLAUDE.template.md\n", encoding="utf-8")
        elif kind == "末尾に足す" and dst.name == ".gitignore":
            text = dst.read_text(encoding="utf-8").rstrip("\n") + "\n\n" if dst.exists() else ""
            dst.write_text(text + MARK + "\n" + "\n".join(gi_lines) + "\n", encoding="utf-8")
    print("\n入れました。次の一手: 対象のフォルダで Claude Code を開き、/setup-project で始め方に「後付け」を選ぶ")


if __name__ == "__main__":
    main()
