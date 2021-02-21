from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import requests
from .models import Stats
from django.contrib import messages
import os


@login_required
def stats(request):
    header = {
        "Authorization": f'Bearer {os.environ.get("PUBG_API_TOKEN")}',
        "Accept": "application/vnd.api+json"
    }
    pubgUsername = request.user.profile.pubgUsername

    if pubgUsername == '':
        messages.warning(request, "You haven't linked your PUBG account. Go to the profile page to link your account.")
    else:
        response = requests.get(f'https://api.pubg.com/shards/steam/players?filter[playerNames]={pubgUsername}',
                                headers=header)

        context = response.json()

        if 'errors' in context:
            messages.warning(request, "There is no PUBG account with that username. make sure your PUBG username is correct in your profile page.")
        else:
            matches = context['data'][0]['relationships']['matches']['data']

            if len(matches) < 1:
                pass
            else:
                for match in matches:
                    matchId = match['id']
                    # print(matchId)
                    if Stats.objects.filter(matchId=matchId).filter(user_id=request.user.profile).exists():
                        pass
                    else:
                        response = requests.get(f'https://api.pubg.com/shards/steam/matches/{matchId}', headers=header)
                        r = response.json()
                        # print(r)
                        participantList = r["included"]
                        for participant in participantList:
                            if participant["type"] == "participant":
                                if participant["attributes"]["stats"]["name"] == pubgUsername:
                                    Stats.objects.create(
                                        matchId=matchId,
                                        kills=participant["attributes"]["stats"]["kills"],
                                        deathType=participant["attributes"]["stats"]["deathType"],
                                        damage=participant["attributes"]["stats"]["damageDealt"],
                                        dbno=participant["attributes"]["stats"]["DBNOs"],
                                        revives=participant["attributes"]["stats"]["revives"],
                                        timeAlive=participant["attributes"]["stats"]["timeSurvived"],
                                        user=request.user.profile
                                    )
                                    # print(participant["attributes"]["stats"])
    baseStats = Stats.objects.filter(user_id=request.user.profile)

    kills = 0
    deaths = 0
    damage = 0
    dbno = 0
    revives = 0
    timeAlive = 0

    for stat in baseStats:
        kills = kills + stat.kills
        if stat.deathType == 'alive':
            pass
        else:
            deaths = deaths + 1
        damage = damage + stat.damage
        dbno = dbno + stat.dbno
        revives = revives + stat.revives
        timeAlive = timeAlive + stat.timeAlive

    timeAlive = timeAlive / len(baseStats)
    totalMatches = len(baseStats)

    totalStats = {
        "totalMatches": totalMatches,
        "kills": kills,
        "deaths": deaths,
        "damage": damage,
        "dbno": dbno,
        "revives": revives,
        "timeAlive": timeAlive
    }

    return render(request, 'stats/stats.html', {
        'playerName': pubgUsername,
        'stats': totalStats
    })

# django background tasks
# matplotlib