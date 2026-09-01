import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.game.game_manager import GameManager


def main():
    game = GameManager()
    game.run()


if __name__ == "__main__":
    main()
