from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class LangCb(CallbackData, prefix='langChange'):
    value: str


class GroupsCb(CallbackData, prefix='groupsList'):
    id: int


class InvActCb(CallbackData, prefix='invAction'):
    invite_id: int
    group_id: int

class GroupActCb(CallbackData, prefix='groupAct'):
    group_id: int
    action: str


class GroupSettingsCb(CallbackData, prefix='groupSetting'):
    group_id: int
    setting: str


class ItemCrCb(CallbackData, prefix='itemCr'):
    group_id: int


class ItemDlCb(CallbackData, prefix='itemDl'):
    item_id: int
    group_id: int


class ItemComCb(CallbackData, prefix='itemCom'):
    item_id: int
    group_id: int


async def group_settings_kb_gen(group_id: int, lang: str):
    kb = InlineKeyboardBuilder()
    for button in kb_texts['settings']:
        kb.button(text=button[lang], callback_data=GroupSettingsCb(group_id=group_id, setting=button['cb']))
    kb.adjust(*(2, 2))
    return kb.as_markup()


async def group_actions_kb_gen(group_id: int, lang: str):
    kb = InlineKeyboardBuilder()
    for button in kb_texts['group']:
        kb.button(text=button[lang], callback_data=GroupActCb(group_id=group_id, action=button['cb']))
    kb.adjust(*(2, 2, 2))
    return kb.as_markup()


async def groups_cb_kb_generator(groups_info: list[tuple[int, str]]):
    kb = InlineKeyboardBuilder()
    for group_id, name in groups_info:
        kb.button(text=name, callback_data=GroupsCb(id=group_id).pack())
    kb.adjust(2, True)
    return kb.as_markup()


async def invites_actions_kb_gen(invitations_info: list[tuple[str, int, int]]):
    """invitations_info: invite_prompt, group_id, invite_id"""
    kb = InlineKeyboardBuilder()
    for invite in invitations_info:
        kb.button(text=invite[0], callback_data=InvActCb(invite_id=invitations_info[2], group_id=invitations_info[1]).pack())
    kb.button(text='❌', callback_data=InvActCb(invite_id=-1, group_id=invitations_info[1]).pack())
    kb.adjust(*(4, 4, 4, 4))
    return kb.as_markup()

async def items_deletion_kb_gen(items_info: tuple[tuple[str, int]], group_id: int):
    kb = InlineKeyboardBuilder()
    for item in items_info:
        kb.button(text=item[0], callback_data=ItemDlCb(item_id=item[1], group_id=group_id).pack())
    kb.button(text='❌', callback_data=ItemDlCb(item_id=-1, group_id=group_id).pack())
    kb.adjust(*(4, 4, 4, 4))
    return kb.as_markup()


async def items_commentary_kb_gen(items_info: tuple[tuple[str, int]], group_id: int):
    kb = InlineKeyboardBuilder()
    for item in items_info:
        kb.button(text=item[0], callback_data=ItemComCb(item_id=item[1], group_id=group_id).pack())
    kb.button(text='❌', callback_data=ItemComCb(item_id=-1, group_id=group_id).pack())

    kb.adjust(*(4, 4, 4, 4))
    return kb.as_markup()


async def kb_generator(title, lang):
    kb = InlineKeyboardBuilder()
    for item in kb_texts[title]:
        kb.button(text=item[lang], callback_data=item['cb'])
    kb.adjust(*(2, 2, 2))
    return kb.as_markup()


LANGUAGE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Русский', callback_data=LangCb(value='ru').pack()),
     InlineKeyboardButton(text='English', callback_data=LangCb(value='en').pack())]])

CREATE_GROUP = 'INSERT INTO groups (name, owner_id, token) VALUES (?, ?, ?)'
CREATE_USER = 'INSERT INTO users (tg_id, name, language) VALUES (?, ?, ?)'
ADD_PARTICIPANT = 'INSERT INTO participants (group_id, user_id) VALUES (?, ?)'
ADD_ITEM = 'INSERT INTO items (group_id, name, hint) VALUES (?, ?, ?)'
ADD_INVITATION = 'INSERT INTO invitations (group_id, user_id, inviter_id) VALUES (?, ?, ?)'
CHANGE_COMMENT = 'UPDATE items SET hint=? WHERE group_id=? AND id=?'
CHANGE_LANGUAGE_BY_ID = 'UPDATE users SET language=? WHERE tg_id=?'
GET_ITEM_ID_BY_PARAMS = 'SELECT id FROM items WHERE group_id=? AND name=?'
GET_ITEMS_BY_GROUP_ID = 'SELECT id, name, hint FROM items WHERE group_id=?'
GET_ALL_USERS = 'SELECT tg_id, name, language FROM users'
GET_ALL_GROUPS = 'SELECT id, name, token, owner_id FROM groups'
GET_GROUP_PARTICIPANTS = 'SELECT user_id FROM participants WHERE group_id=?'
GET_INVITATION_BY_TG_ID = 'SELECT group_id, inviter_id FROM invitations WHERE user_id=?'
GET_GROUP_ID_BY_TOKEN = 'SELECT id FROM groups WHERE token=?'
GET_GROUP_ID_BY_NAME_AND_USER_ID = 'SELECT id FROM groups WHERE name=? AND owner_id=?'
CHECK_USER_BY_ID = 'SELECT tg_id FROM users WHERE tg_id=?'
CHECK_USER_BY_NAME = 'SELECT tg_id FROM users WHERE name=?'
DELETE_ITEM = "DELETE FROM items WHERE group_id=? AND id=?"
DELETE_PARTICIPANT = 'DELETE FROM participants WHERE group_id=? AND user_id=?'

kb_texts = {'main': [{'en': 'My groups', 'ru': 'Мои группы', 'cb': 'groups'},
                     {'en': 'Ingoing invitations', 'ru': "Входящие приглашения", 'cb': 'invites'},
                     {'en': 'Settings', 'ru': 'Настройки', 'cb': 'settings'},
                     {'en': 'Create group', 'ru': 'Создать группу', 'cb': 'create_group'}],
            'group': [{'en': 'Add', 'ru': 'Добавить', 'cb': 'add_item'},
                      {'en': 'Delete', 'ru': 'Удалить', 'cb': 'delete_item'},
                      {'en': 'Comment', 'ru': 'Комментировать', 'cb': 'comment_item'},
                      {'en': 'Settings', 'ru': 'Настройки', 'cb': 'group_settings'},
                      {'en': 'Invite user', 'ru': 'Пригласить пользователя', 'cb': 'invite_user'},
                      {'en': 'Back to menu', 'ru': 'В главное меню', 'cb': 'main_menu'}],
            'settings': [{'en': 'Notifications mode', 'ru': 'Режим уведомлений', 'cb': 'notification_setting'},
                         {'en': 'Leave group', 'ru': 'Покинуть группу', 'cb': 'leave_group'},
                         {'en': 'Get token', 'ru': 'Получить токен', 'cb': 'get_token'},
                         {'en': 'Change invitation settings', 'ru': 'Изменить настройки приглашений',
                          'cb': 'invitation_settings'}]}

replies = {'by': {'en': 'by', 'ru': 'от'},
           'main_menu': {'ru': 'Главное меню:', 'en': 'Main menu:'},
           'groups_list': {'en': 'List of your groups:\n', 'ru': 'Список ваших групп:\n'},
           'group_settings': {'en': 'Group settings:', 'ru': 'Настройки группы:'},
           'group_items': {'en': 'Items in your group:\n', 'ru': 'Предметы в вашей группе:\n'},
           'name_group': {'en': 'Name your group (or send "!" to cancel creation)', 'ru': 'Назовите свою группу (отправьте "!" чтобы вернуться в главное меню)'},
           'invite_user': {
               'en': 'send username in format @username or use user_id if you know it. Also you can send multiple invites by separating them with commas. Send "!" to cancel inviting',
               'ru': 'Отправьте имя пользователя в формате @username или используйте id пользователя если вы его знаете. Так же можете отправить несколько приглашений разделив их запятыми. Отправьте "!" чтобы вернуться в главное меню'},
           'group_created': {'ru': 'группа успешно создана, возвращаю вас в меню...',
                             'en': 'group successfully created, returning you back to the menu...'},
           'group_creation_fail': {'ru': 'У вас уже есть группа с таким названием, введите другое название:',
                                   'en': 'You already have a group with the same name, try other name'},
           'add_item': {'ru': 'Введите название добавляемой позиции или несколько названий разделенных запятыми (Либо введите "!" чтобы вернуться):',
                        'en': 'Enter the name of the item you adding or several names separated by commas (or send "!" to cancel adding):'},
           'item_added': {'ru': 'Позиции успешно добавлены, возращаю вас к группе...',
                          'en': 'Items successfully added, returning you to the group...'},
           'item_comment': {'ru': 'Введите новый комментарий для позиции (Либо введите "!" чтобы вернуться):',
                            'en': 'Enter new comment for the item (or send "!" to cancel commenting):'},
           'item_deleted': {'ru': 'Позиция успешно удалена, возвращаю вас к группе...',
                            'en': 'Item successfully deleted, returning you back to the group...'},
           'item_skipped': {'ru': 'Часть позиций не удалось добавить, так как они уже добавлены в группу:\n',
                            'en': "Some of the items can't be added, cause they already exists in the group:\n"},
           'item_deletion': {'ru': 'Выберите позицию, которую хотите удалить:',
                             'en': 'Choose the item you want to delete:'},
           'item_commented': {'ru': 'Позиция успешно прокомментированна, возвращаю вас к группе...',
                              'en': 'Item successfully commented, returning you back to the group...'},
           'inviting_missed': {
               'ru': 'Следующие имена и id были набранны неправильно, либо пользователь ни разу не использовал нашего бота:\n',
               'en': 'Some of the passed usernames and ids are wrong, or user have never user our bot:\n'},
           'item_commentary': {'ru': 'Выберите позицию, комментарий к которой хотите изменить:',
                               'en': 'Choose the item which comment you want to change:'},
           'inviting_completed': {
               'ru': 'Пользователям успешно отправленны приглашения, они получат их в разделе "Входящие приглашения" в главном меню',
               'en': 'Users successfully invited, they will get invitations in "Ingoing invitations" in the main menu'}}
