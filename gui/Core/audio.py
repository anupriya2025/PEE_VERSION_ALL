import threading
import queue
import pygame
import time

from gui.Core.Recognistion_process.ConfigLoader import ConfigLoader


class AudioController:
    """Manages audio playback using Pygame."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        pass
        # if not cls._instance:
        #     cls._instance = super(AudioController, cls).__new__(cls, *args, **kwargs)
        #     pygame.mixer.init()
        #     cls._instance.config = ConfigLoader()
#             cls._instance.audio_file = cls._instance.config.get('selected_audio_file')
#             cls._instance.sound = pygame.mixer.Sound(cls._instance.audio_file)
#             cls._instance.volume = 1.0
#             cls._instance.is_playing = False
#             cls._instance.is_muted = False
#         return cls._instance
#
#     def play(self, loops=-1):
#         """Play the audio once (no loop)."""
#         if not self.is_playing:
#             self.sound.play(loops=loops)
#             self.is_playing = True
#
#
#     def stop(self):
#         """Stop the audio if playing."""
#         if self.is_playing:
#             self.sound.stop()
#             self.is_playing = False
#
#     def mute(self):
#         self.sound.set_volume(0)
#         self.is_muted = True
#
#     def unmute(self):
#         self.sound.set_volume(self.volume)
#         self.is_muted = False
#
#     def set_volume(self, volume):
#         self.volume = volume
#         if not self.is_muted:
#             self.sound.set_volume(volume)
#
#     def change_audio(self, new_file):
#         self.stop()
#         self.audio_file = new_file
#         self.sound = pygame.mixer.Sound(new_file)
#         self.set_volume(self.volume)
#
#
class AudioThreadManager:
    """Manages audio playback commands in a separate thread."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            pass
            # cls._instance = super(AudioThreadManager, cls).__new__(cls, *args, **kwargs)
            # cls._instance.audio_controller = AudioController()
#             cls._instance.command_queue = queue.Queue()
#         return cls._instance
#
#     def run(self):
#         """Main loop to process commands."""
#         while True:
#             command = self.command_queue.get()
#
#             if command == "play":
#                 self.audio_controller.play()  # plays once
#             elif command == "stop":
#                 self.audio_controller.stop()
#             elif command.startswith("play_with_duration"):
#                 _, duration = command.split(":")
#                 self.audio_controller.play()
#                 time.sleep(float(duration))  # play for specified duration
#                 self.audio_controller.stop()
#             elif command == "mute":
#                 self.audio_controller.mute()
#             elif command == "unmute":
#                 self.audio_controller.unmute()
#             elif command.startswith("set_volume"):
#                 _, volume = command.split(":")
#                 self.audio_controller.set_volume(float(volume))
#             elif command.startswith("change_audio"):
#                 _, new_file = command.split(":", 1)
#                 self.audio_controller.change_audio(new_file)
#             elif command == "quit":
#                 self.audio_controller.stop()
#                 break
#
#     def send_command(self, command):
#         self.command_queue.put(command)
