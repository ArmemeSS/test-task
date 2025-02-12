import json
from pydantic import BaseModel

class Config:
    def __init__(self) -> None:
        self.OPENAI_API_KEY = "sk-p...0cA"

        self.DEFAULT_MODEL = "gpt-3.5-turbo"

        self.PUSH_DIRECTORY = "./push_data"

        self.UPLOAD_DIRECTORY = "./config_data"

        self.AGENTS_CONFIG_PATH = "./config_data/agents.json"

        self.SESSIONS_CONFIG_PATH = "./config_data/sessions.json"
        
        self.GROUPS_CONFIG_PATH = "./config_data/groups_data.json"

        self.TELEGRAM_GROUP_ID = -0

        self.TELEGRAM_GROUP_HASH = ""

        self.TELEGRAM_API_ID = ""

        self.TELEGRAM_API_HASH = ""

        self.CONVERSATION_BASE_LEN = 4
    
    def change_ai_model(self, model_name: str):
        self.DEFAULT_MODEL = model_name

    def set_agents_path(self, file_path: str):
        self.AGENTS_CONFIG_PATH = file_path
    
    def set_sessions_path(self, file_path: str):
        self.SESSIONS_CONFIG_PATH = file_path
    
    def set_groups_path(self, file_path: str):
        self.GROUPS_CONFIG_PATH = file_path

    def set_openai_api_key(self, api_key: str):
        self.OPENAI_API_KEY = api_key

    def set_telegram_api_options(self, api_id: str, api_hash: str):
        self.TELEGRAM_API_ID = api_id
        self.TELEGRAM_API_HASH = api_hash
    
    def get_all_data(self):
        return_data = {
            "open_ai_api_key": self.OPENAI_API_KEY,
            "open_ai_model": self.DEFAULT_MODEL,
            "agents_file_path": self.AGENTS_CONFIG_PATH,
            "sessions_file_path": self.SESSIONS_CONFIG_PATH,
            "groups_file_path": self.GROUPS_CONFIG_PATH,
            "agents_file_path": self.AGENTS_CONFIG_PATH,
            "telegram_api_id": self.TELEGRAM_API_ID,
            "telegram_api_hash": self.TELEGRAM_API_HASH
        }
        return return_data
    
api_config = Config()

