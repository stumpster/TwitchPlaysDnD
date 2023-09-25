import pyaudio
import openai
import os
import time
import wave
import wavio
import whisper

import sounddevice as sd
import numpy as np
import keyboard
import time
from queue import Queue

from character import Character
import utils

class ChatGPTDM:
  def __init__(self):
    self.api_key = utils.config["chatgpt_settings"]["api_key"]

    self.systemmsg = '''You are a game master who is leading a party though a campaign of Dungeons and Dragons. '''
    self.systemmsg += '''The players are: a bard, a barbarian, and a wizard. They are currently in a tavern. ''' 

    self.messages = [{"role": "system", "content": self.systemmsg}]

    self.character = Character("GM")

  def chatInput(self, message):
    self.messages.append({"role": "user", "content": message})
    
    openai.api_key = self.api_key
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=self.messages,
    )

    self.character.writeMessageTextAndSpeak(response["choices"][0]["message"]["content"])

    self.messages.append({response["choices"][0]["message"]["role"]: response["choices"][0]["message"]["content"]})

    # if token number is getting high, remove the oldest message
    if response["usage"]["total_tokens"] > 7000:
      print("Removing oldest message.")
      print(self.messages[1])
      self.messages.pop(1)

  def recordNewMessage(self):

    # chunk = 1024  # Record in chunks of 1024 samples
    # sample_format = pyaudio.paInt32  # 16 bits per sample
    # channels = 2
    # fs = 44100  # Record at 44100 samples per second
    # seconds = 3
    # filename = "output.wav"

    # p = pyaudio.PyAudio()  # Create an interface to PortAudio

    # print('Recording, press enter to stop the recording')

    # stream = p.open(format=sample_format,
    #                 channels=channels,
    #                 rate=fs,
    #                 frames_per_buffer=chunk,
    #                 input=True)

    # frames = []  # Initialize array to store frames

    # # Store data in chunks for 3 seconds
    # # loop until the enter key is pressed
    # while True:
    #   for i in range(0, int(fs / chunk * seconds)):
    #       data = stream.read(chunk)
    #       frames.append(data)
    #   user_input = input()
    #   if user_input == '':
    #     break

    # # Stop and close the stream 
    # stream.stop_stream()
    # stream.close()
    # # Terminate the PortAudio interface
    # p.terminate()

    # print('Finished recording')

    # Set the sample rate and duration (duration is set to a large value, as we'll stop recording with a button press)
    self.record_audio_to_file()
    print("recorded audio")

    # Save the recorded data as a WAV file
    # wf = wave.open(filename, 'wb')
    # wf.setnchannels(channels)
    # wf.setsampwidth(p.get_sample_size(sample_format))
    # wf.setframerate(fs)
    # wf.writeframes(b''.join(frames))
    # wf.close()
    
    # file = open(filename, "rb")
    # transcription = openai.Audio.transcribe("whisper-1", file)
    # print(transcription)
    # self.chatInput(transcription)

  def record_audio_to_file(filename="recorded_audio.wav", samplerate=44100, channels=2, duration=3600):

    audio_queue = Queue()

    # Nested callback function to stop the recording when 'q' is pressed and save chunks to the queue
    def callback(indata, frames, time, status):
        audio_queue.put(indata.copy())
        if keyboard.is_pressed('q'):
            print("Stopping recording.")
            raise sd.CallbackStop

    print("Recording started... Press 'q' to stop the recording.")

    # Start recording
    with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
        # Just sleep while audio is being streamed until the callback stops the stream
        sd.sleep(duration * 1000)

    print("Recording stopped.")

    # Process the audio data from the queue
    audio_data = np.concatenate(list(audio_queue.queue), axis=0)

    # Save to the specified WAV file
    wavio.write(filename, audio_data, samplerate, sampwidth=2)
    print(f"Audio saved to {filename}.")