#!/usr/bin/env python3
"""既存のプロジェクト（進行中のリポジトリや作業フォルダ）に、このテンプレートの仕組みだけを入れる。標準ライブラリのみで動く。

始め方の「後付け」（adopt）で使う。既存のファイルは上書きしない。既定は試し（予定だけ出す）で、--apply で実行する。

  置くもの      : _tools/、_templates/、_examples/hearing/、HISTORY.md、.claude/skills/*、.claude/agents/*、
                  02_conversations/・05_evals/・04_logs/ の README.md
  既存があれば  : そのファイル・フォルダは置かない（「既存のまま」と表示する）
  CLAUDE.md     : なければ置く。あれば CLAUDE.template.md として置き、--link のときだけ、既存の CLAUDE.md の末尾に
                  取り込みの 1 行（@CLAUDE.template.md）を足す
  settings.json : なければ置く。あれば .claude/settings.template.json として置き、足りない権限を表示する（書き換えない）
  .gitignore    : 仕組みが要る行（秘密の情報、個人設定、Python のキャッシュ、一時フォルダ）のうち、足りないものだけを
                  末尾に足す。build/ などの汎用の行は、表示だけする
  名前の衝突    : _tools/ などが、テンプレートのものでない中身で既にあるときは、何も変えずに止める
  README.md     : 触らない
  --update      : 古い版のテンプレートで始めたプロジェクトを新しくする。テンプレートが持つもの（_tools/、_templates/、
                  _examples/hearing/ の中のファイル）は同じ名前のファイルを上書きし、足りないスキル・エージェント・
                  フォルダを足す。ファイルは消さない。同じ名前のスキル・エージェントで中身が違うものは、表示だけする

使い方:
  python3 _tools/adopt.py --target ../my-app            # 試し
  python3 _tools/adopt.py --target ../my-app --apply --link
  python3 _tools/adopt.py --target ../old-project --update          # 古い版のテンプレートを新しくする（試し）
その後、対象のフォルダで Claude Code を開き、/setup-project で始め方に「後付け」を選ぶ。
"""
import argparse
import filecmp
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TREES = ["_tools", "_templates", "_examples/hearing"]
FILES = ["HISTORY.md", "02_conversations/README.md", "05_evals/README.md", "04_logs/README.md"]
MARK = "# --- claude-project-template-ja ---"
# 既存のフォルダ・ファイルがテンプレートのものかを見分ける目印（ないときは名前がぶつかっているとみなして止める）
OWN = {"_tools": "_tools/setup.py", "_templates": "_templates/_SPEC.md",
       "_examples/hearing": "_examples/hearing/questions.json", "HISTORY.md": None}
# .gitignore に足すのは、仕組みが要る行だけ。ほかの行（build/ など）は、既存の使い方とぶつかりうるので表示だけする
GI_NEED = [".env", ".env.*", "!.env.example", "secrets/", ".claude/settings.local.json", "CLAUDE.local.md",
           "__pycache__/", "*.py[cod]", ".playwright-mcp/", "_to_delete/"]
SKIP = {"__pycache__", ".DS_Store"}


def ignore(_, names):
    return [n for n in names if n in SKIP or n.endswith(".pyc")]


def tree_updates(src_dir, dst_dir):
    """src_dir の中で、dst_dir にないか中身が違うファイルの一覧（消すものはない）。"""
    out = []
    for src in sorted(src_dir.rglob("*")):
        if src.is_dir() or SKIP & set(src.parts) or src.suffix == ".pyc":
            continue
        dst = dst_dir / src.relative_to(src_dir)
        if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
            out.append((src, dst, "足す" if not dst.exists() else "上書き"))
    return out


def clashes(target):
    """テンプレートと同じ名前で、中身が別物のフォルダ・ファイル。"""
    out = []
    for name, mark in OWN.items():
        dst = target / name
        if not dst.exists():
            continue
        if mark and not (target / mark).exists():
            out.append(f"{name}/（テンプレートの {mark} がない）")
        if mark is None and "conv.py" not in dst.read_text(encoding="utf-8", errors="ignore"):
            out.append(f"{name}（テンプレートの HISTORY.md ではない。CLAUDE.template.md の @HISTORY.md がこれを読み込んでしまう）")
    return out


def plan(target, link, update=False):
    acts, notes = [], []  # acts: (種類, 元, 先, 説明)
    for t in TREES:
        dst = target / t
        if dst.exists() and update:
            for src, d, how in tree_updates(ROOT / t, dst):
                acts.append(("更新する", src, d, how))
            continue
        acts.append(("既存のまま" if dst.exists() else "置く", ROOT / t, dst, "フォルダ"))
    for f in FILES:
        dst = target / f
        if dst.exists() and update and not filecmp.cmp(ROOT / f, dst, shallow=False):
            notes.append(f"{f} は新しい版と中身が違う（上書きしない。diff {ROOT / f} {dst} で見比べて、手で取り込む）")
        acts.append(("既存のまま" if dst.exists() else "置く", ROOT / f, dst, ""))
    for kind in ("skills", "agents"):
        for src in sorted((ROOT / ".claude" / kind).iterdir()):
            if src.name in SKIP:
                continue
            dst = target / ".claude" / kind / src.name
            if dst.exists() and update and (tree_updates(src, dst) if src.is_dir() else not filecmp.cmp(src, dst, shallow=False)):
                notes.append(f".claude/{kind}/{src.name} は新しい版と中身が違う（プロジェクトで直した可能性があるため上書きしない。"
                             f"テンプレートの同じ場所と diff -r で見比べて、手で取り込む）")
            acts.append(("既存のまま" if dst.exists() else "置く", src, dst, f"{kind} の同名あり" if dst.exists() else ""))
    for old, new in (("04_evals", "05_evals"), ("05_logs", "04_logs")):  # 旧い版のテンプレートのフォルダ名
        if (target / old).is_dir() and not (target / new).exists():
            notes.append(f"{old}/ は旧い版のフォルダ名。この版では {new}/。中身を引き継ぐなら、先に git mv {old} {new} を実行してから"
                         f"やり直す（先にやらないと、空の {new}/ ができて {old}/ と二重になる）")
    own = [n for n in ("SPEC.md", "BRIEF.md", "PLAYBOOK.md", "KICKOFF.md", "PROGRESS.md", "DECISIONS.md") if (target / n).exists()]
    if own and not update:
        notes.append(f"プロジェクトの {', '.join(own)} がある。setup.py はここで止まる。--force を付けると、"
                     "上書きする前に 04_logs/pre-setup-<日付>/ に写してから作り直す。写した中身は、新しい仕様の"
                     "「今の状態（後付け）」に移す")
    claude = target / "CLAUDE.md"
    if not claude.exists():
        acts.append(("置く", ROOT / "CLAUDE.md", claude, ""))
    else:
        acts.append(("置く", ROOT / "CLAUDE.md", target / "CLAUDE.template.md", "既存の CLAUDE.md は変えない"))
        if update:
            notes.append("CLAUDE.md は古い版のテンプレートから始めたものとして扱い、変えない。CLAUDE.template.md（新しい版）と"
                         "見比べて、要る行を手で取り込み、CLAUDE.template.md は消してよい（--link は使わない。ルールが二重になるため）")
        elif link:
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
    lines = [l for l in src.splitlines() if l.strip() and not l.startswith("#") and l not in have]
    want = [l for l in lines if l in GI_NEED]
    rest = [l for l in lines if l not in GI_NEED]
    if want:
        acts.append(("末尾に足す", None, gi, f"{len(want)} 行（{', '.join(want)}）"))
    if rest:
        notes.append(".gitignore に、テンプレートの汎用の行のうち次は足していない（既存の使い方とぶつかりうるため。"
                     f"要るものだけ手で足す）: {', '.join(rest)}")
    return acts, notes, want


def main():
    ap = argparse.ArgumentParser(description="既存のプロジェクトに、テンプレートの仕組みを入れる")
    ap.add_argument("--target", required=True, help="既存のプロジェクトのフォルダ")
    ap.add_argument("--apply", action="store_true", help="実行する（既定は試し）")
    ap.add_argument("--link", action="store_true", help="既存の CLAUDE.md の末尾に @CLAUDE.template.md を足す")
    ap.add_argument("--update", action="store_true", help="古い版のテンプレートの仕組み（_tools/ など）を新しくする")
    a = ap.parse_args()
    target = Path(a.target).resolve()
    if not target.is_dir():
        sys.exit(f"フォルダがありません: {a.target}")
    if target == ROOT:
        sys.exit("テンプレートそのものには入れられません。")
    if (target / "_tools" / "setup.py").exists() and (target / "_templates").exists() and not a.update:
        print("注意: すでにテンプレートの仕組みが入っているようです。既存のものは上書きしません。"
              "新しい版にするなら --update を付けてください。")
    bad = clashes(target)
    if bad:
        sys.exit("テンプレートと同じ名前で、別のものがあります。名前を変えるか移してから、やり直してください（何も変えていません）:\n  "
                 + "\n  ".join(bad))
    acts, notes, gi_lines = plan(target, a.link, a.update)
    print(f"{target} に入れます（{'実行' if a.apply else '試し。何も変えていません'}）")
    for kind, _, dst, note in acts:
        print(f"  {kind:　<5} {dst.relative_to(target)}" + (f"  — {note}" if note else ""))
    for n in notes:
        print(f"  注意  {n}")
    if not a.apply:
        print("\n実行するには --apply を付けてください。")
        return
    for kind, src, dst, _ in acts:
        if kind == "更新する":
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif kind == "置く":
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
    if a.update:
        print("\n新しくしました。次の一手: 対象のフォルダで python3 _tools/doctor.py を実行し、「注意」に出たスキル・CLAUDE.md・"
              "HISTORY.md を、テンプレートと見比べて手で取り込む（セットアップのやり直しは要らない）")
    else:
        print("\n入れました。次の一手: 対象のフォルダで Claude Code を開き、/setup-project で始め方に「後付け」を選ぶ")


if __name__ == "__main__":
    main()
