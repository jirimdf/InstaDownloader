# Instagram Stories Downloader

[![Tests](https://github.com/jirimdf/InstaDownloader/actions/workflows/tests.yml/badge.svg)](https://github.com/jirimdf/InstaDownloader/actions/workflows/tests.yml)

A Python script that downloads Instagram stories from a public account. It uses a headless Chrome browser (Selenium) to fetch the stories through a third-party download service and saves new images and videos to a local folder. It can be scheduled to run automatically, for example every 2 hours.

## Features

- Downloads images and videos from stories of a public Instagram account
- Runs in headless mode (no browser window)
- Skips already downloaded stories (`downloaded_links.txt`) and never overwrites existing files
- Username and folder are passed as arguments, no need to edit the code
- Clear error messages for private accounts, accounts without stories and website changes
- Logs each run to `task.txt`
- Can be scheduled with Windows Task Scheduler or cron

## Tech stack

- Python 3
- Selenium (headless Chrome)
- Requests

## Requirements

- Python 3
- Google Chrome

## Installation

```bash
git clone https://github.com/jirimdf/InstaDownloader.git
cd InstaDownloader
pip install -r requirements.txt
```

## Usage

```bash
python main.py <username> [-f FOLDER] [--show-browser]
```

| Argument | Description |
|---|---|
| `username` | Instagram username of a public account |
| `-f`, `--folder` | Folder where the stories are saved (default: `./downloads`) |
| `--show-browser` | Show the Chrome window instead of running headless (useful for debugging) |

Example:

```bash
python main.py some_public_account -f ./stories
```

Files are saved to `<download_folder>/Stories/` in this format:

```
jirimdf_Downloader_{username}_{ddmmYYYY}_{n}.{jpg|mp4}
```

![example](https://github.com/jirimdf/InstaDownloader/assets/163419314/b4130af9-a9a2-4adb-8e7a-dd08d8dc488f)

## Automation

To download new stories regularly, create a task in Windows Task Scheduler (or a cron job on Linux) that runs `python main.py <username> -f <folder>`, for example every 2 hours.

## Tests

```bash
pip install pytest
python -m pytest
```

The tests cover the download logic with mocked responses, so they need no network access or browser. They run automatically on every push via GitHub Actions.

## Notes

- Tested on Windows and Linux.
- The script depends on the structure of a third-party website, so it may stop working if that website changes.
- Respect Instagram's Terms of Service and copyright. Only download content you have the right to use.

## License

This project is licensed under the [MIT License](LICENSE).
