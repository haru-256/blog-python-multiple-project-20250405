# 複数のPython Projectがある場合のLintとテストCIについて

複数のPython projectを1つのリポジトリで管理する場合、CIの設定をどうするか悩むことがあると思います。
通常は、各プロジェクトごとにworkflowを用意し、`paths`に対応プロジェクトを指定することで、特定プロジェクトに対してのみworkflowを実行することになります。
ただ、個々のプロジェクトで使用しているライブラリやpythonのバージョンは違うが、Lintやテストのworkflowは、ほぼ同じ内容になることが多いです。
そのため、この方法では、同じ内容のworkflowがいくつもできあがってしまいます。

```yaml
on:
  push:
    paths:
      - 'project-1/**' # project-1 に変更があった場合
```

この記事では、以下の要望を満たすworkflowを作成します。

- 複数のPython projectを1つのリポジトリで管理している。root直下に、複数のディレクトリが存在し、それぞれがプロジェクトを表す。
  - 例
    - `project-1/`
    - `project-2/`
- lintやテストなど共通のworkflowを1つにまとめたい
- 各プロジェクトごとに使いたいライブラリやpythonのバージョンは異なる。そのため、各プロジェクト直下にある`pyproject.toml`に応じてライブラリやpythonのバージョンを変更してほしい
- 複数のプロジェクトが同時に変更されることはないと仮定する

## 方法

以下のリポジトリの`.github/workflows/python-lint.yaml` に上記要件を満たすような完成形のworkflowがあります。

### 概要

`git diff`で変更されたファイルを取得し、そこから変更されたプロジェクト=ディレクトリを推定します。その後、そのディレクトリにworking directoryを変更し、`pyproject.toml`を読み込んで、必要なライブラリやpythonのバージョンを取得して、workflowを実行します。

### 具体的な流れ

ここではworkflowの中でもキモとなる `id = changes` というstepの中身を説明します。

`changes` では、Lintとテストを実行する対象のプロジェクト = ディレクトリを取得します。
その後のstepで取得したディレクトリをworking directoryにするため、ディレクトリ名を`wd`に格納します。
また、ファイルの変更がない場合は、変数`should_run`をfalseにして、以降のstepをスキップします。

このstepは、以下のような流れで処理を行います。

1. `git diff`で変更されたPythonファイルを取得する
2. 変更されたPythonファイルがなければ、stepを終了する
3. 変更されたPythonファイルから、変更されたディレクトリ一覧を取得する
4. 変更されたディレクトリの数をカウントし、以下の場合は特殊な処理を行う
   - 変更されたディレクトリが0の場合: その後の処理をスキップする
   - 変更されたディレクトリが1以上の場合: エラーを出力して終了する
5. 変更されたディレクトリが1つの場合、そのディレクトリを出力する

```yaml
jobs:
  python-lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Get changed directories
        id: changes
        run: |
          # Get unique directories from changed files
          if [ "${{ github.event_name }}" == "pull_request" ]; then
            # For PRs, compare with base branch
            git fetch origin ${{ github.base_ref }}
            CHANGED_FILES=$(git diff --name-only origin/${{ github.base_ref }} HEAD | grep '\.py$' || echo "")
          else
            # For pushes, compare with previous commit
            CHANGED_FILES=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }} | grep '\.py$' || echo "")
          fi
          echo "::debug::Changed files: $CHANGED_FILES"

          # If no Python files changed, skip tests
          if [ -z "$CHANGED_FILES" ]; then
            echo "No Python files changed"
            echo "should_run=false" >> $GITHUB_OUTPUT
            exit 0
          fi

          # Get unique directories from changed files
          CHANGED_DIRS=$(echo "$CHANGED_FILES" | awk -F/ '{print $1}' | sort -u)
          echo "Changed directories: $CHANGED_DIRS"

          # Count how many directories were changed and check if it's valid
          DIR_COUNT=$(echo "$CHANGED_DIRS" | grep -v "^$" | wc -l)
          if [ "$DIR_COUNT" -eq 0 ]; then
            echo "No Python directories changed"
            echo "should_run=false" >> $GITHUB_OUTPUT
            exit 0
          elif [ "$DIR_COUNT" -gt 1 ]; then
            echo "::error::Changes detected in multiple directories: $CHANGED_DIRS"
            echo "This workflow supports changes in only one directory at a time"
            exit 1
          fi

          # Set the single directory as output
          echo "dirs=$(echo "$CHANGED_DIRS" | tr -d '\n')" >> $GITHUB_OUTPUT
          echo "should_run=true" >> $GITHUB_OUTPUT
```

#### 1. `git diff`で変更されたPythonファイルを取得する

`git diff`を使って、変更されたPythonファイルを取得します。`git diff --name-only`は、変更されたファイルのパスを表示します。`grep '\.py$'`でPythonファイルのみを抽出します。
このとき、`git diff`の引数は、pushとpull requestで異なります。

- pushの場合: `git diff --name-only ${{ github.event.before }} ${{ github.sha }}`
- pull requestの場合: `git diff --name-only origin/${{ github.base_ref }} HEAD`

`github.event.before`は、pushの前のコミットを指し、`github.sha`は、pushされたコミットを指します。これにより、pushされたコミットと前のコミットの差分を取得することができます。
`github.base_ref`は、pull requestのベースブランチを指します。これにより、pull requestの変更内容を取得することができます。

#### 2. 変更されたPythonファイルがなければ、stepを終了する

変更されたPythonファイルがなければ、 `exit 0` でstepを終了します。また、`echo "should_run=false" >> $GITHUB_OUTPUT` でその後のstepに渡すための変数を設定します。`$GITHUB_OUTPUT`は、GitHub Actionsの特別な環境変数で、次のstepに渡すための出力を設定することができます。詳細は[こちら](https://docs.github.com/ja/actions/using-workflows/workflow-commands-for-github-actions#setting-an-output-parameter)を参照してください。

#### 3. 変更されたPythonファイルから、変更されたディレクトリ一覧を取得する

変更されたPythonファイルから、変更されたディレクトリ一覧を取得します。`awk -F/ '{print $1}'`で、ファイルパスからディレクトリ名を抽出します。`sort -u`で、重複を削除します。

awkコマンドの`-F/` オプションは、区切り文字を指定するためのもので、ここではスラッシュ（`/`）を区切り文字として指定しています。これにより、ファイルパスをスラッシュで分割し、最初の部分（ディレクトリ名）を取得します。

#### 4. 変更されたディレクトリの数をカウントし、以下の場合は特殊な処理を行う

変更されたディレクトリが複数存在する場合、それらのどれをworking directoryにするかが不明なため、エラーを出力して終了します。
また、0件の場合は、`echo "should_run=false" >> $GITHUB_OUTPUT` でその後のstepに渡すための変数を設定します。

Github Actionsでは、`echo "::error::{message}"`を使うことで、エラーメッセージを出力することができます。これにより、GitHub ActionsのUI上でエラーとして表示されます。
詳しくは[こちら](https://docs.github.com/ja/actions/using-workflows/workflow-commands-for-github-actions#setting-an-error-message)を参照してください。

#### 5. 変更されたディレクトリが1つの場合、そのディレクトリを出力する

変更されたディレクトリが1つの場合、そのディレクトリを出力します。`echo "wd=$(echo "$CHANGED_DIRS" | tr -d '\n')" >> $GITHUB_OUTPUT` でその後のstepに渡すための変数を設定します。
`wd` は、working directoryを指します。`tr -d '\n'`は、改行を削除するためのコマンドです。これにより、出力される値が1行で表示されます。

### その後のstepでの処理

その後は以下のように、`should_run`を`if`で確認してその後のstepをスキップするかを判定します。更に、working directory を変更するために、`wd`を`working-directory`に指定します。

```yaml
      - name: Install the project
        if: ${{ steps.changes.outputs.should_run }} == 'true'
        run: make install
        working-directory: ${{ steps.changes.outputs.wd }}
```

### 考慮できていないこと

プロジェクト別に開発することを想定しているため、複数プロジェクトを一度に変更することはないのですが(正確にはその場合はPRを分ける必要がある)、ディレクトリ名をrenameした場合や、ディレクトリを移動した場合は、`git diff`で複数ディレクトリ名をが取得されてしまいます。

`git diff --diff-filter=AM`をもちいて、追加されたファイルと修正されたファイルだけに限定することもできますが、プロジェクトは1つだが意図せず複数ディレクトリの変更になってしまうケースは他にもあるため、別の方法を考える必要があります。

そのwork aroundとして、workflow dispatchを使い、手動で対象プロジェクトを指定することができるようにします。
以下のように、`workflow_dispatch`で対象のディレクトリを指定できるようにし、もしその場合は、`wd`をそのディレクトリに変更します。

```yaml
on:
  workflow_dispatch:
    inputs:
      target_dir:
        description: "Directories to run lint and test on"
        required: false
        default: ""
jobs:
  python-lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Get changed directories
        id: changes
        run: |
          # Check if the target_dir input is provided
          if [ -n "${{ github.event.inputs.target_dir }}" ]; then
            echo "wd=${{ github.event.inputs.target_dir }}" >> $GITHUB_OUTPUT
            echo "should_run=true" >> $GITHUB_OUTPUT
            exit 0
          fi
          ... # その後の処理は同じ
```

## まとめ

この記事では、以下のことを紹介しました。

- 複数のPython projectを1つのリポジトリで管理する場合、CIの設定をどうするか悩むことがある
- 各プロジェクトごとに使いたいライブラリやpythonのバージョンは異なる。そのため、各プロジェクト直下にある`pyproject.toml`に応じてライブラリやpythonのバージョンを変更してほしい
- `git diff`で変更されたファイルを取得し、そこから変更されたプロジェクト=ディレクトリを推定するGithub Actionsのworkflowを作成した

## ディレクトリ構成

```sh
.
├── README.md
├── project-1 # プロジェクト1
│   ├── Makefile
│   ├── README.md
│   ├── main.py
│   ├── test_main.py
│   ├── pyproject.toml # プロジェクト1で使用するライブラリのバージョンを指定
│   └── uv.lock
└── project-2 # プロジェクト2
    ├── Makefile
    ├── README.md
    ├── main.py
    ├── test_main.py
    ├── pyproject.toml # プロジェクト2で使用するライブラリのバージョンを指定
    └── uv.lock
```
