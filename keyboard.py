from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from langs import langs

db = Database()


def choose_lang_button():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    russian = KeyboardButton(text='🇺🇸 English')
    uzbek = KeyboardButton(text='🇷🇺 Русский')
    markup.row(russian, uzbek)
    return markup


def send_contact_button(lang):
    return ReplyKeyboardMarkup([
        [KeyboardButton(text=langs[lang]['contact'], request_contact=True)]
    ], resize_keyboard=True)


def generate_main_menu(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=langs[lang]['start_order'])],
            [KeyboardButton(text=langs[lang]['history_order']), KeyboardButton(text=langs[lang]['cart'])],
            [KeyboardButton(text=langs[lang]['settings']), KeyboardButton(text=langs[lang]['support'])],
        ],
        resize_keyboard=True
    )


def generate_locations_button(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=langs[lang]['my_addresses']), KeyboardButton(text=langs[lang]['send_location'], request_location=True)],
            [KeyboardButton(text=langs[lang]['back'])],
        ],
        resize_keyboard=True
    )


def generate_submit_location(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=langs[lang]['yes']), KeyboardButton(text=langs[lang]['no'])],
            [KeyboardButton(text=langs[lang]['back'])],
        ],
        resize_keyboard=True
    )


def generate_users_location(chat_id, lang):
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    locations = db.get_locations(chat_id)
    buttons = []
    for location in locations:
        btn = KeyboardButton(text=location[0])
        buttons.append(btn)
    buttons.append(KeyboardButton(text=langs[lang]['back']))
    markup.add(*buttons)
    return markup


def generate_category_menu(lang):
    markup = InlineKeyboardMarkup(row_width=2)
    categories = db.get_all_categories()
    buttons = []
    for category in categories:
        if lang == 'ru':
            btn = InlineKeyboardButton(text=category[1], callback_data=f'view-category_{category[0]}')
            buttons.append(btn)
        else:
            btn = InlineKeyboardButton(text=category[2], callback_data=f'view-category_{category[0]}')
            buttons.append(btn)
    markup.add(*buttons)
    return markup


def generate_products_by_category(category_id, lang):
    markup = InlineKeyboardMarkup(row_width=2)
    products = db.get_products_by_category_id(category_id)
    buttons = []
    if lang == 'ru':
        for product in products:
            btn = InlineKeyboardButton(text=product[1], callback_data=f'view-product_{product[0]}')
            buttons.append(btn)
    else:
        for product in products:
            btn = InlineKeyboardButton(text=product[5], callback_data=f'view-product_{product[0]}')
            buttons.append(btn)
    markup.add(*buttons)
    markup.row(
        InlineKeyboardButton(text=langs[lang]['back'], callback_data='main_menu')
    )
    return markup


def generate_product_detail_menu(lang, product_id, category_id, c=1):
    markup = InlineKeyboardMarkup(row_width=3)
    quantity = c

    buttons = []
    btn_minus = InlineKeyboardButton(text=str('➖'), callback_data=f'minus_{quantity}_{product_id}')
    btn_quantity = InlineKeyboardButton(text=str(quantity), callback_data=f'coll')
    btn_plus = InlineKeyboardButton(text=str('➕'), callback_data=f'plus_{quantity}_{product_id}')
    buttons.append(btn_minus)
    buttons.append(btn_quantity)
    buttons.append(btn_plus)
    markup.add(*buttons)
    markup.row(
        InlineKeyboardButton(text=langs[lang]['add_to_cart'], callback_data=f'cart_{product_id}_{quantity}')
    )
    markup.row(
        InlineKeyboardButton(text=langs[lang]['back'], callback_data=f'back_{category_id}')
    )
    return markup


def generate_cart_menu(cart_id, lang):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(text=langs[lang]['make_order'], callback_data=f'order_{cart_id}')
    )
    cart_products = db.get_cart_products_for_delete(cart_id)
    for cart_product_id, product_name in cart_products:
        markup.row(
            InlineKeyboardButton(text=f'❌ {product_name} ❌', callback_data=f'delete_{cart_product_id}')
        )
    markup.row(
        InlineKeyboardButton(text=langs[lang]['delete_cart'], callback_data=f'clean_{cart_id}')
    )
    return markup


def generate_type_payment(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='💳 Click'), KeyboardButton(text='💳 Payme')],
            [KeyboardButton(text=langs[lang]['cash'])], [KeyboardButton(text=langs[lang]['back'])]
        ],
        resize_keyboard=True
    )


def generate_admin_tools(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=langs[lang]['change_menu']), KeyboardButton(text=langs[lang]['statistics'])],
        ],
        resize_keyboard=True
    )


def generate_change_category(lang):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.row(
        InlineKeyboardButton(text=langs[lang]['create_new'], callback_data='change')
    )
    categories = db.get_all_categories()
    buttons = []
    if lang == 'ru':
        for category in categories:
            btn = InlineKeyboardButton(text=category[1], callback_data=f'edit-category_{category[0]}')
            buttons.append(btn)
    else:
        for category in categories:
            btn = InlineKeyboardButton(text=category[2], callback_data=f'edit-category_{category[0]}')
            buttons.append(btn)
    markup.add(*buttons)
    return markup


def generate_products_for_changes(category_id, lang):
    markup = InlineKeyboardMarkup(row_width=1)
    products = db.get_products_by_category_id(category_id)
    buttons = []
    for product in products:
        btn = InlineKeyboardButton(text=product[1], callback_data=f'edit-product_{product[0]}')
        buttons.append(btn)
    markup.add(*buttons)
    markup.row(
        InlineKeyboardButton(text=langs[lang]['add_new_prod'], callback_data=f'add-product_{category_id}')
    )
    markup.row(
        InlineKeyboardButton(text=langs[lang]['delete_category'], callback_data=f'clear_{category_id}')
    )
    markup.row(
        InlineKeyboardButton(text=langs[lang]['back'], callback_data='exit')
    )
    return markup


def generate_confirm_for_admin(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=langs[lang]['confirm']), KeyboardButton(text=langs[lang]['cancel'])],
        ],
        resize_keyboard=True
    )


def generate_product_detail_for_admin(product_id, category_id, lang):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.row(
        InlineKeyboardButton(text=langs[lang]['destroy_book'], callback_data=f'destroy_{product_id}')
    )
    markup.row(
        InlineKeyboardButton(text=langs[lang]['back'], callback_data='exiting')
    )
    return markup


def generate_period_for_admin(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=langs[lang]['one_month']), KeyboardButton(text=langs[lang]['three_month'])],
            [KeyboardButton(text=langs[lang]['six_month']), KeyboardButton(text=langs[lang]['twelve_month'])],
            [KeyboardButton(text=langs[lang]['back'])],
        ],
        resize_keyboard=True
    )


def generate_settings(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=langs[lang]['change_lang']), KeyboardButton(text=langs[lang]['back'])],
        ],
        resize_keyboard=True
    )
