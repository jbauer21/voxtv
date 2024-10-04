import unittest
from unittest.mock import patch, MagicMock
from graphical_utils import FacialAnimation

class TestFacialAnimation(unittest.TestCase):
    def setUp(self):
        # Create an instance of the FacialAnimation class with a mocked after_callback
        self.facial_animation = FacialAnimation(after_callback=MagicMock())

    def tearDown(self):
        # Close the Tkinter window after each test
        self.facial_animation.close()

    def test_initial_state(self):
        # Test initial state of the animation
        self.assertFalse(self.facial_animation.running)
        self.assertEqual(self.facial_animation.current_image_index, 0)
        self.assertEqual(self.facial_animation.queue.qsize(), 0)

    def test_start_animation(self):
        # Test starting the animation
        self.facial_animation.start_animation()
        self.assertTrue(self.facial_animation.running)
        self.facial_animation.after_callback.assert_called_with(200, self.facial_animation.animate)

    def test_stop_animation(self):
        # Test stopping the animation
        self.facial_animation.start_animation()
        self.facial_animation.stop_animation()
        self.assertFalse(self.facial_animation.running)
        self.assertEqual(self.facial_animation.queue.qsize(), 1)
        command, arg = self.facial_animation.queue.get()
        self.assertEqual(command, "set_image")
        self.assertEqual(arg, self.facial_animation.idle_image)

    def test_animate(self):
        # Run animate method with animation running
        self.facial_animation.start_animation()
        self.facial_animation.animate()
        
        # Check that current_image_index was updated
        self.assertEqual(self.facial_animation.current_image_index, 1)
        self.assertEqual(self.facial_animation.queue.qsize(), 1)
        command, arg = self.facial_animation.queue.get()
        self.assertEqual(command, "set_image")
        self.assertEqual(arg, self.facial_animation.images[1])
        
        # Check that animate was scheduled again
        self.facial_animation.after_callback.assert_called_with(200, self.facial_animation.animate)

    def test_update_gui(self):
        # Mock the label config method
        self.facial_animation.label.config = MagicMock()
        
        # Put a command in the queue and run update_gui
        self.facial_animation.queue.put(("set_image", self.facial_animation.mouth_open_image))
        self.facial_animation.update_gui()
        
        # Check that the label's image was updated
        self.facial_animation.label.config.assert_called_with(image=self.facial_animation.mouth_open_image)
        
        # Check that update_gui was scheduled again
        self.facial_animation.after_callback.assert_called_with(50, self.facial_animation.update_gui)

if __name__ == "__main__":
    unittest.main()