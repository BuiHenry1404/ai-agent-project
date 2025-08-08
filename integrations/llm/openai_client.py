from autogen_ext.models.openai import OpenAIChatCompletionClient
import os
import dotenv


dotenv.load_dotenv()

class ModelClientProvider:
    @staticmethod
    def get():
        
        return OpenAIChatCompletionClient(
            model="gemini-2.5-flash",
            api_key=os.getenv("GEMINI_API_KEY")
        )