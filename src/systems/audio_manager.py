import os
import json


class AudioManager:
    def __init__(self, game):
        self.game = game
        self.music_volume = game.settings.get("audio.music_volume", 0.7)
        self.sfx_volume = game.settings.get("audio.sfx_volume", 0.8)
        self._music = None

    def play_music(self, filename):
        audio_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "assets",
            "audio",
        )
        filepath = os.path.join(audio_dir, filename)
        if os.path.exists(filepath):
            self._music = self.game.loader.loadMusic(filepath)
            if self._music:
                self._music.setVolume(self.music_volume)
                self._music.loop()
                self._music.play()

    def stop_music(self):
        if self._music:
            self._music.stop()
            self._music = None

    def set_music_volume(self, volume):
        self.music_volume = volume
        if self._music:
            self._music.setVolume(volume)

    def set_sfx_volume(self, volume):
        self.sfx_volume = volume
