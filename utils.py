import json
import obsws_python as obs

with open('config.json') as f:
  config = json.load(f)

obsClient = obs.ReqClient(host=config["obs_settings"]["host"], port=config["obs_settings"]["port"], password=config["obs_settings"]["password"])

def addNewlines(message, char_limit=30):
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

def getItemId(source):
  # get the integer of the item id from the source name
  print("Getting item id for " + source)
  item_id = obsClient.get_scene_item_id(scene_name=config["obs_settings"]["scene_name"], source_name=source)
  return item_id.scene_item_id