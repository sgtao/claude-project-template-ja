#!/usr/bin/env python3
"""成果物のフォルダ（03_outputs/ の中）に、最初の .gitignore を作る。標準ライブラリのみ。

選び方（上から順に当てはめる）:
  1. 複製して改造（MODE=fork）で、複製元に .gitignore がある → それを土台にする（優先）。
     テンプレートの補完は「秘密の情報」「Claude の個人設定」の足りない行だけ
  2. 制作（KIND=build）で言語・技術が分かる → github/gitignore の該当ファイル + テンプレートの補完
     （言語は 引数 --langs > 答え GI_LANGS > フォルダの中身 > 答え STACK の語 の順に決める）
  3. それ以外（知的作業・専門作業、言語が決まらない制作）→ テンプレートの .gitignore（_templates/_gitignore.template）

github/gitignore は実行時にネットから取る。取れないとき（オフライン、失敗）は
_templates/gitignore/ の同梱の写しで代わりにする。どちらを使ったかは先頭のコメントと表示に出る。
すでに .gitignore があるときは作らない（--force なら 04_logs/pre-gitignore-<日付>/ に写してから作り直す）。

置き場所: 答えの TARGET_DIR（03_outputs/ の中のフォルダ。ファイル名なら親）。
          03_outputs/ そのもの、または未指定なら 03_outputs/ の直下に 1 つ作る。

使い方:
  python3 _tools/gitignore.py                              # _examples/answers/current.json の答えから
  python3 _tools/gitignore.py --dir 03_outputs/my-app --langs Python,Node
  python3 _tools/gitignore.py --dir 03_outputs/my-app --upstream 01_sources/orig   # 複製元の .gitignore を優先
  python3 _tools/gitignore.py --dir 03_outputs/my-app --langs Go --force            # 作り直し
  python3 _tools/gitignore.py --list                       # 選べる言語
  環境変数 GITIGNORE_OFFLINE=1 か --offline: ネットを使わず、同梱の写しだけを使う
"""
import argparse
import datetime
import json
import os
import re
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "_templates"
BUNDLE = TPL / "gitignore"
BASE_URL = "https://raw.githubusercontent.com/github/gitignore/main/"
TIMEOUT = 8

# 別名 → github/gitignore のファイル名（拡張子なし）。小文字で引く
ALIASES = {
    "python": "Python", "py": "Python", "django": "Python", "flask": "Python", "fastapi": "Python",
    "node": "Node", "nodejs": "Node", "node.js": "Node", "javascript": "Node", "js": "Node",
    "typescript": "Node", "ts": "Node", "react": "Node", "vue": "Node", "svelte": "Node",
    "nextjs": "Node", "next.js": "Node", "nuxt": "Node",
    "vite": "Node", "three.js": "Node", "threejs": "Node",
    "go": "Go", "golang": "Go", "rust": "Rust", "java": "Java", "kotlin": "Android", "android": "Android",
    "swift": "Swift", "swiftui": "Swift", "ios": "Swift", "ruby": "Ruby", "c": "C",
    "c++": "C++", "cpp": "C++", "dart": "Dart", "flutter": "Dart", "unity": "Unity",
    "terraform": "Terraform", "c#": "VisualStudio", "csharp": "VisualStudio", "dotnet": "VisualStudio",
    ".net": "VisualStudio", "visualstudio": "VisualStudio",
}
# フォルダの中身から言語を見つける目印（ファイル名 or 拡張子）
MARKERS = [
    ("package.json", "Node"), ("pyproject.toml", "Python"), ("requirements.txt", "Python"), ("setup.py", "Python"),
    ("go.mod", "Go"), ("Cargo.toml", "Rust"), ("pom.xml", "Java"), ("build.gradle", "Java"),
    ("Package.swift", "Swift"), ("Gemfile", "Ruby"), ("pubspec.yaml", "Dart"), ("main.tf", "Terraform"),
    (".py", "Python"), (".ts", "Node"), (".js", "Node"), (".go", "Go"), (".rs", "Rust"), (".swift", "Swift"),
    (".rb", "Ruby"), (".java", "Java"), (".dart", "Dart"), (".tf", "Terraform"), (".cs", "VisualStudio"),
]
FILE_EXT = re.compile(r"\.(md|txt|csv|tsv|json|ya?ml|html?|pdf|docx?|xlsx?|pptx?|png|jpe?g|svg|gif|mp4|py|js|ts|sh)$", re.I)
ANSWERS = ROOT / "_examples" / "answers" / "current.json"


def canonical(name):
    """入力の語 → github/gitignore のファイル名（拡張子なし）。分からなければ None。"""
    key = name.strip().lower()
    if key in ALIASES:
        return ALIASES[key]
    for p in BUNDLE.glob("*.gitignore"):
        if p.stem.lower() == key:
            return p.stem
    return None


def bundled_names():
    return sorted(p.stem for p in BUNDLE.glob("*.gitignore"))


SPLIT = r"[,、，/・\s]+|と|および"
NAME_OK = re.compile(r"^[A-Za-z][A-Za-z0-9+#.\-]*$")


def parse_langs(text):
    """「Python, Node」「Python と Flask」などから、分かる言語を順に取り出す。知らない語は unknown に残す。"""
    out, unknown = [], []
    for w in re.split(SPLIT, text or ""):
        if not w:
            continue
        c = canonical(w)
        if c:
            if c not in out:
                out.append(c)
        else:
            unknown.append(w)
    return out, unknown


def scan_stack(text):
    """自由記述の STACK から、言語の語（単語として）を拾う。"""
    out = []
    for w, c in ALIASES.items():
        if len(w) <= 2 and w != "c#":  # c、go、js、ts、py などの短い語は、普通の語や略語と紛れるので拾わない
            continue
        pat = r"(?<![A-Za-z0-9+#.])" + re.escape(w) + r"(?![A-Za-z0-9+#])"
        if re.search(pat, text or "", re.I) and c not in out:
            out.append(c)
    return out


def detect(d):
    """フォルダの中身（3 階層まで）から言語を見つける。"""
    out = []
    if not d.is_dir():
        return out
    for p in sorted(d.rglob("*")):
        if len(p.relative_to(d).parts) > 3 or any(x in {"node_modules", ".git", ".venv"} for x in p.parts):
            continue
        if not p.is_file():
            continue
        for mark, c in MARKERS:
            if (p.name == mark or (mark.startswith(".") and p.suffix == mark)) and c not in out:
                out.append(c)
    return out


NET_DOWN = False  # 一度ネットに失敗したら、この実行ではもう試さない（言語の数だけ待たない）


def fetch(name, offline):
    """(本文, 取得元の説明)。ネットを先に、だめなら同梱の写し。どちらもなければ (None, 理由)。"""
    global NET_DOWN
    offline = offline or os.environ.get("GITIGNORE_OFFLINE") == "1"
    why = "オフライン指定" if offline else ("先の取得に失敗したため試さない" if NET_DOWN else "")
    offline = offline or NET_DOWN
    if not offline:
        base = os.environ.get("GITIGNORE_BASE_URL", BASE_URL)
        url = base + urllib.parse.quote(name) + ".gitignore"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "claude-project-template"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read().decode("utf-8"), f"取得 {url}"
        except Exception as e:  # ネットの失敗は同梱の写しで代える
            why = f"取得に失敗（{type(e).__name__}）"
            NET_DOWN = True
    p = BUNDLE / f"{name}.gitignore"
    if p.exists():
        return p.read_text(encoding="utf-8"), f"同梱の写し _templates/gitignore/{name}.gitignore（{why}）"
    return None, f"{name}: {why}、同梱の写しもない"


def sections():
    """_gitignore.template を、節の名前 → 行のリストにする（#@ 名前 で始まる）。"""
    out, cur = {}, None
    for line in (TPL / "_gitignore.template").read_text(encoding="utf-8").splitlines():
        if line.startswith("#@ "):
            cur = line[3:].strip()
            out[cur] = []
        elif cur:
            out[cur].append(line)
    return out


def patterns(lines):
    return {l.strip() for l in lines if l.strip() and not l.lstrip().startswith("#")}


def add_section(have, title, lines):
    """have にない行だけを、title のコメントつきで返す。足す行がなければ空。"""
    out, pending = [], []
    for l in lines:
        s = l.strip()
        if not s:
            if out and out[-1] != "":
                pending = [""]
            continue
        if s.startswith("#"):
            pending = (pending or []) + [l]
            continue
        if s in have or any(h.startswith("!") and h[1:].startswith(s.rstrip("/")) for h in have):
            continue  # すでにある行、または言語別の否定の行（!.vscode/settings.json など）が効かなくなる行は足さない
        out += pending + [l]
        pending = []
        have.add(s)
    while out and out[-1] == "":
        out.pop()
    return ([f"# ---- {title} ----", *out, ""] if out else [])


def resolve_dir(root, target_dir):
    """TARGET_DIR → .gitignore を置くフォルダ（03_outputs/ の中）。置けない指定なら (None, 理由)。

    答えは「03_outputs/my-plugin/（別の git リポジトリにする）」のように説明つきなので、
    03_outputs/ で始まるパスの部分だけを取り出す。<名前> のような未定の部分は、その手前のフォルダまでにする。
    """
    t = (target_dir or "").strip().strip("`")
    if not t:
        return root / "03_outputs", ""
    p = Path(t)
    if p.is_absolute():
        try:
            t = p.relative_to(root).as_posix()
        except ValueError:
            return None, f"{t} はこのリポジトリの外です"
    m = re.search(r"(?<![A-Za-z0-9_./-])(?:\./)?(03_outputs(?:/[^\s（()）`、，,。]*)?)", t)
    if not m:
        return None, f"「{t}」は 03_outputs/ の中ではないため、成果物の .gitignore は作りません（もとのリポジトリの .gitignore を使う）"
    parts = []
    for seg in m.group(1).split("/"):
        if not seg or "<" in seg or ">" in seg:
            break
        parts.append(seg)
    p = Path(*parts)
    if FILE_EXT.search(p.name) and len(p.parts) > 1:  # ファイル名なら親のフォルダ（my.app のような名前はフォルダ）
        p = p.parent
    if ".." in p.parts:
        return None, f"{t} に .. は使えません"
    return root / p, ""


def find_upstream(root, upstream):
    """複製元（パス or URL）→ ローカルのフォルダ。なければ None。"""
    u = (upstream or "").strip().strip("`")
    if not u:
        return None
    for cand in [Path(u), root / u]:
        if cand.is_dir():
            return cand
    base = re.sub(r"\.git$", "", u.rstrip("/").split("/")[-1])
    cand = root / "01_sources" / base
    return cand if base and cand.is_dir() else None


def build_text(root, d, kind, mode, langs_arg, answers, upstream, offline):
    """(本文, 説明の行のリスト, 実際に使った選び方)。"""
    notes = []
    sec = sections()
    safety = sec.get("safety", [])
    # 1. 複製元の .gitignore を優先
    if mode == "fork":
        up = find_upstream(root, upstream or answers.get("UPSTREAM", ""))
        if up and (up / ".gitignore").is_file():
            body = (up / ".gitignore").read_text(encoding="utf-8").rstrip("\n").splitlines()
            have = patterns(body)
            extra = add_section(have, "テンプレートの補完（秘密の情報と個人設定のうち、足りない行だけ）", safety)
            head = [f"# 複製元の .gitignore（{up.relative_to(root) if up.is_relative_to(root) else up}）を優先して使う"]
            notes.append(f"複製元の .gitignore を土台にしました（{up}）。補完した行: {len(patterns(extra))} 行")
            return "\n".join([*head, *body, "", *extra]).rstrip("\n") + "\n", notes, "複製元の .gitignore を優先"
        notes.append("複製元の .gitignore が見つからないため、通常の選び方（言語 or テンプレート）に切り替えました")
    # 2. 制作 → github/gitignore
    langs, unknown = [], []
    if langs_arg:
        langs, unknown = parse_langs(langs_arg)
    elif kind == "build":
        langs, unknown = parse_langs(answers.get("GI_LANGS", ""))
        if not langs:
            langs = detect(d)
            if langs:
                notes.append(f"フォルダの中身から言語を判定しました: {', '.join(langs)}")
        if not langs:
            langs = scan_stack(answers.get("STACK", ""))
            if langs:
                notes.append(f"答えの STACK から言語を拾いました: {', '.join(langs)}")
    # 別名や同梱にない名前でも、github/gitignore のファイル名らしければ取りにいく（ネットが使えれば取れる）
    langs += [u for u in unknown if NAME_OK.match(u) and u not in langs]
    bad = [u for u in unknown if not NAME_OK.match(u)]
    if bad:
        notes.append(f"言語として読めない語は使っていません: {', '.join(bad)}（--list で選べる言語を見る）")
    parts, used = [], []
    for name in langs:
        text, src = fetch(name, offline)
        if text is None:
            notes.append(f"{src}（この言語は飛ばしました）")
            continue
        used.append(name)
        parts.append((name, text.rstrip("\n").splitlines(), src))
        notes.append(f"{name}: {src}")
    if used:
        have, out = set(), []
        for name, lines, src in parts:
            out += [f"# ---- github/gitignore: {name}（{src.split('（')[0].split(' ')[0]}） ----", *lines, ""]
            have |= patterns(lines)
        for key, title in (("safety", "テンプレートの補完: 秘密の情報と個人設定"), ("extras", "テンプレートの補完: 一時ファイル・大きな生成物・OS とエディタ")):
            out += add_section(have, title, sec.get(key, []))
        return "\n".join(out).rstrip("\n") + "\n", notes, "github/gitignore の言語別 + テンプレートの補完"
    # 3. テンプレートの .gitignore
    if kind == "build" and not langs_arg:
        notes.append("言語が決まらなかったため、テンプレートの .gitignore にしました。"
                     "言語が決まったら --langs <言語> --force で作り直してください")
    have, out = set(), []
    for key, title in (("safety", "秘密の情報と個人設定"), ("extras", "一時ファイル・大きな生成物・OS とエディタ"),
                       ("basic", "Python と Node の基本")):
        out += add_section(have, f"テンプレート: {title}", sec.get(key, []))
    return "\n".join(out).rstrip("\n") + "\n", notes, "テンプレートの .gitignore"


def create(root, target_dir=None, langs="", kind="", mode="", upstream="", answers=None, offline=False, force=False):
    """作った .gitignore のパスと、説明の行のリストを返す。作らなかったときのパスは None。"""
    root = Path(root)
    answers = answers or {}
    kind = kind or answers.get("KIND", "")
    mode = mode or answers.get("MODE", "")
    d, why = resolve_dir(root, target_dir if target_dir is not None else answers.get("TARGET_DIR", ""))
    if d is None:
        return None, [why]
    dest = d / ".gitignore"
    if dest.exists() and not force:
        return None, [f"{dest.relative_to(root)} はすでにあるため作りません（作り直すなら --force）"]
    text, notes, how = build_text(root, d, kind, mode, langs, answers, upstream, offline)
    today = datetime.date.today().isoformat()
    rel = d.relative_to(root).as_posix()
    head = (f"# .gitignore（{today} に _tools/gitignore.py が作成。選び方: {how}）\n"
            f"# 直してよい。作り直すときは python3 _tools/gitignore.py --dir {rel} --langs <言語> --force（今の版は 04_logs/ に写される）\n\n")
    d.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        bk = root / "04_logs" / f"pre-gitignore-{today}" / rel
        n = 2
        while bk.exists():
            bk = root / "04_logs" / f"pre-gitignore-{today}-{n}" / rel
            n += 1
        bk.mkdir(parents=True)
        shutil.copy2(dest, bk / ".gitignore")
        notes.append(f"作り直す前の版を写しました: {bk.relative_to(root).as_posix()}/.gitignore")
    dest.write_text(head + text, encoding="utf-8")
    return dest, notes


def main():
    ap = argparse.ArgumentParser(description="成果物のフォルダに最初の .gitignore を作る")
    ap.add_argument("--dir", help="作るフォルダ（03_outputs/ の中）。省略すると答えの TARGET_DIR")
    ap.add_argument("--langs", default="", help="言語・技術（カンマ区切り。例: Python,Node）")
    ap.add_argument("--kind", default="", choices=["", "build", "knowledge", "craft"])
    ap.add_argument("--mode", default="", choices=["", "new", "adopt", "migrate", "fork"])
    ap.add_argument("--upstream", default="", help="複製元のフォルダ（fork のとき、その .gitignore を優先）")
    ap.add_argument("--root", default=str(ROOT), help="作る先のリポジトリ（既定はこのリポジトリ）")
    ap.add_argument("--offline", action="store_true", help="ネットを使わず、同梱の写しだけを使う")
    ap.add_argument("--force", action="store_true", help="すでにあっても作り直す（今の版は 04_logs/ に写す）")
    ap.add_argument("--list", action="store_true", help="選べる言語を表示")
    a = ap.parse_args()
    if a.list:
        print("同梱の写しがある言語: " + ", ".join(bundled_names()))
        print("別名: " + ", ".join(f"{k}→{v}" for k, v in sorted(ALIASES.items())))
        print("ネットが使えれば、github/gitignore の root にあるファイル名（例: Elixir、Haskell）も --langs に書ける")
        return
    root = Path(a.root).resolve()
    answers_file = root / "_examples" / "answers" / "current.json"
    answers = json.loads(answers_file.read_text(encoding="utf-8")) if answers_file.exists() else {}
    langs = a.langs
    dest, notes = create(root, a.dir, langs, a.kind, a.mode, a.upstream, answers, a.offline, a.force)
    for n in notes:
        print(("・" if dest else "注意: ") + n)
    if dest:
        print(f"作りました: {dest.relative_to(root).as_posix()}（{len(dest.read_text(encoding='utf-8').splitlines())} 行）")
    elif not notes or "作りません" not in notes[0]:
        sys.exit(1)


if __name__ == "__main__":
    main()
