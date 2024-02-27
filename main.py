from flask import Flask, request, jsonify
from clan_data import ClanData


app = Flask(__name__)

@app.route("/get-clan/<clan_tag>")
def get_clan(clan_tag):
  clan_data = {
    "clan_tag": clan_tag,
    "canadian_power_tag": "Q8UGY2V2",
    "name": "Canadian Power",
    "leader": "Mega Voltron"
  }

  test = ClanData(clan_tag)

  clan_data["test"] =  test.getClanData()

  return jsonify(clan_data), 200


@app.route("/healthy-check")
def healthy_check(): 
  return "OK :)", 200

if __name__ == "__main__":
  app.run(debug=True)