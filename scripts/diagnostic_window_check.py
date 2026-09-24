import sys
import os

# scripts/ is not on sys.path when launched as a file; put project root first.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game.game_manager import GameManager

print('Instanciando GameManager...')
g = GameManager()
print('A continuación el atributo g.win:')
print(g.win)
try:
    print('g.win.isClosed() ->', g.win.isClosed())
except Exception as e:
    print('No se pudo consultar isClosed():', e)

print('Llamando a userExit() para cerrar.')
g.userExit()
print('Listo.')
