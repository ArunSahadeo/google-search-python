#!/usr/bin/env python3 -u

import datetime, json, os, sys, time
import sqlite3
import shutil

def checkConfig(config_file):
    if not os.path.isfile(config_file):
        return

    firefox_profile_config = open(os.path.expanduser('~/.mozilla/firefox/profiles.ini'))
    firefox_profile = None

    with firefox_profile_config as profile_file:
        for line in profile_file:
            name, val = line.partition('=')[::2]
            if '.default' in val:
                firefox_profile = val.rstrip()
                break

    with open(config_file, 'r') as f:
        history_paths  = json.load(f)
        history_paths = history_paths['paths']
        for history_path in history_paths:
            history_path = os.path.expanduser(history_path)
            if '$PROFILE_FOLDER' in history_path:
                history_path = history_path.replace('$PROFILE_FOLDER', firefox_profile)
            if len(history_path) < 1 or not os.path.isfile(history_path):
                continue
            browser_sqlite_dbs.append(history_path)

browser_sqlite_dbs = []

if os.name == 'posix':
    nix_paths_config = 'nix_paths.json'
    checkConfig(nix_paths_config)
else:
    print(False)

if not len(browser_sqlite_dbs) > 0:
    print("No SQLite files found!")
    sys.exit(0)

for index, db_path in enumerate(browser_sqlite_dbs):
    db_timestamp = os.path.getmtime(db_path)
    browser = None
    
    if "chromium" in db_path:
        browser = "chromium"
    elif "firefox" in db_path:
        browser = "firefox"

    now = time.time()
    one_week_ago = now - (60 * 60 * 24 * 7)

    if db_timestamp < one_week_ago:
        continue

    old_filename = os.path.basename(db_path)
    shutil.copy(db_path, os.getcwd())
    src_file = os.path.join(os.getcwd(), old_filename)
    dst_file = str("{:s}_browser_history").format(browser)
    new_file = os.path.join(os.getcwd(), dst_file)
    os.replace(src_file, dst_file)

    if not os.path.isfile(new_file):
        continue

    conn = sqlite3.connect(new_file)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT title from urls WHERE title LIKE "%Google Search%" ORDER BY id DESC LIMIT 1')
        select_result = cursor.fetchone()[0]
        print(select_result)
    except Exception as error:
        print(error)
