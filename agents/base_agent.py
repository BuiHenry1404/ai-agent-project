from autogen_agentchat.agents import AssistantAgent

class BaseAgent:
    def __init__(self, name: str, model_client, tools=None, system_message=""):
        self.agent = AssistantAgent(
            name=name,
            model_client=model_client,
            tools=tools or [],
            system_message=system_message.strip(),
        )

    def get(self):
        return self.agent