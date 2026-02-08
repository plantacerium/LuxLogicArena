import json
import ollama
from core import GameAdapter

class UniversalLLMPlayer:
    def __init__(self, model_name="gemma2"):
        self.model_name = model_name

    def play(self, game: GameAdapter, max_turns=20):
        print(f"--- Iniciando Agente Universal con {self.model_name} ---")
        
        turn = 0
        while not game.is_game_over() and turn < max_turns:
            # 1. PERCEPCIÓN
            obs = game.get_observation_text()
            rules = game.get_rules_text()
            valid_actions = game.get_valid_actions_schema()
            
            # 2. RAZONAMIENTO (Prompt Genérico)
            prompt = f"""
            CONTEXTO: Estás jugando un juego.
            OBJETIVO: {rules}
            
            ESTADO ACTUAL:
            {obs}
            
            ACCIONES POSIBLES (Ejemplos):
            {json.dumps(valid_actions[:5])} ...
            
            INSTRUCCIÓN:
            Analiza el estado y responde con un JSON válido que represente tu acción.
            """
            
            print(f"\nTurno {turn}: Pensando...")
            try:
                response = ollama.generate(
                    model=self.model_name,
                    prompt=prompt,
                    format="json",
                    options={"temperature": 0.1}
                )
                
                action_json = json.loads(response['response'])
                print(f"Acción decidida: {action_json}")
                
                # 3. ACCIÓN
                reward = game.execute_action(action_json)
                print(f"Resultado: Recompensa {reward}")
                
            except Exception as e:
                print(f"Error del agente: {e}")
            
            turn += 1
        
        print("Juego terminado.")
