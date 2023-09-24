from twitchAPI import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
import json
import os
import handlechat
import time

# load config file with our api and channel configuration
# use example_config.json to create your own config file

with open('config.json') as f:
  config = json.load(f)

APP_ID = config["params"]["app_id"]
APP_SECRET = config["params"]["app_secret"]
TARGET_CHANNEL = config["params"]["target_channel"]
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

# this will be called when the event READY is triggered, which will be on bot start
async def on_ready(ready_event: EventData):
  print('Bot is ready for work, joining channels')
  # join our target channel, if you want to join multiple, either call join for each individually
  # or even better pass a list of channels as the argument
  await ready_event.chat.join_room(TARGET_CHANNEL)
  # you can do other bot initialization things in here

# this will be called whenever a message in a channel was send by either the bot OR another user
async def on_message(msg: ChatMessage):
  #test the time that the message takes to process
  start = time.time()
  handlechat.handleMessage(msg.user.name, msg.text)
  print(f'in {msg.room.name}, {msg.user.name} said: {msg.text}')
  end = time.time() - start
  print(f"Time to process: {end}")

# will roll the dice based on the config set up in the JSON file
async def roll_command(cmd: ChatCommand):
  if cmd.user.badges != None and 'broadcaster' in cmd.user.badges:
    handlechat.rollDice(2,6)

# will remove all current users and add new ones to characters
async def swap_command(cmd: ChatCommand):
  if cmd.user.badges != None and 'broadcaster' in cmd.user.badges:
    handlechat.changeUsers()
    await cmd.reply('Swapping users!')

# will mute all chat messages
async def mute_command(cmd: ChatCommand):
  if cmd.user.badges != None and 'broadcaster' in cmd.user.badges:
    handlechat.muteChat()
    await cmd.reply('Stopping voice chat')

# will unmute all chat messages
async def unmute_command(cmd: ChatCommand):
  if cmd.user.badges != None and 'broadcaster' in cmd.user.badges:
    handlechat.unmuteChat()
    await cmd.reply('Resuming voice chat')

# this is where we set up the bot
async def run():
  # set up twitch api instance and add user authentication with some scopes
  twitch = await Twitch(APP_ID, APP_SECRET)
  auth = UserAuthenticator(twitch, USER_SCOPE)
  token, refresh_token = await auth.authenticate()
  await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)

  # create chat instance
  chat = await Chat(twitch)

  # register the handlers for the events you want

  # listen to when the bot is done starting up and ready to join channels
  chat.register_event(ChatEvent.READY, on_ready)
  # listen to chat messages
  chat.register_event(ChatEvent.MESSAGE, on_message)

  # you can directly register commands and their handlers, this will register the !info command
  chat.register_command('roll', roll_command)
  chat.register_command('swap', swap_command)
  chat.register_command('mute', mute_command)
  chat.register_command('unmute', unmute_command)

  # we are done with our setup, lets start this bot up!
  chat.start()

  os.makedirs("local", exist_ok=True)

  # lets run till we press enter in the console
  try:
    input('press ENTER to stop\n')
  finally:
    # now we can close the chat bot and the twitch api client
    chat.stop()
    await twitch.close()


# lets run our setup
asyncio.run(run())

# handlechat.handleMessage("testuser", "test message test message")