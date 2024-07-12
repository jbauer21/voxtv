import openai
from openai import OpenAI
from utils import record_audio, play_audio
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List

#OPENAI_KEY = 'API-Key Here'
client = openai.OpenAI()
LLM_MODEL = 'gpt-4o'

llm = ChatOpenAI(openai_api_key=OPENAI_KEY, model=LLM_MODEL, temperature=0.7)

template = """
You are the character Vox from the series Hazbin Hotel. 
You are trapped inside my laptop. 
Make sure to use a lot of expletives.
If you are going to censor explitives, be sure to only use asterisks (*)
Please only respond with what the character would say.

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

    response_audio = client.audio.speech.create(
        model="tts-1",
        voice="fable",
        input=response.content
    )
    with open('output.mp3', 'wb') as f:
        for chunk in response_audio.iter_bytes():
            f.write(chunk)
    
    play_audio('output.mp3')
