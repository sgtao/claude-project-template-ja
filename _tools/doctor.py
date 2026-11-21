#!/usr/bin/env python3
"""リポジトリの状態の点検。セットアップ直後と、作業の再開時に使う。標準ライブラリのみで動く。

使い方:
  python3 _tools/doctor.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# テンプレートに最初から入っているファイル
REQUIRED = ["README.md", "CLAUDE.md", "HISTORY.md", ".gitignore", ".claude/settings.json",
            "02_conversations/README.md", "_examples/hearing/questions.json",
            "_tools/conv.py", "_tools/setup.py", "_tools/check_spec.py", "_tools/check_cases.py",
            "_tools/check_skill.py", "_tools/selftest.py",
            "_templates/_SPEC.md", "_templates/_BRIEF.md", "_templates/_PROGRESS.md",
            "_templates/_DECISIONS.md", "_templates/_LEDGER.csv",
            "_templates/_KICKOFF.build.md", "_templates/_KICKOFF.knowledge.md",
            "_templates/_PLAYBOOK.md", "_templates/_KICKOFF.craft.md", "_templates/_cases.csv",
            "_templates/_MODE.md", "_templates/_KICKOFF.mode.md"]
# セットアップで作られるファイル（仕様のファイルごと）
CREATED = {"SPEC.md": ["PROGRESS.md", "DECISIONS.md", "KICKOFF.md"],
           "BRIEF.md": ["PROGRESS.md", "DECISIONS.md", "KICKOFF.md", "LEDGER.csv"],
           "PLAYBOOK.md": ["PROGRESS.md", "DECISIONS.md", "KICKOFF.md", "04_evals/cases.csv"]}


def main():
    ng = 0

    def report(ok, msg, hint=""):
        nonlocal ng
        ng += not ok
        print(f"  {'OK ' if ok else 'NG '} {msg}" + (f" → {hint}" if hint and not ok else ""))

    print("必要なファイル")
    for f in REQUIRED:
        report((ROOT / f).exists(), f, "テンプレートから取り直す")

    print("設定ファイルの形式")
    for f in [".claude/settings.json", ".mcp.json", ".mcp.json.example", "_examples/hearing/questions.json"]:
        p = ROOT / f
        if p.exists():
            try:
                json.loads(p.read_text(encoding="utf-8"))
                report(True, f"{f} は JSON として読める")
            except ValueError as e:
                report(False, f"{f} が JSON として読めない", str(e))

    print("セットアップ")
    active = [n for n in CREATED if (ROOT / n).exists()]
    report(bool(active), f"仕様のファイル: {', '.join(active) or 'まだない（セットアップ前）'}",
           "python3 _tools/setup.py か /setup-project を実行する")
    report(len(active) <= 1, "仕様のファイルは 1 つだけ", "使わないほうを消す")
    for f in sorted({f for n in active for f in CREATED[n]}):
        report((ROOT / f).exists(), f"{f}（セットアップで作られる）",
               f"_templates/_{Path(f).name} を写すか、python3 _tools/setup.py --force でやり直す")
    if active:
        r = subprocess.run([sys.executable, str(ROOT / "_tools" / "check_spec.py"), *active],
                           capture_output=True, text=True)
        report(r.returncode == 0, "合格条件の点検（check_spec.py）", "python3 _tools/check_spec.py で内容を見る")

    print("環境")
    report(sys.version_info >= (3, 9), f"Python {sys.version.split()[0]}（3.9 以上）")
    report((ROOT / ".git").exists(), "git の初期化", "git init && git add -A && git commit -m 'init'")
    convs = [p for p in (ROOT / "02_conversations").glob("*.md") if p.name != "README.md"]
    print(f"  --  会話の記録: {len(convs)} 件")

    print(f"\n結果: NG {ng} 件")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    main()
