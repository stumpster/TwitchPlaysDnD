import boto3
import datetime
import json
import librosa
import obsws_python as obs
import os
import random
import sys
import subprocess
import time
import utils
from character import Character

activeUsers = {}
activeChars = {}
charList = []

with open('config.json') as f:
  config = json.load(f)
  for character in config["characters"]:
    charList.append(Character(character, config["characters"][character]["voice"]))

obsClient = obs.ReqClient(host=config["obs_settings"]["host"], port=config["obs_settings"]["port"], password=config["obs_settings"]["password"])

def updateUser(user):
  # add a user to the list of users with the time of their latest message
  global activeUsers
  activeUsers[user] = datetime.datetime.now()

def changeUsers():
  # Pull a user that has sent a message within the last five minutes
  global activeUsers
  global activeChars
  chosenList = []
  for character in charList:
    while True:
      random_key = random.choice(list(activeUsers.keys()))
      if random_key in chosenList:
        continue
      if (datetime.datetime.now() - activeUsers[random_key]).total_seconds() < 300:
        activeChars[random_key] = character
        # add user to chosen list so they can't get chosen again
        chosenList.append(random_key)
        character.setPlayer(random_key)
        break

def handleMessage(user, message):
  # if the user is one of the characters, have them talk
  # also update the time of the users last message
  global activeChars
  
  print(activeChars)
  updateUser(user)
  if user in activeChars.keys():
    # write to file attached to character
    activeChars[user].writeMessageTextAndSpeak(message)
  
def rollDice(numDice=config["dice_settings"]["dice_number"], numSides=config["dice_settings"]["dice_sides"]):
  value = 0
  for i in range(numDice):
    value += random.randint(1, numSides)
    print("Rolled " + str(value))
    
  with open("local/diceresult.txt", "w") as f:
    print("Writing to diceresult.txt")
    f.write(str(value))
  
  diceAnimationId = utils.getItemId(config["dice_settings"]["obs_dice_animation_name"])
  diceBackgroundId = utils.getItemId(config["dice_settings"]["obs_dice_background_name"])
  diceResultId = utils.getItemId(config["dice_settings"]["obs_dice_result_name"])

  obsClient.set_scene_item_enabled(scene_name=config["obs_settings"]["scene_name"], item_id=diceAnimationId, enabled=True)
  time.sleep(config["dice_settings"]["obs_dice_animation_length"])
  obsClient.set_scene_item_enabled(scene_name=config["obs_settings"]["scene_name"], item_id=diceAnimationId, enabled=False)
  obsClient.set_scene_item_enabled(scene_name=config["obs_settings"]["scene_name"], item_id=diceBackgroundId, enabled=True)
  obsClient.set_scene_item_enabled(scene_name=config["obs_settings"]["scene_name"], item_id=diceResultId, enabled=True)
  time.sleep(config["dice_settings"]["obs_dice_result_length"])
  obsClient.set_scene_item_enabled(scene_name=config["obs_settings"]["scene_name"], item_id=diceBackgroundId, enabled=False)
  obsClient.set_scene_item_enabled(scene_name=config["obs_settings"]["scene_name"], item_id=diceResultId, enabled=False)
  return value