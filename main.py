#!/usr/bin/env python3 -u

import datetime, json, operator, os, sys, time
import sqlite3
import shutil

def getLatestResult(browser_sqlite_dbs):
    
    search_queries = []

    for db_path in browser_sqlite_dbs:
        browser = None
        now = time.time()
        one_week_ago = now - (60 * 60 * 24 * 7)

        if os.path.getmtime(db_path) < one_week_ago:
            return

        if "chromium" in str(db_path).lower():
            browser = "chromium"
        elif "chrome" in str(db_path).lower():
            browser = "chrome"
        elif "firefox" in str(db_path).lower():
            browser = "firefox"

        old_filename = os.path.basename(db_path)
        shutil.copy(db_path, os.getcwd())
        src_file = os.path.join(os.getcwd(), old_filename)
        dst_file = str("%s_browser_history" % (browser))
        new_file = os.path.join(os.getcwd(), dst_file)
        os.replace(src_file, dst_file)

        if not os.path.isfile(new_file):
            return

        conn = sqlite3.connect(new_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if browser == "chromium" or browser == "chrome":
                cursor.execute('SELECT title, last_visit_time from urls WHERE title LIKE "%Google Search%" ORDER BY id DESC LIMIT 1')
                select_result = cursor.fetchone()
                search_queries.append({'query': select_result['title'], 'last_visited': select_result['last_visit_time'] })
            elif browser == "firefox":
                cursor.execute('SELECT title, last_visit_date FROM moz_places WHERE title LIKE "%Google Search%" ORDER BY id DESC LIMIT 1')
                select_result = cursor.fetchone()
                search_queries.append({'query': select_result['title'], 'last_visited': select_result['last_visit_date'] })
        except Exception as error:
            print(error)

    if not len(search_queries): return

    latest_query = max(search_queries, key=operator.itemgetter('last_visited'))

    latest_query = latest_query['query']

    print(latest_query)


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
            browser_sqlite_dbs.append(history_path)

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

getLatestResult(browser_sqlite_dbs)
