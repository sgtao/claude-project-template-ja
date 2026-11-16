#!/usr/bin/env python3
"""ヒアリング形式の初期セットアップ。標準ライブラリのみで動く。

質問は _examples/hearing/questions.json、ひな形は _examples/templates/ にある。
答えから SPEC.md（制作）か BRIEF.md（知的作業）と、最初のプロンプト KICKOFF.md を作る。

使い方:
  python3 _tools/setup.py                         # 端末で対話
  python3 _tools/setup.py --answers answers.json  # 答えのファイルから（Claude や自動実行用）
  python3 _tools/setup.py --answers a.json --out /tmp/x  # 別の場所に出す（試し書き）
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "_examples"


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
            print(f"  {i}. {c['label']}")
        while True:
            raw = input("  番号 > ").strip()
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


def fill(text, ans):
    def rep(m):
        v = ans.get(m.group(1), "")
        return v if v else f"[要記入: {m.group(1)}]"
    return re.sub(r"\{\{([A-Z_]+)\}\}", rep, text)


def main():
    ap = argparse.ArgumentParser(description="ヒアリング形式の初期セットアップ")
    ap.add_argument("--answers", help="答えの JSON ファイル")
    ap.add_argument("--out", default=str(ROOT), help="出力先（既定はリポジトリのトップ）")
    ap.add_argument("--force", action="store_true", help="記入済みのファイルも上書きする")
    a = ap.parse_args()

    questions = load_questions()
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
    for key in ("WORK_TYPE", "MAIN_MODEL"):
        if ans.get(key):
            ans[key + "_LABEL"] = labels.get(key, {}).get(ans[key], ans[key])

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    build = ans["KIND"] == "build"
    doc = "SPEC.md" if build else "BRIEF.md"
    ans["DOC"] = doc
    plan = [
        (EX / "templates" / ("SPEC.template.md" if build else "BRIEF.template.md"), out / doc),
        (EX / "templates" / ("kickoff-build.md" if build else "kickoff-knowledge.md"), out / "KICKOFF.md"),
        (EX / "templates" / "PROGRESS.template.md", out / "PROGRESS.md"),
    ]
    for src, dst in plan:
        if dst.exists() and not a.force:
            old = dst.read_text(encoding="utf-8")
            if "{{" not in old and "セットアップ前" not in old:
                sys.exit(f"{dst.name} は記入済みです。上書きするなら --force を付けてください。")
        dst.write_text(fill(src.read_text(encoding="utf-8"), ans), encoding="utf-8")
    ans_dir = out / "_examples" / "answers"
    ans_dir.mkdir(parents=True, exist_ok=True)
    (ans_dir / "current.json").write_text(
        json.dumps(ans, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    other = "BRIEF.md" if build else "SPEC.md"
    print(f"\n作成しました: {doc} / KICKOFF.md / PROGRESS.md / _examples/answers/current.json")
    print(f"使わない {other} は、消しても残しても構いません。")
    print("次の一手: Claude Code を開き、KICKOFF.md の内容を最初のメッセージとして渡してください。")


if __name__ == "__main__":
    main()
