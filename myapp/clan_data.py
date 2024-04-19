import urllib.request
import json
import os
from dotenv import load_dotenv
import statistics
from scipy.stats import norm
from math import sqrt

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


  def __organizeData(self, data):
    retval = []
    table_data = []
    graph_data = []
    clan_name = ""
    for item in data[0]['items']:
      currentPlayer = {
        "Name": "",
        "Trophies": 0,
        "Points": 0,
        "Avg Points": 0,
        "Weeks": 0,
        "Donations": 0,
        "Donations Received": 0
      }
      currentPlayerWarHistory = {
        "Name": "",
        "War Weeks": [],
        "War Points": []
      }

      currentPlayer["Name"] = item["name"]
      currentPlayer["Trophies"] = item["trophies"]
      currentPlayer["Donations"] = item["donations"]
      currentPlayer["Donations Received"] = item["donationsReceived"]

      currentPlayerWarHistory["Name"] = item["name"]

      # Get the data for Points, Avg Points, and Weeks
      points = 0
      weeks = 0
      for war in data[1]["items"]:
        found_player = False
        for standing in war["standings"]:
          if standing["clan"]["tag"][1:] == self.clan_tag[3:] and clan_name == "":
            clan_name = standing["clan"]["name"]
          for participant in standing["clan"]["participants"]:
            if participant["tag"] == item["tag"] and standing["clan"]["tag"][1:] == self.clan_tag[3:]:
              weeks += 1
              points += participant["fame"]
              currentPlayerWarHistory["War Weeks"].append(str(war["seasonId"]) + '-' + str(war["sectionIndex"]))
              currentPlayerWarHistory["War Points"].append(participant["fame"])
              found_player = True
              break
          if found_player:
            break
    
      currentPlayer["Points"] = points
      
      if weeks != 0:
        currentPlayer["Avg Points"] = round(points / weeks)
      else:
        currentPlayer["Avg Points"] = points
        
      currentPlayer["Weeks"] = weeks

      table_data.append(currentPlayer)
      graph_data.append(currentPlayerWarHistory)

    retval.append(table_data)
    retval.append(graph_data)
    retval.append(clan_name) 
    return retval
 

  def __getRiverraceLog(self, key):
    base_url = "https://api.clashroyale.com/v1"

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

    return riverrace_log


  def __getCurrentRiverrace(self, key):
    base_url = "https://api.clashroyale.com/v1"

    endpoint = f"/clans/{self.clan_tag}/currentriverrace"

    request = urllib.request.Request(
      base_url + endpoint,
      None,
      {
        "Authorization": "Bearer %s" % key
      }
    )

    response = urllib.request.urlopen(request).read().decode("utf-8")

    curr_riverrace = json.loads(response)

    return curr_riverrace
  

  def __getClanFameHistory(self, key):
    clan_fame_history = []
    data = self.__getRiverraceLog(key)
    clan_name = ""
    most_recent_week = [data['items'][0]['seasonId'], data['items'][0]['sectionIndex']]
    for war in data['items']:
      for standing in war['standings']:
        if standing.get("clan").get("tag")[1:] == self.clan_tag[3:]:
          total_fame = 0
          clan_name = standing.get("clan").get("name")
          for participant in standing["clan"]["participants"]:
            total_fame += participant.get('fame')
          clan_fame_history.append(total_fame)
          
    return [clan_fame_history, clan_name, most_recent_week]
  
  
  def __calcProbabilitiesForFive(self, main_clan_fame_history, other_clan_fame_history):
    a_mean = statistics.mean(main_clan_fame_history[0])
    a_var = statistics.variance(main_clan_fame_history[0], a_mean)
    b_mean = statistics.mean(other_clan_fame_history[0][0])
    b_var = statistics.variance(other_clan_fame_history[0][0], b_mean)
    c_mean = statistics.mean(other_clan_fame_history[1][0])
    c_var = statistics.variance(other_clan_fame_history[1][0], c_mean)
    d_mean = statistics.mean(other_clan_fame_history[2][0])
    d_var = statistics.variance(other_clan_fame_history[2][0], d_mean)
    e_mean = statistics.mean(other_clan_fame_history[3][0])
    e_var = statistics.variance(other_clan_fame_history[3][0], e_mean)
    # a is the random variable for the main clan, b is the random variable for index 0 of other clans array,
    # c is the random variable for index 1 of the other clans array, and so on ...
    cdfs = {
      "a>b": 0,
      "a>c": 0,
      "a>d": 0,
      "a>e": 0,
    }

    # fill cdfs
    #   the curr_mean and curr_var are for the new random variable D where D = A - B
    #   since to calculate P(A>B), we need P(A-B>0)
    curr_mean = 0
    curr_var = 0

    curr_mean = a_mean - b_mean
    curr_var = a_var + b_var
    z_score = (0 - curr_mean) / sqrt(curr_var)
    prob = 1 - norm.cdf(z_score)
    cdfs["a>b"] = prob

    curr_mean = a_mean - c_mean
    curr_var = a_var + c_var
    z_score = (0 - curr_mean) / sqrt(curr_var)
    prob = 1 - norm.cdf(z_score)
    cdfs["a>c"] = prob
    
    curr_mean = a_mean - d_mean
    curr_var = a_var + d_var
    z_score = (0 - curr_mean) / sqrt(curr_var)
    prob = 1 - norm.cdf(z_score)
    cdfs["a>d"] = prob

    curr_mean = a_mean - e_mean
    curr_var = a_var + e_var
    z_score = (0 - curr_mean) / sqrt(curr_var)
    prob = 1 - norm.cdf(z_score)
    cdfs["a>e"] = prob

    
    print(cdfs)
    first_prob = cdfs["a>b"] * cdfs["a>c"] * cdfs["a>d"] * cdfs["a>e"]
    print(first_prob)

    second_prob = (1 - cdfs["a>b"]) * cdfs["a>c"] * cdfs["a>d"] * cdfs["a>e"]
    second_prob += (1 - cdfs["a>c"]) * cdfs["a>b"] * cdfs["a>d"] * cdfs["a>e"]
    second_prob += (1 - cdfs["a>d"]) * cdfs["a>c"] * cdfs["a>b"] * cdfs["a>e"]
    second_prob += (1 - cdfs["a>e"]) * cdfs["a>c"] * cdfs["a>d"] * cdfs["a>b"]
    print(second_prob)

    third_prob = (1 - cdfs["a>b"]) * (1 - cdfs["a>c"]) * cdfs["a>d"] * cdfs["a>e"]
    third_prob += (1 - cdfs["a>b"]) * (1 - cdfs["a>d"]) * cdfs["a>c"] * cdfs["a>e"]
    third_prob += (1 - cdfs["a>b"]) * (1 - cdfs["a>e"]) * cdfs["a>c"] * cdfs["a>d"]
    third_prob += (1 - cdfs["a>c"]) * (1 - cdfs["a>d"]) * cdfs["a>b"] * cdfs["a>e"]
    third_prob += (1 - cdfs["a>c"]) * (1 - cdfs["a>e"]) * cdfs["a>b"] * cdfs["a>d"]
    third_prob += (1 - cdfs["a>d"]) * (1 - cdfs["a>e"]) * cdfs["a>b"] * cdfs["a>c"]
    print(third_prob)

    fourth_prob = cdfs["a>b"] * (1 - cdfs["a>c"]) * (1 - cdfs["a>d"]) * (1 - cdfs["a>e"])
    fourth_prob += cdfs["a>c"] * (1 - cdfs["a>b"]) * (1 - cdfs["a>d"]) * (1 - cdfs["a>e"])
    fourth_prob += cdfs["a>d"] * (1 - cdfs["a>c"]) * (1 - cdfs["a>b"]) * (1 - cdfs["a>e"])
    fourth_prob += cdfs["a>e"] * (1 - cdfs["a>c"]) * (1 - cdfs["a>d"]) * (1 - cdfs["a>b"])
    print(fourth_prob)

    fifth_prob = (1 - cdfs["a>b"]) * (1 - cdfs["a>c"]) * (1 - cdfs["a>d"]) * (1 - cdfs["a>e"])
    print(fifth_prob)

    #total_prob should sum to 1
    total_prob = first_prob + second_prob + third_prob + fourth_prob + fifth_prob
    print(total_prob)

    return [first_prob, second_prob, third_prob, fourth_prob, fifth_prob]


  def __calcProbabilitiesForFour(self, main_clan_fame_history, other_clan_fame_history):
    a_mean = statistics.mean(main_clan_fame_history[0])
    a_var = statistics.variance(main_clan_fame_history[0], a_mean)
    b_mean = statistics.mean(other_clan_fame_history[0][0])
    b_var = statistics.variance(other_clan_fame_history[0][0], b_mean)
    c_mean = statistics.mean(other_clan_fame_history[1][0])
    c_var = statistics.variance(other_clan_fame_history[1][0], c_mean)
    d_mean = statistics.mean(other_clan_fame_history[2][0])
    d_var = statistics.variance(other_clan_fame_history[2][0], d_mean)
    # a is the random variable for the main clan, b is the random variable for index 0 of other clans array,
    # c is the random variable for index 1 of the other clans array, and so on ...
    cdfs = {
      "a>b": 0,
      "a>c": 0,
      "a>d": 0,
    }

    # fill cdfs
    #   the curr_mean and curr_var are for the new random variable D where D = A - B
    #   since to calculate P(A>B), we need P(A-B>0)
    curr_mean = 0
    curr_var = 0

    curr_mean = a_mean - b_mean
    curr_var = a_var + b_var
    z_score = (0 - curr_mean) / sqrt(curr_var)
    prob = 1 - norm.cdf(z_score)
    cdfs["a>b"] = prob

    curr_mean = a_mean - c_mean
    curr_var = a_var + c_var
    z_score = (0 - curr_mean) / sqrt(curr_var)
    prob = 1 - norm.cdf(z_score)
    cdfs["a>c"] = prob
    
    curr_mean = a_mean - d_mean
    curr_var = a_var + d_var
    z_score = (0 - curr_mean) / sqrt(curr_var)
    prob = 1 - norm.cdf(z_score)
    cdfs["a>d"] = prob

    
    print(cdfs)
    first_prob = cdfs["a>b"] * cdfs["a>c"] * cdfs["a>d"]
    print(first_prob)

    second_prob = (1 - cdfs["a>b"]) * cdfs["a>c"] * cdfs["a>d"]
    second_prob += (1 - cdfs["a>c"]) * cdfs["a>b"] * cdfs["a>d"]
    second_prob += (1 - cdfs["a>d"]) * cdfs["a>c"] * cdfs["a>b"]
    print(second_prob)

    third_prob = (1 - cdfs["a>b"]) * (1 - cdfs["a>c"]) * cdfs["a>d"]
    third_prob += (1 - cdfs["a>b"]) * (1 - cdfs["a>d"]) * cdfs["a>c"]
    third_prob += (1 - cdfs["a>c"]) * (1 - cdfs["a>d"]) * cdfs["a>b"]
    print(third_prob)


    fourth_prob = (1 - cdfs["a>b"]) * (1 - cdfs["a>c"]) * (1 - cdfs["a>d"])
    print(fourth_prob)

    #total_prob should sum to 1
    total_prob = first_prob + second_prob + third_prob + fourth_prob
    print(total_prob)

    return [first_prob, second_prob, third_prob, fourth_prob]


  def __calcProbabilitiesForThree(main_clan_fame_history, other_clan_fame_history):
    a_mean = statistics.mean(main_clan_fame_history[0])
    a_var = statistics.variance(main_clan_fame_history[0], a_mean)
    b_mean = statistics.mean(other_clan_fame_history[0][0])
    b_var = statistics.variance(other_clan_fame_history[0][0], b_mean)
    c_mean = statistics.mean(other_clan_fame_history[1][0])
    c_var = statistics.variance(other_clan_fame_history[1][0], c_mean)
    # a is the random variable for the main clan, b is the random variable for index 0 of other clans array,
    # c is the random variable for index 1 of the other clans array, and so on ...
    cdfs = {
      "a>b": 0,
      "a>c": 0,
    }

    # fill cdfs
    #   the curr_mean and curr_var are for the new random variable D where D = A - B
    #   since to calculate P(A>B), we need P(A-B>0)
    curr_mean = 0
    curr_var = 0

    curr_mean = a_mean - b_mean
    curr_var = a_var + b_var
    z_score = (0 - curr_mean) / sqrt(curr_var)
    prob = 1 - norm.cdf(z_score)
    cdfs["a>b"] = prob

    curr_mean = a_mean - c_mean
    curr_var = a_var + c_var
    z_score = (0 - curr_mean) / sqrt(curr_var)
    prob = 1 - norm.cdf(z_score)
    cdfs["a>c"] = prob

    
    print(cdfs)
    first_prob = cdfs["a>b"] * cdfs["a>c"]
    print(first_prob)

    second_prob = (1 - cdfs["a>b"]) * cdfs["a>c"]
    second_prob += (1 - cdfs["a>c"]) * cdfs["a>b"]
    print(second_prob)

    third_prob = (1 - cdfs["a>b"]) * (1 - cdfs["a>c"])
    print(third_prob)

    #total_prob should sum to 1
    total_prob = first_prob + second_prob + third_prob
    print(total_prob)

    return [first_prob, second_prob, third_prob]


  def __calcProbabilitiesForTwo(self, main_clan_fame_history, other_clan_fame_history):
    a_mean = statistics.mean(main_clan_fame_history[0])
    a_var = statistics.variance(main_clan_fame_history[0], a_mean)
    b_mean = statistics.mean(other_clan_fame_history[0][0])
    b_var = statistics.variance(other_clan_fame_history[0][0], b_mean)
    # a is the random variable for the main clan, b is the random variable for index 0 of other clans array,
    # c is the random variable for index 1 of the other clans array, and so on ...
    cdfs = {
      "a>b": 0,
    }

    # fill cdfs
    #   the curr_mean and curr_var are for the new random variable D where D = A - B
    #   since to calculate P(A>B), we need P(A-B>0)
    curr_mean = 0
    curr_var = 0

    curr_mean = a_mean - b_mean
    curr_var = a_var + b_var
    z_score = (0 - curr_mean) / sqrt(curr_var)
    prob = 1 - norm.cdf(z_score)
    cdfs["a>b"] = prob

    
    print(cdfs)
    first_prob = cdfs["a>b"]
    print(first_prob)

    second_prob = (1 - cdfs["a>b"])
    print(second_prob)

    #total_prob should sum to 1
    total_prob = first_prob + second_prob
    print(total_prob)

    return [first_prob, second_prob]


  def __calcProbabilities(self, key):
    curr_rivverrace = ""
    try:
      curr_riverrace = self.__getCurrentRiverrace(key)
    except:
      return self.clan_tag + " clan not in riverrace"
    

    main_clan_fame_history = self.__getClanFameHistory(key)



    other_clans_fame_history=[]
    for clan in curr_riverrace['clans']:
      if clan.get('tag')[1:] != self.clan_tag[3:]:
        curr_clan = ClanData(clan.get('tag'))
        other_clans_fame_history.append(curr_clan.__getClanFameHistory(key))

    probabilities = []

    is_one_clan_historyless = False
    if len(main_clan_fame_history[0]) == 0:
      is_one_clan_historyless = True
    for clan_history in other_clans_fame_history:
      if len(clan_history[0]) == 0:
        is_one_clan_historyless = True
    
    if is_one_clan_historyless:
      probabilities = []
    else:
      if len(other_clans_fame_history) == 4:
        probabilities = self.__calcProbabilitiesForFive(main_clan_fame_history, other_clans_fame_history)
      elif len(other_clans_fame_history) == 3:
        probabilities = self.__calcProbabilitiesForFour(main_clan_fame_history, other_clans_fame_history)
      elif len(other_clans_fame_history) == 2:
        probabilities = self.__calcProbabilitiesForThree(main_clan_fame_history, other_clans_fame_history)
      elif len(other_clans_fame_history) == 1:
        probabilities = self.__calcProbabilitiesForTwo(main_clan_fame_history, other_clans_fame_history)
      else:
        probabilities = []

    #organize the graph data so that all the histories are of length 10

    #create lables for the war history
    seasonID = main_clan_fame_history[2][0]
    sectionIndex = main_clan_fame_history[2][1]
    lables = []
    while len(lables) < 10:
      curr_label = str(seasonID) + '-' + str(sectionIndex)
      lables.append(curr_label)
      if sectionIndex != 0:
        sectionIndex -= 1
      else:
        seasonID -= 1
        sectionIndex = 3
    
    #remove the most recent clan label from the clan data cause its no longer needed
    main_clan_fame_history.pop()
    for clan in other_clans_fame_history:
      clan.pop()

    while len(main_clan_fame_history[0]) < 10:
      main_clan_fame_history[0].append(0)

    for clan in other_clans_fame_history:
      while len(clan[0]) < 10:
        clan[0].append(0)

    lables.reverse()

    main_clan_fame_history[0].reverse()

    for clan in other_clans_fame_history:
      clan[0].reverse()
      
    return [probabilities, main_clan_fame_history, other_clans_fame_history, lables]
    
    
    
    
  def getClanData(self):
    load_dotenv()
    CLASH_API_KEY = os.environ['CLASH_API_KEY']
    
    try:
      data = self.__callAPI(CLASH_API_KEY)
      return self.__organizeData(data)
    except Exception as e: 
      if "Forbidden" in str(e):
        BACKUP_CLASH_API_KEY = os.environ['BACKUP_CLASH_API_KEY']
        data = self.__callAPI(BACKUP_CLASH_API_KEY)
        return self.__organizeData(data)
      elif "Not Found" in str(e):
        data = [self.clan_tag]
        return data
      

  def getClanProbabilityData(self):
    load_dotenv()
    CLASH_API_KEY = os.environ['CLASH_API_KEY']
    self.__calcProbabilities(CLASH_API_KEY)
    try:
      return self.__calcProbabilities(CLASH_API_KEY)
    except Exception as e: 
      if "Forbidden" in str(e):
        BACKUP_CLASH_API_KEY = os.environ['BACKUP_CLASH_API_KEY']
        return self.__calcProbabilities(BACKUP_CLASH_API_KEY)
      elif "Not Found" in str(e):
        data = [self.clan_tag]
        return data



