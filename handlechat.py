import datetime
import json
import obsws_python as obs
import random
import time
import utils
from character import Character
from chatgptdm import ChatGPTDM

class ChatManager:
  def __init__(self):
    self.activeUsers = {}
    self.activeChars = {}
    self.charList = []

    with open('config.json') as f:
      config = json.load(f)
    self.chatGPTDMEnabled = config["chatgpt_settings"]["enabled"]
    
    if not self.chatGPTDMEnabled:
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
    self.actionPollList = {}
    self.pollStarted = False
    self.pollStartTime = 0
    self.msgShortcutList = {}
    self.msgShortcutCount = 1
    self.timerLength = 20

    if self.chatGPTDMEnabled:
      self.ChatGPTDM = ChatGPTDM()
      self.ChatGPTDM.clearAllMessages()

    with open("local/timer.txt", "w") as f:
      f.write(str(self.timerLength-1))
    
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
    if self.chatGPTDMEnabled:
      if message in self.msgShortcutList.keys():
        self.actionPollList[self.msgShortcutList[message]] += 1
      elif message.startswith("!submit"):
        # if the GM isn't in conversation, start a poll if there isn't one already
        if self.ChatGPTDM.getConversationStatus() == False and self.pollStarted == False:
          self.startPoll()

        message = message.replace("!submit ", "")
        self.actionPollList[message] = 1
        self.msgShortcutList["!"+str(self.msgShortcutCount)] = message
        self.msgShortcutCount += 1
      elif message in self.actionPollList.keys():
        self.actionPollList[message] += 1
      if self.pollStarted:
        self.updatePollList()

    else:
      # if the user is one of the characters, have them talk
      # also update the time of the users last message
      self.updateUser(user)
      if user in self.activeChars.keys() and not self.muted:
        # write to file attached to character
        self.activeChars[user].writeMessageTextAndSpeak(message)

  def updatePollList(self):
    # update the poll list   
    with open("local/poll.txt", "w") as f:
      for entry in sorted(self.actionPollList.items(), key=lambda x:x[1], reverse=True):
        f.write(str(utils.getKey(entry[0],self.msgShortcutList)) + " " + entry[0] + ": " + str(entry[1]) + "\n")

  def startPoll(self):
    self.pollStarted = True
    self.pollStartTime = time.time()
    with open("local/timer.txt", "w") as f:
      timeLeft = int(self.timerLength - (time.time() - self.pollStartTime))
      f.write(str(timeLeft))
    utils.showItem("Timer")

  def stopPoll(self):
    self.pollStarted = False
    utils.hideItem("Timer")
    with open("local/timer.txt", "w") as f:
      # fudging this a little bit since the timer takes a second to update
      f.write(str(self.timerLength-1))

  def updateTimer(self):
    if self.chatGPTDMEnabled:
      if self.pollStarted:
        timeLeft = int(self.timerLength - (time.time() - self.pollStartTime))
        if timeLeft < 0:
          self.stopPoll()
          # handle the poll results
          print("Poll is over sending results")
          print(self.actionPollList)
          if self.actionPollList != {}:
            messageToSend = sorted(self.actionPollList.items(), key=lambda x:x[1], reverse=True)[0][0]
            print(messageToSend)
            with open("local/poll.txt", "w") as f:
              f.write("Winning action: \n" + messageToSend)
            self.ChatGPTDM.chatInput(messageToSend)
            self.resetPoll()
        else:
          with open("local/timer.txt", "w") as f:
            f.write(str(timeLeft))

  def resetPoll(self):
    self.actionPollList = {}
    self.msgShortcutList = {}
    self.msgShortcutCount = 1
    with open("local/poll.txt", "w") as f:
      f.write("")

  def muteCharacters(self):
    # prevent messages from being processed so no character text is written and no voicelines are spoken
    self.muted = True

  def unmuteCharacters(self):
    # unmute the chat and allow for messages to be processed
    self.muted = False
  
  def rollDice(self, numDice=None, numSides=None, bonus=None):
    utils.hideItem("Poll")
    self.stopPoll()
    if numDice == None:
      numDice = self.numDice
    if numSides == None:
      numSides = self.numSides
    if bonus == None:
      bonus = 0

    value = 0
    for i in range(numDice):
      value += random.randint(1, numSides)
      print("Total value of die is " + str(value))
    
    value += bonus
    with open("local/diceresult.txt", "w") as f:
      print("Writing to diceresult.txt")
      f.write(str(value))

    utils.showItem(self.diceAnimation)
    time.sleep(self.diceAnimationLength)
    utils.hideItem(self.diceAnimation)
    utils.showItem(self.diceStatic)
    utils.showItem(self.diceResult)
    if numDice == 1 and value == 1:
      print("Critical Fail!")
      utils.showItem("CritFail")
    elif numDice == 1 and (value-bonus) == numSides:
      print("Critical Success!")
      utils.showItem("Crit")
    time.sleep(self.diceResultLength)
    utils.hideItem(self.diceResult)
    utils.hideItem(self.diceStatic)
    utils.hideItem("Crit")
    utils.hideItem("CritFail")

    if self.chatGPTDMEnabled:
      self.ChatGPTDM.chatInput("The dice result is a " + str(value))
      self.resetPoll()
      self.stopPoll()
      utils.showItem("Poll")