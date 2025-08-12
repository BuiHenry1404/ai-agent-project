import os
from typing import Optional
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo
from dotenv import load_dotenv

# Load environment variables
# load_dotenv()

class LLMProviderManager:
    """Manages the Google Gemini LLM provider for the autogen framework"""
    
    def __init__(self):
        self.gemini_client: Optional[OpenAIChatCompletionClient] = None
        
    def get_gemini_client(self) -> OpenAIChatCompletionClient:
        """Get Google Gemini client with proper configuration"""
        if not self.gemini_client:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
                
            self.gemini_client = OpenAIChatCompletionClient(
                model="gemini-2.5-flash",
                model_info=ModelInfo(
                    vision=True, 
                    function_calling=True, 
                    json_output=True, 
                    family="google", 
                    structured_output=True
                ),
                api_key=api_key
            )
        return self.gemini_client
    
    def get_client(self) -> OpenAIChatCompletionClient:
        """Always return the Gemini client"""
        return self.get_gemini_client()


# Global instance
llm_manager = LLMProviderManager()
