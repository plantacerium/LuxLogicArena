from abc import ABC, abstractmethod
from typing import Any, Dict, List

class GameAdapter(ABC):
    """
    Contrato universal. Si tu juego implementa esto,
    el Agente Universal puede jugarlo.
    """
    
    @abstractmethod
    def get_observation_text(self) -> str:
        """Convierte el estado actual en una descripción de texto/ASCII para el LLM."""
        pass

    @abstractmethod
    def get_rules_text(self) -> str:
        """Devuelve las reglas y el objetivo en texto claro."""
        pass

    @abstractmethod
    def get_valid_actions_schema(self) -> List[Dict]:
        """Devuelve una lista o esquema JSON de qué se puede hacer ahora."""
        pass

    @abstractmethod
    def execute_action(self, llm_response: Dict[str, Any]) -> float:
        """
        Toma el JSON del LLM, lo traduce a código del juego, 
        ejecuta y devuelve la recompensa (reward).
        """
        pass

    @abstractmethod
    def is_game_over(self) -> bool:
        pass
