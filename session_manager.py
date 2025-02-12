import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon import functions, types
from telethon.errors import ChatAdminRequiredError, ChatWriteForbiddenError
from config import Config
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest


class SessionManager:
    def __init__(self, api_id: str, api_hash: str, sessions_path: str, groups_path: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.sessions_path = sessions_path
        self.groups_path = groups_path
        self.sessions = {}
        self.groups = []

    def load_sessions(self):
        with open(self.sessions_path, 'r') as file:
            sessions_data = list(json.load(file))

        for session in sessions_data:
            phone = session["phone"]
            try:
                session_string = session["session"]
            except KeyError:
                session_string = session["sessions"]

            client = TelegramClient(StringSession(session_string), self.api_id, self.api_hash)

            self.sessions[phone] = client
    
    def load_groups(self):
        groups_data = []
        with open(self.groups_path, 'r') as file:
            groups_data = list(json.load(file))

        #     print(groups_data)
        # print(groups_data)
        # print(type(groups_data))

        # for group in groups_data:
        #     group_id = group["group_id"]
        #     group_hash = group["group_link"]
        #     sessions_names = list(group["sessions_names"])

        #     groups_data.append({
        #         "group_id": group_id,
        #         "group_link": group_hash,
        #         "sessions_names": sessions_names
        #     })
        self.groups = groups_data

    async def update_groups_sessions(self, groups_data, sessions_data):

        for i, gr_data in enumerate(groups_data):
            for name in gr_data["sessions_names"]:
                if name in sessions_data:
                    group = await self.connect_to_group(name=name, group_id=gr_data["group_id"], group_link=gr_data["group_link"])
                else:
                    groups_data[i]["sessions_names"].remove(name)
        
        return groups_data
    
    def hash_from_group_link(self, group_link: str):
        group_split = group_link.split('+')
        if len(group_split) > 1:
            group_hash = group_split[1]
        else:
            group_hash = group_split
        
        return group_hash

    def get_users_in_group(self, group_id):
        for group_data in self.groups:
            if group_id == group_data["group_id"]:
                return (group_data["sessions_names"], group_data["group_link"])
            else:
                continue

    def get_session(self, name):

        return self.sessions.get(name)

    def get_all_sessions(self):

        return self.sessions
    
    def get_all_groups(self):

        return self.groups
    
    async def connect_to_group(self, name, group_id, group_link=None):

        client = self.get_session(name)
        if not client:
            raise ValueError(f"Session '{name}' not found.")
        try:
            group = await client.get_entity(group_id)
            print("(Already) Group was connected.")
            return group
        except:
            try:
                if group_link is not None:
                    group_hash = self.hash_from_group_link(group_link)
                    print(f"Group hash: {group_hash}")
                    updates = await client(ImportChatInviteRequest(group_hash))
                else:
                    updates = await client(JoinChannelRequest(
                        channel=group_id
                    ))
                
                group = await client.get_entity(group_id)
                print("Group was connected.")
                return group
            except Exception as e:
                raise ValueError(f"Failed to connect to group: {e}")

    async def send_message_to_group(self, name, group_id, text, timeout, message_id=None, reply=False):

        client = self.get_session(name)
        if not client:
            raise ValueError(f"Session '{name}' not found.")

        #await client.start()
        try:
            group = await client.get_entity(group_id)

            if message_id is not None:
                await client.send_read_acknowledge(group_id, max_id=message_id)

            await asyncio.sleep(1)

            async with client.action(group, 'typing'):
                await asyncio.sleep(timeout/3)
                if not reply:
                    sent_message = await client.send_message(group_id, text)
                else:
                    sent_message = await client.send_message(group_id, text, reply_to=message_id)

            await client.action(group, 'cancel')

            return sent_message
            #await client.send_message(group, message)
        except ChatAdminRequiredError:
            raise PermissionError("The account is not an admin in this group.")
        except ChatWriteForbiddenError:
            raise PermissionError("The account does not have permission to write in this group.")
        except Exception as e:
            raise ValueError(f"Failed to send message: {e}")

    async def disconnect_session(self, name):
        try:
            client = self.get_session(name)
            if client:
                await client.disconnect()
        except Exception as e:
            print(f"Error disconnecting client with: {e}")