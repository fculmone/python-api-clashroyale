import urllib.request
import json
import os
from dotenv import load_dotenv

class ClanData:
  def __init__(self, clan_tag: str):
    self.clan_tag = clan_tag
  
  def getClanData(self):
    clan_tag = "%23" + self.clan_tag

    load_dotenv()
    
    CLASH_API_KEY = os.environ['CLASH_API_KEY']

    base_url = "https://api.clashroyale.com/v1"

    endpoint = f"/clans/{clan_tag}/members"

    request = urllib.request.Request(
      base_url + endpoint,
      None,
      {
        "Authorization": "Bearer %s" % CLASH_API_KEY
      }
    )

    try:
      response = urllib.request.urlopen(request).read().decode("utf-8")

      clan_data = json.loads(response)

      endpoint = f"/clans/{clan_tag}/riverracelog?limit=10"

      request = urllib.request.Request(
        base_url + endpoint,
        None,
        {
          "Authorization": "Bearer %s" % CLASH_API_KEY
        }
      )

      response = urllib.request.urlopen(request).read().decode("utf-8")

      riverrace_log = json.loads(response)

      data = [clan_data, riverrace_log]

      return data
    except:
      error = {
        "Cannot find clan tag": self.clan_tag
      }

      data = [error]
      return data


