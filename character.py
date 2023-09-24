import boto3
import librosa
import os
import random
import sys
import time
import utils

class Character:
  def __init__(self, name, voice):
    self.name = name
    self.voice = voice
    self.player = ""

    self.image_item_id = utils.getItemId(self.name + " Image")
    self.message_text_item_id = utils.getItemId(self.name + " Chat")
    self.player_text_item_id = utils.getItemId(self.name + " Player")
  
  def getName(self):
    return self.name
  
  def getImageItemId(self):
    return self.image_item_id
  
  def getVoice(self):
    return self.voice

  def getPlayer(self):  
    return self.player
  
  def setPlayer(self, player):
    print("Changing " + self.name + " to " + player)
    self.player = player
    with open("local/" + self.name + "player.txt", "w") as f:
      print("Writing to " + self.name + "player.txt")
      f.write(player)

  def shakeCharacter(self, length):
  # shake the character for the length of the recording to simulate talking
    end_time = time.time() + length
    while time.time() < end_time:
      utils.obsClient.set_scene_item_transform(scene_name=utils.config["obs_settings"]["scene_name"], item_id=self.image_item_id, transform={'rotation': random.uniform(-2.0, 2.0)})
      time.sleep(0.04)
    utils.obsClient.set_scene_item_transform(scene_name=utils.config["obs_settings"]["scene_name"], item_id=self.image_item_id, transform={'rotation': 0.0})

  def writeMessageTextAndSpeak(self, message):
    with open("local/" + self.name + ".txt", "w") as f:
      print("Writing to " + self.name + "chat.txt")
      f.write(message)

    #sleep for a bit to make sure the file is written and updated in OBS
    time.sleep(0.2)

    polly_client = boto3.Session(
      aws_access_key_id = utils.config["aws_settings"]["aws_access_key_id"],                     
      aws_secret_access_key = utils.config["aws_settings"]["aws_secret_access_key"],
      region_name = utils.config["aws_settings"]["aws_region"]).client('polly')

    response = polly_client.synthesize_speech(VoiceId=self.voice,
      OutputFormat='mp3', 
      Text = message,
      Engine = 'standard')

    file = open("local/" + self.name + '.mp3', 'wb')
    file.write(response['AudioStream'].read())
    file.close()
    if sys.platform == "win32":
      lengthOfRecording = librosa.get_duration(path="local/" + self.name + '.mp3')
      os.startfile(os.getcwd() + "/local/" + self.name + '.mp3')
      self.shakeCharacter(lengthOfRecording)
    else:
      # The following works on macOS and Linux. (Darwin = mac, xdg-open = linux).
      opener = "open" if sys.platform == "darwin" else "xdg-open"
      subprocess.call([opener, output])