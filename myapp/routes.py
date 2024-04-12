from flask import Blueprint, request, jsonify
from myapp.clan_data import ClanData


main = Blueprint('main', __name__)

@main.route("/get-clan/<clan_tag>")
def get_clan(clan_tag):
  clan = ClanData(clan_tag)
  clan_data = clan.getClanData()
  return jsonify(clan_data), 200

@main.route("/get-clan-probability/<clan_tag>")
def get_clan_probability(clan_tag):
  clan = ClanData(clan_tag)
  clan_data = clan.getClanProbabilityData()
  return jsonify(clan_data), 200


@main.route("/healthy-check")
def healthy_check():
  return "OK :)", 200

