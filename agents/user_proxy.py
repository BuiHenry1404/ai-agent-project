from autogen_agentchat.agents import UserProxyAgent

class UserAgent:
    def __init__(self):
        self.agent = UserProxyAgent(name="User")

    def get(self):
        return self.agent