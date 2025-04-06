# Pythonのmonorepoの共通Lint & Test用Github Action workflow

以下の記事のrepositoryです。

- [Pythonのmonorepoの共通Lint & Test用Github Action workflow](https://qiita.com/haru-256/items/99a3d14bd4d67334dafb)

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
