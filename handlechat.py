import boto3
import datetime
import json
import librosa
#import obspython as obs
import obsws_python as obs
import os
import random
import sys
import subprocess
import time

activeUsers = {}
activeChars = {}
charList = []

with open('config.json') as f:
  config = json.load(f)
  for character in config["characters"]:
    charList.append(character)

  OBS_HOST = config["obs_settings"]["host"]
  OBS_PORT = config["obs_settings"]["port"]
  OBS_PASSWORD = config["obs_settings"]["password"]
  LOCAL_FILESTORE = config["obs_settings"]["local_filestore"]
  AWS_ACCESS_KEY_ID = config["aws_settings"]["aws_access_key_id"]
  AWS_SECRET_ACCESS_KEY = config["aws_settings"]["aws_secret_access_key"]
  AWS_REGION = config["aws_settings"]["aws_region"]

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
        # TODO: notify channel of the change
        print("Changing " + character + " to " + random_key)
        break

def handleMessage(user, message):
  # if the user is one of the characters, have them talk
  # also update the time of the users last message
  global activeChars
  
  print(activeChars)
  updateUser(user)
  if user in activeChars.keys():
    # TODO: have a message get sent as a particular character
    # TODO: Replace with values in the config file

    # write to file attached to character
    with open("local/" + activeChars[user] + ".txt", "w") as f:
      print("Writing to " + activeChars[user] + "chat.txt")
      f.write(add_newlines(message))

    polly_client = boto3.Session(
      aws_access_key_id = AWS_ACCESS_KEY_ID,                     
      aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
      region_name = AWS_REGION).client('polly')

    response = polly_client.synthesize_speech(VoiceId=getCharacterVoice(activeChars[user]),
      OutputFormat='mp3', 
      Text = message,
      Engine = 'standard')

    file = open("local/" + activeChars[user] + '.mp3', 'wb')
    file.write(response['AudioStream'].read())
    file.close()
    if sys.platform == "win32":
      lengthOfRecording = librosa.get_duration(path="local/" + activeChars[user] + '.mp3')
      os.startfile(os.getcwd() + "/local/" + activeChars[user] + '.mp3')
      shakeCharacter(activeChars[user], lengthOfRecording)
    else:
      # The following works on macOS and Linux. (Darwin = mac, xdg-open = linux).
      opener = "open" if sys.platform == "darwin" else "xdg-open"
      subprocess.call([opener, output])

def shakeCharacter(character, length):
  cl = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD)
  item_id = cl.get_scene_item_id(scene_name="Scene", source_name=character + "image")
  print(f"Item ID: {item_id.scene_item_id}")
  print(length)
  end_time = time.time() + length
  while time.time() < end_time:
    cl.set_scene_item_transform(scene_name="Scene", item_id=item_id.scene_item_id, transform={'rotation': random.uniform(-2.0, 2.0)})
    time.sleep(0.04)
  cl.set_scene_item_transform(scene_name="Scene", item_id=item_id.scene_item_id, transform={'rotation': 0.0})
  

def getCharacterVoice(character):
  with open('config.json') as f:
    config = json.load(f)
    for char in config["characters"]:
      if char == character:
        return config["characters"][char]["voice"]

def add_newlines(message, char_limit=30):
    # Add newlines to a message every char_limit characters without splitting words.
    words = message.split()
    lines = []
    current_line = []

    for word in words:
        if len(' '.join(current_line) + ' ' + word) <= char_limit:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]

    # Add the last line if there's any content left
    if current_line:
        lines.append(' '.join(current_line))

    return '\n'.join(lines)

def rollDice(numDice=1, numSides=6):
    
  cl = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD)

  value = 0
  for i in range(numDice):
    value += random.randint(1, numSides)
    print("Rolled " + str(value))
  

  steve = cl.get_scene_item_id(scene_name="Scene", source_name="Steveimage")
  sarah = cl.get_scene_item_id(scene_name="Scene", source_name="Sarahimage")
  print(f"Steve: {steve.scene_item_id}")
  print(f"Sarah: {sarah.scene_item_id}")

  # write to file attached to character
  with open("local/dice.txt", "w") as f:
    print("Writing to dice.txt")
    f.write(str(value))
  cl.set_scene_item_enabled(scene_name="Scene", item_id=7, enabled=True)
  time.sleep(2.2)
  cl.set_scene_item_enabled(scene_name="Scene", item_id=7, enabled=False)
  cl.set_scene_item_enabled(scene_name="Scene", item_id=8, enabled=True)
  cl.set_scene_item_enabled(scene_name="Scene", item_id=9, enabled=True)
  time.sleep(8)
  cl.set_scene_item_enabled(scene_name="Scene", item_id=8, enabled=False)
  cl.set_scene_item_enabled(scene_name="Scene", item_id=9, enabled=False)
  return value