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


def copy_template(dest):
    """テンプレートの仕組みだけを一時フォルダに写す（試しのプロジェクト）。"""
    for d in ("_tools", "_templates", "_examples/hearing"):
        shutil.copytree(ROOT / d, dest / d)
    for d in ("02_conversations", "04_evals", "05_logs"):
        (dest / d).mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / d / "README.md", dest / d / "README.md")
    return dest


def t_cycle(tmp):
    proj = copy_template(tmp / "proj")
    T = proj / "_tools"
    af = tmp / "a.json"
    af.write_text(json.dumps(base_answers("craft", "new"), ensure_ascii=False), encoding="utf-8")
    ok(run(T / "setup.py", "--answers", af).returncode == 0, "cycle：試しのプロジェクトを setup する")
    r1 = run(T / "conv.py", "new", "first-talk", "--title", "最初の会話", "--date", "0101")
    run(T / "conv.py", "add", "--q-title", "質問 1", "--q", "目印の質問 ZQX", "--a", "回答")
    r2 = run(T / "conv.py", "new", "keep-talk", "--date", "0101")
    ok(r1.returncode == 0 and r2.returncode == 0, "cycle：会話の記録を 2 件作る")
    (proj / "04_evals" / "0101-01_run").mkdir()
    (proj / "04_evals" / "0101-01_run" / "README.md").write_text("実行の記録\n", encoding="utf-8")
    (proj / "PLAN.md").write_text("# 計画\n", encoding="utf-8")

    print("cycle：試し（--apply なし）では何も変えない")
    before = sorted(p.relative_to(proj).as_posix() for p in proj.rglob("*") if p.is_file())
    r = run(T / "cycle.py", "close", "v0-0-1", "--keep", "0101-02")
    after = sorted(p.relative_to(proj).as_posix() for p in proj.rglob("*") if p.is_file())
    ok(r.returncode == 0 and before == after, "close の試しでファイルが変わらない")

    print("cycle：--apply で締める")
    r = run(T / "cycle.py", "close", "v0-0-1", "--keep", "0101-02", "--apply")
    log = proj / "05_logs" / "v0-0-1"
    ok(r.returncode == 0, "close --apply が通る" + (f"（{r.stderr.strip()[:120]}）" if r.returncode else ""))
    ok((log / "PLAYBOOK.v0-0-1.md").exists() and (proj / "PLAYBOOK.md").exists(), "仕様のファイルは写し（直下に残る）")
    ok((log / "PLAN.md").exists() and not (proj / "PLAN.md").exists(), "PLAN.md は移る")
    ok((log / "conversations" / "0101-01_first-talk.md").exists(), "会話の記録が移る")
    ok((proj / "02_conversations" / "0101-02_keep-talk.md").exists(), "--keep の会話は直下に残る")
    ok((log / "evals" / "0101-01_run" / "README.md").exists() and (proj / "04_evals" / "cases.csv").exists(),
       "実行記録は移り、cases.csv は残る")
    ok((log / "README.md").exists(), "05_logs/v0-0-1/README.md ができる")
    ok(run(T / "cycle.py", "close", "v0-0-1").returncode == 1, "同じ名前で 2 回締めると止まる（負例）")

    print("cycle：移した会話を conv.py で引ける")
    r = run(T / "conv.py", "show", "0101-01", "1")
    ok(r.returncode == 0 and "ZQX" in r.stdout, "conv.py show で移した記録を表示できる")
    r = run(T / "conv.py", "find", "ZQX")
    ok("0101-01 Q1" in r.stdout, "conv.py find で移した記録を見つける")
    r = run(T / "conv.py", "new", "third", "--date", "0101")
    ok(r.stdout.strip().endswith("0101-03_third.md"), f"移した記録と番号が重ならない（{r.stdout.strip()}）")

    print("cycle：版の途中で作ったフォルダに --merge で足す")
    pre = proj / "05_logs" / "v0-0-2"
    pre.mkdir()
    (pre / "README.md").write_text("先に置いた計画の説明\n", encoding="utf-8")
    ok(run(T / "cycle.py", "close", "v0-0-2").returncode == 1, "既存のフォルダには --merge なしでは足さない（負例）")
    r = run(T / "cycle.py", "close", "v0-0-2", "--merge", "--keep", "0101-02", "--apply")
    ok(r.returncode == 0 and (pre / "README_cycle.md").exists()
       and (pre / "README.md").read_text(encoding="utf-8") == "先に置いた計画の説明\n", "--merge で既存の README.md を残して足す")

    print("cycle：次の計画を始める")
    r = run(T / "cycle.py", "start", "v0-0-3")
    plan = proj / "PLAN.md"
    ok(r.returncode == 0 and plan.exists() and "{{" not in plan.read_text(encoding="utf-8")
       and "05_logs/v0-0-2/" in plan.read_text(encoding="utf-8"), "start で PLAN.md ができ、最後に締めた記録を指す")
    ok(run(T / "cycle.py", "start", "v0-0-4").returncode == 1, "PLAN.md があると start は止まる（負例）")


def t_adopt(tmp):
    tgt = tmp / "existing"
    (tgt / ".claude" / "skills" / "verify").mkdir(parents=True)
    keep = {"CLAUDE.md": "# 既存のルール\n- テストは pytest\n", "README.md": "# 既存の README\n",
            ".claude/settings.json": json.dumps({"permissions": {"allow": ["Bash(pytest*)"]}}),
            ".claude/skills/verify/SKILL.md": "---\nname: verify\ndescription: 既存の同名スキル\n---\n",
            ".gitignore": "node_modules/\n"}
    for f, body in keep.items():
        (tgt / f).write_text(body, encoding="utf-8")
    snap = {f: (tgt / f).read_text(encoding="utf-8") for f in keep}

    print("adopt：試し（--apply なし）では何も変えない")
    r = run(TOOLS / "adopt.py", "--target", tgt)
    files = sorted(p.relative_to(tgt).as_posix() for p in tgt.rglob("*") if p.is_file())
    ok(r.returncode == 0 and files == sorted(keep), "試しでファイルが増えない")

    print("adopt：--apply --link")
    r = run(TOOLS / "adopt.py", "--target", tgt, "--apply", "--link")
    ok(r.returncode == 0, "adopt.py --apply が通る" + (f"（{r.stderr.strip()[:120]}）" if r.returncode else ""))
    for f in ("README.md", ".claude/settings.json", ".claude/skills/verify/SKILL.md"):
        ok((tgt / f).read_text(encoding="utf-8") == snap[f], f"既存の {f} を上書きしない")
    claude = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
    ok(claude.startswith(snap["CLAUDE.md"]) and "@CLAUDE.template.md" in claude, "既存の CLAUDE.md は残し、取り込みの 1 行だけ足す")
    gi = (tgt / ".gitignore").read_text(encoding="utf-8")
    ok(gi.startswith("node_modules/") and gi.count("node_modules/") == 1 and ".env" in gi, ".gitignore は足りない行だけ足す")
    for f in ("CLAUDE.template.md", "HISTORY.md", "_tools/setup.py", "_templates/_PLAYBOOK.md",
              ".claude/skills/milestone/SKILL.md", ".claude/agents/reviewer.md", ".claude/settings.template.json",
              "05_logs/README.md", "_examples/hearing/questions.json"):
        ok((tgt / f).exists(), f"{f} を置く")
    ok("足りないもの" in r.stdout, "既存の settings.json に足りない権限を表示する")
    r2 = run(TOOLS / "adopt.py", "--target", tgt, "--apply", "--link")
    ok(r2.returncode == 0 and (tgt / "CLAUDE.md").read_text(encoding="utf-8").count("@CLAUDE.template.md") == 1,
       "2 回目は何も重ねない（取り込みの行は 1 つのまま）")

    print("adopt：入れた後に setup（始め方＝後付け）が通る")
    af = tmp / "a.json"
    af.write_text(json.dumps(base_answers("build", "adopt"), ensure_ascii=False), encoding="utf-8")
    r = run(tgt / "_tools" / "setup.py", "--answers", af)
    ok(r.returncode == 0 and "## 今の状態（後付け）" in (tgt / "SPEC.md").read_text(encoding="utf-8"),
       "後付けの SPEC.md ができる")
    ok(run(TOOLS / "adopt.py", "--target", ROOT).returncode == 1, "テンプレートそのものには入れない（負例）")

    print("adopt：--update で古い版の仕組みを新しくする")
    old = tmp / "old"
    copy_template(old)
    (old / "_tools" / "check_cases.py").unlink()
    (old / "_tools" / "setup.py").write_text("# 古い版\n", encoding="utf-8")
    (old / "_tools" / "my_check.py").write_text("# プロジェクトで足した検査\n", encoding="utf-8")
    (old / "CLAUDE.md").write_text("# 古い版のルール\n", encoding="utf-8")
    (old / ".claude" / "skills" / "verify").mkdir(parents=True)
    (old / ".claude" / "skills" / "verify" / "SKILL.md").write_text("---\nname: verify\ndescription: 直した版\n---\n", encoding="utf-8")
    r = run(TOOLS / "adopt.py", "--target", old, "--update", "--link", "--apply")
    ok(r.returncode == 0, "adopt.py --update --apply が通る")
    ok((old / "_tools" / "setup.py").read_text(encoding="utf-8") == (TOOLS / "setup.py").read_text(encoding="utf-8")
       and (old / "_tools" / "check_cases.py").exists(), "テンプレートが持つファイルは新しくなり、足りないものは足される")
    ok((old / "_tools" / "my_check.py").exists(), "プロジェクトで足したファイルは消さない")
    ok((old / "CLAUDE.md").read_text(encoding="utf-8") == "# 古い版のルール\n", "--update では CLAUDE.md に取り込みの行を足さない")
    ok("直した版" in (old / ".claude" / "skills" / "verify" / "SKILL.md").read_text(encoding="utf-8")
       and "中身が違う" in r.stdout, "直した同名のスキルは上書きせず、違いを表示する")


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
