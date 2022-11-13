import pprint
from datetime import datetime, timedelta
from twistedfate.match import Match
import requests
import json
import zipfile
from io import BytesIO
import os
import urllib


def getAccessToken(email: str, password: str):
    body = {
        "password": password,
        "username": email
    }

    headers = {'content-type': 'application/json'}
    token = requests.post("https://lolesports-api.bayesesports.com/auth/login", json.dumps(body), headers=headers)
    token = token.json()

    print(token)

    authHeader = "Bearer " + token["accessToken"]
    return {'Authorization': authHeader}


token = {}
dumps = 'dumps/'


def downloadGame(gameSummary):
    if not gameSummary["downloadAvailable"]:
        return None
    url = "https://lolesports-api.bayesesports.com/historic/v1/riot-lol/games/" + str(
        gameSummary["id"]
    ) + "/downloadDump"
    print(url)
    dl_url = requests.get(url, headers=token)
    dl_url = dl_url.json()["url"]

    r = requests.get(dl_url, stream=True)

    z = zipfile.ZipFile(BytesIO(r.content))
    z.extractall(dumps)
    os.rename(os.path.join(dumps, "dump.json"), os.path.join(dumps, str(gameSummary["id"]) + ".json"))
    gameSummary["gameData"] = json.load(open(os.path.join(dumps, str(gameSummary["id"]) + ".json")))
    return gameSummary["gameData"]


def downloadGames(gameSummaries):
    matches = []
    for m in gameSummaries:
        match = m['match']
        for game in match["games"]:
            if game["downloadAvailable"]:
                game["gameData"] = getGame(game)["gameData"]
        matches.append(Match(match))
    return matches


def getLeagues():
    url = "https://lolesports-api.bayesesports.com/historic/v1/riot-lol/leagues"
    headers = token
    return json.loads(requests.get(url, headers=headers).content)


def getLeagueMatches(leagues, date_from: datetime):
    url = "https://lolesports-api.bayesesports.com/historic/v1/riot-lol/matches?leagueIds="
    for league in leagues:
        url += league["id"] + ","
    url = url[:-1]
    url += "&"

    if date_from is not None:
        date = date_from + timedelta(minutes=1)
        date = date.isoformat()
        # date = date.format("YYYY-MM-DD HH:mm:ss")
        date = date.replace(" ", "T")
        date += "Z"
        date = urllib.parse.quote(date.encode("utf-8"))
        url += "matchDateFrom=" + date + "&"
    url += "size=100"
    print(url)
    headers = token
    return json.loads(requests.get(url, headers=headers).content)["results"]


def getGame(gameSummary):
    if os.path.isfile(os.path.join(dumps, str(gameSummary["id"]+ ".json"))):
        gameSummary["gameData"] = json.load(open("dumps/" + str(gameSummary["id"]) + ".json"))
        return gameSummary
    else:
        gameSummary = downloadGame(gameSummary)
        return gameSummary
