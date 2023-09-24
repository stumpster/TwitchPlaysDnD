# TwitchPlaysDnD
Inspired by DougDoug's 'Twitch Plays D&amp;D' 

# Setup

## Library

1. Clone or download this library.
1. Download and install [python](https://www.python.org/downloads/).
1. Install the necessary python libraries (run `pip install -r requirements.txt`).

## Twitch

1. Create a Twitch chat bot application at the [Twitch Developers](https://dev.twitch.tv/console/apps) page.
1. Set the OAuth Redirect URL to `http://localhost:17563`.
1. Make a copy of the `example_config.json` file and name it `config.json`.
1. Copy and paste the `Client ID` and `Client Secret` into this `config.json` file in the `app_id` and `app_secret` sections.
1. Add your Twitch channel to the `target_channel`.

## OBS

1. Go to Tools > WebSocket Server Settings.
1. Generate a password and copy that into the `obs_settings password` in `config.json`. 
1. Set your `Scene` name in `config.json`.
1. In order for dice rolling to work you will need to have an dice animation, static dice image, and a text field set up as sources inside OBS. By default, these OBS sources are expected to be named `Dice Animation`, `Dice Background`, and `Dice Result` respectively. You can change these expected source names in the `config.json` file if you would like.
1. In the `characters` section of `config.json` you will need to give them a name and assign them a voice (voices are covered below in the [AWS](#aws) section). In order for the character to move an image while they are talking the OBS image source should be named `<character> Image`. As an example, if I set up a character named `Steven` then the OBS image associated with that character should be named `Steven Image`.

## AWS

**Note: Cloud computing can incur costs, make sure you understand the [AWS Polly pricing](https://aws.amazon.com/polly/pricing/) before configuring.**

1. Create a new [AWS account](https://aws.amazon.com/).
1. Create an IAM user in AWS to access AWS Polly through by: **These steps are not mandatory, but it is highly recommended that you DO NOT create an access key on the root account.**
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

TODO:
- Documentation and clean stuff up

Nice to haves:
- Force audio stop for voice chats that are too lengthy
- Send messages back to the channel from inside other functions

TBD:
- Performance testing with large user base or with multiple characters all talking at the same time
- User token regeneration (expires after 4 hours?) - doesn't seem necessary, seemed to last for more than 4 hours
- Expand the config to control full scene activity (e.g. location of characters, etc)