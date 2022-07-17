from itertools import combinations_with_replacement
from flask import Flask, jsonify, request
from flask_cors import CORS
import pymongo
from pymongo import MongoClient
from bson.json_util import dumps

app = Flask(__name__)
CORS(app)


CONNECTION_STRING = "mongodb+srv://root:Fuflo1297@cluster0.zjfbluk.mongodb.net/?retryWrites=true&w=majority"

def get_db_col(dbname, colname):
    client = pymongo.MongoClient(CONNECTION_STRING)
    db = pymongo.database.Database(client, dbname)
    col = pymongo.collection.Collection(db, colname)

    return col

@app.route('/')
def ping_server():
    return "Hello World"

@app.route('/test')
def test():
    cities = get_db_col("places","cities500")

    cursor = cities.aggregate([
        {"$match": {"population": {"$gte": 18900000}}},
        { "$sample": { "size": 1 } }
    ])

    list_cursor = list(cursor)
    return dumps(list_cursor)

@app.route('/get_random_15000')
def getRandom():
    cities = get_db_col("places","cities500")

    cursor = cities.aggregate([
        {"$match": {"population": {"$gte": 15000}}},
        { "$sample": { "size": 1 } }
    ])

    list_cursor = list(cursor)
    return dumps(list_cursor)

@app.route('/get_random_place')
def getRandomPlace():
    
    cities = get_db_col("places","cities500")

    population = request.args.get('pop')
    zone = request.args.get('zone')


    if population == "":
        population = "15000"
    
    if zone == "worldwide":
        cursor = cities.aggregate([
        { "$match": {"population": {"$gte": int(population)}}},
        { "$sample": { "size": 1 } }
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
            "americas": ["North America","South America"],
            "europe": ["Europe"],
            "asia": ["Asia"],
            "oceania": ["Oceania"],
            "asia/oceania": ["Asia", "Oceania"]
        }

        
        cursor = cities.aggregate([
        { "$match": {"continent": {"$in": continents[zone]},"population": {"$gte": int(population)}}},
        { "$sample": { "size": 1 } }
        ])

    list_cursor = list(cursor)
    return dumps(list_cursor)

if __name__=='__main__':
    app.run(host="0.0.0.0", port=5000)