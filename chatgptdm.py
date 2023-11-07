import boto3
import concurrent.futures
import elevenlabs
import glob
import librosa
import os
import random
import string
import time

from openai import OpenAI

# from character import Character
from chatgptnpc import ChatGPTNPC
import utils

class ChatGPTDM:
  def __init__(self):
    self.openai_client = OpenAI(api_key=utils.config["chatgpt_settings"]["api_key"])

    self.systemmsg = '''You are a game master who is leading a party though a campaign of Dungeons and Dragons.'''
    self.systemmsg += ' The players are: '
    for name, properties in utils.config["characters"].items():
      if properties['is_gm'] == False:
        self.systemmsg += name + ", " + properties['description'] + ", "
    self.systemmsg += ''' and they are currently in a tavern. You should describe the scene but limit your description to two sentences.
    While you are playing the game, prompt the players to roll dice to determine the outcome of their actions. After
    prompting the players to roll dice, end the message to indicate that the players should respond. Only one player
    should be prompted to roll dice at a time. If an NPC needs to roll a dice, you should roll the dice for them.
    The players are currently level 3 and should face challenges appropriate to their level.
    Make sure that the challenges the players face are a mixture of combat, traps, puzzles, and social encounters.
    When you are speaking as an NPC or the characters are speaking, wrap the characters message inside angle brackets containing the name of the NPC or character.
    Chat from an NPC or character should always be on a new line. NPCs should be described in two sentences or less in the following format:
    1. This description should be inside square brackets after the angle brackets containing the name of the character.
    2. This description should contain whether or not the character is male or female.
    For example, if the character is a male dwarf bartender with an eyepatch, you would write 
    <Bob> [male dwarf bartender with eyepatch] Hello, how are you?
    If you are speaking as the game master that text should not be on the same line as text assigned to a character.
    If you are describing a scene or an important item, put the description inside curly brackets. As an example, describing a magic item might look like:
    The players find the Sword of Light {a sword that glows with a bright light when held by a good character}.
    '''
    self.messages = [{"role": "system", "content": self.systemmsg}]

    # self.character = Character("GM")

    self.NPCList = []
    self.characterAndNPCNumberMapping = {}
    self.namedMessageCount = {}
    self.conversationOrder = []
    self.currentNPCCount = 0
    self.doingConversation = False
    self.conversationCount = 0
    self.femaleVoiceList = []
    self.maleVoiceList = []

    # resp = utils.obsClient.get_input_settings(name="GM Image")
    # check in the config.json if the user wants to use AWS or Eleven Labs for voice generation
    if utils.config["aws_settings"]["enabled"]:
      self.polly_client = boto3.Session(
          aws_access_key_id = utils.config["aws_settings"]["aws_access_key_id"],                     
          aws_secret_access_key = utils.config["aws_settings"]["aws_secret_access_key"],
          region_name = utils.config["aws_settings"]["aws_region"]).client('polly')

      self.femaleVoiceList = ["Nicole", "Emma", "Raveena", "Ivy", 
        "Joanna", "Kendra", "Kimberly", "Salli", "Zeina", "Zhiyu", "Lotte", "Aditi",
        "Celine",  "Chantal", "Marlene", "Vicki", "Carla", "Bianca", "Mizuki", 
        "Camila", "Ines", "Penelope", "Lupe"]
      self.maleVoiceList = ["Russell", "Brian", "Matthew", "Ruben", "Mathieu", "Hans",
        "Giorgio", "Takumi", "Ricardo", "Cristiano", "Miguel", "Geraint"]

    elif utils.config["eleven_labs_settings"]["enabled"]:
      elevenlabs.set_api_key(utils.config["eleven_labs_settings"]["api_key"])
      tempVoiceList = elevenlabs.voices()
      for x in tempVoiceList:
        if x.labels['gender'] == 'female':
          self.femaleVoiceList.append(x)
        else:
          self.maleVoiceList.append(x)
    else:
      print("No voice provider enabled. Please enable AWS or Eleven Labs in config.json.")
      exit()

    for name, properties in utils.config["characters"].items():
      self.NPCList.append(ChatGPTNPC(name, properties['voice']))
      self.NPCList[len(self.NPCList)-1].generateCharacterImage(properties['description'])
      if properties['is_gm']:
        self.NPCList[len(self.NPCList)-1].setLocation(name)
        self.NPCList[len(self.NPCList)-1].changeImageToNPC()

    # clear out the NPC images
    for x in range(0, 4):
      utils.hideItem("NPC" + str(x))

  def clearAllMessages(self):
    """
    Clears all messages in the local NPC and GM text files.

    This method iterates through the NPC text files (NPC0.txt, NPC1.txt, NPC2.txt, and NPC3.txt) and clears their contents.
    It also clears the contents of the GM text file (GM.txt).

    Returns:
      None
    """
    for x in range(0, 4):
      with open("local/NPC" + str(x) + ".txt", "w") as f:
        f.write("")
    with open("local/GM.txt", "w") as f:
      f.write("")

  def getConversationCount(self):
    """
    Returns the number of conversations that have been processed by the chatbot.
    """
    return self.conversationCount

  def getConversationStatus(self):
    """
    Returns the current conversation status of the chatbot.

    Returns:
    bool: True if the chatbot is currently engaged in a conversation, False otherwise.
    """
    return self.doingConversation

  def chatInput(self, message):
    """
    Sends a message to the GPT API for processing and builds a new conversation based on that response.

    Args:
      message (str): The message to send to the GPT API.

    Returns:
      None
    """
    self.doingConversation = True
    if message.startswith("Draw: "):
      message = message.replace("Draw: ", "")
      # just going to cheat and use the first 5 characters of the message as the name
      utils.generateImage(message[:5], message)
      location = self.getNextLocation()
      utils.obsClient.set_input_settings(
        name=location,
        settings={'file': str(os.getcwd()) + '\\local\\' + message[:5] + ".png"},
        overlay=False
      )
      utils.obsClient.set_scene_item_enabled(
        scene_name=utils.config["obs_settings"]["scene_name"],
        item_id=utils.getItemId(location),
        enabled=True
      )
      self.resetConversation()
    else:
      message = message.replace("Action: ", "")
      self.messages.append({"role": "user", "content": message})
    
      print("Sending message to GPT-3")
      print(self.messages)

      try:
        response = self.openai_client.chat.completions.create(
          model = utils.config["chatgpt_settings"]["model"],
          messages = self.messages,
        )
      except:
        print("Error sending message to GPT")
        print(response)
        return

      print(response)

      self.buildConversation(response["choices"][0]["message"]["content"])

      self.messages.append({"role": "assistant", "content": response["choices"][0]["message"]["content"]})

      # if token number is getting high, remove the oldest message
      if response["usage"]["prompt_tokens"] > 3500:
        print("Removing oldest message.")
        print(self.messages[1])
        self.messages.pop(1)

  def splitMessages(self, s, n=200):
    segments = []
    start = 0

    while start < len(s):
        # If the remaining part of the string is shorter than n, just append it to the segments
        if len(s) - start <= n:
            segments.append(s[start:])
            break

        # Extract the substring starting from the nth character from the current starting point
        remainder = s[start + n:]

        # Find the next punctuation mark in the remainder
        splitPoint = next((i for i, char in enumerate(remainder) if char in ['.','!','?']), None)

        # If a punctuation mark is found, append the segment up to that point to the segments
        if splitPoint is not None:
            segments.append(s[start:start + n + splitPoint + 1])
            start += n + splitPoint + 1
        else:
            # If no punctuation is found, append the next n characters and move on
            segments.append(s[start:start + n])
            start += n

    return segments
  
  def generateArt(self, message):
    artList = []
    for line in message.splitlines():
      if line.contains("{"):
        artList.append("{" + line.split("{")[1].split("}")[0] + "}")
    return artList

  def buildConversation(self, message):
    """
    Builds a conversation by generating voice lines for each message in the input message string.

    Args:
      message (str): The message string to generate voice lines for.

    Returns:
      None
    """
    # make sure that angle brackets are on their own line
    message = message.replace("<", "\n<")

    # split up messages that are too long into their own messages
    allMessages = self.generateArt(message)
    speakingCharacter = "GM"
    for line in message.splitlines():
      if (line == ""):
        speakingCharacter = "GM"
        continue
      if ("<" in line):
        speakingCharacter = line.split("<")[1].split(">")[0]
      else:
        speakingCharacter = "GM"
      if len(line) > 150:
        splitMessages = self.splitMessages(line)
        for x in range(0, len(splitMessages)):
          if x == 0:
            allMessages.append(splitMessages[x])
          else:
            # make sure the character is still speaking
            allMessages.append("<" + speakingCharacter + "> " + splitMessages[x])
      else:
        allMessages.append(line)
    
    print(allMessages)
    with concurrent.futures.ThreadPoolExecutor() as executor:
      for line in allMessages:
        print("Processing line " + line + "\n")
        if "{" in line:
          print("Generating artwork\n")
          artMessage = line.split("{")[1].split("}")[0]
          executor.submit(utils.generateImage, artMessage[:5], artMessage)
        if "<" in line:
          character = line.split("<")[1].split(">")[0]
        else:
          character = "GM"
        
        # find first index of character in NPCList
        NPCIndex = next((index for (index, NPC) in enumerate(self.NPCList) if NPC.getName() == character), None)
        print("NPCIndex is " + str(NPCIndex))
        if NPCIndex is None:
          # randomly pick a voice for the character and add it to the list, try to check for male/female but not perfect
          if 'female' in line:
            self.NPCList.append(ChatGPTNPC(character, self.femaleVoiceList[random.randint(0, len(self.femaleVoiceList) - 1)]))
          else:
            self.NPCList.append(ChatGPTNPC(character, self.maleVoiceList[random.randint(0, len(self.maleVoiceList) - 1)]))
          NPCIndex = len(self.NPCList) - 1
        print("NPCIndex is " + str(NPCIndex))
        self.NPCList[NPCIndex].incrementMessageCount()
        self.conversationOrder.append([NPCIndex, self.NPCList[NPCIndex].getMessageCount(), utils.stripMessage(line)])

        print("Submitting " + line + " for " + character + " with id " + str(self.NPCList[NPCIndex].getMessageCount()))
        executor.submit(self.generateVoiceLine, line, NPCIndex, self.NPCList[NPCIndex].getMessageCount())

    # wait for all the messages to be generated, number of mp3 files should be equal to the number of messages
    while len(glob.glob1(os.getcwd() + "\\local\\","*.mp3")) < len(self.conversationOrder):
      time.sleep(1)
      print("Glob length is " + str(len(glob.glob1(os.getcwd() + "\\local\\" + str(self.conversationCount), "*.mp3"))) + " and conversation order length is " + str(len(self.conversationOrder)))
    
    # play the messages in order
    print(self.conversationOrder)
    for NPCIndex, messageId, message in self.conversationOrder:
      self.playNPCMessage(NPCIndex, messageId, message)
      time.sleep(0.15)
    self.resetConversation()

  def resetConversation(self):
    """
    Resets the conversation order and message counts.

    Args:
      None

    Returns:
      None
    """
    self.conversationOrder = []
    self.doingConversation = False
    self.conversationCount += 1
    for NPC in self.NPCList:
      NPC.clearMessageCount()

  def playNPCMessage(self, NPCIndex, messageId, message):
    """
    Plays the NPC message with the given index and ID, and displays it on the screen.

    Args:
      NPCIndex (int): The index of the NPC whose message is being played.
      messageId (int): The ID of the message being played.
      message (str): The message being played.

    Returns:
      None
    """
    try:
      lengthOfRecording = librosa.get_duration(path="local/" + str(self.conversationCount) + self.NPCList[NPCIndex].getName() + str(messageId) + '.mp3')
      os.startfile(os.getcwd() + "/local/" + str(self.conversationCount) + self.NPCList[NPCIndex].getName() + str(messageId) + '.mp3')
    except:
      # if for some reason we have an issue with the audio file, just show the text for some length of time
      lengthOfRecording = 5
    self.showAndPulseNPC(NPCIndex, message, lengthOfRecording)

  def showAndPulseNPC(self, NPCIndex, message, length):
    """
    Assigns a character to a slot if they aren't already, then pulses the character using the opacity to simulate talking.

    Args:
      NPCIndex (int): The index of the NPC in the NPCList.
      message (str): The message to be displayed by the NPC.
      length (int): The length of time in seconds for the pulse animation.

    Returns:
      None
    """
    # assign the character to a slot if they aren't already
    if (self.NPCList[NPCIndex].hasLocation() == False):
      self.NPCList[NPCIndex].setLocation(self.getNextLocation())

    # pulse the character using the opacity to simulate talking
    self.NPCList[NPCIndex].changeImageToNPC()
    self.NPCList[NPCIndex].pulseCharacter(message, length)
    return

  def getNextLocation(self):
    """
    Returns the next available location for a character to be assigned to.

    Args:
      None

    Returns:
      str: The next available location for a character to be assigned to.
    """
    if (self.currentNPCCount == 4):
      # all slots are full, so we need to rotate out the oldest character
      self.currentNPCCount = 0
    temp = self.currentNPCCount
    self.currentNPCCount += 1
    return "NPC" + str(temp)

  def generateVoiceLine(self, message, NPCIndex, characterChatId):
    """
    Generates a voice line for the specified NPC with the given message and character chat ID.

    Args:
        message (str): The message to generate a voice line for.
        NPCIndex (int): The index of the NPC to generate the voice line for.
        characterChatId (int): The ID of the character chat.

    Returns:
        None
    """
    if characterChatId == 1:
      self.NPCList[NPCIndex].generateCharacterImage(message)

    # strip message of descriptors and character name
    print("\nStripping message for " + self.NPCList[NPCIndex].getName() + " message " + message + " with id " + str(characterChatId))
    try:
      message = utils.stripMessage(message)
    except:
      print("Error stripping message for " + self.NPCList[NPCIndex].getName() + " message " + message + " with id " + str(characterChatId) + "\n")
      return
    # generate the message
    try:
      print("\nGenerating voice for " + self.NPCList[NPCIndex].getName() + " message " + message + " with id " + str(characterChatId))
      filename = str(self.conversationCount) + self.NPCList[NPCIndex].getName() + str(characterChatId)
      utils.createVoiceLine(self.NPCList[NPCIndex].getVoice(), message, filename)
      return
    except:
      print("Error generating message for " + self.NPCList[NPCIndex].getName() + " message " + message + " with id " + str(characterChatId) + "\n")   
      return