# Issues管理

このディレクトリはプロジェクトのissueをローカルで管理するためのものです。

## ディレクトリ構造

```
issues/
├── README.md                          # このファイル
├── TEMPLATE.md                        # Issue作成テンプレート
├── 001-feature-gap-analysis.md       # Issue #1: 機能差分調査
├── 002-example-issue.md               # Issue #2: (例)
└── ...
```

## Issue作成方法

### 1. 次のissue番号を確認

```bash
ls issues/*.md | tail -1
# 最後のファイル名から次の番号を決定
```

### 2. テンプレートをコピー

```bash
cp issues/TEMPLATE.md issues/XXX-issue-title.md
```

### 3. 内容を編集

ファイルを開いて、以下のセクションを埋める：

- タイトル
- ステータス（Open/In Progress/Closed）
- 優先度（Low/Medium/High/Critical）
- ラベル
- 担当者
- 関連Issue
- 説明
- タスク
- 補足情報

### 4. コミット

```bash
git add issues/XXX-issue-title.md
git commit -m "Add issue #XXX: タイトル"
```

## Issue更新方法

### ステータス変更

ファイル冒頭の`Status`フィールドを更新：

```markdown
**Status**: In Progress  # または Closed
```

### タスク進捗

チェックボックスを更新：

```markdown
- [x] 完了したタスク
- [ ] 未完了のタスク
```

### コメント追加

ファイル末尾に`## Updates`セクションを追加：

```markdown
## Updates

### 2025-10-30

進捗状況や追加情報をここに記載...
```

## Issue検索

### 全issue一覧

```bash
ls -1 issues/*.md | grep -v "README\|TEMPLATE"
```

### Openなissueを検索

```bash
grep -l "Status.*Open" issues/*.md
```

### ラベルで検索

```bash
grep -l "Labels.*enhancement" issues/*.md
```

### キーワード検索

```bash
grep -r "ModelSettings" issues/
```

## GitHub Issueへの移行

後でGitHub issueに移行する場合：

1. GitHub Web UIでissue作成
2. マークダウンファイルの内容をコピー&ペースト
3. ローカルファイルにGitHub issue番号を追記：

```markdown
**GitHub Issue**: #123
```

## 命名規則

- ファイル名: `NNN-short-title.md`（NNNは3桁のゼロパディング）
- 例: `001-feature-gap-analysis.md`, `002-add-streaming-support.md`
- タイトルはケバブケース（小文字、ハイフン区切り）

## ステータスの定義

- **Open**: 新規作成、未着手
- **In Progress**: 作業中
- **Closed**: 完了またはクローズ
- **Blocked**: ブロック中（他のissueや外部要因待ち）
- **On Hold**: 保留中

## 優先度の定義

- **Critical**: 即座に対応が必要（バグ、セキュリティ問題）
- **High**: 次のリリースで対応
- **Medium**: 重要だが緊急ではない
- **Low**: 将来的に対応
