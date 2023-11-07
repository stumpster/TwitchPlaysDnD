import BingImageCreator
import boto3
import elevenlabs
import json
import obsws_python as obs
import os
import requests

from openai import OpenAI
from PIL import Image

with open('config.json') as f:
  config = json.load(f)

obsClient = obs.ReqClient(host=config["obs_settings"]["host"], port=config["obs_settings"]["port"], password=config["obs_settings"]["password"])

bingImageCreator = BingImageCreator.ImageGen(
    auth_cookie=config["bing_settings"]["auth_cookie"],
    auth_cookie_SRCHHPGUSR=None
)

if config["aws_settings"]["enabled"]:
  polly_client = boto3.Session(
    aws_access_key_id = config["aws_settings"]["aws_access_key_id"],                     
    aws_secret_access_key = config["aws_settings"]["aws_secret_access_key"],
    region_name = config["aws_settings"]["aws_region"]).client('polly')
else:
  elevenlabs.set_api_key(config["eleven_labs_settings"]["api_key"])

def getItemId(source):
  """
  Returns the integer ID of the specified OBS scene item.

  Args:
      source (str): The name of the OBS scene item.

  Returns:
      int: The integer ID of the specified OBS scene item.
  """
  print("Getting item id for " + source)
  item_id = obsClient.get_scene_item_id(scene_name=config["obs_settings"]["scene_name"], source_name=source)
  return item_id.scene_item_id

def hideItem(item_name):
  """
  Hides the item with the given item name.

  Args:
  - item_name (str): The name of the item to be hidden.

  Returns:
  - None
  """
  obsClient.set_scene_item_enabled(
          scene_name=config["obs_settings"]["scene_name"],
          item_id=getItemId(item_name),
          enabled=False
  )

def showItem(item_name):
  """
  Enables the visibility of the item with the given name in the OBS scene.

  Args:
    item_name (str): The name of the item to be shown.

  Returns:
    None
  """
  obsClient.set_scene_item_enabled(
    scene_name=config["obs_settings"]["scene_name"],
    item_id=getItemId(item_name),
    enabled=True
  )

def getKey(val, my_dict):
  """
  Returns the key of the first occurrence of a given value in a dictionary.

  Args:
    val: The value to search for in the dictionary.
    my_dict: The dictionary to search for the value in.

  Returns:
    The key of the first occurrence of the given value in the dictionary, or None if the value is not found.
  """
  for key, value in my_dict.items():
    if val == value:
      return key
  return None
        
def stripMessage(message):
  """
  Removes descriptors and character name from a message.

  Args:
  message (str): The message to be stripped.

  Returns:
  str: The stripped message.
  """
  if ">" in message:
    message = message[:message.find('<')] + message[message.find('>')+1:]
  if "]" in message:
    message = message[:message.find('[')] + message[message.find(']')+1:]
  return message

def generateImage(name, characterDescription):
  """
  Generates an image for a given character description using either OpenAI or Bing.

  Args:
  - name (str): The name of the character.
  - characterDescription (str): A description of the character.

  Returns:
  - None
  """
  if config["chatgpt_settings"]["art_enabled"]:
    print("Using openAI to generate image")

    client = OpenAI(api_key = config["chatgpt_settings"]["api_key"])

    response = client.images.generate(
      model="dall-e-3",
      prompt=characterDescription + ", digital art, in a Dungeons and Dragons setting",
      size="1024x1024",
      quality="standard",
      n=1,
    )

    image_url = response.data[0].url

    # download the image
    image_response = requests.get(image_url)
    with open("local/" + name + "_0.jpeg", "wb") as f:
      f.write(image_response.content)

  else:
    print("Using Bing to generate image")
    bingImageCreator.save_images(
      bingImageCreator.get_images(characterDescription + " digital art in a Dungeons and Dragons setting"),
      output_dir=os.getcwd() + "\\local\\",
      file_name=name,
      download_count=1
    )

  # shrink image to 512x512
  if os.path.isfile("local/" + name + "_0.jpeg"):
    print("Converting " + name + ".jpeg to " + name + ".png")
    im = Image.open("local/" + name + "_0.jpeg")
    rgb_im = im.convert('RGB')
    rgb_im = rgb_im.resize((512, 512))
    rgb_im.save("local/" + name + ".png")
    os.remove("local/" + name + "_0.jpeg")
  return

def createVoiceLine(voice, message, filename):
  """
  Synthesizes speech using Amazon Polly or ElevenLabs and saves the resulting audio file to disk.

  Args:
    voice (str): The name of the voice to use for the speech synthesis.
    message (str): The text to synthesize into speech.
    filename (str): The name of the file to save the resulting audio to.

  Returns:
    None
  """
  try:
    if config["aws_settings"]["enabled"]:
      response = polly_client.synthesize_speech(VoiceId=voice,
        OutputFormat='mp3', 
        Text = message,
        Engine = 'standard')

      print("\nWriting to " + filename + ".mp3")
      file = open("local\\" + filename + '.mp3', 'wb')
      file.write(response['AudioStream'].read())
      file.close()
    # otherwise use ElevenLabs to generate the voice line
    else:
      elevenlabs.save(
        elevenlabs.generate(
          text=message, voice=voice
        ),
        "local\\" + filename + ".mp3"
      )
  except:
    #print error that we ran into
    print("Error creating voice line for " + filename)
    
def getVoiceClassFromName(name):
  """
  Returns the voice for a given voice name.

  Args:
    name (str): The name of the voice.

  Returns:
    Voice: The voice for the given voice name.
  """
  for x in elevenlabs.voices():
    if x.name == name:
      return x
  print("\nVoice not found\n")
  return None