import urllib.request
import json
import os
from dotenv import load_dotenv

class ClanData:
  def __init__(self, clan_tag: str):
    clan_tag = clan_tag.upper()
    if clan_tag[0] == '#':
      clan_tag = clan_tag.replace('#', '')
    self.clan_tag = "%23" + clan_tag

  def __callAPI(self, key):
    base_url = "https://api.clashroyale.com/v1"

    endpoint = f"/clans/{self.clan_tag}/members"

    request = urllib.request.Request(
      base_url + endpoint,
      None,
      {
        "Authorization": "Bearer %s" % key
      }
    )

    response = urllib.request.urlopen(request).read().decode("utf-8")

    clan_data = json.loads(response)

    endpoint = f"/clans/{self.clan_tag}/riverracelog?limit=10"

    request = urllib.request.Request(
      base_url + endpoint,
      None,
      {
        "Authorization": "Bearer %s" % key
      }
    )

    response = urllib.request.urlopen(request).read().decode("utf-8")

    riverrace_log = json.loads(response)

    data = [clan_data, riverrace_log]

    return data


  
  def getClanData(self):
    load_dotenv()
    CLASH_API_KEY = os.environ['CLASH_API_KEY']
    
    try:
      data = self.__callAPI(CLASH_API_KEY)
      return data
    except Exception as e: 
      if "Forbidden" in str(e):
        BACKUP_CLASH_API_KEY = os.environ['BACKUP_CLASH_API_KEY']
        data = self.__callAPI(BACKUP_CLASH_API_KEY)
        return data
      elif "Not Found" in str(e):
        data = [self.clan_tag]
        return data


