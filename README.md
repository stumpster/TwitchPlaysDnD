# TwitchPlaysDnD
Inspired by DougDoug's 'Twitch Plays D&amp;D' 

# Setup for player-led game

## Library

1. Clone or download this library.
1. Download and install [python](https://www.python.org/downloads/).
1. Install the necessary python libraries (run `pip install -r requirements.txt`).

## Twitch

1. Create a Twitch chat bot application at the [Twitch Developers](https://dev.twitch.tv/console/apps) page.
1. Set the OAuth Redirect URL to `http://localhost:17563`.
1. Make a copy of the `example_config.json` file and rename it to `config.json`.
1. Copy and paste the `Client ID` and `Client Secret` from the Twitch application management page into the `config.json` file in the `app_id` and `app_secret` sections.
1. Add your Twitch channel to the `target_channel`.

## OBS

1. Go to Tools > WebSocket Server Settings.
1. Generate a password and copy that into the `obs_settings password` in `config.json`. 
1. Set your `Scene` name in `config.json`.
1. In order for dice rolling to work you will need to have an dice animation, static dice image, and a text field set up as sources inside OBS. By default, these OBS sources are expected to be named `Dice Animation`, `Dice Background`, and `Dice Result` respectively. You can change these expected source names in the `config.json` file if you would like. Edit the `obs_dice_animation_length` to match your animation length and the `obs_dice_result_length` for how long you would like the result to be displayed.
1. In the `characters` section of `config.json` you will need to give your characters a name and assign them a voice (voices are covered below in the [AWS](#aws) section). In order for the character to move an image while they are talking the OBS image source should be named `<character> Image`. As an example, if I set up a character named `Steven` then the OBS image associated with that character should be named `Steven Image`.
1. In OBS your character image will also need to have a Color Correction filter assigned to it. By default, this is expected to be named `Opacity` but you can change this name in the `config.json` file if you would like.

## Voice - Either ElevenLabs or AWS

### AWS

**Note: Cloud computing can incur costs, make sure you understand the [AWS Polly pricing](https://aws.amazon.com/polly/pricing/) before configuring.**

1. Create a new [AWS account](https://aws.amazon.com/).
1. Create an IAM user in AWS to access AWS Polly through by:
    1. In the AWS console search for the `IAM` component and click on it.
    1. Click on `Users` and click on `Create User`.
    1. Give this user a name (e.g. `Polly`) and click `Next`.
    1. Click on `Attach policies directly` and search for `AmazonPollyFullAccess`. Select it and click `Next`.
    1. Click `Create User`
    1. Back in the IAM Users page, click on the new user and click on `Security Credentials`.
    1. Scroll down and in the `Access Keys` section click on `Create access key`.
    1. Click on `Local code`, click `Next`, and then click `Create access key`.
    1. Copy the access key and secret access key to the `config.json` fields under `aws_settings`.
1. Modify your `character` voices in `config.json` according to the voices that you would like to use from the [AWS Polly voicelist](https://docs.aws.amazon.com/polly/latest/dg/voicelist.html). By default, only voices that are available as `Standard Voices` can be used since these have much more AWS free credits available.

### ElevenLabs

**Note: ElevenLabs is easier to set up and generally has better voices but offers *much* less free usage than AWS. The free tier of ElevenLabs only allows for 10000 characters instead of AWS which allows for millions.**

1. Create a new [ElevenLabs account](https://elevenlabs.io/text-to-speech)
1. Click on your profile in the top right.
1. Copy your API key to the `config.json` file in the `eleven_labs_settings` section.
1. In the `config.json` mark the `enabled` field in AWS to `false` and the `enabled` field for Eleven Labs to `true`.
1. Modify your `character` voices in `config.json` according to the names of the voices in Eleven Labs.

# Chat Commands

The owner of the channel can send the following commands in their Twitch chat to facilitate running games:

- !roll
    - This will roll the default dice that you have listed in the `config.json` file. By default, this is set in the `example_config.json` to be 1d20.
- !roll `X`d`Y`
    - This will roll X dice of Y sides. As an example, `!roll 2d6` will roll 2 six-sided dice.
- !swap
    - This will remove all current users from characters and assign new ones from users who have been active in chat over the last five minutes
- !mute
    - This will prevent new voice and text for the characters from being processed (the messages sent while muted will be lost)
- !unmute
    - Undoes the !mute command

# Setup for ChatGPT-led game

*Note: Running a ChatGPT-led game will have some cost associated with it since using the OpenAI API has an associated (albeit low) cost. With the default GPT-3.5 the maximum cost per message and response should be limited to $0.014. This is enough for approximately ~45 minutes of streaming before any history is lost.*

Follow steps above to set up Twitch, OBS, and AWS with the following changes:
1. Instead of having specific characters set in OBS you will need to have generic image NPC fields `NPC0` to `NPC3` and text fields `NPC0 Chat` to `NPC3 Chat` 
1. Ignore the `character` fields in the `config.json` as these will not be used, ChatGPT will make new characters and automatically assign voices to them as they are created.
1. Set up an additional field for `GM` and `GM Chat`

## OpenAI/ChatGPT

1. Open an account over at [OpenAI's platform page](https://platform.openai.com)
1. Add funds to the account
1. Generate an API key from your [API key page](https://platform.openai.com/account/api-keys)
1. Add this field to the `chatgpt_settings` section of your `config.json` and set `enabled` to `true`
1. If you'd like to modify the scenario that ChatGPT is DM'ing for, adjust the `self.systemmsg` in the `chatgptdm.py` file. By default, ChatGPT is presented with the following scenario: `You are a game master who is leading a party though a campaign of Dungeons and Dragons. The players are: a fighter named Roger, a cleric named Karrix, and a wizard named Sylvania. They are currently in a tavern. `

## Bing

1. Find your auth cookie using the steps [here](https://github.com/acheong08/BingImageCreator/tree/main#getting-authentication) to use Bing to generate images using DALLE-3.
1. Add this auth cookie to the `config.json` file in the `bing_settings`
*Note: This is the default to use since it's free, but a little bit slower than OpenAI.*

# Chat Commands

The owner of the channel can send the following commands in their Twitch chat to facilitate running games:
- !roll
    - This will roll the default dice that you have listed in the `config.json` file. By default, this is set in the `example_config.json` to be 1d20.
- !roll `X`d`Y`
    - This will roll X dice of Y sides. As an example, `!roll 2d6` will roll 2 six-sided dice.

Any chatters in the channel can submit these commands:
- !submit
    - This command will be used by chat to submit actions to the ChatGPT GM. This starts a poll to vote on the next action and will give a shortcut for other chat members to vote on that action using:
- !`x`
    - A shortcut for a command will be given (e.g. `!1`, `!2`, etc) and can be used by chat members to vote on the next action