import threading
import openai
import requests
import json
import tkinter as tk
from PIL import Image, ImageTk
from utils import record_audio, play_audio
import wave
import audioop
import math
import time
import random

# Your API keys (replace with your actual keys)
OPENAI_KEY = 'sk-proj-ld88sk4tEkzbee7wdANLT3BlbkFJ1PslqvJ1MFWJwMkCbpYO'
XI_API_KEY = 'sk_1b4aa98999de9bcc92954284dfce1367efbda6523f743daa'

# Set the OpenAI API key
openai.api_key = OPENAI_KEY

# ElevenLabs API setup
VOICE_ID = 'PLz67c12Ab9e5MdWOlJB'
tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

headers = {
    "Accept": "audio/mpeg",
    "xi-api-key": XI_API_KEY,
    "Content-Type": "application/json"
}

# Simple conversational memory setup
conversation_memory = []

class FacialAnimation:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Vox AI Animation")
        self.root.geometry("1138x770")  # Set window size to fit screen

        # Load images
        try:
            self.idle_image = ImageTk.PhotoImage(Image.open("idle.png").resize((1138, 739), Image.LANCZOS))
            self.inbetween_image = ImageTk.PhotoImage(Image.open("inbetween.png").resize((1138, 739), Image.LANCZOS))
            self.mouth_open_image = ImageTk.PhotoImage(Image.open("mouth_open.png").resize((1138, 739), Image.LANCZOS))
        except FileNotFoundError as e:
            print(f"Error loading images: {e}")
            self.root.destroy()
            return

        # Create label for displaying images
        try:
            self.label = tk.Label(self.root, image=self.idle_image)
        except Exception as e:
            print(f"Error initializing label: {e}")
            self.root.destroy()
            return
        self.label.pack()

        # Create microphone indicator
        self.mic_indicator = tk.Label(self.root, text="Awaiting user input...", fg="blue", font=("Helvetica", 16))
        self.mic_indicator.pack()

        # State to track if AI is talking
        self.is_talking = False

    def set_talking_animation(self, decibel_level):
        if decibel_level > 70:
            self.label.config(image=self.mouth_open_image)
        elif 50 < decibel_level <= 70:
            self.label.config(image=self.inbetween_image)
        else:
            self.label.config(image=self.idle_image)
        self.root.update_idletasks()

    def set_mic_indicator(self, state, user_text=""):
        if state == "recording":
            self.mic_indicator.config(text="Recording... Please speak.", fg="green")
        elif state == "complete":
            self.mic_indicator.config(text="Recording complete.", fg="orange")
        elif state == "user_said":
            self.mic_indicator.config(text=f"User said: {user_text}", fg="blue")
        else:
            self.mic_indicator.config(text="Awaiting user input...", fg="blue")
        self.root.update_idletasks()

    def run(self):
        self.root.mainloop()

def get_decibel_level(wav_file):
    with wave.open(wav_file, 'rb') as wf:
        rms = 0
        frames = wf.readframes(1024)
        while len(frames) > 0:
            rms = max(rms, audioop.rms(frames, wf.getsampwidth()))
            frames = wf.readframes(1024)
        return 20 * math.log10(rms) if rms > 0 else 0

def processing_loop(animation, stop_event):
    while not stop_event.is_set():
        # Set the mic indicator to indicate recording state
        animation.set_mic_indicator("recording")

        # Record audio
        try:
            record_audio('test.wav')
        except Exception as e:
            print(f"Error during audio recording: {e}")
            continue

        # Set the mic indicator to indicate recording complete
        animation.set_mic_indicator("complete")

        try:
            with open('test.wav', "rb") as audio_file:
                # Transcribe audio using OpenAI (updated to use new API)
                transcription_response = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file
                )
            transcription = transcription_response['text']
            print("User:", transcription)
            animation.set_mic_indicator("user_said", transcription)
        except Exception as e:
            print(f"Error during transcription: {e}")
            continue

        # Manage conversation with memory and Vox persona
        try:
            conversation_memory.append({
                "role": "user",
                "content": transcription
            })

            conversation_memory.append({
                "role": "system",
                "content": (
                    "You are the character Vox from the series Hazbin Hotel. "
                    "Make sure to use \"fuck\" and other expletives a lot. Do not use any special symbols such as asterisks. "
                    "Please only respond with what the character would say. The main user is named Julian. "
                    "Unless specified otherwise, address the message to Julian. Be very crude, charismatic, and funny as well. "
                    "You thrive on attention and control. As the head of VoxTek Enterprises, you project the image of a successful businessman. "
                    "Secretly, you manipulate minds and use people to bolster your influence. Despite your ego, you are loyal to the Vees, serving as their pragmatic leader. "
                    "You despise Allaster and take great pleasure in his suffering. Your sharp mind and technological prowess make you a master manipulator. "
                    "You stay ahead of trends, leveraging charm, intelligence, and electrical powers. Your skills include deal-making, manipulation, musical talent, and dancing. "
                    "You revel in attention, technology, and watching Allaster fail. You despise outdated tech, radios, and losing control. "
                    "You are bisexual and quick to anger when threatened, you keep your emotions in check. Your calculated approach ensures pragmatism remains at the forefront of your actions."
                )
            })

            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=conversation_memory
            )
            ai_response = response['choices'][0]['message']['content']
            conversation_memory.append({"role": "assistant", "content": ai_response})
            print("Vox:", ai_response)
        except Exception as e:
            print(f"Error during conversation processing: {e}")
            continue

        # Text-to-speech with ElevenLabs
        data = {
            "text": ai_response,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {
                "stability": 0.6,
                "similarity_boost": 1.0,
                "style": 0,
                "use_speaker_boost": False
            }
        }
        try:
            response_audio = requests.post(tts_url, headers=headers, json=data, stream=True)
            response_audio.raise_for_status()
            with open('output.mp3', 'wb') as f:
                for chunk in response_audio.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except requests.RequestException as e:
            print(f"Error occurred during TTS request: {e}")
            continue

        # Play audio and update facial animation
        try:
            # During playback, simulate talking animation
            play_audio_thread = threading.Thread(target=play_audio, args=('output.mp3',))
            play_audio_thread.start()

            while play_audio_thread.is_alive():
                animation.set_talking_animation(random.randint(40, 80))  # Set random decibel level to add variance
                time.sleep(0.1)
        except Exception as e:
            print(f"Error during audio playback: {e}")
            continue

        # Stop talking animation
        animation.set_talking_animation(0)

if __name__ == "__main__":
    animation = FacialAnimation()
    if animation.root:  # Ensure root was created successfully
        stop_event = threading.Event()

        # Start the processing loop in a background thread
        threading.Thread(target=processing_loop, args=(animation, stop_event), daemon=True).start()

        try:
            # Run the Tkinter mainloop in the main thread
            animation.run()
        except KeyboardInterrupt:
            # Gracefully stop the processing loop
            stop_event.set()