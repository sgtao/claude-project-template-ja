#!/usr/bin/env python3
"""テンプレートそのものの自己検査。テンプレートを直したら実行する。標準ライブラリのみで動く。

一時フォルダの中だけで試し、リポジトリのファイルは変えない。

検査すること:
  setup   : 見本の答えと、対象 3 × 始め方 4 の 12 通りで setup.py が通り、未展開の記法が残らない。
            始め方ごとの節が、その始め方のときだけ出る。既存の見本の見出しが改修前から消えていない
  checks  : check_cases.py・check_skill.py・check_spec.py が、正例で合格、負例で不合格になる
  cycle   : cycle.py が会話と評価を 05_logs/ に移し、移した会話を conv.py で引ける
  adopt   : adopt.py が既存の CLAUDE.md・README.md・settings.json を上書きせず、仕組みを置く

使い方:
  python3 _tools/selftest.py              # すべて
  python3 _tools/selftest.py setup checks # 一部だけ
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "_tools"
KINDS = {"build": "SPEC.md", "knowledge": "BRIEF.md", "craft": "PLAYBOOK.md"}
MODES = ("new", "adopt", "migrate", "fork")
# 始め方ごとに、その始め方のときだけ出る見出し
MODE_MARK = {"adopt": "## 今の状態（後付け）", "migrate": "## 移行元と移行先", "fork": "## 複製元"}
LEFTOVER = re.compile(r"\{\{|<!--\s*(when|end)\b")
FAILS = []


def ok(cond, msg):
    print(f"  {'OK ' if cond else 'NG '} {msg}")
    if not cond:
        FAILS.append(msg)
    return cond


def run(*args, cwd=None, inp=None):
    return subprocess.run([sys.executable, *map(str, args)], cwd=cwd, input=inp,
                          capture_output=True, text=True)


def base_answers(kind, mode):
    a = {"PROJECT_NAME": f"試し {kind}-{mode}", "KIND": kind, "MODE": mode, "GOAL": "試しの目的",
         "DELIVERABLE": "試しの成果物", "MAIN_MODEL": "opus"}
    if kind == "knowledge":
        a["WORK_TYPE"] = "extract"
    if kind == "craft":
        a["CRAFT_TYPE"] = "both"
    if mode in ("adopt", "migrate"):
        a["CURRENT_STATE"] = "既存のリポジトリ"
    if mode == "migrate":
        a.update(MIGRATE_FROM="旧", MIGRATE_TO="新")
    if mode == "fork":
        a["UPSTREAM"] = "https://example.com/upstream"
    return a


def setup_into(tmp, answers, name):
    out = tmp / name
    af = tmp / f"{name}.json"
    af.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")
    r = run(TOOLS / "setup.py", "--answers", af, "--out", out)
    return out, r


def headings(path):
    return [l for l in path.read_text(encoding="utf-8").splitlines()
            if re.match(r"^#{1,3} ", l) and not l.startswith("# ")]


def t_setup(tmp):
    print("setup：見本の答え")
    for af in sorted((ROOT / "_examples" / "answers").glob("*.json")):
        if af.name == "current.json":
            continue
        ans = json.loads(af.read_text(encoding="utf-8"))
        out, r = setup_into(tmp, ans, "ex-" + af.stem)
        if not ok(r.returncode == 0, f"{af.name} で setup.py が通る" + (f"（{r.stderr.strip()[:120]}）" if r.returncode else "")):
            continue
        left = [f"{p.name}:{i}" for p in out.rglob("*.md") for i, l in
                enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if LEFTOVER.search(l)]
        ok(not left, f"{af.name} の出力に未展開の記法がない {left[:3]}")

    print("setup：改修前の見出しが残っている（browser-game・contract-review）")
    base = json.loads((TOOLS / "selftest_baseline.json").read_text(encoding="utf-8"))
    for key, hs in base.items():
        ex, name = key.split("/")
        p = tmp / f"ex-{ex}" / name
        missing = [h for h in hs if p.exists() and h not in headings(p)] if p.exists() else ["（ファイルがない）"]
        ok(not missing, f"{key} の見出し {len(hs)} 個が残る {missing[:3]}")

    print("setup：対象 3 × 始め方 4")
    for kind, doc in KINDS.items():
        for mode in MODES:
            out, r = setup_into(tmp, base_answers(kind, mode), f"m-{kind}-{mode}")
            tag = f"{kind}×{mode}"
            if not ok(r.returncode == 0, f"{tag} で setup.py が通る" + (f"（{r.stderr.strip()[:160]}）" if r.returncode else "")):
                continue
            files = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
            need = {doc, "KICKOFF.md", "PROGRESS.md", "DECISIONS.md"}
            need |= {"LEDGER.csv"} if kind == "knowledge" else set()
            need |= {"04_evals/cases.csv"} if kind == "craft" else set()
            others = set(KINDS.values()) - {doc}
            ok(need <= files and not (others & files), f"{tag} のファイル: {sorted(need - files) or 'すべてある'}")
            text = "\n".join((out / f).read_text(encoding="utf-8") for f in files if f.endswith(".md"))
            ok(not LEFTOVER.search(text), f"{tag} に未展開の記法がない")
            spec = (out / doc).read_text(encoding="utf-8")
            wrong = [m for md, m in MODE_MARK.items() if (m in spec) != (md == mode)]
            ok(not wrong, f"{tag} の {doc} の始め方の節が正しい {wrong}")
            ok("## 始め方" in spec, f"{tag} の {doc} に「## 始め方」がある")


def main():
    names = sys.argv[1:] or ["setup", "checks", "cycle", "adopt"]
    tests = {n[2:]: f for n, f in globals().items() if n.startswith("t_")}
    unknown = [n for n in names if n not in tests]
    if unknown:
        sys.exit(f"知らない検査: {unknown}（{', '.join(tests)}）")
    with tempfile.TemporaryDirectory() as d:
        for n in names:
            sub = Path(d) / n
            sub.mkdir()
            tests[n](sub)
    print(f"\n結果: NG {len(FAILS)} 件")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
