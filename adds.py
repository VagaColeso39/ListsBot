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


class InvAccCb(CallbackData, prefix='invAccept'):
    group_id: int
    invite_id: int
    accepted: bool


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


async def invite_accept_kb_gen(group_id: int, invite_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text='✅', callback_data=InvAccCb(group_id=group_id, invite_id=invite_id, accepted=True))
    kb.button(text='❌', callback_data=InvAccCb(group_id=group_id, invite_id=invite_id, accepted=False))
    kb.adjust(2)
    return kb.as_markup()


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
    kb.button(text='❌', callback_data=GroupsCb(id=-1).pack())

    kb.adjust(*(4, 4, 4, 4), True)
    return kb.as_markup()


async def notification_actions_kb_gen(group_id: int, lang: str):
    kb = InlineKeyboardBuilder()
    kb.button(text=replies['notification_moving'][lang], callback_data=GroupsCb(id=group_id))
    kb.button(text=kb_texts['self_delete'][0][lang], callback_data=kb_texts['self_delete'][0]['cb'])
    return kb.as_markup()


async def invites_actions_kb_gen(invitations_info: list[tuple[str, int, int]]):
    """invitations_info: invite_prompt, group_id, invite_id"""
    kb = InlineKeyboardBuilder()
    for invite in invitations_info:
        kb.button(text=invite[0],
                  callback_data=InvActCb(invite_id=invite[2], group_id=invite[1]).pack())
    kb.button(text='❌', callback_data=InvActCb(invite_id=-1, group_id=-1).pack())
    kb.adjust(*(4, 4, 4, 4))
    return kb.as_markup()


async def items_deletion_kb_gen(items_info: tuple[tuple[str, int]], group_id: int):
    kb = InlineKeyboardBuilder()
    for item in items_info:
        kb.button(text=item[0], callback_data=ItemDlCb(item_id=item[1], group_id=group_id).pack())
    kb.button(text='❌', callback_data=ItemDlCb(item_id=-1, group_id=group_id).pack())
    kb.adjust(*(4, 4, 4, 4))
    return kb.as_markup()


async def items_commentary_kb_gen(items_info: tuple[tuple[str, int]], group_id: int) -> InlineKeyboardMarkup:
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
ADD_NOTIFICATION = 'INSERT INTO notifications (notify, group_id, user_id) VALUES (?, ?, ?)'
ADD_PARTICIPANT = 'INSERT INTO participants (group_id, user_id) VALUES (?, ?)'
ADD_ITEM = 'INSERT INTO items (group_id, name, hint) VALUES (?, ?, ?)'
ADD_INVITATION = 'INSERT INTO invitations (group_id, user_id, inviter_id) VALUES (?, ?, ?)'
CHANGE_COMMENT = 'UPDATE items SET hint=? WHERE group_id=? AND id=?'
CHANGE_LANGUAGE_BY_ID = 'UPDATE users SET language=? WHERE tg_id=?'
CHANGE_NOTIFICATIONS = 'UPDATE notifications SET notify=? WHERE user_id=? AND group_id=?'
GET_ITEM_ID_BY_PARAMS = 'SELECT id FROM items WHERE group_id=? AND name=?'
GET_ITEMS_BY_GROUP_ID = 'SELECT id, name, hint FROM items WHERE group_id=?'
GET_ALL_USERS = 'SELECT tg_id, name, language FROM users'
GET_ALL_GROUPS = 'SELECT id, name, token, owner_id FROM groups'
GET_GROUP_PARTICIPANTS = 'SELECT user_id FROM participants WHERE group_id=?'
GET_INVITATION_BY_TG_ID = 'SELECT group_id, inviter_id, invite_id FROM invitations WHERE user_id=?'
GET_INVITATION_ID = 'SELECT invite_id FROM invitations WHERE group_id=? AND inviter_id=? AND user_id=?'
GET_GROUP_ID_BY_TOKEN = 'SELECT id FROM groups WHERE token=?'
GET_GROUP_ID_BY_NAME_AND_USER_ID = 'SELECT id FROM groups WHERE name=? AND owner_id=?'
GET_NOTIFICATIONS_BY_GROUP_ID = 'SELECT user_id, notify FROM notifications WHERE group_id=?'
CHECK_USER_BY_ID = 'SELECT tg_id FROM users WHERE tg_id=?'
CHECK_USER_BY_NAME = 'SELECT tg_id FROM users WHERE name=?'
CHECK_INVITATION = 'SELECT invite_id FROM invitations WHERE user_id=? AND group_id=?'
DELETE_ITEM = "DELETE FROM items WHERE group_id=? AND id=?"
DELETE_PARTICIPANT = 'DELETE FROM participants WHERE group_id=? AND user_id=?'
DELETE_INVITATION = 'DELETE FROM invitations WHERE invite_id=?'

notifications_texts = {'add_participant': {'ru': 'В группу {group_name} добавлен пользователь @{user_name}',
                                           'en': 'User @{user_name} is added to the group {group_name}'},
                       'add_item': {'ru': 'В группу {group_name} добавлена позиция {item_name}',
                                    'en': 'Item {item_name} is added to the group {group_name}'},
                       'delete_item': {'ru': 'В группе {group_name} удалена позиция {item_name}',
                                       'en': 'Item {item_name} is deleted from the group {group_name}'},
                       'comment_item': {
                           'ru': 'В группе {group_name} пользователь @{user_name} прокомментировал позицию {item_name}: {hint_text}',
                           'en': 'In group {group_name} user @{user_name} commented position {item_name}: {hint_text}'},
                       'delete_participant': {'ru': 'Пользователь @{user_name} покинул группу {group_name}'},
                       'en': "User @{user_name} left the group {group_name}"}

kb_texts = {'main': [{'en': 'My groups', 'ru': 'Мои группы', 'cb': 'groups'},
                     {'en': 'Incoming invites', 'ru': "Входящие приглашения", 'cb': 'invites'},
                     {'en': 'Settings', 'ru': 'Настройки', 'cb': 'settings'},
                     {'en': 'Create group', 'ru': 'Создать группу', 'cb': 'create_group'}],
            'group': [{'en': 'Add', 'ru': 'Добавить', 'cb': 'add_item'},
                      {'en': 'Delete', 'ru': 'Удалить', 'cb': 'delete_item'},
                      {'en': 'Comment', 'ru': 'Комментировать', 'cb': 'comment_item'},
                      {'en': 'Settings', 'ru': 'Настройки', 'cb': 'group_settings'},
                      {'en': 'Invite user', 'ru': 'Пригласить пользователя', 'cb': 'invite_user'},
                      {'en': 'Back to menu', 'ru': 'В главное меню', 'cb': 'main_menu'}],
            'settings': [{'en': 'Notifications mode', 'ru': 'Режим уведомлений', 'cb': 'notification'},
                         {'en': 'Leave group', 'ru': 'Покинуть группу', 'cb': 'leave_group'},
                         {'en': 'Get token', 'ru': 'Получить токен', 'cb': 'get_token'},
                         {'en': 'Change invitation settings', 'ru': 'Изменить настройки приглашений',
                          'cb': 'invitation',
                          }, {'en': '❌', 'ru': '❌', 'cb': 'cancel'}],
            'self_delete': [{'en': 'Mark as read', 'ru': 'Отметить прочитанным', 'cb': 'self_delete'}]}

replies = {'by': {'en': 'by', 'ru': 'от'},
           'main_menu': {'ru': 'Главное меню:', 'en': 'Main menu:'},
           'groups_list': {'en': 'List of your groups:\n', 'ru': 'Список ваших групп:\n'},
           'group_settings': {'en': 'Group settings:', 'ru': 'Настройки группы:'},
           'group_items': {'en': 'Items in your group:\n', 'ru': 'Предметы в вашей группе:\n'},
           'name_group': {'en': 'Name your group (or send "!" to cancel creation)',
                          'ru': 'Назовите свою группу (или отправьте "!" чтобы вернуться в главное меню)'},
           'invites_list': {'ru': 'Входящие приглашения:', 'en': 'Incoming invites:'},
           'accept_invite': {'ru': 'Принять приглашение?', 'en': 'Accept Invite?'},
           'invite_accepted': {'ru': 'Приглашение успешно принято', 'en': 'Invite successfully accepted'},
           'invite_declined': {'ru': 'Приглашение успешно отклонено', 'en': 'Invite successfully declined'},
           'invalid_action': {'ru': 'Данное действие вам не доступно, вероятно вы более не находитесь в данной группе',
                              'en': 'This action is not available for you, probably you were deleted from this group'},
           'invite_user': {
               'en': 'send username in format @username or use user_id if you know it. Also you can send multiple invites by separating them with commas. Send "!" to cancel inviting',
               'ru': 'Отправьте имя пользователя в формате @username или используйте id пользователя если вы его знаете. Так же можете отправить несколько приглашений разделив их запятыми. Отправьте "!" чтобы вернуться в главное меню'},
           'group_created': {'ru': 'группа успешно создана, возвращаю вас в меню...',
                             'en': 'group successfully created, returning you back to the menu...'},
           'group_creation_fail': {
               'ru': 'У вас уже есть группа с таким названием, введите другое название (или отправьте "!" чтобы вернуться в главное меню)',
               'en': 'You already have a group with the same name, try other name (or send "!" to cancel creation)'},
           'notification_change': {'ru': 'Уведомления от этой группы успешно {state}, возвращаю вас в меню настроек',
                                   'en': 'Notifications from that group successfully turned {}, returning you back to the settings menu'},
           'add_item': {
               'ru': 'Введите название добавляемой позиции или несколько названий разделенных запятыми (Либо введите "!" чтобы вернуться):',
               'en': 'Enter the name of the item you adding or several names separated by commas (or send "!" to cancel adding):'},
           'item_added': {'ru': 'Позиции успешно добавлены, возращаю вас к группе...',
                          'en': 'Items successfully added, returning you to the group...'},
           'item_comment': {
               'ru': '{comment}\n Введите новый комментарий для позиции (Либо введите "!" чтобы вернуться):',
               'en': '{comment}\n Enter new comment for the item (or send "!" to cancel commenting):'},
           'item_deleted': {'ru': 'Позиция успешно удалена, возвращаю вас к группе...',
                            'en': 'Item successfully deleted, returning you back to the group...'},
           'item_skipped': {'ru': 'Часть позиций не удалось добавить, так как они уже добавлены в группу:\n',
                            'en': "Some of the items can't be added, cause they already exists in the group:\n"},
           'item_deletion': {'ru': 'Выберите позицию, которую хотите удалить:',
                             'en': 'Choose the item you want to delete:'},
           'item_commented': {'ru': 'Позиция успешно прокомментированна, возвращаю вас к группе...',
                              'en': 'Item successfully commented, returning you back to the group...'},
           'notification_moving': {'ru': 'Перейти к группе', 'en': 'Move to the group'},
           'inviting_missed': {
               'ru': 'Следующие имена и id были набранны неправильно, либо пользователь ни разу не использовал нашего бота:\n',
               'en': 'Some of the passed usernames and ids are wrong, or user have never user our bot:\n'},
           'item_commentary': {'ru': 'Выберите позицию, комментарий к которой хотите изменить:',
                               'en': 'Choose the item which comment you want to change:'},
           'inviting_completed': {
               'ru': 'Пользователям успешно отправленны приглашения, они получат их в разделе "Входящие приглашения" в главном меню',
               'en': 'Users successfully invited, they will get invitations in "Incoming invites" in the main menu'}}
