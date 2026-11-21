# スキル、サブエージェント、MCP の設定

## 最初から入っているもの（何もしなくても使える）

### スキル（`.claude/skills/`）
Claude Code でこのリポジトリを開くと、スラッシュコマンドとして使える。依頼の内容から自動でも呼ばれる。

| スキル | 用途 |
|---|---|
| `/setup-project` | ヒアリング形式の初期セットアップ |
| `/milestone` | マイルストーンを 1 つ進める。作業の再開にも使う |
| `/verify` | 機械検査、実物の通し、独立した審査、仕込み検査 |
| `/handoff` | 引き継ぎメモと、次のセッションの最初のメッセージを作る |
| `/next-cycle` | 版を締めて記録を `04_logs/` に移し、次の版の計画（`PLAN.md`）を作る |
| `/retro` | 履歴から、ルール・合格条件・検査の修正案を作る |

### サブエージェント（`.claude/agents/`）
| 名前 | モデル | 用途 |
|---|---|---|
| `reviewer` | Opus | 制作の経緯を知らない立場での審査。ファイルは書き換えない |
| `implementer` | Sonnet | 範囲の決まった実装、抽出、執筆、検査の実行 |

モデルを変えるときは、各ファイルの先頭の `model:` を書き換える。

### 権限（`.claude/settings.json`）
- 確認なしで実行：`_tools/` のスクリプト、git の状態の確認、add、commit
- 毎回確認：`rm`、`git push`、`git reset`、`git rebase`
- 読ませない：`.env`、`secrets/`

自分だけの設定は `.claude/settings.local.json` に書く（git には入らない）。
今の設定は、Claude Code の中で `/permissions` と入力すると見られる。

## MCP（有効化は手動）

`.mcp.json.example` に、API キーの要らない 2 つを設定例として入れてある。

| サーバー | 用途 | 使う場面 |
|---|---|---|
| `playwright` | ブラウザを操作し、スクリーンショットやコンソールを見る | ゲーム、Three.js、Web アプリの確認 |
| `context7` | ライブラリの最新のドキュメントを引く | 新しいライブラリや、版の違いが効く実装 |

### 有効にする手順
1. Node.js が入っていることを確かめる：`node -v`
2. 設定例を写す：`cp .mcp.json.example .mcp.json`
3. 使わないサーバーの項目を `.mcp.json` から消す
4. Claude Code を開き直す。初回に、このリポジトリの MCP サーバーを使うかを聞かれるので、承認する
5. Claude Code の中で `/mcp` と入力し、接続の状態を確かめる

コマンドで足す場合（`.mcp.json` に書き込まれる）：

```bash
claude mcp add --scope project playwright -- npx -y @playwright/mcp@latest
```

### 足すときの目安
- 検査に使うもの（画面を見る、実行する）を優先する。検査が増えるほど、結果が安定する
- API キーが要るサーバーは、キーを `.mcp.json` に直接書かない。環境変数で渡し（`"env": {"KEY": "${KEY}"}`）、
  値は `.env` か OS の設定に置く
- サーバーを足すと、道具の説明の分だけ文脈を使う。使わないものは外す
- 外部のサービスに書き込む道具（メールの送信、チケットの作成など）は、`CLAUDE.md` の
  「承認を待つ操作」の対象

## スキルを足すとき
- `.claude/skills/<名前>/SKILL.md` を作る。先頭に `name` と `description` を書く。
  `description` には、どんな言葉で呼ばれたら使うかを書く
- 手順は、番号を付けて短く書く。確かめられる手順は `_tools/` のスクリプトにして、スキルから呼ぶ
- 書いたら `python3 _tools/check_skill.py .claude/skills/<名前>` で形を確かめる
- `/retro` で同じ手順の指摘が 2 回出たら、スキルにする合図

## 設定の書式が変わったとき
Claude Code の設定の書式は、版によって変わることがある。うまく読み込まれないときは、
公式のドキュメント（https://docs.claude.com/en/docs/claude-code/overview）で、
skills、subagents、settings、MCP の各ページを確かめる。
