"""Font loading for UI text.

One place to swap fonts: UI consumers ask for a font here instead of
loading TTFs directly, so replacing assets later touches this file only.
Fonts load once (Panda3D's loader caches by path).

Calibration: the TTFs render at a different text-units size than the
Panda3D default font (measured with TextNode.getHeight of "HP 100":
default 0.988, menu 2.188, ingame 1.000). The TEXT_SCALE constants below
compensate, so consumers keep their original scale values.
"""

# Measured height ratio vs the Panda3D default font.
MENU_TEXT_SCALE = 0.45    # 2.188 -> 0.984
INGAME_TEXT_SCALE = 0.99  # 1.000 -> 0.990


def menu_font(game):
    """Font for menus (title, controls, pause)."""
    return game.loader.loadFont("assets/fonts/font_menu.ttf")


def ingame_font(game):
    """Font for in-game HUD text."""
    return game.loader.loadFont("assets/fonts/font_ingame.ttf")
