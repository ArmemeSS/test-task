import time
import os
import asyncio
from session_manager import SessionManager
from agent_manager import AgentManager
import threading
from config import api_config
from prompts import message_topic
from telethon import events
import random

class MultiAgentIntegration:
    def __init__(self) -> None:
        self.session_manager = SessionManager(
            api_id=api_config.TELEGRAM_API_ID, 
            api_hash=api_config.TELEGRAM_API_HASH,
            sessions_path=api_config.SESSIONS_CONFIG_PATH,
            groups_path=api_config.GROUPS_CONFIG_PATH
            )
        self.agent_manager = AgentManager(
            model_name=api_config.DEFAULT_MODEL, 
            agents_path=api_config.AGENTS_CONFIG_PATH,
            api_key=api_config.OPENAI_API_KEY
            )
        
        self.groups = []
        self.session_agents = {}
    
    def set_groups_list(self):
        print("Start loading groups")
        self.session_manager.load_groups()
        print("End loading groups")
        groups_data = self.session_manager.get_all_groups()
        self.groups = groups_data
        
    async def set_session_agents_callback(self):
        self.session_manager.load_sessions()

        sessions = self.session_manager.get_all_sessions()
        agents = self.agent_manager.get_agents()
        agents_cycle = iter(agents)
        session_agents = {}
        for session_name, client in sessions.items():
            agent = next(agents_cycle, None)
            if not agent:
                agents_cycle = iter(agents)
                agent = next(agents_cycle)
                #await self.session_manager.disconnect_session(session_name)
            try:
                await asyncio.sleep(2)
                print(f'Connection started for {session_name}')
                await client.start()
                print(f'Connection success for {session_name}')
                session_agents[session_name] = [client, agent]
            except Exception as e:
                print(f'Connection error for {session_name}: {str(e)}')
                continue

        self.session_agents = session_agents

        await asyncio.sleep(2)
    
    async def update_config_files(self):
        self.set_groups_list()
        print("Groups loaded")
        await self.set_session_agents_callback()
        print("Sessions loaded")
        self.groups = await self.session_manager.update_groups_sessions(groups_data=self.groups, sessions_data=self.session_agents)
        print("Groups updated")

    async def start_with_topic(self, group_id, session_name: str, topic: str):

        sessions_client, session_agent = self.session_agents[session_name]

        response = session_agent['agent'].run({
                            "input": topic,
                            "chat_history": [topic]
                        })
        response_timeout = float(len(response)*0.7)

        sent_message = await self.session_manager.send_message_to_group(
                            name=session_name,
                            group_id=group_id,
                            text=response,
                            timeout=response_timeout,
                            reply=True
                        )
        
        return sent_message
    
    async def push_data_callback(self, group_id):

        while True:

            session_names, _ = self.session_manager.get_users_in_group(group_id=group_id)

            session_name = random.choice(list(session_names))
            
            sessions_client, _ = self.session_agents[session_name]

            files_list = os.listdir(api_config.PUSH_DIRECTORY)

            random_item = random.choice(list(files_list))

            file_location = os.path.join(api_config.PUSH_DIRECTORY, random_item)

            await sessions_client.send_file(group_id, file_location)

            await asyncio.sleep(random.randint(300, 370))
            #await asyncio.sleep(random.randint(10, 20))
    
    async def session_is_valid(self, session_name):

        client, agent = self.session_agents[session_name]

        try: 
            await client.start()
            return True
        except:
            return False
    
    async def start_agents_for_group(self, group_id):
        
        group = None

        reply_choose = [True, False, False, False]

        grouped_sessions = {}
        last_agent_responses = {}

        sessions_list, chat_link = self.session_manager.get_users_in_group(group_id=group_id)

        for session_name in sessions_list:
            sessions_client, session_agent = self.session_agents[session_name]
            try:
                session_group = await sessions_client.get_entity(group_id)
                print(f"Listening to group({session_name}): {session_group.title}")
                grouped_sessions[session_name] = [sessions_client, session_agent]
                group = session_group
            except Exception as e:
                print(f"Error finding group in session {session_name}: {e}")
                continue

        if not group:
            raise ValueError("Could not connect to the group with any session.")      
        
        def to_send_msg(session_name):
            #send_choose = [True, False, False, True, True]
            c_session_name, (c_client, _) = random.choice(list(grouped_sessions.items()))
            if session_name == c_session_name:
                return True
            else:
                return False

        async def handle_message(event, session_name, client, agent):

            c_session_name, (c_client, c_agent) = random.choice(list(grouped_sessions.items()))

            if event.id in last_agent_responses:
                pass 

            if to_send_msg(session_name):
                print("Skip")
                return

            if event.out:
                print("Event out")
                return
        
            try:
                user_message = event.raw_text

                if len(user_message) == 0:
                    return

                print(f"USER MESSAGE: {user_message}")

                await asyncio.sleep(random.randint(10, 30))

                if event.is_reply:
                    original_message = await event.get_reply_message()
                    original_message_id = original_message.id

                    if original_message_id in last_agent_responses:
                        session_name, agent = last_agent_responses[original_message_id]

                        response = agent['agent'].run({
                            "input": user_message,
                            "chat_history": [original_message.text, user_message]
                        })

                        response_timeout = float(len(response)*0.7)

                        print(f"Agent {agent['name']} responds to reply: {response}")
                        random_reply = random.choice([not value for value in reply_choose])
                        sent_message = await self.session_manager.send_message_to_group(
                            name=session_name,
                            group_id=group_id,
                            text=response,
                            message_id=original_message_id,
                            timeout=response_timeout,
                            reply=True
                        )
                        last_agent_responses[sent_message.id] = (session_name, agent)

                else:
                    selected_agent = agent

                    print(f"Message handled by agent: {selected_agent['name']} in session: {session_name}")

                    response = self.agent_manager.get_agent_response(user_message=user_message, selected_agent=selected_agent)
                    response_timeout = float(len(response)*0.7)
                    print(f"Response: {response}")
                    random_reply = random.choice(reply_choose)

                    last_reply_key = list(last_agent_responses.keys())[-1] if last_agent_responses else None
                    sent_message = await self.session_manager.send_message_to_group(
                        name=session_name,
                        group_id=group_id,
                        text=response,
                        message_id=last_reply_key,
                        timeout=response_timeout,
                        reply=random_reply
                    )

                    last_agent_responses[sent_message.id] = (session_name, agent)

            except Exception as e:
                print(f"Error while handling message: {e}")
        
        async def assign_handler(event, session_name):
            #session_name, (client, agent) = random.choice(list(grouped_sessions.items()))
            s_client, s_agent = self.session_agents[session_name]
            await handle_message(event, session_name, s_client, s_agent)

        for session_name, (client, _) in grouped_sessions.items():
            print("Add event handler!")
            client.add_event_handler(lambda event: asyncio.create_task(assign_handler(event, session_name)), events.NewMessage(chats=group))
        
        session_name, (client, agent) = random.choice(list(grouped_sessions.items()))
        if len(last_agent_responses) == 0:
            user_message = message_topic.info_topic
            first_message = await self.start_with_topic(group_id=group_id, session_name=session_name, topic=user_message)
            last_agent_responses[first_message.id] = (session_name, agent)

        await asyncio.gather(*[client.run_until_disconnected() for client, _ in grouped_sessions.values()])

    
    def run_async_task(self, loop, coro):
        return loop.run_until_complete(coro)

    def push_data_to_chat(self, group_id):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.run_async_task(loop, self.push_data_callback(group_id=group_id))

    def run_one_group_agents(self, group_id):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.run_async_task(loop, self.start_agents_for_group(group_id=group_id))

    async def start_agents(self):

        await self.update_config_files()

        tasks = []

        for group_data in self.groups:
            group_id = group_data["group_id"]
            tasks.append(self.start_agents_for_group(group_id))
            tasks.append(self.push_data_callback(group_id))

        await asyncio.gather(*tasks)

    async def stop_group_sessions(self, group_id):
        sessions_list, _ = self.session_manager.get_users_in_group(group_id=group_id)
        for session_name in sessions_list:
            await self.session_manager.disconnect_session(name=session_name)
    
    async def stop_all_sessions(self):
        for session_name, (client, agent) in self.session_agents.items():
            await self.session_manager.disconnect_session(name=session_name)
            