import os
import math
from itertools import combinations_with_replacement
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.json_util import dumps

app = Flask(__name__)
CORS(app)


mongo_places = PyMongo(app, uri='mongodb://' + os.environ['MONGODB_USERNAME'] + ':' +
                       os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/places?authSource=admin')
mongo_stats = PyMongo(app, uri='mongodb://' + os.environ['MONGODB_USERNAME'] + ':' +
                      os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/stats?authSource=admin')

places_db = mongo_places.db
stats_db = mongo_stats.db


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
    a = math.sin(dLat / 2) * math.sin(dLat / 2) +  math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
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



@app.route('/')
def ping_server():
    return "Hello World"


@app.route('/test')
def test():
    cities = places_db["cities500"]

    cursor = cities.aggregate([
        {"$match": {"population": {"$gte": 18900000}}},
        {"$sample": {"size": 1}}
    ])

    list_cursor = list(cursor)
    return dumps(list_cursor)


@app.route('/get_random_place', methods=["GET"])
def getRandomPlace():

    cities = places_db["cities500"]

    population = request.args.get('pop')
    zone = request.args.get('zone')

    try:
        if zone == "worldwide":
            cursor = cities.aggregate([
                {"$match": {"population": {"$gte": int(population)}}},
                {"$sample": {"size": 1}}
            ])
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

            cursor = cities.aggregate([
                {"$match": {"continent": {"$in": continents[zone]}, "population": {
                    "$gte": int(population)}}},
                {"$sample": {"size": 1}}
            ])

        return dumps(list(cursor))
    except Exception as error:
        return jsonify({'error': error})


@app.route('/get_leaderboard', methods=["GET"])
def getLeaderboard():

    leaderboard = stats_db["leaderboard"]

    try:
        cursor = leaderboard.aggregate([
            {"$sort": {"score": -1}},
            {"$sample": {"size": 100}}
        ])

        return dumps(list(cursor))
    except Exception as error:
        return jsonify({'error': error})


@app.route('/get_rank_from_leaderboard', methods=["GET"])
def getRankFromLeaderboard():

    leaderboard = stats_db["leaderboard"]

    highscore = request.args.get('highscore')

    try:
        rank = leaderboard.find(
            {"score": {"$gt": int(highscore)}}).sort("score", -1)
        return dumps(len(list(rank)))
    except Exception as error:
        return jsonify({'error': error})


@app.route('/get_history', methods=["GET"])
def getHistory():

    history = stats_db["history"]

    username = request.args.get('username')

    try:
        cursor = history.find({"username": username})
        return dumps(list(cursor))
    except Exception as error:
        return jsonify({'error': error})


@app.route("/save_history", methods=["POST"])
def saveHistory():
    reqBody = request.get_json()

    history = stats_db["history"]

    username = request.args.get('username')

    try:
        history.replace_one(
            {"username": username},
            {"username": username, "history": reqBody},
            True
        )
        return jsonify({'success': 200})
    except Exception as error:
        return jsonify({'error': error})


@app.route("/save_score_to_leaderboard", methods=["POST"])
def saveScoreToLeaderboard():
    reqBody = request.get_json()

    leaderboard = stats_db["leaderboard"]

    # recomputing score and multis to avoid cheated score posting

    totalBaseScore = 0
    for path in reqBody["paths"]:
        totalBaseScore += generateScore(getDistanceFromLatLonInKm(path[0]["lat"],path[0]["lng"],path[1]["lat"],path[1]["lng"]), reqBody["gamemode"])

    reqBody["basescore"] = totalBaseScore
    multi = getGameMulti(reqBody["gamemode"],reqBody["population"])
    reqBody["multi"] = multi
    reqBody["score"] = totalBaseScore * multi

    try:
        leaderboard.insert_one(reqBody)
        return jsonify({'success': 200})
    except Exception as error:
        return jsonify({'error': error})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)