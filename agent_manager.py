import json
import random
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import SystemMessagePromptTemplate, PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate
from langchain.chains.llm import LLMChain
from langchain.agents import Tool, AgentExecutor
from langchain.agents.conversational_chat.base import ConversationalChatAgent
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from prompts import AGENT_PROMPT_TEMPLATE
from config import api_config


class AgentManager:
    def __init__(self, model_name: str, agents_path: str, api_key: str):
        self.llm = ChatOpenAI(model=model_name, api_key=api_key, temperature=1)
        self.agents_path = agents_path
        self.agents = []
        self.chat_history = []
        self.load_agents(self.agents_path)

    def create_agent(self, name: str, bio: str, directive: list):
        formatted_prompt = AGENT_PROMPT_TEMPLATE.format(
        name=name,
        bio=bio,
        directive=directive
        )

        system_prompt = SystemMessagePromptTemplate(
            prompt=PromptTemplate(
                template=formatted_prompt
            )
        )

        conversational_agent = ConversationalChatAgent.from_llm_and_tools(
            llm=self.llm,
            tools=[],
            system_message=formatted_prompt
        )

        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=conversational_agent,
            tools=[],
            verbose=True,
            handle_parsing_errors=True
        )

        self.agents.append({
            "name": name,
            "bio": bio,
            "directive": directive,
            "prompt": formatted_prompt,
            "agent": agent_executor
        })

    def load_agents(self, agents_config_path: str):
        with open(agents_config_path, 'r') as file:
            agents_data = json.load(file)

        for agent_data in agents_data:
            name = agent_data["name"]
            bio = agent_data["bio"]
            directive = agent_data["directives"]

            self.create_agent(name, bio, directive)

    def execute_agents(self):
        self.load_agents()

    def get_agents(self):
        return self.agents

    def add_message_to_history(self, message: str):
        self.chat_history.append(message)

    def get_agent_response(self, user_message: str, selected_agent=None):
        self.add_message_to_history(user_message)
        if not selected_agent:
            selected_agent = random.choice(self.get_agents())

        #print(selected_agent)

        inputs = {
            "input": user_message,
            "chat_history": self.chat_history
        }

        response = selected_agent["agent"].run(inputs)

        self.add_message_to_history(response)

        print(f"{selected_agent['name']}: {response}")

        return response
        
