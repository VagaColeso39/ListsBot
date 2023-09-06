from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

lang_cb = CallbackData('lang', 'value')
groups_cb = CallbackData('group', 'id')


async def groups_cb_kb_generator(groups_info: list[tuple[int, str]]):
    kb = InlineKeyboardMarkup()
    for group_id, name in groups_info:
        kb.add(InlineKeyboardButton(name, callback_data=groups_cb.new(group_id)))
    return kb


async def kb_generator(title, lang):
    kb = InlineKeyboardMarkup()
    for item in kb_texts[title]:
        kb.add(InlineKeyboardButton(item[lang], callback_data=item['cb']))
    return kb


LANGUAGE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton('Русский', callback_data=lang_cb.new('ru')),
     InlineKeyboardButton('English', callback_data=lang_cb.new('en'))]])

CREATE_GROUP = 'INSERT INTO groups (name, owner_id, token) VALUES (?, ?, ?)'
CREATE_USER = 'INSERT INTO users (tg_id, name, language) VALUES (?, ?, ?)'
CHANGE_LANGUAGE_BY_ID = 'UPDATE users SET language=? WHERE tg_id=?'
GET_ITEMS_BY_GROUP_ID = 'SELECT id, name, hint FROM items WHERE group_id=?'
GET_ALL_USERS = 'SELECT tg_id, name, language FROM users'
GET_ALL_GROUPS = 'SELECT id, name, token, owner_id FROM groups'
GET_GROUP_PARTICIPANTS = 'SELECT user_id FROM participants WHERE group_id=?'
GET_INVITATION_BY_TG_ID = 'SELECT group_id FROM invitations WHERE user_id=?'
GET_GROUP_ID_BY_TOKEN = 'SELECT id FROM groups WHERE token=?'
GET_GROUP_ID_BY_NAME_AND_USER_ID = 'SELECT id FROM groups WHERE name=?, owner_id=?'
CHECK_USER_BY_ID = 'SELECT tg_id FROM users WHERE tg_id=?'

kb_texts = {'main': [{'en': 'My groups', 'ru': 'Мои группы', 'cb': 'groups'},
                      {'en': 'Ingoing invitations', 'ru': "Входящие приглашения", 'cb': 'invites'},
                      {'en': 'Settings', 'ru': 'Настройки', 'cb': 'settings'},
                      {'en': 'Create group', 'ru': 'Создать группу', 'cb': 'create_group'}]}

replies = {'main_menu': {'ru': 'Главное меню:', 'en': 'Main menu:'},
           'groups_list': {'en': 'List of your groups:', 'ru': 'Список ваших групп:'}}
