import openai
from openai import OpenAI
from utils import record_audio, play_audio
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.pydantic_v1 import BaseModel, Field
import requests
import json
from typing import List

OPENAI_KEY = 'sk-proj-ld88sk4tEkzbee7wdANLT3BlbkFJ1PslqvJ1MFWJwMkCbpYO'
XI_API_KEY = 'sk_1b4aa98999de9bcc92954284dfce1367efbda6523f743daa'

VOICE_ID = "PLz67c12Ab9e5MdWOlJB" 
tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

headers = {
  "Accept": "application/json",
  "xi-api-key": XI_API_KEY,
  "Content-Type": "application/json"
}





client = openai.OpenAI()
LLM_MODEL = 'gpt-4o'

llm = ChatOpenAI(openai_api_key=OPENAI_KEY, model=LLM_MODEL, temperature=0.7)

template = """
You are the character Vox from the series Hazbin Hotel. 
Make sure to use a lot of cursewords.
Do not use any special symbols such as asterisks.
Please only respond with what the character would say.
The main user is named Julian. Unless specified otherwise, address the message to Julian.
Be somewhat crude, but be charismatic and funny as well.
current conversation:
{history}
Human:{input}
Vox:
"""
PROMPT = PromptTemplate(ai_prefix="Vox, Media King of Demons", input_variables=["history", "input"], template=template)

class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    """In memory implementation of chat message history."""
    messages: List[AIMessage] = Field(default_factory=list)

    def add_messages(self, messages: List[AIMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryHistory()
    return store[session_id]

chain = PROMPT | llm

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history=get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

while True:
    record_audio('test.wav')
    audio_file = open('test.wav', "rb")
    transcription_response = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )

    transcription = transcription_response.text
    print(transcription)
    response = chain_with_history.invoke(
        {"input": transcription},
        config={"configurable": {"session_id": "unique_session_id"}}
    )
    print(response.content)

    data = {
    "text": response.content,
    "model_id": "eleven_turbo_v2",
    "voice_settings": {
        "stability": 0.45,
        "similarity_boost": 1,
        "style": 0,
        "use_speaker_boost": False
    }
    }
    response_audio = requests.post(tts_url, headers=headers, json=data, stream=True)
    with open('output.mp3', 'wb') as f:
        for chunk in response_audio.iter_content(chunk_size=2048):
            f.write(chunk)
    
    play_audio('output.mp3')
