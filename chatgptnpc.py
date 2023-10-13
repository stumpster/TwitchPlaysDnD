import os
import random
import time

import utils

class ChatGPTNPC:
  def __init__(self, name, voice):
    """
    Initializes a new instance of the ChatGPTNPC class.

    Args:
      name (str): The name of the NPC.
      voice (str): The voice of the NPC.

    Returns:
      None
    """
    self.name = name
    self.voice = voice
    self.hasImage = False
    self.location = ""
    print("Created " + self.name + " with voice " + self.voice)
    self.messageCount = 0

  def getName(self):
    """
    Returns the name of the NPC.
    """
    return self.name
  
  def getVoice(self):
    """
    Returns the voice of the NPC.
    """
    return self.voice

  def hasLocation(self):
    """
    Returns True if the NPC has a location, False otherwise.
    """
    return self.location != ""

  def getLocation(self):
    """
    Returns the current location of the NPC.

    Returns:
    str: The current location of the NPC.
    """
    return self.location
  
  def setLocation(self, location):
    """
    Sets the location of the NPC to the specified location.

    Args:
      location (str): The name of the location to assign the NPC to.

    Returns:
      None
    """
    self.location = location
    print("Assigning " + self.name + " to " + self.location)

  def incrementMessageCount(self):
    """
    Increments the message count for the NPC.

    This method increments the message count for the NPC instance by 1.

    Args:
      None

    Returns:
      None
    """
    self.messageCount += 1
  
  def getMessageCount(self):
    """
    Returns the number of messages received by the Twitch chatbot.
    """
    return self.messageCount

  def clearMessageCount(self):
    """
    Resets the message count for the NPC to zero.
    """
    self.messageCount = 0

  def changeImageToNPC(self):
    """
    Changes the image of the NPC in OBS to the image associated with the NPC object.

    Uses OBS WebSocket API to set the input settings and enable the scene item.

    Args:
        self: The NPC object.

    Returns:
        None
    """
    utils.obsClient.set_input_settings(
      name=self.location,
      settings={'file': str(os.getcwd()) + '\\local\\' + self.name + ".png"},
      overlay=False
    )
    utils.obsClient.set_scene_item_enabled(
      scene_name=utils.config["obs_settings"]["scene_name"],
      item_id=utils.getItemId(self.location),
      enabled=True
    )
      
  def pulseCharacter(self, message, length):
    """
    Writes the given message to a file and pulses the opacity of the character's source in OBS for the given length of time.

    Args:
      message (str): The message to write to the file.
      length (float): The length of time to pulse the character's opacity, in seconds.

    Returns:
      None
    """
    with open("local/" + self.location + ".txt", "w") as f:
      f.write(message)
    end_time = time.time() + length
    while time.time() < end_time:
      utils.obsClient.set_source_filter_settings(
        source_name=self.location,
        filter_name="Opacity",
        settings={'opacity': random.uniform(0.5, 1.0)}
      )
      time.sleep(0.08)
    utils.obsClient.set_source_filter_settings(
      source_name=self.location,
      filter_name="Opacity",
      settings={'opacity': 1.0}
    )

  def generateCharacterImage(self, message):
    """
    Generates an image for the character with the given description.

    Args:
        message (str): The message containing the character description.

    Returns:
        None
    """
    if self.hasImage:
      return
    self.hasImage = True

    characterDescription = ""
    if "[" in message:
      characterDescription = message.split("[")[1].split("]")[0]
    if characterDescription == "":
      characterDescription = "a D&D character named " + self.name
    print("\n\nGenerating image for " + self.name + " with description " + characterDescription)

    utils.generateImage(self.name, characterDescription)
    return
  
  def setHasImage(self, hasImage):
    """
    Sets the value of the `hasImage` attribute for this NPC object.

    Args:
      hasImage (bool): The new value for the `hasImage` attribute.

    Returns:
      None
    """
    self.hasImage = hasImage