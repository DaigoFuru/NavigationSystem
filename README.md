# NavigationSystem

This is an algorithm by which the solar boat can aim the goal automatically
 
# Overview
 
todo: システムの概要
 
# Requirement
 
 
* python 3.8.1
  * formatter: black

 
# Installation
 
mac OSの場合

## pythonのinstall

1. まず pyenv をインストール：

`brew install pyenv`

`pyenv -v`

2. pyenv の設定（.bash_profile の設定変更）：

`vi ~/.zprofile`

以下を記載して`:wq`

`echo 'export PYENV_ROOT=/usr/local/var/pyenv
if which pyenv > /dev/null; then eval "$(pyenv init -)"; fi' >`

※mac OSがCatalina以前(~10.15.7)の場合は`zprofile -> bash_profile`にして実行

3. Python のアップデート：

3.8.1がダウンロード可能であることを確認
`pyenv install --list`

`pyenv install 3.8.1`

`pyenv versions`

このままだと global（* マーク）が system のままなので, ver.2 系列しか使えない. そこで global を 3.8.1 に変更

`pyenv global 3.8.1`

`pyenv versions`

変更されていることを確認してから, ターミナルを再起動（ここ重要）. 最後にバージョンを確認

`python -V`

これでターミナルから python を実行すれば 3.8.1が使えるようになる。

 
# Usage

```bash
python3 main.py parameter_sample.txt
```
 
# Note
 
todo: 注意点などがあれば書く
 
# Author
 
 
* YukiSaegusa, Amusac
* University of Tokyo
 
 [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
