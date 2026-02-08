import json
import ollama
import sys
import random

# Importamos el servidor del juego proporcionado
# Asegúrate de que este script esté en la raíz del repo para que encuentre los módulos
from _00_entry.game_server import GameServer

MODEL_NAME = "gemma2"  # Cambia a "gemma3" si ya lo tienes en tu lista de 'ollama list'

def render_board_ascii(server: GameServer) -> str:
    """
    Convierte el estado interno del tablero en una representación ASCII
    que el LLM pueda entender visualmente.
    """
    if not server.board:
        return "Tablero vacío."

    grid_size = server.grid_size
    # Crear una matriz vacía
    display = [['.' for _ in range(grid_size)] for _ in range(grid_size)]

    # Símbolos para las piezas:
    # P: Prisma, M: Espejo, S: Splitter
    # Mayúscula = Jugador 1, Minúscula = Jugador 2
    symbols = {
        "PRISM": "P",
        "MIRROR": "M",
        "SPLITTER": "S"
    }

    for (x, y), stone in server.board.stones.items():
        char = symbols.get(stone.stone_type.name, "?")
        if stone.player == 2:
            char = char.lower()
        
        # Añadir indicador de rotación si es necesario (simplificado para no saturar al LLM)
        display[y][x] = char

    # Construir el string con coordenadas
    header = "   " + "".join([f"{i%10}" for i in range(grid_size)])
    rows = []
    for y in range(grid_size):
        row_str = f"{y:2d} " + "".join(display[y])
        rows.append(row_str)
    
    return header + "\n" + "\n".join(rows)

def get_valid_actions_summary(server: GameServer):
    """
    Obtiene acciones válidas y devuelve un resumen o una muestra aleatoria
    para no saturar el contexto del LLM con 500 acciones posibles.
    """
    actions_response = server.get_valid_actions()
    valid_actions = actions_response.get("valid_actions", [])
    
    if not valid_actions:
        return [], "No valid actions."

    # Filtramos acciones simples para sugerir al LLM
    place_actions = [a for a in valid_actions if a['type'] == 'place']
    # Tomamos una muestra para darle ejemplos
    sample = random.sample(place_actions, min(5, len(place_actions))) if place_actions else []
    
    return valid_actions, json.dumps(sample)

def ask_ollama(board_str, valid_sample, player_id):
    """
    Construye el prompt y consulta a Ollama.
    """
    prompt = f"""
    Estás jugando un juego de estrategia por turnos en una cuadrícula 19x19.
    Tu objetivo es controlar territorio usando láseres y espejos.
    Eres el JUGADOR {player_id}. (Tus piezas son MAYÚSCULAS, el oponente minúsculas).

    ESTADO DEL TABLERO:
    {board_str}

    LEYENDA:
    . = Vacío
    P/p = Prisma (Refracta)
    M/m = Espejo (Refleja)
    S/s = Splitter (Divide el rayo)

    REGLAS:
    - Debes colocar una pieza o rotar una existente.
    - Formato de respuesta: ESTRICTAMENTE JSON.

    EJEMPLOS DE ACCIONES VÁLIDAS:
    {valid_sample}

    Tu tarea: Genera un objeto JSON con tu próximo movimiento.
    Usa coordenadas x (0-18) e y (0-18).
    Ejemplo de salida JSON:
    {{"type": "place", "x": 10, "y": 10, "stone_type": "MIRROR"}}
    
    RESPUESTA JSON:
    """

    try:
        response = ollama.generate(model=MODEL_NAME, prompt=prompt, format="json")
        return response['response']
    except Exception as e:
        print(f"Error conectando con Ollama: {e}")
        return None

def main():
    print(f"Iniciando AI Player con modelo: {MODEL_NAME}")
    
    # 1. Iniciar servidor directamente
    server = GameServer(grid_size=19)
    server.reset({"starting_energy": 20})
    
    step = 0
    max_steps = 20  # Límite para prueba

    while not server.game_over and step < max_steps:
        current_player = server.current_player
        print(f"\n--- Turno {step + 1} (Jugador {current_player}) ---")
        
        # 2. Renderizar tablero para el LLM
        board_ascii = render_board_ascii(server)
        print(board_ascii)

        # 3. Obtener acciones válidas (para validar después)
        all_valid_actions, sample_str = get_valid_actions_summary(server)
        
        # 4. Consultar a Ollama
        print("Pensando...")
        llm_response_json = ask_ollama(board_ascii, sample_str, current_player)
        
        action = None
        try:
            # Limpiamos posibles bloques de código markdown ```json ... ```
            clean_json = llm_response_json.replace("```json", "").replace("```", "").strip()
            action = json.loads(clean_json)
            print(f"La IA sugiere: {action}")
        except:
            print(f"Error parseando JSON de la IA: {llm_response_json}")

        # 5. Validación y Fallback (Si la IA alucina o falla)
        # Verificamos si la acción es legal simplificadamente (o simplemente intentamos ejecutarla)
        result = server.step(action)
        
        if result.get("error") or result.get("reward") == -0.1: # -0.1 es el castigo por invalida en tu codigo
            print(">> Acción inválida intentada por la IA. Ejecutando movimiento aleatorio de fallback.")
            # Fallback: Elegir movimiento aleatorio válido para que el juego no se trabe
            if all_valid_actions:
                fallback_action = random.choice(all_valid_actions)
                server.step(fallback_action)
                print(f">> Fallback ejecutado: {fallback_action}")
            else:
                server.step({"type": "pass"})
        
        step += 1

    print("\nJuego Terminado.")
    print(f"Ganador: {server.winner}, Razón: {server.victory_reason}")

if __name__ == "__main__":
    main()
