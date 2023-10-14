import boto3
import concurrent.futures
import elevenlabs
import glob
import librosa
import openai
import os
import random
import time

# from character import Character
from chatgptnpc import ChatGPTNPC
import utils

class ChatGPTDM:
  def __init__(self):
    self.openai_api_key = utils.config["chatgpt_settings"]["api_key"]
    self.eleven_labs_api_key = utils.config["eleven_labs_settings"]["api_key"]

    self.systemmsg = '''You are a game master who is leading a party though a campaign of Dungeons and Dragons. 
    The players are: a fighter named Roger, a cleric named Karrix, and a wizard named Sylvania.
    They are currently in a tavern. You should describe the scene but limit your description to two sentences.
    Prompt the players to roll dice to determine the outcome of their actions. After
    prompting the players to roll dice, end the message to indicate that the players should respond. Only one player
    should be prompted to roll dice at a time. If an NPC needs to roll a dice, you should roll the dice for them.
    The players are currently level 3 and should face challenges appropriate to their level.
    Make sure that the challenges the players face are a mixture of combat, traps, puzzles, and social encounters.
    When you are speaking as an NPC, wrap the characters message inside angle brackets containing the name of the NPC.
    Chat from an NPC should always be on a new line.
    For example, if you are speaking as a character named Bob, you would write <Bob> Hello, how are you?
    You should describe the character. This description should be no more than two sentences.
    This description should be inside square brackets after the angle brackets containing the name of the character.
    For example, if the character is a dwarf bartender with an eyepatch, you would write 
    <Bob> [dwarf bartender with eyepatch] Hello, how are you?
    If you are speaking as the game master that text should not be on the same line as text assigned to a character.
    '''
    self.messages = [{"role": "system", "content": self.systemmsg}]

    # self.character = Character("GM")

    self.characterAndNPCNumberMapping = {}
    self.namedMessageCount = {}
    self.conversationOrder = []
    self.currentNPCCount = 0
    self.doingConversation = False
    self.conversationCount = 0

    # resp = utils.obsClient.get_input_settings(name="GM Image")

    # check in the config.json if the user wants to use AWS or Eleven Labs for voice generation
    if utils.config["aws_settings"]["enabled"]:
      self.polly_client = boto3.Session(
          aws_access_key_id = utils.config["aws_settings"]["aws_access_key_id"],                     
          aws_secret_access_key = utils.config["aws_settings"]["aws_secret_access_key"],
          region_name = utils.config["aws_settings"]["aws_region"]).client('polly')

      self.voiceList = ["Nicole", "Russell", "Emma", "Brian", "Raveena", "Ivy", 
        "Joanna", "Kendra", "Kimberly", "Matthew", "Salli", 
        "Geraint", "Zeina", "Zhiyu", "Ruben", "Lotte", "Aditi",
        "Celine", "Mathieu", "Chantal", "Marlene", "Vicki", "Hans",
        "Carla", "Bianca", "Giorgio", "Mizuki", "Takumi", "Ricardo",
        "Camila", "Ines", "Cristiano", "Penelope", "Miguel",
        "Lupe"]
      
      # set default GM voice to Joey for AWS
      self.NPCList = [ChatGPTNPC("GM", "Joey")]

    elif utils.config["eleven_labs_settings"]["enabled"]:
      elevenlabs.set_api_key(self.eleven_labs_api_key)
      self.voiceList = elevenlabs.voices()
      print (self.voiceList[-3:])
      # set default GM voice to Antoni for Eleven Labs
      self.NPCList = [ChatGPTNPC("GM", self.voiceList[6])]
    else:
      print("No voice provider enabled. Please enable AWS or Eleven Labs in config.json.")
      exit()
    
    self.NPCList[0].setLocation("GM Image")
    self.NPCList[0].setHasImage(True)

    # print(resp)

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
    self.messages.append({"role": "user", "content": message})
    
    print("Sending message to GPT-3")
    print(self.messages)

    try:
      openai.api_key = self.openai_api_key
      response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=self.messages,
      )
    except:
      print("Error sending message to GPT-3")
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
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
      for line in message.splitlines():
        if (line == ""):
          continue
        if ("<" in line):
          character = line.split("<")[1].split(">")[0]
        else:
          character = "GM"
        
        # find first index of character in NPCList
        NPCIndex = next((index for (index, NPC) in enumerate(self.NPCList) if NPC.getName() == character), None)
        print("NPCIndex is " + str(NPCIndex))
        if NPCIndex is None:
          # randomly pick a voice for the character and add it to the list
          self.NPCList.append(ChatGPTNPC(character, self.voiceList[random.randint(0, len(self.voiceList) - 1)]))
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

    # reset the conversation order and message counts
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
    lengthOfRecording = librosa.get_duration(path="local/" + str(self.conversationCount) + self.NPCList[NPCIndex].getName() + str(messageId) + '.mp3')
    os.startfile(os.getcwd() + "/local/" + str(self.conversationCount) + self.NPCList[NPCIndex].getName() + str(messageId) + '.mp3')
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
      if (self.currentNPCCount == 4):
        # all slots are full, so we need to rotate out the oldest character
        self.currentNPCCount = 0
      self.NPCList[NPCIndex].setLocation("NPC" + str(self.currentNPCCount))
      self.currentNPCCount += 1

    # pulse the character using the opacity to simulate talking
    self.NPCList[NPCIndex].changeImageToNPC()
    self.NPCList[NPCIndex].pulseCharacter(message, length)
    return

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
      # if AWS is enabled, use Polly to generate the voice line
      if utils.config["aws_settings"]["enabled"]:
        response = self.polly_client.synthesize_speech(VoiceId=self.NPCList[NPCIndex].getVoice(),
          OutputFormat='mp3', 
          Text = message,
          Engine = 'standard')

        print("\nWriting to " + str(self.conversationCount) + self.NPCList[NPCIndex].getName() + str(characterChatId) + ".mp3")
        file = open("local\\" + str(self.conversationCount) + self.NPCList[NPCIndex].getName() + str(characterChatId) + '.mp3', 'wb')
        file.write(response['AudioStream'].read())
        file.close()
      # otherwise use ElevenLabs to generate the voice line
      else:
        elevenlabs.save(
          elevenlabs.generate(
            message, self.eleven_labs_api_key, self.NPCList[NPCIndex].getVoice()
          ),
          "local\\" + str(self.conversationCount) + self.NPCList[NPCIndex].getName() + str(characterChatId) + ".mp3"
        )
      return
    except:
      print("Error generating message for " + self.NPCList[NPCIndex].getName() + " message " + message + " with id " + str(characterChatId) + "\n")
      print(response)        
      return