import datetime
import json
import obsws_python as obs
import random
import time
import utils
from character import Character

class ChatManager:
  def __init__(self):
    self.activeUsers = {}
    self.activeChars = {}
    self.charList = []

    with open('config.json') as f:
      config = json.load(f)
    
    for character in config["characters"]:
      self.charList.append(Character(character))

    self.numDice = config["dice_settings"]["dice_number"]
    self.numSides = config["dice_settings"]["dice_sides"]
    self.sceneName = config["obs_settings"]["scene_name"]
    self.diceAnimation = config["dice_settings"]["obs_dice_animation_name"]
    self.diceStatic = config["dice_settings"]["obs_dice_background_name"]
    self.diceResult = config["dice_settings"]["obs_dice_result_name"]
    self.diceAnimationLength = config["dice_settings"]["obs_dice_animation_length"]
    self.diceResultLength = config["dice_settings"]["obs_dice_result_length"]
    self.muted = False
    
  def updateUser(self, user):
    # add a user to the list of users with the time of their latest message
    self.activeUsers[user] = datetime.datetime.now()

  def changeUsers(self):
    # Pull users that has sent a message within the last five minutes and assign them to a character
    chosenList = []
    for character in self.charList:
      while True:
        random_key = random.choice(list(self.activeUsers.keys()))
        if random_key in chosenList:
          continue
        if (datetime.datetime.now() - self.activeUsers[random_key]).total_seconds() < 300:
          self.activeChars[random_key] = character
          # add user to chosen list so they can't get chosen again
          chosenList.append(random_key)
          character.setPlayer(random_key)
          break

  def handleMessage(self, user, message):
    # if the user is one of the characters, have them talk
    # also update the time of the users last message
    self.updateUser(user)
    if user in self.activeChars.keys() and not self.muted:
      # write to file attached to character
      self.activeChars[user].writeMessageTextAndSpeak(message)

  def muteCharacters(self):
    # prevent messages from being processed so no character text is written and no voicelines are spoken
    self.muted = True

  def unmuteCharacters(self):
    # unmute the chat and allow for messages to be processed
    self.muted = False
  
  def rollDice(self, numDice=None, numSides=None):
    if numDice == None:
      numDice = self.numDice
    if numSides == None:
      numSides = self.numSides

    print("Rolling " + str(numDice) + "d" + str(numSides))
    value = 0
    for i in range(numDice):
      value += random.randint(1, numSides)
      print("Total value of die is " + str(value))
      
    with open("local/diceresult.txt", "w") as f:
      print("Writing to diceresult.txt")
      f.write(str(value))
    
    diceAnimationId = utils.getItemId(self.diceAnimation)
    diceBackgroundId = utils.getItemId(self.diceStatic)
    diceResultId = utils.getItemId(self.diceResult)

    utils.obsClient.set_scene_item_enabled(scene_name=self.sceneName, item_id=diceAnimationId, enabled=True)
    time.sleep(self.diceAnimationLength)
    utils.obsClient.set_scene_item_enabled(scene_name=self.sceneName, item_id=diceAnimationId, enabled=False)
    utils.obsClient.set_scene_item_enabled(scene_name=self.sceneName, item_id=diceBackgroundId, enabled=True)
    utils.obsClient.set_scene_item_enabled(scene_name=self.sceneName, item_id=diceResultId, enabled=True)
    time.sleep(self.diceResultLength)
    utils.obsClient.set_scene_item_enabled(scene_name=self.sceneName, item_id=diceBackgroundId, enabled=False)
    utils.obsClient.set_scene_item_enabled(scene_name=self.sceneName, item_id=diceResultId, enabled=False)