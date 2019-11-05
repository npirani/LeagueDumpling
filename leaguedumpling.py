# importing libraries 
import requests
import json 
import os
import sys
import time as t
import board
import neopixel
from colour import Color
from datetime import datetime, time

# load settings from json file
with open(os.path.join(sys.path[0], "config.json"), "r") as f:
    settings = json.load(f)[0]

# setting neopixel pin to D18
pixel_pin = board.D18

# number of neopixels
num_pixels = 2
ORDER = neopixel.GRB

# initializing neopixels with dayPerc as the default brightness
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=float(settings['dayPerc']), auto_write=False,
                           pixel_order=ORDER)

# api-endpoints, URLs stored in config.json in case of version change
baseURL = "https://" + settings['region'] + ".api.riotgames.com"
matchListURL = baseURL + settings['matchListURL']
matchDetailURL = baseURL + settings['matchDetailURL']
summonerURL = baseURL + settings['summonerURL'] + settings['summoner']
spectatorURL = baseURL + settings['spectatorURL']
  
# defining 2 params dicts for the parameters to be sent to the API 
listPARAMS = {'api_key': settings['apiKey'],
            'endIndex': settings['matchNum']} 
PARAMS = {'api_key': settings['apiKey']} 

# match vars
lastMatches = []
lastMatchResults = []
error = False
errorCount = 0

# hardcoded IDs as backup
summonerId = "ChangeMe" 
accountId = "ChangeMe"

# gets IDs from summoner name
def getSummonerId():
    global error
    global matchListURL
    global spectatorURL
    global accountId
    global summonerId
    r = requests.get(url = summonerURL, params = PARAMS)
    print("GET:  " + r.url)
    if (r.status_code == requests.codes.ok):
        print("OK")
        data = r.json() 
        summonerId = data['id']
        accountId = data['accountId']
    else: 
        print('ERROR:   ' + str(r.status_code) + "  MESSAGE:    " + r.text)
        error = True
    matchListURL += accountId
    spectatorURL += summonerId

# checks if player is in a game
def checkInGame():
    r = requests.get(url = spectatorURL, params = PARAMS)
    print("GET:  " + r.url)
    if (r.status_code == requests.codes.ok):
        print("Summoner in game")
        return True
    else: 
        print('Summoner not in game')
        return False

# refreshes the match list
def refreshMatchList():
    global error
    # sending get request and saving the response as response object 
    r = requests.get(url = matchListURL, params = listPARAMS)
    print("GET:  " + r.url)
    if (r.status_code == requests.codes.ok):
        print("OK")
        # extracting data in json format 
        data = r.json() 
        lastMatches.clear()
        for k in data['matches']:
            lastMatches.append(k['gameId'])
        if len(lastMatches) == 0:
            print('No matches stored/returned?')
            error = True
        else:
            error = False
    else: 
        print('ERROR:   ' + str(r.status_code) + "  MESSAGE:    " + r.text)
        error = True

# refreshes the match results
def refreshMatchResults():
    global error
    lastMatchResults.clear()
    for matchId in lastMatches:
        r = requests.get(matchDetailURL + str(matchId), PARAMS)
        win = False
        participantId = -1
        print("GET:  " + r.url)
        if (r.status_code == requests.codes.ok):
            data = r.json()
            win = (data['teams'][0]['win'] == 'Win')
            for p in data['participantIdentities']:
                if p['player']['summonerId'] == summonerId:
                    participantId = p['participantId']
            if participantId == -1:
                print("No participants found for match: " + str(matchId))
                error = True
            else:
                error = False
            if ((win and participantId < 6) or (not win and participantId >= 6)):
                lastMatchResults.append(True)
            else:
                lastMatchResults.append(False)
        else: 
            print('ERROR:   ' + str(r.status_code) + "  MESSAGE:    " + r.text)
            error = True

# convert decimal RGB to 8 bit int
def floatToRGBInt(colorFloat):
    return  int(round(255.0 * colorFloat))

# set the LEDs to the error colour
def setError():
    pixels.fill((255, 255, 0))
    pixels.show()

# sets the LEDs to match win/loss perc
def setMatchColour():
    global lastMatchResults
    winPerc = 0.0
    c = Color(hsl=(0.83333333333, 1, 0.6))
    for m in lastMatchResults:
        if m:
            winPerc += 1
    winPerc = winPerc / len(lastMatchResults)
    c.hue = c.hue - (winPerc - 0.5) * 120 / 360
    c.luminance = 0.90 - abs((winPerc - 0.5) * 0.8)
    pixels.fill((floatToRGBInt(c.red), floatToRGBInt(c.green), floatToRGBInt(c.blue)))
    pixels.show()

# animation for when a summoner is in-game
def inGameAnimation():
    global pixels
    inGameColour = [100, 255, 120]
    count = 100
    maxCount = 100
    direction = -1
    t_end = datetime.now().timestamp() + 60 * 5
    while datetime.now().timestamp() < t_end:
        if count == 0:
            direction = 1
            t.sleep(0.1)
        if count == maxCount:
            direction = -1
            t.sleep(0.2)
        pixels.fill((inGameColour[0], inGameColour[1], inGameColour[2]))
        pixels.show()
        inGameColour[0] += direction
        inGameColour[1] += direction
        inGameColour[2] += direction
        count += direction
        t.sleep(0.025)

# check to see if current time is between begin and end
def isTimeBetween(beginTime, endTime):
    checkTime = datetime.now().time()
    if beginTime < endTime:
        return checkTime >= beginTime and checkTime <= endTime
    else:
        return checkTime >= beginTime or checkTime <= endTime

# sets day or night brightness depending on current time and config
def setNightDayBrightness():
    if isTimeBetween(time(int(settings['nightStart']), 00), time(int(settings['nightEnd']), 00)):
        pixels.brightness = float(settings['nightPerc'])
        print("Night brightness set")
    else:
        pixels.brightness = float(settings['dayPerc'])
        print("Day brightness set")


# start the script
getSummonerId()
if error:
    print("Could not get IDs from summoner name")
    setError()
while True:
    if settings['nightMode'] == 1:
        setNightDayBrightness()
    if checkInGame():
        inGameAnimation()
    else:
        refreshMatchList()
        print(len(lastMatches))
        print(error)
        while error:
            setError()
            errorCount += 1
            t.sleep(5)
            print("Trying to refresh matchlist. Try {}".format(errorCount))
            refreshMatchList()
            if errorCount >= 5:
                print('Try limit reached')
                errorCount = 0
                break
        if error:
            setError()
            t.sleep(600)
            continue
        refreshMatchResults()
        setMatchColour()
        t.sleep(300)

    
