import os
from sqlite3 import DatabaseError
import string
from dotenv import load_dotenv
import math
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)
CORS(app)

SUPABASE_URL= os.getenv('SUPABASE_URL')
SUPABASE_KEY= os.getenv('SUPABASE_KEY')
SUPABASE_SECRET_KEY= os.getenv('SUPABASE_SECRET_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def ping_server():
    return "Hello World"


@app.route('/test')
def test():
    continents = {
        "africa": ["Africa"],
        "americas": ["North America", "South America"],
        "europe": ["Europe"],
        "asia": ["Asia"],
        "oceania": ["Oceania"],
        "asia/oceania": ["Asia", "Oceania"]
    }
    data =  supabase.table('random_places').select('*').gte('population', 1000000).limit(1).execute().data
    print(data)

    return jsonify(data)


@app.route('/get_random_place', methods=["GET"])
def getRandomPlace():

    pop = request.args.get('pop')
    zone = request.args.get('zone')

    try:
        if zone == "worldwide":
            data =  supabase.table('random_places').select('*').gte('population', int(pop)).limit(1).execute().data
        else:

            # Africa5048
            # Antarctica3
            # Asia44091
            # Europe94085
            # North America42562
            # Oceania5700
            # South America7389
            continents = {
                "africa": ["Africa"],
                "americas": ["North America", "South America"],
                "europe": ["Europe"],
                "asia": ["Asia"],
                "oceania": ["Oceania"],
                "asia/oceania": ["Asia", "Oceania"]
            }

            continentsBASED = {
                "africa": '("Africa")',
                "americas": '("North America", "South America")',
                "europe": '("Europe")',
                "asia": '("Asia")',
                "oceania": '("Oceania")',
                "asia/oceania": '("Asia","Oceania")'
            }

            data =  supabase.table('random_places_'+zone).select('*').gte('population', int(pop)).limit(1).execute().data

        return jsonify(data)
    except Exception as error:
        return jsonify({'error': error})


@app.route('/get_leaderboard', methods=["GET"])
def getLeaderboard():
    try:
        data = supabase.table('leaderboard').select('*').execute().data

        return jsonify(data)
    except Exception as error:
        return jsonify({'error': error})


# @app.route('/get_rank_from_leaderboard', methods=["GET"])
# def getRankFromLeaderboard():

#     leaderboard = stats_db["leaderboard"]

#     highscore = request.args.get('highscore')

#     try:
#         rank = leaderboard.find(
#             {"score": {"$gt": int(highscore)}}).sort("score", -1)
#         return dumps(len(list(rank)))
#     except Exception as error:
#         return jsonify({'error': error})


# @app.route('/get_history', methods=["GET"])
# def getHistory():

#     history = stats_db["history"]

#     username = request.args.get('username')

#     try:
#         cursor = history.find({"username": username})
#         return dumps(list(cursor))
#     except Exception as error:
#         return jsonify({'error': error})


# @app.route("/save_history", methods=["POST"])
# def saveHistory():
#     reqBody = request.get_json()

#     history = stats_db["history"]

#     username = request.args.get('username')

#     try:
#         history.replace_one(
#             {"username": username},
#             {"username": username, "history": reqBody},
#             True
#         )
#         return jsonify({'success': 200})
#     except Exception as error:
#         return jsonify({'error': error})


# @app.route("/save_score_to_leaderboard", methods=["POST"])
# def saveScoreToLeaderboard():
#     reqBody = request.get_json()

#     leaderboard = stats_db["leaderboard"]

#     # recomputing score and multis to avoid cheated score posting

#     totalBaseScore = 0
#     for path in reqBody["paths"]:
#         totalBaseScore += generateScore(getDistanceFromLatLonInKm(
#             path[0]["lat"], path[0]["lng"], path[1]["lat"], path[1]["lng"]), reqBody["gamemode"])

#     reqBody["basescore"] = totalBaseScore
#     multi = getGameMulti(reqBody["gamemode"], reqBody["population"])
#     reqBody["multi"] = multi
#     reqBody["score"] = totalBaseScore * multi

#     try:
#         leaderboard.insert_one(reqBody)
#         return jsonify({'success': 200})
#     except Exception as error:
#         return jsonify({'error': error})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)


def generateScore(distance, gamemode):
    if gamemode == 'europe':
        if distance > 1500:
            return 0
        elif distance <= 50:
            return 1000
        else:
            return math.floor(1000 * (1 - ((distance - 50) / 1450)) ** 2)
    elif (gamemode == 'americas'):
        if (distance > 2000):
            return 0
        elif (distance <= 50):
            return 1000
        else:
            return math.floor(1000 * (1 - ((distance - 50) / 1950)) ** 2)

    elif (gamemode == 'africa'):
        if (distance > 2500):
            return 0
        elif (distance <= 50):
            return 1000
        else:
            return math.floor(1000 * (1 - ((distance - 50) / 2450)) ** 2)

    elif (gamemode == 'asia/oceania'):
        if (distance > 2000):
            return 0
        elif (distance <= 50):
            return 1000
        else:
            return math.floor(1000 * (1 - ((distance - 50) / 1950)) ** 2)

    else:
        if (distance > 2500):
            return 0
        elif (distance <= 50):
            return 1000
        else:
            return math.floor(1000 * (1 - ((distance - 50) / 2450)) ** 2)


def getDistanceFromLatLonInKm(lat1, lng1, lat2, lng2):
    R = 6371
    dLat = deg2rad(lat2 - lat1)
    dLon = deg2rad(lng2 - lng1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(deg2rad(lat1)) * \
        math.cos(deg2rad(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c
    return math.floor(d)


def deg2rad(deg):
    return deg * (math.pi / 180)


def getGameMulti(zone, population):
    zoneMultis = {
        "worldwide": 4,
        "europe": 0,
        "africa": 0,
        "americas": 1,
        "asia/oceania": 2.5
    }
    popMultis = {
        "500": 5,
        "10000": 3,
        "50000": 2,
        "100000": 1,
        "500000": 0
    }
    return 1 + zoneMultis[zone] + popMultis[population]




