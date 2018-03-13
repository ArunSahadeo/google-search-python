#!/usr/bin/env python3 -u

import datetime, json, operator, os, sys, time
import sqlite3
import shutil

def getLatestResult(latest_query):
    browser = None

    if "chromium" in str(latest_query).lower():
        browser = "chromium"
    elif "chrome" in str(latest_query).lower():
        browser = "chrome"
    elif "firefox" in str(latest_query).lower():
        browser = "firefox"

    now = time.time()
    one_week_ago = now - (60 * 60 * 24 * 7)

    if latest_query['modification_time'] < one_week_ago:
        return

    old_filename = os.path.basename(latest_query['path'])
    shutil.copy(latest_query['path'], os.getcwd())
    src_file = os.path.join(os.getcwd(), old_filename)
    dst_file = str("%s_browser_history" % (browser))
    new_file = os.path.join(os.getcwd(), dst_file)
    os.replace(src_file, dst_file)

    if not os.path.isfile(new_file):
        return

    conn = sqlite3.connect(new_file)
    cursor = conn.cursor()

    try:
        if browser == "chromium" or browser == "chrome":
            cursor.execute('SELECT title from urls WHERE title LIKE "%Google Search%" ORDER BY id DESC LIMIT 1')
        elif browser == "firefox":
            cursor.execute('SELECT title FROM moz_places WHERE title LIKE "%Google Search%" ORDER BY id DESC LIMIT 1')
        select_result = cursor.fetchone()[0]
        print(select_result)
    except Exception as error:
        print(error)

def checkConfig(config_file):
    if not os.path.isfile(config_file):
        return

    AppData = str(os.getenv('APPDATA')) if os.name == 'nt' else None
    AppLocal = os.path.join(os.getenv('USERPROFILE'), 'AppData\Local') if os.name == 'nt' else None

    firefox_profile_config = open(os.path.expanduser('~/.mozilla/firefox/profiles.ini')) if os.name == 'posix' else open( os.path.join("%s\Mozilla\Firefox\profiles.ini") % (AppData) )
    firefox_profile = None

    with firefox_profile_config as profile_file:
        for line in profile_file:
            name, val = line.partition('=')[::2]
            if '.default' in val:
                if 'Profiles/' in val:
                    val = val.replace('Profiles/', '')
                firefox_profile = val.rstrip()
                break

    with open(config_file, 'r') as f:
        history_paths  = json.load(f)
        history_paths = history_paths['paths']
        for history_path in history_paths:
            if os.name == "posix":
                history_path = os.path.expanduser(history_path)
            if '$APPDATA' in history_path:
                history_path = history_path.replace('$APPDATA', AppData)
            if '$APPLOCAL' in history_path:
                history_path = history_path.replace('$APPLOCAL', AppLocal)
            if '$PROFILE_FOLDER' in history_path:
                history_path = history_path.replace('$PROFILE_FOLDER', firefox_profile)
            if len(history_path) < 1 or not os.path.isfile(history_path):
                continue
            browser_sqlite_dbs.append({ 'path': history_path, 'modification_time': os.path.getmtime(history_path) })

browser_sqlite_dbs = []

if os.name == 'posix':
    nix_paths_config = 'nix_paths.json'
    checkConfig(nix_paths_config)
elif os.name == 'nt':
    win_paths_config = 'win_paths.json'
    checkConfig(win_paths_config)

if not len(browser_sqlite_dbs) > 0:
    print("No SQLite files found!")
    sys.exit(0)

latest_query = max(browser_sqlite_dbs, key=operator.itemgetter('modification_time'))

getLatestResult(latest_query)
