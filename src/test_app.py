import unittest
from unittest.mock import patch, MagicMock
import threading
from app import animation, chain_with_history, record_audio, play_audio

class TestAppWithGraphicalUtils(unittest.TestCase):
    def setUp(self):
        # Mock external functions
        self.patcher_record_audio = patch('app.record_audio', MagicMock())
        self.patcher_play_audio = patch('app.play_audio', MagicMock())
        self.patcher_openai_client = patch('openai.OpenAI', MagicMock())
        self.patcher_requests_post = patch('requests.post', MagicMock())

        self.mock_record_audio = self.patcher_record_audio.start()
        self.mock_play_audio = self.patcher_play_audio.start()
        self.mock_openai_client = self.patcher_openai_client.start()
        self.mock_requests_post = self.patcher_requests_post.start()

        # Initialize FacialAnimation
        self.animation_thread = threading.Thread(target=animation.run, daemon=True)
        self.animation_thread.start()

    def tearDown(self):
        # Stop patchers
        self.patcher_record_audio.stop()
        self.patcher_play_audio.stop()
        self.patcher_openai_client.stop()
        self.patcher_requests_post.stop()

        # Close animation
        animation.close()

    def test_transcription_and_response(self):
        # Mock the transcription response
        mock_transcription_response = MagicMock()
        mock_transcription_response.text = "Hello Vox!"
        self.mock_openai_client.audio.transcriptions.create.return_value = mock_transcription_response

        # Mock the LLM response
        mock_llm_response = MagicMock()
        mock_llm_response.content = "Hey Julian, what's up!"
        with patch.object(chain_with_history, 'invoke', return_value=mock_llm_response):
            # Simulate the transcription and response workflow
            record_audio('test.wav')
            transcription = mock_transcription_response.text
            animation.start_animation() if True else animation.stop_animation()
            response = chain_with_history.invoke(
                {"input": transcription},
                config={"configurable": {"session_id": "unique_session_id"}}
            )
            self.assertEqual(response.content, "Hey Julian, what's up!")

            # Check if the talking animation started
            self.assertTrue(animation.running)

            # Simulate playing the response
            play_audio('output.mp3')
            animation.start_animation() if False else animation.stop_animation()

            # Check if the talking animation stopped
            self.assertFalse(animation.running)

    def test_talking_animation(self):
        # Test starting and stopping the talking animation
        animation.start_animation() if True else animation.stop_animation()
        self.assertTrue(animation.running)

        animation.start_animation() if False else animation.stop_animation()
        self.assertFalse(animation.running)

if __name__ == "__main__":
    unittest.main()