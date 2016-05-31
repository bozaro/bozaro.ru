#!/usr/bin/python3
import json
import requests, os, os.path
import argparse

import sys

parser = argparse.ArgumentParser(description='Simple pull requets statistics')
parser.add_argument("--user", dest="username", type=str,
                    default=os.environ.get("USER"),
                    help="GitHub user name (default: %s)" % os.environ.get("USER"))
parser.add_argument("--password", dest="password", type=str,
                    required=True,
                    help="GitHub password")

args = parser.parse_args()
projectUrl = "https://api.github.com/repos/EpicGames/UnrealEngine"

cacheDir = os.path.join(os.path.dirname(sys.argv[0]), "pulls")
if not os.path.exists(cacheDir):
    os.mkdir(cacheDir, 0o755)

r = requests.get("%s/pulls?state=all&direction=asc&page=2" % projectUrl, auth=(args.username, args.password))
if r.status_code != 200: raise IOError("Unexpected HTTP status: %d" % r.status_code)

# Save response
f = open("pulls.all.json", "wb")
f.write(r.content)
f.close()

print ("Downloading pull requests information...")
pullRequests = {}
for i in range(1, 100):
    path = os.path.join(cacheDir, "pr.%d.json" % i)
    if not os.path.exists(path):
        print("  Pull request %d" % i)
        # Get pull request info
        r = requests.get("%s/pulls/%d" % (projectUrl, i), auth=(args.username, args.password))
        if r.status_code != 200: raise IOError("Unexpected HTTP status: %d" % r.status_code)

        # Save response
        f = open(path + "~", "wb")
        f.write(r.content)
        f.close()
        os.rename(path + "~", path)
    pullRequests[i] = path

print ("Read information from pull requests...")
o = open("result.txt", "wt", encoding="utf-8")
o.write("\t".join([
    "id",
    "created_at",
    "user",
    "avatar",
    "commits",
]))
o.write("\n")
for i in pullRequests:
    path = pullRequests[i]
    f = open(path, "rt", encoding="utf-8")
    j = json.loads(f.read(), "utf-8")
    line = "\t".join([
        str(j["number"]),
        j["created_at"],
        j["user"]["login"],
        j["user"]["avatar_url"],
        str(j["commits"]),
    ])
    o.write(line)
    o.write("\n")
    print (line)
o.close()
