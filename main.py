from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
import asyncio
import sqlite3
import random
import hashlib
from adds import *

TOKEN = 'MYTOKEN'
bot = Bot(TOKEN)
dp = Dispatcher()

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
    def __init__(self, group_id: int, item_id: int, name: str, hint: str = ''):
        self.group_id = group_id
        self.id = item_id
        self.name = name
        self.hint = hint


class User:
    def __init__(self, tg_id: int, name: str, language: str, new=False, auto_notify: bool = True):
        self.id = tg_id
        self.name = name
        self.language = language
        self.state = (False,)
        self.groups = {}
        self.invitations = {}
        self.auto_notify = auto_notify
        if new:
            cursor.execute(CREATE_USER, (tg_id, name, 'ru'))

    async def turn_notifications(self, group_id: int):
        await self.groups[group_id].change_notification(self.id)

    async def add_group(self, group_id: int):
        self.groups[group_id] = groups[group_id]

    async def leave_from_group(self, group_id: int):
        del self.groups[group_id]

    async def add_invitation(self, group_id: int, inviter_id: int, invite_id: int):
        self.invitations[invite_id] = (group_id, inviter_id)

    async def delete_invitation(self, invite_id: int):
        del self.invitations[invite_id]
        cursor.execute(DELETE_INVITATION, (invite_id,))

    async def create_group(self, group_name: str):
        check = cursor.execute(GET_GROUP_ID_BY_NAME_AND_USER_ID, (group_name, self.id)).fetchone()
        if check:
            return False

        token = await create_token(self.id, group_name)
        cursor.execute(CREATE_GROUP, (group_name, self.id, token))
        group_id = cursor.execute(GET_GROUP_ID_BY_TOKEN, (token,)).fetchone()[0]
        cursor.execute(ADD_PARTICIPANT, (group_id, self.id))
        groups[group_id] = Group(group_id, group_name, self.id, token)
        await self.add_group(group_id)
        await groups[group_id].add_participant(self.id)
        return True


class Group:
    def __init__(self, id: int, name: str, owner_id: int, token: str):
        self.id = id
        self.name = name
        self.owner_id = owner_id
        self.token = token
        self.participants = {}
        self.notifications = {}
        self.items = {}

    async def change_notification(self, user_id: int):
        self.notifications[user_id] = not self.notifications[user_id]
        cursor.execute(CHANGE_NOTIFICATIONS, (self.notifications[user_id], user_id, self.id))

    async def check_user(self, user_id):
        if user_id in [user.id for user in self.participants]:
            return True
        return False

    async def add_notifications(self, notifications: tuple[tuple[int, bool]]):
        for user_id, notify in notifications:
            self.notifications[user_id] = notify

    async def create_invitation(self, receiver_id: int, inviter_id: int, invite_id: int):
        await users[receiver_id].add_invitation(self.id, inviter_id, invite_id)

    async def delete_invitation(self, receiver_id: int, invite_id: int):
        await users[receiver_id].delete_invitation(invite_id)

    async def add_participant(self, user_id: int, new=True):
        if new:
            for participant in self.participants.values():
                text = notifications_texts['add_participant'][participant.language].format(
                    user_name=users[user_id].name, group_name=self.name)
                await bot.send_message(participant.id, text,
                                       reply_markup=await notification_actions_kb_gen(self.id, participant.language))
            self.notifications[user_id] = users[user_id].auto_notify
            cursor.execute(ADD_NOTIFICATION, (True, self.id, user_id))
            cursor.execute(ADD_PARTICIPANT, (self.id, user_id))
        self.participants[user_id] = users[user_id]

    async def add_item(self, item: Item, new: bool = True):
        if new:
            for participant in self.participants.values():
                text = notifications_texts['add_item'][participant.language].format(
                    item_name=item.name, group_name=self.name)
                await bot.send_message(participant.id, text,
                                       reply_markup=await kb_generator('self_delete', participant.language))
        self.items[item.id] = item

    async def comment_item(self, item_id: int, item_hint: str, user_id: int, lang: str):
        for participant in self.participants.values():
            if not self.notifications[participant.id]:
                continue
            text = notifications_texts['comment_item'][participant.language].format(
                group_name=self.name, user_name=users[user_id].name, item_name=self.items[item_id].name,
                hint_text=item_hint)
            await bot.send_message(participant.id, text,
                                   reply_markup=await kb_generator('self_delete', participant.language))
        if self.items[item_id].hint:
            item_hint = f'{self.items[item_id].hint}ㅤ\n{item_hint} ({replies["by"][lang]} @{users[user_id].name})'
        else:
            item_hint = f'{item_hint} ({replies["by"][lang]} @{users[user_id].name}) ㅤ'

        self.items[item_id].hint = item_hint
        cursor.execute(CHANGE_COMMENT, (item_hint, self.id, item_id))

    async def delete_item(self, item_id: int, group_id: int):
        for participant in self.participants.values():
            text = notifications_texts['delete_item'][participant.language].format(
                group_name=groups[group_id].name, item_name=self.items[item_id].name)
            await bot.send_message(participant.id, text,
                                   reply_markup=await kb_generator('self_delete', participant.language))
        del self.items[item_id]
        cursor.execute(DELETE_ITEM, (self.id, item_id))

    async def delete_user(self, user_id: int):
        del self.participants[user_id]
        await users[user_id].leave_from_group(self.id)
        cursor.execute(DELETE_PARTICIPANT, (self.id, user_id))
        for participant in self.participants.values():
            text = notifications_texts['delete_participant'][participant.language].format(
                user_name=users[user_id].name, group_name=self.name)
            await bot.send_message(participant.id, text,
                                   reply_markup=await kb_generator('self_delete', participant.language))


async def formate_items(lang, group_id):
    items = groups[group_id].items.values()
    string = replies['group_items'][lang] + '\n'.join(
        f'{item.name} ({item.hint.split("ㅤ")[-1][1:]})...' if item.hint else item.name for item in items)
    return string


@dp.callback_query(GroupActCb.filter(F.action == 'add_item'))
async def create_item_starter(callback: CallbackQuery, callback_data: CallbackData):
    user_id = callback.message.chat.id
    group_id = callback_data.group_id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        users[user_id].state = (False,)
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    users[user_id].state = ('add_item', group_id)
    await callback.message.edit_text(replies['add_item'][users[user_id].language])



@dp.callback_query(GroupActCb.filter(F.action == 'delete_item'))
async def delete_item_starter(callback: CallbackQuery, callback_data: CallbackData):
    items = groups[callback_data.group_id].items.values()
    info = ((item.name, item.id) for item in items)
    user_id = callback.message.chat.id
    group_id = callback_data.group_id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        users[user_id].state = (False,)
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    kb = await items_deletion_kb_gen(info, group_id)
    await callback.message.edit_text(replies['item_deletion'][users[user_id].language], reply_markup=kb)


@dp.callback_query(GroupActCb.filter(F.action == 'comment_item'))
async def comment_item_starter(callback: CallbackQuery, callback_data: CallbackData):
    items = groups[callback_data.group_id].items.values()
    info = ((item.name, item.id) for item in items)
    user_id = callback.message.chat.id
    group_id = callback_data.group_id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        users[user_id].state = (False,)
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    kb = await items_commentary_kb_gen(info, group_id)
    await callback.message.edit_text(replies['item_commentary'][users[user_id].language], reply_markup=kb)


@dp.callback_query(GroupActCb.filter(F.action == 'group_settings'))
async def group_settings(callback: CallbackQuery, callback_data: CallbackData):
    user_id = callback.message.chat.id
    group_id = callback_data.group_id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        users[user_id].state = (False,)
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    kb = await group_settings_kb_gen(group_id, lang)
    await callback.message.edit_text(replies['group_settings'][lang], reply_markup=kb)


@dp.callback_query(GroupActCb.filter(F.action == 'invite_user'))
async def invite_user(callback: CallbackQuery, callback_data: CallbackData):
    user_id = callback.message.chat.id
    group_id = callback_data.group_id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        users[user_id].state = (False,)
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    await callback.message.edit_text(replies['invite_user'][lang])
    users[user_id].state = ('inviting', group_id)


@dp.callback_query(GroupActCb.filter(F.action == 'main_menu'))
async def move_to_main_menu(callback: CallbackQuery, callback_data: CallbackData):
    await callback.message.edit_text(replies['main_menu'][users[callback.message.chat.id].language],
                                     reply_markup=await kb_generator('main', users[callback.message.chat.id].language))


@dp.callback_query(ItemDlCb.filter())
async def delete_item(callback: CallbackQuery, callback_data: CallbackData):
    item_id = callback_data.item_id
    group_id = callback_data.group_id
    user_id = callback.message.chat.id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    if item_id == -1:
        string = await formate_items(lang, group_id)
        await callback.message.edit_text(string, reply_markup=await group_actions_kb_gen(group_id, lang))
        return
    await groups[group_id].delete_item(item_id, group_id)
    await callback.message.edit_text(replies['item_deleted'][lang])
    string = await formate_items(lang, group_id)
    await callback.message.answer(string, reply_markup=await group_actions_kb_gen(group_id, lang))


@dp.callback_query(ItemComCb.filter())
async def comment_item_handler(callback: CallbackQuery, callback_data: CallbackData):
    item_id = callback_data.item_id
    group_id = callback_data.group_id
    user_id = callback.message.chat.id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    if item_id == -1:
        string = await formate_items(lang, group_id)
        await callback.message.edit_text(string, reply_markup=await group_actions_kb_gen(group_id, lang))
        return
    users[user_id].state = ('comment_item', group_id, item_id)
    await callback.message.edit_text(replies['item_comment'][lang].format(comment=groups[group_id].items[item_id].hint))


@dp.callback_query(LangCb.filter())
async def lang_change(callback: CallbackQuery, callback_data: CallbackData):
    tg_id = callback.message.chat.id
    lang = callback_data.value
    if lang == 'ru':
        users[tg_id].language = 'ru'
    else:
        users[tg_id].language = 'en'
    await callback.message.edit_text(replies['main_menu'][lang], reply_markup=await kb_generator('main', lang))
    cursor.execute(CHANGE_LANGUAGE_BY_ID, (lang, tg_id))


@dp.callback_query(F.data == 'groups')
async def groups_list_handler(callback: CallbackQuery):
    user_id = callback.message.chat.id
    t = [(groups[group_id].id, groups[group_id].name) for group_id in users[user_id].groups.keys()]
    kb = await groups_cb_kb_generator(t)
    await callback.message.edit_text(replies['groups_list'][users[user_id].language], reply_markup=kb)


@dp.callback_query(F.data == 'create_group')
async def group_namer_handler(callback: CallbackQuery):
    user_id = callback.message.chat.id
    users[user_id].state = ('group_creation',)
    await callback.message.edit_text(replies['name_group'][users[user_id].language])


@dp.callback_query(F.data == 'invites')
async def invites_list_handler(callback: CallbackQuery):
    user_id = callback.message.chat.id
    invitations: dict[int: tuple[int, int]] = users[user_id].invitations  # invite_id: (group_id, inviter_id)
    invitations_for_gen = []
    for invite in invitations.items():
        invitations_for_gen.append(
            (f'{groups[invite[1][0]].name}, @{users[invite[1][1]].name}', invite[1][0], invite[0]))
    kb = await invites_actions_kb_gen(invitations_for_gen)
    await callback.message.edit_text(replies['invites_list'][users[user_id].language], reply_markup=kb)


@dp.callback_query(F.data == 'self_delete')
async def self_deletion_handler(callback: CallbackQuery):
    await callback.message.delete()


@dp.callback_query(InvActCb.filter())
async def invite_list_handler(callback: CallbackQuery, callback_data: CallbackData):
    group_id = callback_data.group_id
    invite_id = callback_data.invite_id
    user_id = callback.message.chat.id
    lang = users[user_id].language
    if group_id == -1:
        await callback.message.edit_text(replies['main_menu'][lang], reply_markup=await kb_generator('main', lang))
        return
    await callback.message.edit_text(replies['accept_invite'][lang],
                                     reply_markup=await invite_accept_kb_gen(group_id, invite_id))


@dp.callback_query(InvAccCb.filter())
async def invite_acception_handler(callback: CallbackQuery, callback_data: CallbackData):
    group_id = callback_data.group_id
    invite_id = callback_data.invite_id
    accepted = callback_data.accepted
    user_id = callback.message.chat.id
    lang = users[user_id].language
    if accepted:
        await callback.message.edit_text(replies['invite_accepted'][lang],
                                         reply_markup=await group_actions_kb_gen(group_id, lang))
        await groups[group_id].add_participant(user_id)
        users[user_id].groups[group_id] = groups[group_id]
    else:
        await callback.message.edit_text(replies['invite_declined'][lang],
                                         reply_markup=await kb_generator('main', lang))
    await groups[group_id].delete_invitation(user_id, invite_id)


@dp.callback_query(GroupSettingsCb.filter(F.setting == 'cancel'))
async def cancel_settings_menu(callback: CallbackQuery, callback_data: CallbackData):
    group_id = callback_data.group_id
    user_id = callback.message.chat.id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    string = await formate_items(lang, group_id)
    await callback.message.edit_text(string, reply_markup=await group_actions_kb_gen(group_id, lang))


@dp.callback_query(GroupSettingsCb.filter(F.setting == 'leave_group'))
async def get_token_setting(callback: CallbackQuery, callback_data: CallbackData):
    group_id = callback_data.group_id
    user_id = callback.message.chat.id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        users[user_id].state = (False,)
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    await groups[group_id].delete_user(user_id)
    await callback.message.edit_text(replies['main_menu'][lang], reply_markup=await kb_generator('main', lang))


@dp.callback_query(GroupSettingsCb.filter(F.setting == 'get_token'))
async def get_token_setting(callback: CallbackQuery, callback_data: CallbackData):
    group_id = callback_data.group_id
    token = groups[group_id].token
    user_id = callback.message.chat.id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    await callback.message.answer(f'`{token}`', parse_mode="MARKDOWN")


@dp.callback_query(GroupSettingsCb.filter(F.setting == 'notification'))
async def change_group_notification(callback: CallbackQuery, callback_data: CallbackData):
    group_id = callback_data.group_id
    user_id = callback.message.chat.id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    await groups[group_id].change_notification(user_id)
    if lang == 'ru':
        await callback.message.edit_text(replies['notification_change']['ru'].format(
            'включены' if groups[group_id].notifications[user_id] else 'выключены'),
            reply_markup=await group_settings_kb_gen(group_id, lang))
    elif lang == 'en':
        await callback.message.edit_text(
            replies['notification_change']['en'].format('on' if groups[group_id].notifications[user_id] else 'off'),
            reply_markup=await group_settings_kb_gen(group_id, lang))


@dp.callback_query(GroupsCb.filter())
async def group_cb_handler(callback: CallbackQuery, callback_data: CallbackData):
    group_id = callback_data.id
    user_id = callback.message.chat.id
    lang = users[user_id].language
    if not groups[group_id].check_user(user_id):
        users[user_id].state = (False,)
        await callback.message.edit_text(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    if group_id == -1:
        await callback.message.edit_text(replies['main_menu'][lang], reply_markup=await kb_generator('main', lang))
        return
    string = await formate_items(lang, group_id)
    await callback.message.edit_text(string, reply_markup=await group_actions_kb_gen(group_id, lang))


@dp.message(F.text.in_({'/start'}))
async def start_menu(message: Message):
    tg_id = message.chat.id
    if not await check_user(tg_id):
        users[tg_id] = User(tg_id, message.chat.username, language='ru', new=True)
        await change_language(message)
    else:
        await message.answer(replies['main_menu'][users[tg_id].language],
                             reply_markup=await kb_generator('main', users[tg_id].language))
    await message.delete()


@dp.message(lambda x: users[x.chat.id].state[0] == 'add_item')
async def create_item(message: Message):
    user_id = message.chat.id
    group_id = users[user_id].state[1]
    lang = users[message.chat.id].language
    if not groups[group_id].check_user(user_id):
        users[user_id].state = (False,)
        await message.answer(replies['invalid_action'][lang], reply_markup=await kb_generator('main', lang))
        return
    if message.text == '!':
        await message.answer(replies['group_items'][lang],
                             reply_markup=await group_actions_kb_gen(group_id, lang))
        await message.delete()
        return
    skipped = []
    for item_name in message.text.split(', '):
        if cursor.execute(GET_ITEM_ID_BY_PARAMS, (group_id, item_name)).fetchone():
            skipped.append(item_name)
            continue
        cursor.execute(ADD_ITEM, (group_id, item_name, ''))
        item_id = cursor.execute(GET_ITEM_ID_BY_PARAMS, (group_id, item_name)).fetchone()[0]
        item = Item(group_id, item_id, item_name)
        await groups[group_id].add_item(item)
        await message.answer(replies['item_added'][lang])

    if skipped:
        await message.answer(replies['item_skipped'][lang] + ', '.join(skipped))

    string = await formate_items(lang, group_id)
    await message.answer(string, reply_markup=await group_actions_kb_gen(group_id, lang))


@dp.message(lambda x: users[x.chat.id].state[0] == 'group_creation')
async def group_creation_handler(message: Message):
    user_id = message.chat.id

    if message.text == '!':
        await message.answer(replies['main_menu'][users[user_id].language],
                             reply_markup=await kb_generator('main', users[user_id].language))
    elif await users[user_id].create_group(message.text):
        await message.answer(replies['group_created'][users[user_id].language],
                             reply_markup=await kb_generator('main', users[message.chat.id].language))
        users[user_id].state = (False,)
    else:
        await message.answer(replies['group_creation_fail'][users[user_id].language])
    await message.delete()


@dp.message(lambda x: users[x.chat.id].state[0] == 'comment_item')
async def comment_item(message: Message):
    user_id = message.chat.id
    language = users[user_id].language
    _, group_id, item_id = users[user_id].state
    if not groups[group_id].check_user(user_id):
        users[user_id].state = (False,)
        await message.answer(replies['invalid_action'][language], reply_markup=await kb_generator('main', language))
        return
    users[user_id].state = (0,)
    if message.text == '!':
        await message.answer(await formate_items(language, group_id),
                             reply_markup=await group_actions_kb_gen(group_id, language))
        await message.delete()
        return
    await groups[group_id].comment_item(item_id, message.text, user_id, language)
    await message.answer(replies['item_commented'][language])
    await message.answer(await formate_items(language, group_id),
                         reply_markup=await group_actions_kb_gen(group_id, language))


@dp.message(lambda x: users[x.chat.id].state[0] == 'inviting')
async def invite_user(message: Message):
    user_id = message.chat.id
    language = users[user_id].language
    group_id = users[user_id].state[1]
    if not groups[group_id].check_user(user_id):
        users[user_id].state = (False,)
        await message.answer(replies['invalid_action'][language], reply_markup=await kb_generator('main', language))
        return
    if message.text == '!':
        await message.answer(await formate_items(language, group_id),
                             reply_markup=await group_actions_kb_gen(group_id, language))
        await message.delete()
        return
    passed = []
    at_least_one = False
    for info in message.text.split(', '):
        invited_id = (0,)
        if '@' == info[0]:
            invited_id = cursor.execute(CHECK_USER_BY_NAME, (info[1:],)).fetchone()
        elif info.isdigit():
            invited_id = cursor.execute(CHECK_USER_BY_ID, (int(info),)).fetchone()

        check = cursor.execute(CHECK_INVITATION, (invited_id, group_id)).fetchone()
        if check:
            invited_id = 0

        if invited_id:
            invited_id = invited_id[0]
            cursor.execute(ADD_INVITATION, (group_id, invited_id, user_id))
            invite_id = cursor.execute(GET_INVITATION_ID, (group_id, user_id, invited_id)).fetchone()[0]
            await groups[group_id].create_invitation(invited_id, user_id, invite_id)
            at_least_one = True

        else:
            passed.append(info)

        if at_least_one:
            await message.answer(replies['inviting_completed'][language])

        if passed:
            await message.answer(replies['inviting_missed'][language] + '\n'.join(passed))
        await message.answer(await formate_items(language, group_id),
                             reply_markup=await group_actions_kb_gen(group_id, language))


@dp.message(F.text.in_({'/lang', '/language'}))
async def change_language(message: Message):
    await message.answer('Выберите язык/Choose language', reply_markup=LANGUAGE_KEYBOARD)


async def main():
    for user_info in cursor.execute(GET_ALL_USERS).fetchall():
        users[user_info[0]] = User(user_info[0], user_info[1], user_info[2])
        for invitation_info in cursor.execute(GET_INVITATION_BY_TG_ID, (user_info[0],)).fetchall():
            await users[user_info[0]].add_invitation(invitation_info[0], invitation_info[1], invitation_info[2])

    for group_info in cursor.execute(GET_ALL_GROUPS).fetchall():
        groups[group_info[0]] = Group(group_info[0], group_info[1], group_info[3], group_info[2])
        for participant_id in cursor.execute(GET_GROUP_PARTICIPANTS, (group_info[0],)).fetchall():
            await groups[group_info[0]].add_participant(participant_id[0], False)
            await users[participant_id[0]].add_group(group_info[0])
        for item_info in cursor.execute(GET_ITEMS_BY_GROUP_ID, (group_info[0],)).fetchall():
            await groups[group_info[0]].add_item(Item(group_info[0], item_info[0], item_info[1], item_info[2]), False)
        notifications = cursor.execute(GET_NOTIFICATIONS_BY_GROUP_ID, (group_info[0],)).fetchall()
        await groups[group_info[0]].add_notifications(notifications)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
