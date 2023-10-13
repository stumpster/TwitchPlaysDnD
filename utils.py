import BingImageCreator
import json
import obsws_python as obs
import openai
import os
import requests

from PIL import Image

with open('config.json') as f:
  config = json.load(f)

obsClient = obs.ReqClient(host=config["obs_settings"]["host"], port=config["obs_settings"]["port"], password=config["obs_settings"]["password"])

bingImageCreator = BingImageCreator.ImageGen(
    auth_cookie=config["bing_settings"]["auth_cookie"],
    auth_cookie_SRCHHPGUSR=None
)

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

def generateImage(name, characterDescription, useOpenAI=False):
  """
  Generates an image for a given character description using either OpenAI or Bing.

  Args:
  - name (str): The name of the character.
  - characterDescription (str): A description of the character.
  - useOpenAI (bool): Whether to use OpenAI to generate the image. Defaults to False.

  Returns:
  - None
  """
  if useOpenAI:
    print("Using openAI to generate image")
    
    openai.api_key = config["chatgpt_settings"]["api_key"]
    response = openai.Image.create(
      prompt=characterDescription + ", digital art, in a Dungeons and Dragons setting",
      n=1,
      size="512x512"
    )
    image_url = response['data'][0]['url']

    # download the image
    image_response = requests.get(image_url)
    with open("local/" + name + ".png", "wb") as f:
      f.write(image_response.content)

  else:
    print("Using Bing to generate image")
    bingImageCreator.save_images(
      bingImageCreator.get_images(characterDescription + ", digital art, in a Dungeons and Dragons setting"),
      output_dir=os.getcwd() + "\\local\\",
      file_name=name,
      download_count=1
    )

    # convert the image to a png
    if os.path.isfile("local/" + name + "_0.jpeg"):
      print("Converting " + name + ".jpeg to " + name + ".png")
      im = Image.open("local/" + name + "_0.jpeg")
      rgb_im = im.convert('RGB')
      rgb_im = rgb_im.resize((512, 512))
      rgb_im.save("local/" + name + ".png")
      os.remove("local/" + name + "_0.jpeg")
  return