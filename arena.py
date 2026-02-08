import json
import time
import random
import ollama
from typing import List, Dict, Any

# Importamos el servidor del juego
from _00_entry.game_server import GameServer

# --- CONFIGURACIÓN DE LA ARENA ---
MODELO_JUGADOR_1 = "gemma3:12b"  # O gemma3 si está disponible
MODELO_JUGADOR_2 = "llama3"  # Puedes poner "gemma2" aquí también para un espejo
DELAY_ENTRE_TURNOS = 1.0     # Segundos para poder ver lo que pasa

class AIAgent:
    def __init__(self, player_id: int, model_name: str):
        self.player_id = player_id
        self.model_name = model_name
        self.my_symbols = "MAYÚSCULAS (P, M, S)" if player_id == 1 else "minúsculas (p, m, s)"
        self.opp_symbols = "minúsculas (p, m, s)" if player_id == 1 else "MAYÚSCULAS (P, M, S)"

    def get_move(self, board_ascii: str, valid_actions: List[Dict]) -> Dict:
        """Consulta a Ollama para obtener el siguiente movimiento."""
        
        # Tomamos una muestra de acciones válidas para enseñar al modelo el formato
        sample_actions = random.sample(valid_actions, min(3, len(valid_actions))) if valid_actions else []
        
        prompt = f"""
        Eres una IA jugando un juego de mesa estratégico de láseres y espejos.
        Eres el JUGADOR {self.player_id}.
        
        TU OBJETIVO: Controlar el tablero y eliminar piezas enemigas.
        TUS PIEZAS: {self.my_symbols}.
        PIEZAS ENEMIGAS: {self.opp_symbols}.
        
        TABLERO ACTUAL:
        {board_ascii}
        
        INSTRUCCIONES:
        1. Analiza el tablero.
        2. Selecciona una acción de la lista de válidas o crea una nueva lógica.
        3. RESPONDE SOLO CON UN JSON VÁLIDO.
        
        Ejemplos de acciones válidas ahora mismo:
        {json.dumps(sample_actions)}
        
        Genera tu movimiento en JSON (type: "place", "rotate", "laser", o "pass"):
        """

        try:
            # options={"temperature": 0.2} hace que el modelo sea más determinista y cometa menos errores de sintaxis
            response = ollama.generate(
                model=self.model_name, 
                prompt=prompt, 
                format="json", 
                options={"temperature": 0.2}
            )
            
            # Limpieza básica del JSON
            clean_json = response['response'].replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            print(f"Error en Agente {self.player_id} ({self.model_name}): {e}")
            return None

def render_board(server: GameServer) -> str:
    """Dibuja el tablero en ASCII para que la IA lo vea."""
    if not server.board: return "Vacio"
    
    grid = [['.' for _ in range(server.grid_size)] for _ in range(server.grid_size)]
    symbols = {"PRISM": "P", "MIRROR": "M", "SPLITTER": "S"}
    
    for (x, y), stone in server.board.stones.items():
        char = symbols.get(stone.stone_type.name, "?")
        # Jugador 1 = Mayúscula, Jugador 2 = Minúscula
        grid[y][x] = char if stone.player == 1 else char.lower()

    # Coordenadas X
    header = "   " + "".join([f"{i%10}" for i in range(server.grid_size)])
    rows = [header]
    for y in range(server.grid_size):
        # Coordenadas Y + Fila
        rows.append(f"{y:2d} " + "".join(grid[y]))
    
    return "\n".join(rows)

def main():
    # 1. Inicializar Servidor y Agentes
    server = GameServer(grid_size=10) # Reducido a 10x10 para que sea más rápido para la IA
    server.reset({"starting_energy": 10})
    
    p1 = AIAgent(1, MODELO_JUGADOR_1)
    p2 = AIAgent(2, MODELO_JUGADOR_2)
    
    agents = {1: p1, 2: p2}
    
    print(f"--- INICIANDO ARENA: {MODELO_JUGADOR_1} vs {MODELO_JUGADOR_2} ---")
    
    turn = 0
    while not server.game_over and turn < 50: # Límite de seguridad
        current_pid = server.current_player
        current_agent = agents[current_pid]
        
        print(f"\n\n=== TURNO {turn} | JUGADOR {current_pid} ({current_agent.model_name}) ===")
        
        # Visualizar
        board_str = render_board(server)
        print(board_str)
        
        # Obtener acciones válidas reales del motor
        valid_resp = server.get_valid_actions()
        valid_actions = valid_resp.get("valid_actions", [])
        
        # Pensar
        print(f"Agente {current_pid} pensando...")
        action = current_agent.get_move(board_str, valid_actions)
        
        # Ejecutar y Validar
        success = False
        if action:
            print(f"Intento de acción: {action}")
            result = server.step(action)
            
            # Verificar si el servidor aceptó la jugada (reward != -0.1 suele ser error en este server)
            if result.get("reward", 0) != -0.1 and not result.get("error"):
                success = True
                print(f"--> ÉXITO. Recompensa: {result.get('reward')}")
            else:
                print("--> MOVIMIENTO ILEGAL detectado por el motor.")
        
        # FALLBACK: Si la IA falla o da un movimiento ilegal, hacemos un movimiento aleatorio
        if not success:
            print("!! FALLBACK: Ejecutando movimiento aleatorio para no detener el juego.")
            if valid_actions:
                random_action = random.choice(valid_actions)
                server.step(random_action)
                print(f"--> Fallback ejecutado: {random_action['type']} en ({random_action.get('x')}, {random_action.get('y')})")
            else:
                server.step({"type": "pass"})

        turn += 1
        time.sleep(DELAY_ENTRE_TURNOS)

    # Fin del juego
    print("\n" + "="*30)
    print("JUEGO TERMINADO")
    print(f"Ganador: Jugador {server.winner}")
    print(f"Razón: {server.victory_reason}")
    print("="*30)

if __name__ == "__main__":
    main()
