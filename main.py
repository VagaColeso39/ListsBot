import aiogram
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import Filter
import asyncio
import sqlite3
import random
import hashlib
from adds import *


class UserStateFilter(Filter):
    def __init__(self, state: str):
        self.state = state


    async def __call__(self, message:Message) -> bool:
        return users[message.chat.id] == self.state


TOKEN = "5857365241:AAFw-p6c5MUuuFlhdlpqE4VTugM_Ah37R8c"
bot = Bot(TOKEN)
dp = Dispatcher(bot)

conn = sqlite3.connect('main.db')
conn.isolation_level = None
cursor = sqlite3.Cursor(conn)

groups = {}
users = {}




async def check_user(tg_id: int):
    if cursor.execute(CHECK_USER_BY_ID, (tg_id,)).fetchone():
        return True
    return False


async def create_token(user_id: int, group_name: str):
    string = f'{user_id}f{group_name}f{random.randint(1, 10000)}'
    token = hashlib.sha256(string.encode()).hexdigest()
    return token


class Item:
    def __init__(self, group_id: int, item_id, name: str, hint: str = None):
        self.group_id = group_id
        self.id = item_id
        self.name = name
        self.hint = hint


class User:
    def __init__(self, tg_id: int, name: str, language: str, groups: dict = None,
                 invitations: list = None, new=False):
        """groups: dict(group_id: Group)
           invitations: list(group_id)"""
        self.tg_id = tg_id
        self.name = name
        self.language = language
        if groups is not None:
            self.groups = groups
        else:
            self.groups = {}
        if invitations is not None:
            self.invitations = invitations
        else:
            self.invitations = []

        if new:
            cursor.execute(CREATE_USER, (tg_id, name, 'ru'))

    def turn_notifications(self, group_id: int):
        self.groups[group_id].change_notification(self.tg_id)

    def add_group(self, group_id: int):
        self.groups[group_id] = groups[group_id]

    def add_invitation(self, group_id: int):
        self.invitations.append(group_id)

    async def create_group(self, group_name: str):
        check = cursor.execute(GET_GROUP_ID_BY_NAME_AND_USER_ID, (group_name, self.tg_id)).fetchone()
        if check:
            return False

        token = await create_token(self.tg_id, group_name)
        cursor.execute(CREATE_GROUP, (group_name, self.tg_id, token))
        group_id = cursor.execute(GET_GROUP_ID_BY_TOKEN, (token,)).fetchone()
        groups[group_id] = Group(group_id, group_name, self.tg_id, token)
        self.add_group(group_id)


class Group:
    def __init__(self, id: int, name: str, owner_id: int, token: str, participants: list[User] = None,
                 items: list[Item] = None,
                 notifications: dict["id": bool] = None):
        self.id = id
        self.name = name
        self.owner_id = owner_id
        self.token = token
        if participants is not None:
            self.participants = participants
        else:
            self.participants = []
        if notifications is not None:
            self.notifications = notifications
        else:
            self.notifications = []
        if items is not None:
            self.items = items
        else:
            self.items = []

    def change_notification(self, user_id):
        self.notifications[user_id] = not self.notifications[user_id]

    def create_invitation(self, receiver_id: int):
        users[receiver_id].add_invitation(self.id)

    def add_participant(self, user_id):
        self.participants.append(users[user_id])

    def add_item(self, item: Item):
        self.items.append(item)


@dp.callback_query_handler(lang_cb.filter())
async def lang_change(callback: CallbackQuery, callback_data: dict):
    tg_id = callback.message.chat.id
    lang = callback_data['value']
    if lang == 'ru':
        users[tg_id].language = 'ru'
    else:
        users[tg_id].language = 'en'
    await callback.message.answer(replies['main_menu'][lang], reply_markup=await kb_generator('main', lang))
    cursor.execute(CHANGE_LANGUAGE_BY_ID, (lang, tg_id))


@dp.callback_query_handler(text='groups')
async def groups_list_handler(callback: CallbackQuery):
    user_id = callback.message.chat.id
    t = [(g.id, g.name) for g in users[user_id].groups.items()]
    kb = await groups_cb_kb_generator(t)
    await callback.message.answer(replies['groups_list'][users[user_id].language], reply_markup=kb)


@dp.callback_query_handler(text='create_group')
async def group_creator_handler(callback: CallbackQuery):
    user_id = callback.message.chat.id
    users[user_id].creating_group = True
    await callback.message.answer(replies['name_group'][users[user_id].language])


@dp.callback_query_handler(groups_cb.filter())
async def group_cb_handler(callback: CallbackQuery, callback_data: dict):
    group_id = callback_data['id']
    items = groups[group_id].items
    lang = users[callback.message.chat.id].language
    string = replies['group_items'][lang] + '\n'.join(f'{item.name} ({item.hint})' for item in items)
    await callback.message.answer(string)


@dp.message_handler(commands=['lang', 'language'])
async def change_language(message: Message):
    await message.answer('Выберите язык/Choose language', reply_markup=LANGUAGE_KEYBOARD)


@dp.message_handler(commands=['start'])
async def start_menu(message: Message):
    tg_id = message.chat.id
    if not await check_user(tg_id):
        users[tg_id] = User(tg_id, message.chat.username, language='ru', new=True)
        await change_language(message)

    await message.answer(replies['main_menu'][users[tg_id].language],
                         reply_markup=await kb_generator('main', users[tg_id].language))


dp.message_handler()


async def main():
    for user_info in cursor.execute(GET_ALL_USERS).fetchall():
        users[user_info[0]] = User(user_info[0], user_info[1], user_info[2])
        for group_id in cursor.execute(GET_INVITATION_BY_TG_ID, (user_info[0],)).fetchall():
            users[user_info[0]].add_invitation(group_id)

    for group_info in cursor.execute(GET_ALL_GROUPS).fetchall():
        groups[group_info[0]] = Group(group_info[0], group_info[1], group_info[3], group_info[2])
        for participant_id in cursor.execute(GET_GROUP_PARTICIPANTS, (group_info[0],)).fetchall():
            groups[group_info[0]].add_participant(participant_id)
            users[participant_id].add_group(group_info[0])
        for item_info in cursor.execute(GET_ITEMS_BY_GROUP_ID, (group_info[0],)).fetchall():
            groups[group_info[0]].add_item(Item(group_info[0], item_info[0], item_info[1], item_info[2]))

    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
