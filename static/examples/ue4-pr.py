#!/usr/bin/python3
import json
import requests, os, os.path
import argparse

import sys
import csv


def write_file(path, content):
    f = open(path + "~", "wb")
    f.write(content)
    f.close()
    os.rename(path + "~", path)


def escape(c):
    return c.replace("\0", "")


parser = argparse.ArgumentParser(description='Simple pull requets statistics')
parser.add_argument("--user", dest="username", type=str,
                    default=os.environ.get("USER"),
                    help="GitHub user name (default: %s)" % os.environ.get("USER"))
parser.add_argument("--password", dest="password", type=str,
                    required=True,
                    help="GitHub password")
parser.add_argument("--limit", dest="limit", type=int,
                    default=2500,
                    help="GitHub pull request count (default: %d)" % 2500)
parser.add_argument("--output", dest="output", type=str,
                    default="result.csv",
                    help="Output file name (default: %s)" % os.environ.get("result.csv"))
parser.add_argument("--total", dest="total", type=str,
                    default="total.csv",
                    help="Total file name (default: %s)" % os.environ.get("total.csv"))

args = parser.parse_args()
projectUrl = "https://api.github.com/repos/EpicGames/UnrealEngine"

cacheDir = os.path.join(os.path.dirname(sys.argv[0]), ".pulls")
if not os.path.exists(cacheDir):
    os.mkdir(cacheDir, 0o755)

print ("Downloading pull requests information (pages)...")
page = 0
pageSize = 50
pages = []
while True:
    page += 1
    path = os.path.join(cacheDir, "page.%04d.json" % page)
    pages.append(path)
    if os.path.exists(path):
        f = open(path, "rt", encoding="utf-8")
        j = json.loads(f.read(), "utf-8")
        if len(j) == pageSize:
            continue
    print("  Downloading page: %d" % page)
    r = requests.get("%s/pulls?state=all&direction=asc&page=%d&per_page=%d" % (projectUrl, page, pageSize),
                     auth=(args.username, args.password))
    if r.status_code != 200: raise IOError("Unexpected HTTP status: %d" % r.status_code)

    # Save response
    write_file(path, r.content)

    j = json.loads(r.content.decode("utf-8"), "utf-8")
    if len(j) < pageSize:
        print ("  Last page downloaded")
        break

print ("Downloading pull requests information (content)...")
pullRequests = []
for page in pages:
    f = open(page, "rt", encoding="utf-8")
    j = json.loads(f.read(), "utf-8")
    f.close()
    for pr in j:
        id = pr["number"]
        path = os.path.join(cacheDir, "pr.%05d.json" % id)
        pullRequests.append(path)
        if os.path.exists(path):
            continue

        print("  Downloading pr: %d" % id)
        r = requests.get("%s/pulls/%d" % (projectUrl, id),
                         auth=(args.username, args.password))
        if r.status_code != 200: raise IOError("Unexpected HTTP status: %d" % r.status_code)

        # Save response
        write_file(path, r.content)

print ("Read information from pull requests...")
f = open(args.output, "wt", encoding="utf-8")
o = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
o.writerow([
    "id",
    "created_at",
    "user",
    "avatar",
    "commits",
    "title",
])
total = {}
avatar = {}
for path in pullRequests:
    f = open(path, "rt", encoding="utf-8")
    j = json.loads(f.read(), "utf-8")
    login = j["user"]["login"]
    if int(j["number"]) > args.limit: continue
    o.writerow([
        str(j["number"]),
        j["created_at"],
        escape(login),
        j["user"]["avatar_url"],
        str(j["commits"]),
        escape(j["title"]),
    ])
    avatar[login] = j["user"]["avatar_url"]
    total[login] = total.get(login, 0) + 1
f.close()

f = open(args.total, "wt", encoding="utf-8")
o = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
o.writerow([
    "user",
    "total",
])
for login in total:
    o.writerow([
        login,
        avatar[login],
        total[login],
    ])
f.close()
