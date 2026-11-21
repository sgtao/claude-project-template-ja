#!/usr/bin/env python3
"""サイクル（版）を締めて、記録を 04_logs/ に移し、次のサイクルの計画を始める。標準ライブラリのみで動く。

1 つのプロジェクトで v0.0.1 → v0.0.2 → … と改修を重ねるときに使う。`/next-cycle` スキルから呼ぶ。

  close <名前>  : 今のサイクルの記録を 04_logs/<名前>/ にまとめる。既定は試し（何も変えずに予定だけ出す）。
                  --apply で実行する。
                  写す（直下に残す）: 仕様のファイル、PROGRESS.md、DECISIONS.md、05_evals/cases.csv
                  移す（直下から消える）: PLAN.md、HANDOFF.md（旧い形）、MANUAL-CHECK.md、06_handoff/ のメモ、02_conversations/ の記録、
                                          05_evals/ の実行記録（cases.csv と README.md を除く）
                  05_evals/cases.csv は、写しの証拠のパスを移した先に直し、直下のほうは result を「未実行」、
                  evidence を空に戻す（前の版の結果は note に残す）。次の版で評価をやり直すため
                  --keep <番号> で、続けて書き足す会話の記録を残す（例 --keep 1121-02）
                  --merge で、すでにある 04_logs/<名前>/（版の途中で計画を置いていた場合など）に足す。
                  同じ名前のファイルがあれば止める
  start <名前>  : _templates/_PLAN.md から、次のサイクルの PLAN.md を作る
  list          : 締めたサイクルの一覧

使い方:
  python3 _tools/cycle.py close v0-0-1             # 試し
  python3 _tools/cycle.py close v0-0-1 --apply     # 実行
  python3 _tools/cycle.py start v0-0-2
"""
import argparse
import csv
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "04_logs"
SPEC_DOCS = ("SPEC.md", "BRIEF.md", "PLAYBOOK.md")
COPY = (*SPEC_DOCS, "PROGRESS.md", "DECISIONS.md", "LEDGER.csv")
MOVE = ("PLAN.md", "HANDOFF.md", "MANUAL-CHECK.md")
NAME_RE = re.compile(r"^[a-z0-9]+([.\-][a-z0-9]+)*$")
CONV_RE = re.compile(r"^(\d{4}-\d{2})_.+\.md$")


def snap_name(name, cycle):
    p = Path(name)
    return f"{p.stem}.{cycle}{p.suffix}"


def head_commit():
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%h %s"],
                           capture_output=True, text=True)
        return r.stdout.strip() or "（コミットなし）"
    except OSError:
        return "（git なし）"


def plan_close(cycle, keep):
    dest = LOGS / cycle
    acts = []  # (動作, 元, 先)
    for n in COPY:
        if (ROOT / n).is_file():
            acts.append(("写す", ROOT / n, dest / snap_name(n, cycle)))
    for n in MOVE:
        if (ROOT / n).is_file():
            acts.append(("移す", ROOT / n, dest / n))
    conv = ROOT / "02_conversations"
    for p in sorted(conv.glob("*.md")) if conv.is_dir() else []:
        m = CONV_RE.match(p.name)
        if m and m.group(1) not in keep:
            acts.append(("移す", p, dest / "conversations" / p.name))
    ho = ROOT / "06_handoff"
    for p in sorted(ho.glob("*.md")) if ho.is_dir() else []:
        if p.name != "README.md":
            acts.append(("移す", p, dest / "handoff" / p.name))
    ev = ROOT / "05_evals"
    for p in sorted(ev.iterdir()) if ev.is_dir() else []:
        if p.name in ("README.md", ".DS_Store", ".gitkeep"):
            continue
        if p.name == "cases.csv":
            acts.append(("写す", p, dest / "evals" / "cases.csv"))
        else:
            acts.append(("移す", p, dest / "evals" / p.name))
    return dest, acts


def roll_cases(root_csv, snap_csv, cycle):
    """締めた後の評価ケース：写しは証拠のパスを移した先に直し、直下は次の版のために未実行に戻す。"""
    with root_csv.open(encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        cols, rows = rd.fieldnames or [], list(rd)
    if not {"result", "evidence"} <= set(cols):
        return 0
    moved = f"04_logs/{cycle}/evals/"
    fix = lambda ev: ";".join(moved + s.strip()[len("05_evals/"):] if s.strip().startswith("05_evals/") else s.strip()
                              for s in ev.replace("；", ";").split(";")) if ev else ev
    snap = [{**r, "evidence": fix(r.get("evidence") or "")} for r in rows]
    if "note" not in cols:
        cols = [*cols, "note"]
    nxt = []
    for r in rows:
        old = (r.get("note") or "").strip()
        if (r.get("result") or "").strip() == "未実行" and old.startswith("前の版"):
            nxt.append(r)  # この版で評価していない。前の版への参照をそのまま残す
            continue
        prev = f"前の版 {cycle}: {r.get('result') or '未記入'}"
        if (r.get("evidence") or "").strip():
            prev += f"（証拠は 04_logs/{cycle}/evals/ の写しを参照）"
        nxt.append({**r, "result": "未実行", "evidence": "", "note": prev + (f" ｜ {old}" if old else "")})
    for path, data in ((snap_csv, snap), (root_csv, nxt)):
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(data)
    return len(rows)


def readme(cycle, acts, keep):
    rel = lambda p: p.relative_to(ROOT).as_posix()
    rows = "\n".join(f"| `{rel(d)}` | {a} | `{rel(s)}` |" for a, s, d in acts)
    kept = f"\n続けて書き足すため、直下に残した会話の記録：{', '.join(keep)}\n" if keep else ""
    return f"""# 04_logs/{cycle}/ — サイクル {cycle} の記録

締めた日：{datetime.date.today().isoformat()}　締めた時点のコミット：{head_commit()}

このフォルダは**読み取り専用の記録**として扱い、書き換えない。直すことがあれば、今のサイクルの記録に書く。
次のサイクルの計画（`PLAN.md`）の材料にする。

| ここにあるもの | 動作 | 元の場所 |
|---|---|---|
{rows}
{kept}
## 調べ方
- 会話：`python3 _tools/conv.py toc`・`find`・`show` は、このフォルダの `conversations/` も見る
- 仕様・進み具合・台帳の写しは、締めた時点で固定。今の正本は直下のファイル
"""


def cmd_close(a):
    if not NAME_RE.match(a.name):
        sys.exit("名前は英小文字・数字と . - で書いてください。例: v0-0-1、v1.2、2026q1")
    dest, acts = plan_close(a.name, set(a.keep or []))
    if dest.exists() and not a.merge:
        sys.exit(f"04_logs/{a.name}/ はすでにあります。別の名前にするか、そこに足すなら --merge を付けてください。")
    clash = [d.relative_to(ROOT).as_posix() for _, _, d in acts if d.exists()]
    if clash:
        sys.exit("同じ名前のファイルが 04_logs にすでにあります: " + ", ".join(clash))
    if not acts:
        sys.exit("移すものも写すものもありません。")
    print(f"サイクル {a.name} を締めます（{'実行' if a.apply else '試し。何も変えていません'}）")
    for act, s, d in acts:
        print(f"  {act}  {s.relative_to(ROOT)}  →  {d.relative_to(ROOT)}")
    if any(s.name == "cases.csv" for _, s, _ in acts):
        print("  戻す  05_evals/cases.csv（result を「未実行」、evidence を空に。前の版の結果は note に残す）")
    if not a.apply:
        print("\n実行するには --apply を付けてください。移すファイルは直下から消えます（git には残ります）。")
        return
    dest.mkdir(parents=True, exist_ok=True)
    for act, s, d in acts:
        d.parent.mkdir(parents=True, exist_ok=True)
        if act == "写す":
            shutil.copy2(s, d)
        else:
            shutil.move(str(s), str(d))
    cases = ROOT / "05_evals" / "cases.csv"
    n = roll_cases(cases, dest / "evals" / "cases.csv", a.name) if cases.is_file() and (dest / "evals" / "cases.csv").is_file() else 0
    if n:
        print(f"05_evals/cases.csv の {n} 件を「未実行」に戻しました（前の版の結果は note と 04_logs/{a.name}/evals/ にあります）")
    rd = dest / ("README_cycle.md" if (dest / "README.md").exists() else "README.md")
    rd.write_text(readme(a.name, acts, a.keep or []), encoding="utf-8")
    print(f"\n締めました: 04_logs/{a.name}/（{rd.name} に一覧）")
    print(f"次の一手: python3 _tools/cycle.py start <次の名前> で PLAN.md を作る")


def cmd_start(a):
    if not NAME_RE.match(a.name):
        sys.exit("名前は英小文字・数字と . - で書いてください。例: v0-0-2")
    plan = ROOT / "PLAN.md"
    if plan.exists():
        sys.exit("PLAN.md がすでにあります。前のサイクルを締めてから（cycle.py close）始めてください。")
    tpl = ROOT / "_templates" / "_PLAN.md"
    if not tpl.exists():
        sys.exit("ひな形がありません: _templates/_PLAN.md")
    prev = sorted((p for p in LOGS.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime) if LOGS.is_dir() else []
    doc = next((n for n in SPEC_DOCS if (ROOT / n).exists()), "SPEC.md")
    vals = {"CYCLE": a.name, "DATE": datetime.date.today().isoformat(), "DOC": doc,
            "PREV": f"04_logs/{prev[-1].name}/" if prev else "（前のサイクルなし）"}
    text = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: vals.get(m.group(1), f"[要記入: {m.group(1)}]"),
                  tpl.read_text(encoding="utf-8"))
    plan.write_text(text, encoding="utf-8")
    print(f"作成しました: PLAN.md（サイクル {a.name}、前のサイクルの記録: {vals['PREV']}）")


def cmd_list(a):
    if not LOGS.is_dir() or not any(LOGS.iterdir()):
        print("締めたサイクルはありません。")
        return
    for p in sorted(LOGS.iterdir(), key=lambda p: p.stat().st_mtime):
        if p.is_dir():
            n = len(list((p / "conversations").glob("*.md"))) if (p / "conversations").is_dir() else 0
            print(f"{p.name}  会話 {n} 件")


def main():
    ap = argparse.ArgumentParser(description="サイクルを締めて、次を始める")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("close", help="今のサイクルの記録を 04_logs/ にまとめる")
    s.add_argument("name"); s.add_argument("--apply", action="store_true")
    s.add_argument("--keep", action="append", help="直下に残す会話の番号（例 1121-02）")
    s.add_argument("--merge", action="store_true", help="すでにある 04_logs/<名前>/ に足す")
    s.set_defaults(f=cmd_close)
    s = sub.add_parser("start", help="次のサイクルの PLAN.md を作る"); s.add_argument("name"); s.set_defaults(f=cmd_start)
    s = sub.add_parser("list", help="締めたサイクルの一覧"); s.set_defaults(f=cmd_list)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
