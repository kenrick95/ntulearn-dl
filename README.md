`ntulearn-dl` is a script to batch downloading course materials from NTULearn (former edveNTUre).

## Features
* Login with username and password and store the session
* Batch download course documents
* Group files by folder
* Nice console display

## To-do

* Add argparse
* add netrc support

## Assumptions
Installed:
* Python 2.7
* pip or easy_install

## Library dependencies

* `requests`
* `beautifulsoup4`

## How to use?

1. Download the repository
2. Install dependencies
    - `pip install requests`
    - `pip install beautifulsoup4`
3. Edit `config.py`: replace `USERNAME` and `PASSWORD` with those of yours
4. `python ntulearn-dl.py`
5. ???
6. Profit!
