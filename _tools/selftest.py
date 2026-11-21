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


def t_checks(tmp):
    sample = ROOT / "_examples" / "craft-sample"
    print("checks：正例で合格する")
    ok(run(TOOLS / "check_cases.py", sample / "cases.csv").returncode == 0, "見本の cases.csv")
    ok(run(TOOLS / "check_skill.py", sample / "invoice-check").returncode == 0, "見本のスキル invoice-check")
    skills = sorted((ROOT / ".claude" / "skills").iterdir())
    r = run(TOOLS / "check_skill.py", *skills)
    ok(r.returncode == 0, f"テンプレートのスキル {len(skills)} 個" + ("" if r.returncode == 0 else f"（{r.stdout.strip()[-160:]}）"))
    good_spec = "## 合格条件\n1. 30fps を保つ（確認：計測スクリプト）\n2. 起動まで 3 秒以内\n"
    (tmp / "SPEC.md").write_text(good_spec, encoding="utf-8")
    ok(run(TOOLS / "check_spec.py", tmp / "SPEC.md").returncode == 0, "check_spec：記入済みの仕様")

    print("checks：負例で不合格になる")
    head = "id,kind,input,expected,result,evidence,note\n"
    neg_cases = {
        "負例がない": "C-1,正例,a,b,合格,,\n",
        "未実行がある": "C-1,正例,a,b,未実行,,\nC-2,負例,a,b,合格,,\n",
        "不合格がある": "C-1,正例,a,b,不合格,,\nC-2,負例,a,b,合格,,\n",
        "kind の誤り": "C-1,ふつう,a,b,合格,,\nC-2,負例,a,b,合格,,\n",
        "id の重複": "C-1,正例,a,b,合格,,\nC-1,負例,a,b,合格,,\n",
        "証拠のパスがない": "C-1,正例,a,b,合格,evals/none.md,\nC-2,負例,a,b,合格,,\n",
        "0 件": "",
    }
    for name, body in neg_cases.items():
        p = tmp / f"cases-{len(name)}-{abs(hash(name)) % 997}.csv"
        p.write_text(head + body, encoding="utf-8")
        ok(run(TOOLS / "check_cases.py", p).returncode == 1, f"check_cases：{name}")
    p = tmp / "cases-pending.csv"
    p.write_text(head + "C-1,正例,a,b,未実行,,\nC-2,負例,a,b,合格,,\n", encoding="utf-8")
    ok(run(TOOLS / "check_cases.py", p, "--allow-pending").returncode == 0, "check_cases：--allow-pending では未実行を警告にとどめる（正例）")

    neg_skills = {
        "frontmatter がない": "# 見出しだけ\n",
        "description がない": "---\nname: s1\n---\n本文\n",
        "name が不正": "---\nname: My_Skill\ndescription: 「試して」と言われたときに使う、試しのスキルの説明文です。\n---\n",
        "参照が切れている": "---\nname: s1\ndescription: 「試して」と言われたときに使う、試しのスキルの説明文です。\n---\n[基準](references/none.md)\n",
        "未記入が残る": "---\nname: s1\ndescription: 「試して」と言われたときに使う、試しのスキルの説明文です。\n---\n[要記入: 手順]\n",
    }
    for i, (name, body) in enumerate(neg_skills.items()):
        d = tmp / f"skill{i}" / "s1"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(body, encoding="utf-8")
        ok(run(TOOLS / "check_skill.py", d).returncode == 1, f"check_skill：{name}")
    d = tmp / "skill-empty" / "s1"
    d.mkdir(parents=True)
    ok(run(TOOLS / "check_skill.py", d).returncode == 1, "check_skill：SKILL.md がない")

    for name, body in {"未記入が残る": "## 合格条件\n1. [要記入: 合格条件]\n",
                       "数値も確かめ方もない": "## 合格条件\n1. 動きが滑らかである\n",
                       "11 個ある": "## 合格条件\n" + "".join(f"{i}. {i} 秒以内\n" for i in range(1, 12))}.items():
        p = tmp / "neg" / f"{abs(hash(name)) % 997}" / "SPEC.md"
        p.parent.mkdir(parents=True)
        p.write_text(body, encoding="utf-8")
        ok(run(TOOLS / "check_spec.py", p).returncode == 1, f"check_spec：{name}")


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
