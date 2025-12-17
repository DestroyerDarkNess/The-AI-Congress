from abc import ABC, abstractmethod
from typing import List, Dict

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """
        Generate text from the LLM based on the provided messages.
        
        Args:
            messages: A list of message dictionaries (role, content).
            model: The model identifier to use.
            
        Returns:
            The generated text content.
        """
        pass
