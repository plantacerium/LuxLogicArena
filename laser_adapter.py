from core import GameAdapter
from _00_entry.game_server import GameServer # Tu juego original

class LaserGameAdapter(GameAdapter):
    def __init__(self, size=10):
        self.server = GameServer(grid_size=size)
        self.server.reset()
        self.my_player = 1

    def get_rules_text(self) -> str:
        return "Usa espejos (MIRROR) y prismas para iluminar objetivos. Gana controlando territorio."

    def get_observation_text(self) -> str:
        # Aquí reutilizamos la lógica ASCII que hicimos antes
        # ... (código de renderizado ASCII) ...
        return "(Representación ASCII del tablero 10x10)"

    def get_valid_actions_schema(self):
        res = self.server.get_valid_actions()
        return res.get("valid_actions", [])

    def execute_action(self, action_json: dict) -> float:
        res = self.server.step(action_json)
        # El juego cambia de turno automáticamente, así que ajustamos lógica si es necesario
        return res.get("reward", 0.0)

    def is_game_over(self) -> bool:
        return self.server.game_over
