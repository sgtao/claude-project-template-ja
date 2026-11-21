#!/usr/bin/env python3
"""ヒアリング形式の初期セットアップ。標準ライブラリのみで動く。

質問は _examples/hearing/questions.json、ひな形は _templates/ にある。
答えをひな形に差し込み、リポジトリのトップに次のファイルを作る（ひな形の名前から先頭の _ を外す）。

  制作（build）       : SPEC.md、PROGRESS.md、DECISIONS.md、KICKOFF.md
  知的作業（knowledge）: BRIEF.md、LEDGER.csv、PROGRESS.md、DECISIONS.md、KICKOFF.md
  専門作業（craft）    : PLAYBOOK.md、04_evals/cases.csv、PROGRESS.md、DECISIONS.md、KICKOFF.md

DECISIONS.md、LEDGER.csv、04_evals/cases.csv は書き足していく台帳なので、すでにあれば --force でも上書きしない。

ひな形の書き方:
  {{KEY}}                     答えを入れる。答えがなければ [要記入: KEY]
  {{> _MODE.md}}              _templates/_MODE.md の中身をその場所に入れる（入れ子は 3 段まで）
  <!-- when KIND=build,craft MODE=fork -->  〜  <!-- end -->
                              条件（空白区切りはすべて満たす。カンマは「または」）に合うときだけ残す。入れ子はしない

使い方:
  python3 _tools/setup.py                         # 端末で対話
  python3 _tools/setup.py --answers answers.json  # 答えのファイルから（Claude や自動実行用）
  python3 _tools/setup.py --answers a.json --out /tmp/x  # 別の場所に出す（試し書き）
"""
import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "_examples"
TPL = ROOT / "_templates"
LEDGERS = {"DECISIONS.md", "LEDGER.csv", "04_evals/cases.csv"}  # 書き足していく台帳。あれば残す
DOCS = {"build": "SPEC.md", "knowledge": "BRIEF.md", "craft": "PLAYBOOK.md"}
SPEC_DOCS = tuple(DOCS.values())
LABELED = ("KIND", "MODE", "WORK_TYPE", "CRAFT_TYPE", "SYNC_POLICY", "COMMIT_POLICY", "MAIN_MODEL")


def plan_files(kind):
    """(ひな形, 出力するファイル名) の一覧。"""
    doc = DOCS[kind]
    files = [
        (TPL / f"_{doc}", doc),
        (TPL / f"_KICKOFF.{kind}.md", "KICKOFF.md"),
        (TPL / "_PROGRESS.md", "PROGRESS.md"),
        (TPL / "_DECISIONS.md", "DECISIONS.md"),
    ]
    if kind == "knowledge":
        files.append((TPL / "_LEDGER.csv", "LEDGER.csv"))
    if kind == "craft":
        files.append((TPL / "_cases.csv", "04_evals/cases.csv"))
    return doc, files


def load_questions():
    return json.loads((EX / "hearing" / "questions.json").read_text(encoding="utf-8"))["questions"]


def applies(q, ans):
    cond = q.get("when")
    return not cond or all(ans.get(k) in v for k, v in cond.items())


def ask(q):
    print(f"\n■ {q['ask']}")
    if q.get("example"):
        print(f"  例: {q['example']}")
    choices = q.get("choices")
    if choices:
        for i, c in enumerate(choices, 1):
            mark = "（既定）" if c["value"] == q.get("default") else ""
            print(f"  {i}. {c['label']}{mark}")
        while True:
            raw = input("  番号 > ").strip()
            if not raw and q.get("default"):
                return q["default"]
            if raw.isdigit() and 1 <= int(raw) <= len(choices):
                return choices[int(raw) - 1]["value"]
            print("  番号で答えてください。")
    while True:
        raw = input("  > ").strip()
        if raw or not q.get("required"):
            return raw or q.get("default", "")
        print("  必須の項目です。")


def validate(questions, ans):
    errors = []
    for q in questions:
        if not applies(q, ans):
            continue
        v = ans.get(q["key"], "")
        if q.get("required") and not v:
            errors.append(f"{q['key']}: 必須です（{q['ask']}）")
        if v and q.get("choices") and v not in [c["value"] for c in q["choices"]]:
            errors.append(f"{q['key']}: {v} は選択肢にありません")
    return errors


INCLUDE_RE = re.compile(r"\{\{>\s*([\w.\-]+)\s*\}\}")
WHEN_RE = re.compile(r"^\s*<!--\s*when\s+(.+?)\s*-->\s*$")
END_RE = re.compile(r"^\s*<!--\s*end\s*-->\s*$")


def include(text, depth=0):
    """{{> 名前}} を _templates/ のファイルの中身で置き換える。"""
    if depth > 3:
        sys.exit("ひな形の取り込み（{{> ...}}）が深すぎます。循環していないか確かめてください。")

    def rep(m):
        p = TPL / m.group(1)
        if not p.exists():
            sys.exit(f"ひな形がありません: _templates/{m.group(1)}")
        return include(p.read_text(encoding="utf-8").rstrip("\n"), depth + 1)
    return INCLUDE_RE.sub(rep, text)


def cond_ok(cond, ans):
    for term in cond.split():
        key, _, vals = term.partition("=")
        if ans.get(key) not in vals.split(","):
            return False
    return True


def select(text, ans, name="ひな形"):
    """<!-- when ... --> 〜 <!-- end --> を、答えに合うものだけ残す。"""
    out, keep, open_at = [], True, None
    for i, line in enumerate(text.splitlines(keepends=True), 1):
        m = WHEN_RE.match(line)
        if m:
            if open_at:
                sys.exit(f"{name} {i} 行目: when の中に when があります（{open_at} 行目から）")
            open_at, keep = i, cond_ok(m.group(1), ans)
            continue
        if END_RE.match(line):
            if not open_at:
                sys.exit(f"{name} {i} 行目: 対応する when のない end があります")
            open_at, keep = None, True
            continue
        if keep:
            out.append(line)
    if open_at:
        sys.exit(f"{name} {open_at} 行目: when が end で閉じられていません")
    return re.sub(r"\n{3,}", "\n\n", "".join(out))


def render(src, ans):
    return fill(select(include(src.read_text(encoding="utf-8")), ans, src.name), ans)


def fill(text, ans):
    def rep(m):
        v = ans.get(m.group(1), "")
        return v if v else f"[要記入: {m.group(1)}]"
    return re.sub(r"\{\{([A-Z_]+)\}\}", rep, text)


def main():
    ap = argparse.ArgumentParser(description="ヒアリング形式の初期セットアップ")
    ap.add_argument("--answers", help="答えの JSON ファイル")
    ap.add_argument("--out", default=str(ROOT), help="出力先（既定はリポジトリのトップ）")
    ap.add_argument("--force", action="store_true",
                    help="作成済みの SPEC.md／BRIEF.md／PLAYBOOK.md、KICKOFF.md、PROGRESS.md などを作り直す。"
                         "上書きする前に 05_logs/pre-setup-<日付>/ に写す（台帳は上書きしない）")
    a = ap.parse_args()

    questions = load_questions()
    done = [n for n in (*SPEC_DOCS, "KICKOFF.md", "PROGRESS.md") if (Path(a.out) / n).exists()]
    if done and not a.force:  # 答える前に止める（答えた後で無駄にしない）
        sys.exit(f"セットアップ済みです（{', '.join(done)} があります）。やり直すなら --force を付けてください"
                 "（上書きする前に、今のファイルを 05_logs/pre-setup-<日付>/ に写します）。")
    if a.answers:
        ans = json.loads(Path(a.answers).read_text(encoding="utf-8"))
    else:
        print("プロジェクトの初期設定を始めます。分からない項目は空のまま Enter で進めます。")
        ans = {}
        try:
            for q in questions:
                if applies(q, ans):
                    ans[q["key"]] = ask(q)
        except (EOFError, KeyboardInterrupt):
            sys.exit("\n中断しました。ファイルは変更していません。")
    for q in questions:  # 既定値を補う
        if applies(q, ans) and not ans.get(q["key"]) and q.get("default"):
            ans[q["key"]] = q["default"]
    errors = validate(questions, ans)
    if errors:
        sys.exit("答えに不備があります:\n  " + "\n  ".join(errors))

    ans["DATE"] = datetime.date.today().isoformat()
    labels = {q["key"]: {c["value"]: c["label"] for c in q.get("choices", [])} for q in questions}
    for key in LABELED:
        if ans.get(key):
            ans[key + "_LABEL"] = labels.get(key, {}).get(ans[key], ans[key])

    out = Path(a.out)
    kind = ans["KIND"]
    doc, files = plan_files(kind)
    ans["DOC"] = doc
    missing = [str(src.relative_to(ROOT)) for src, _ in files if not src.exists()]
    if missing:
        sys.exit("ひな形がありません: " + ", ".join(missing) + "（テンプレートから取り直してください）")

    # 書く前にすべて確かめる（途中で止まって、一部だけ書かれた状態にしない）
    written, kept, blocked = [], [], []
    for _, name in files:
        if (out / name).exists():
            if name in LEDGERS:
                kept.append(name)
            elif not a.force:
                blocked.append(name)
    if blocked:
        sys.exit(f"{', '.join(blocked)} はすでにあります。上書きするなら --force を付けてください。")

    out.mkdir(parents=True, exist_ok=True)
    over = [name for _, name in files if name not in kept and (out / name).exists()]
    if over:  # --force でも、上書きする前のファイルは消さずに写しておく
        bk = out / "05_logs" / f"pre-setup-{ans['DATE']}"
        n = 2
        while bk.exists():
            bk = out / "05_logs" / f"pre-setup-{ans['DATE']}-{n}"
            n += 1
        for name in over:
            (bk / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(out / name, bk / name)
        print(f"上書きする前のファイルを写しました: {bk.relative_to(out).as_posix()}/（{', '.join(over)}）")
    for src, name in files:
        if name in kept:
            continue
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_text(render(src, ans), encoding="utf-8")
        written.append(name)
    ans_dir = out / "_examples" / "answers"
    ans_dir.mkdir(parents=True, exist_ok=True)
    (ans_dir / "current.json").write_text(
        json.dumps(ans, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\n作成しました: {' / '.join(written)} / _examples/answers/current.json")
    if kept:
        print(f"すでにあったため残しました: {' / '.join(kept)}")
    for other in SPEC_DOCS:
        if other != doc and (out / other).exists():
            print(f"注意: 使わない {other} が残っています。不要なら消してください。")
    print("次の一手: Claude Code を開き、KICKOFF.md の枠の中を最初のメッセージとして渡してください。")


if __name__ == "__main__":
    main()
