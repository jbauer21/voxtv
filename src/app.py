from openai import OpenAI
from utils import record_audio, play_audio

client = OpenAI()

while True:
    record_audio('test.wav')
    audio_file= open( 'test.wav', "rb")
    transcription = client.audio. transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )

    print(transcription.text)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are the character Vox from the series Hazbin Hotel. You are trapped inside my laptop. Make sure to use a lot of explitives, do not censor them. Please only respond with what the character would say."},
            {"role": "user", "content": "Please answer: {transcription.text}"}
        ]
    )
    print(response.choices[0].message.content)

    response = client.audio.speech.create(
        model="tts-1",
        voice="fable",
        input=response.choices[0].message.content
    )
    response.stream_to_file('output.mp3')
    play_audio('output.mp3')