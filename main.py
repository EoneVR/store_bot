from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, LabeledPrice
from geopy.geocoders import Nominatim
from datetime import datetime
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import aiohttp
from collections import defaultdict

from langs import langs
from database import Database
from state_admin import AddProductStates
from keyboard import choose_lang_button, send_contact_button, generate_main_menu, generate_locations_button, \
    generate_submit_location, generate_users_location, generate_category_menu, generate_products_by_category, \
    generate_product_detail_menu, generate_cart_menu, generate_type_payment, generate_admin_tools, \
    generate_change_category, generate_products_for_changes, generate_confirm_for_admin, \
    generate_product_detail_for_admin, generate_period_for_admin, generate_settings

token = ''
PAYMENT_CLICK = ''
PAYMENT_PAYME = ''
bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()
admin_id = [138104571]
user_navigation_history = defaultdict(list)


@dp.message_handler(commands=['start'])
async def command_start(message: Message):
    chat_id = message.chat.id
    db.create_users_table()
    await bot.send_message(chat_id, 'Select language\nВыберите язык', reply_markup=choose_lang_button())


@dp.message_handler(regexp='🇺🇸 English|🇷🇺 Русский')
async def register_user(message: Message):
    lang = message.text
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    user = db.first_select_user(chat_id)
    lang = 'en' if lang == '🇺🇸 English' else 'ru'
    if user:
        db.set_user_language(chat_id, lang)
        await message.answer(langs[lang]['authorization'])
        await show_main_menu(message)
    else:
        db.first_register_user(chat_id, full_name)
        db.set_user_language(chat_id, lang)
        await message.answer(langs[lang]['registration'], reply_markup=send_contact_button(lang))


@dp.message_handler(content_types=['contact'])
async def finish_register(message: Message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    lang = db.get_user_language(chat_id)
    db.update_user_to_finish_register(chat_id, phone)
    db.create_carts_table()
    try:
        db.insert_to_cart(chat_id)
    except:
        pass
    await message.answer(langs[lang]['reg_complete'], reply_markup=ReplyKeyboardRemove())
    await show_main_menu(message)


async def show_main_menu(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await message.answer(langs[lang]['sel_category'], reply_markup=generate_main_menu(lang))


@dp.message_handler(regexp='🛍 Start order|🛍 Начать заказ')
async def delivery(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    db.create_table_locations()
    user_navigation_history[chat_id].append(show_main_menu)
    await message.answer(langs[lang]['location'], reply_markup=generate_locations_button(lang))


@dp.message_handler(content_types=['location'])
async def get_location(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    latitude = message.location.latitude
    longitude = message.location.longitude

    geolocator = Nominatim(user_agent='geopiExercieses')
    geo = geolocator.reverse(str(latitude) + ',' + str(longitude))

    location_name = str(geo)
    db.add_location(chat_id, location_name, latitude, longitude)
    user_navigation_history[chat_id].append(delivery)
    if lang == 'en':
        await message.answer(f'The address where you want to order: {location_name}\nDo you confirm this address?',
                             reply_markup=generate_submit_location(lang))
    else:
        await message.answer(f'Адрес, по которому вы хотите заказать: {location_name}\nВы подтверждаете этот адрес?',
                             reply_markup=generate_submit_location(lang))


@dp.message_handler(regexp='❌ No|❌ Нет')
async def back_to_location(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    user_navigation_history[chat_id].append(get_location)
    await message.answer(langs[lang]['location'], reply_markup=generate_locations_button(lang))


@dp.message_handler(regexp='🗺 My addresses|🗺 Мои адреса')
async def users_address(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    loc = db.get_locations(chat_id)
    user_navigation_history[chat_id].append(delivery)
    if loc is None:
        await message.answer(langs[lang]['no_location'])
    else:
        await message.answer(langs[lang]['choose_address'], reply_markup=generate_users_location(chat_id, lang))


@dp.message_handler(lambda message: message.text and ',' in message.text)
async def get_user_address(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    user_navigation_history[chat_id].append(users_address)
    await message.answer(langs[lang]['address_selected'], reply_markup=generate_main_menu(lang))
    await message.answer(langs[lang]['sel_category'], reply_markup=generate_category_menu(lang))


@dp.message_handler(regexp='✅ Yes|✅ Да')
async def make_order(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    db.create_categories_table()
    db.insert_categories()
    db.create_products_table()
    db.insert_products_table()
    db.create_cart_products_table()
    user_navigation_history[chat_id].append(get_location)
    await message.answer(langs[lang]['address_saved'], reply_markup=generate_main_menu(lang))
    await message.answer(langs[lang]['sel_category'], reply_markup=generate_category_menu(lang))


@dp.message_handler(regexp='⬅ Back|⬅ Назад')
async def back_to_previous_menu(message: Message):
    chat_id = message.chat.id
    if user_navigation_history[chat_id]:
        previous_function = user_navigation_history[chat_id].pop()
        await previous_function(message)
    else:
        await show_main_menu(message)


@dp.callback_query_handler(lambda call: 'view-category' in call.data)
async def show_products(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    _, category_id = call.data.split('_')
    category_id = int(category_id)
    await bot.edit_message_text(langs[lang]['product'], chat_id, message_id,
                                reply_markup=generate_products_by_category(category_id, lang))


@dp.callback_query_handler(lambda call: 'main_menu' in call.data)
async def return_to_main_menu(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=langs[lang]['sel_category'], reply_markup=generate_category_menu(lang))


@dp.callback_query_handler(lambda call: 'view-product' in call.data)
async def show_detail_product(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    _, product_id = call.data.split('_')
    product_id = int(product_id)
    product = db.get_product_detail(product_id)
    cart_id = db.get_user_cart_id(chat_id)
    try:
        quantity = db.get_quantity(cart_id, product[0])
        if quantity is None:
            quantity = 0
    except:
        quantity = 0

    await bot.delete_message(chat_id, message_id)
    with open(product[-2], mode='rb') as img:
        await bot.send_photo(chat_id=chat_id, photo=img,
                             caption=f'''{product[1] if lang == 'ru' else product[5]}

{langs[lang]['description']} : {product[4] if lang == 'ru' else product[7]}
{langs[lang]['author']} : {product[2] if lang == 'ru' else product[6]}
{langs[lang]['price']} : {product[3]}''', reply_markup=generate_product_detail_menu(lang=lang,
                                                                                    product_id=product_id,
                                                                                    category_id=product[-1],
                                                                                    c=quantity))


@dp.callback_query_handler(lambda call: 'back' in call.data)
async def return_to_category(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    _, category_id = call.data.split('_')
    await bot.delete_message(chat_id, message_id)
    await bot.send_message(chat_id, langs[lang]['product'],
                           reply_markup=generate_products_by_category(category_id, lang))


@dp.callback_query_handler(lambda call: 'plus' in call.data)
async def add_product_card(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    _, quantity, product_id = call.data.split('_')
    quantity, product_id = int(quantity), int(product_id)
    quantity += 1
    message_id = call.message.message_id
    product = db.get_product_detail(product_id)
    cart_id = db.get_user_cart_id(chat_id)
    await bot.edit_message_caption(chat_id=chat_id, message_id=message_id,
                                   caption=f'''{product[1] if lang == 'ru' else product[5]}

{langs[lang]['description']} : {product[4] if lang == 'ru' else product[7]}
{langs[lang]['author']} : {product[2] if lang == 'ru' else product[6]}
{langs[lang]['price']} : {product[3]}''', reply_markup=generate_product_detail_menu(lang=lang,
                                                                                    product_id=product_id,
                                                                                    category_id=product[-1],
                                                                                    c=quantity))


@dp.callback_query_handler(lambda call: 'minus' in call.data)
async def remove_product_card(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    _, quantity, product_id = call.data.split('_')
    quantity, product_id = int(quantity), int(product_id)
    message_id = call.message.message_id
    product = db.get_product_detail(product_id)
    cart_id = db.get_user_cart_id(chat_id)
    if quantity <= 1:
        await bot.answer_callback_query(call.id, langs[lang]['zero'])
        pass
    else:
        quantity -= 1
        await bot.edit_message_caption(chat_id=chat_id, message_id=message_id,
                                       caption=f'''{product[1] if lang == 'ru' else product[5]}

{langs[lang]['description']} : {product[4] if lang == 'ru' else product[7]}
{langs[lang]['author']} : {product[2] if lang == 'ru' else product[6]}
{langs[lang]['price']} : {product[3]}''', reply_markup=generate_product_detail_menu(lang=lang,
                                                                                    product_id=product_id,
                                                                                    category_id=product[-1],
                                                                                    c=quantity))


@dp.callback_query_handler(lambda call: 'cart' in call.data)
async def add_choose_product_to_card(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    _, product_id, quantity = call.data.split('_')
    product_id, quantity = int(product_id), int(quantity)

    cart_id = db.get_user_cart_id(chat_id)
    product = db.get_product_detail(product_id)

    final_price = product[3] * quantity
    product_name = product[1] if lang == 'ru' else product[5]
    if db.insert_or_update_cart_product(cart_id, product_name, quantity, final_price):
        await bot.answer_callback_query(call.id, langs[lang]['added_to_cart'])
    else:
        await bot.answer_callback_query(call.id, langs[lang]['change_quantity'])


@dp.message_handler(regexp='🛒 Cart|🛒 Корзина')
async def show_cart(message: Message, edit_message: bool = False):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    cart_id = db.get_user_cart_id(chat_id)
    db.update_total_product_price(cart_id)
    try:
        db.update_total_product_price(cart_id)
    except Exception as e:
        await message.answer(langs[lang]['no_cart'])
        return

    cart_products = db.get_cart_products(cart_id)
    total_products, total_price = db.get_total_products_price(cart_id)
    db.get_cart_products_for_delete(cart_id)
    text = f"{langs[lang]['in_cart']}:\n\n"
    i = 0
    for product_name, quantity, final_price in cart_products:
        i += 1
        text += f'''{i}. {product_name}
{langs[lang]['quantity']}: {quantity}
{langs[lang]['total_cost']}: {final_price} {langs[lang]['currency']}\n\n'''

    text += f'''{langs[lang]['total_products']}: {0 if total_products is None else total_products}
{langs[lang]['total']}: {0 if total_price is None else total_price} {langs[lang]['currency']}'''

    if edit_message:
        await bot.edit_message_text(text, chat_id, message.message_id, reply_markup=generate_cart_menu(cart_id, lang))
    else:
        await bot.send_message(chat_id, text, reply_markup=generate_cart_menu(cart_id, lang))


@dp.callback_query_handler(lambda call: 'delete' in call.data)
async def delete_cart_products(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    _, cart_product_id = call.data.split('_')
    cart_product_id = int(cart_product_id)
    message = call.message

    db.delete_cart_product_from(cart_product_id)

    await bot.answer_callback_query(call.id, text=langs[lang]['delete_product'])
    await show_cart(message, edit_message=True)


@dp.callback_query_handler(lambda call: 'order' in call.data)
async def create_order(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    _, cart_id = call.data.split('_')
    cart_id = int(cart_id)
    db.order_total_price()
    db.order()

    cart_products = db.get_cart_products(cart_id)
    if not cart_products:
        await call.answer(langs[lang]['no_products'])
        return
    await bot.send_message(chat_id, langs[lang]['type_payment'], reply_markup=generate_type_payment(lang))
    await call.answer()


@dp.callback_query_handler(lambda call: 'clean' in call.data)
async def delete_cart(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    _, cart_id = call.data.split('_')
    cart_id = int(cart_id)
    cart_products = db.get_cart_products(cart_id)
    if not cart_products:
        await call.answer(langs[lang]['empty_cart'])
        return
    db.drop_cart_products_default(cart_id)
    await bot.send_message(chat_id, langs[lang]['clean_cart'])
    await show_cart(call.message)
    await call.answer()


@dp.message_handler(regexp='💳 Click|💳 Payme|💵 Наличные|💵 Cash')
async def process_payment(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    cart_id = db.get_user_cart_id(chat_id)
    user_navigation_history[chat_id].append(show_main_menu)
    time_now = datetime.now().strftime('%H:%M:%S')
    new_date = datetime.now().strftime('%Y-%m-%d')

    cart_products = db.get_cart_products(cart_id)
    total_products, total_price = db.get_total_products_price(cart_id)
    db.save_order_total(cart_id, total_products, total_price, time_now, new_date)
    order_total_id = db.orders_total_price_id(cart_id)

    text = f"{langs[lang]['in_cart']}:\n\n"
    for i, (product_name, quantity, final_price) in enumerate(cart_products, start=1):
        text += (
            f"🔹 {i}. {product_name}\n"
            f"   {langs[lang]['quantity']}: {quantity}\n"
            f"   {langs[lang]['total_cost']}: {final_price} {langs[lang]['currency']}\n\n"
        )

    text += (
        f"🔸 {langs[lang]['total_products']}: {total_products if total_products else 0}\n"
        f"🔸 {langs[lang]['delivery']}: 10000 сум\n"
        f"🔸 {langs[lang]['total']}: {total_price if total_price else 0} {langs[lang]['currency']}"
    )

    if message.text == '💳 Click':
        payment_type = 'Click'
        await bot.send_invoice(
            chat_id=chat_id,
            title=f"{langs[lang]['number_order']} {cart_id}",
            description=text,
            payload='bot-defined invoice payload',
            provider_token=PAYMENT_CLICK,
            currency='UZS',
            prices=[
                LabeledPrice(label=f"{langs[lang]['total_cost']}", amount=int(total_price * 100)),
                LabeledPrice(label=f"{langs[lang]['delivery']}", amount=1000000)
            ],
            start_parameter='start_parameter'
        )
    elif message.text == '💳 Payme':
        payment_type = 'Payme'
        await bot.send_invoice(
            chat_id=chat_id,
            title=f"{langs[lang]['number_order']} {cart_id}",
            description=text,
            payload='bot-defined invoice payload',
            provider_token=PAYMENT_PAYME,
            currency='UZS',
            prices=[
                LabeledPrice(label=f"{langs[lang]['total_cost']}", amount=int(total_price * 100)),
                LabeledPrice(label=f"{langs[lang]['delivery']}", amount=1000000)
            ],
            start_parameter='start_parameter'
        )
    else:
        payment_type = 'Cash'
        await message.answer(text)
        await message.answer(langs[lang]['order_placed'], reply_markup=generate_main_menu(lang))
        db.drop_cart_products_default(cart_id)

    for i, (product_name, quantity, final_price) in enumerate(cart_products, start=1):
        db.save_order(order_total_id, product_name, quantity, final_price, payment_type)


@dp.pre_checkout_query_handler(lambda query: True)
async def checkout(pre_checkout_query):
    chat_id = pre_checkout_query.from_user.id
    lang = db.get_user_language(chat_id)
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True, error_message=langs[lang]['error_payment'])


@dp.message_handler(content_types=['successful_payment'])
async def get_payment(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    cart_id = db.get_user_cart_id(chat_id)
    await bot.send_message(chat_id, langs[lang]['payment_success'], reply_markup=generate_main_menu(lang))
    db.drop_cart_products_default(cart_id)


@dp.message_handler(regexp='📓 History of orders|📓 История заказов')
async def show_history_orders(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    cart_id = db.get_user_cart_id(chat_id)
    if lang == 'en':
        try:
            orders_total_price = db.get_orders_total_price(cart_id)
            for i in orders_total_price:
                text = f'''Date of order: {i[-1]}
Time of order: {i[-2]}
Total quantity: {i[3]}
Check amount: {i[2]}\n\n'''
                detail_product = db.get_detail_product(i[0])
                for j in detail_product:
                    text += f'''Product: {j[0]}
Quantity: {j[1]}
Total cost: {j[2]}\n\n'''
                await bot.send_message(chat_id, text)
        except:
            await message.answer("You haven't made any orders yet")
    else:
        try:
            orders_total_price = db.get_orders_total_price(cart_id)
            for i in orders_total_price:
                text = f'''Дата заказа: {i[-1]}
Время заказа: {i[-2]}
Общее количество: {i[3]}
Сумма чека: {i[2]}\n\n'''
                detail_product = db.get_detail_product(i[0])
                for j in detail_product:
                    text += f'''Товар: {j[0]}
Количество: {j[1]}
Общая стоимость: {j[2]}\n\n'''
                await bot.send_message(chat_id, text)
        except:
            await message.answer('Вы еще не сделали ни одного заказа')


@dp.message_handler(regexp='☎ Tech support|☎ Тех поддержка')
async def call_centre(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    phone_number = '+998123456789'
    await message.answer(langs[lang]['message_support'])
    await message.answer_contact(phone_number=phone_number, first_name=langs[lang]['contact_support'])


@dp.message_handler(regexp='⚙ Settings|⚙ Настройки')
async def settings(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    user_navigation_history[chat_id].append(show_main_menu)
    await message.answer(langs[lang]['choose_option'], reply_markup=generate_settings(lang))


@dp.message_handler(regexp='Change language|Сменить язык')
async def change_language(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await message.answer(langs[lang]['select_lang'], reply_markup=choose_lang_button())


@dp.message_handler(commands=['admin'])
async def admin(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    if message.from_user.id in admin_id:
        await message.answer(langs[lang]['hello_admin'], reply_markup=generate_admin_tools(lang))


@dp.message_handler(regexp='🔧 Change menu|🔧 Изменить меню')
async def change_menu(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await message.answer(langs[lang]['change_category'], reply_markup=generate_change_category(lang))


context = {}


@dp.callback_query_handler(lambda call: 'change' in call.data or 'edit-category' in call.data)
async def change_category(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    if call.data == 'change':
        await bot.edit_message_text(langs[lang]['new_name'], chat_id, message_id)
        context[chat_id] = 'awaiting_new_category'
        await call.answer()
    else:
        _, category_id = call.data.split('_')
        category_id = int(category_id)
        await bot.edit_message_text(langs[lang]['change_product'], chat_id, message_id,
                                    reply_markup=generate_products_for_changes(category_id, lang))


@dp.callback_query_handler(lambda call: 'exit' in call.data)
async def return_to_category_admin(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    await bot.delete_message(chat_id, message_id)
    await bot.send_message(chat_id, langs[lang]['change_category'], reply_markup=generate_change_category(lang))


@dp.message_handler(lambda message: context.get(message.chat.id) == 'awaiting_new_category')
async def get_new_category(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    new_category = message.text
    if context.get(chat_id) == 'awaiting_new_category':
        del context[chat_id]
        try:
            category_ru, category_en = map(str.strip, new_category.split('/'))
            db.get_new_category_from_admin(category_ru, category_en)
            if lang == 'en':
                await message.answer(f'New category "{category_en}" successfully added!',
                                     reply_markup=generate_change_category(lang))
            else:
                await message.answer(f'Новая категория "{category_ru}" успешно добавлена!',
                                     reply_markup=generate_change_category(lang))
        except ValueError:
            if lang == 'en':
                await message.answer(
                    "Please provide the categories in the format: 'Category in Russian/ Category in English'.")
            else:
                await message.answer(
                    "Пожалуйста, укажите категории в формате: 'Категория на русском/ Категория на английском'.")


@dp.callback_query_handler(lambda call: 'edit-product' in call.data)
async def show_detail_product_for_admin(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    _, product_id = call.data.split('_')
    product_id = int(product_id)
    product = db.get_product_detail(product_id)
    cart_id = db.get_user_cart_id(chat_id)

    await bot.delete_message(chat_id, message_id)
    with open(product[-2], mode='rb') as img:
        await bot.send_photo(chat_id=chat_id, photo=img,
                             caption=f'''{product[1] if lang == 'ru' else product[5]}

{langs[lang]['description']} : {product[4] if lang == 'ru' else product[7]}
{langs[lang]['author']} : {product[2] if lang == 'ru' else product[6]}
{langs[lang]['price']} : {product[3]}''', reply_markup=generate_product_detail_for_admin(product_id=product_id,
                                                                                         category_id=product[-1],
                                                                                         lang=lang))


@dp.callback_query_handler(lambda call: 'destroy' in call.data)
async def delete_product_for_admin(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    _, product_id = call.data.split('_')
    product_id = int(product_id)
    db.delete_product_for_admin(product_id)
    await bot.delete_message(chat_id, message_id)
    await bot.send_message(chat_id, langs[lang]['delete_book'])


@dp.callback_query_handler(lambda call: 'add-product_' in call.data or 'clear_' in call.data,
                           state='*')
async def add_or_remove(call: CallbackQuery, state: FSMContext):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    _, category_id = call.data.split('_')
    category_id = int(category_id)
    await state.update_data(category_id=category_id)
    if 'clear' in call.data:
        db.delete_category_for_admin(category_id)
        await bot.edit_message_text(langs[lang]['removed_category'], chat_id, message_id)
        await call.answer()
    elif 'add-product' in call.data:
        await bot.edit_message_text(langs[lang]['create_new_prod'], chat_id, message_id)
        await AddProductStates.waiting_for_name.set()
        await call.answer()


@dp.message_handler(state=AddProductStates.waiting_for_name)
async def get_name_on_russian(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await state.update_data(product_name_ru=message.text)
    await message.answer(langs[lang]['create_new_prod_en'])
    await AddProductStates.waiting_for_eng_name.set()


@dp.message_handler(state=AddProductStates.waiting_for_eng_name)
async def get_name_ask_author(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await state.update_data(product_name_en=message.text)
    await message.answer(langs[lang]['ask_author'])
    await AddProductStates.waiting_for_author.set()


@dp.message_handler(state=AddProductStates.waiting_for_author)
async def get_author_on_russian(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await state.update_data(author_ru=message.text)
    await message.answer(langs[lang]['ask_author_en'])
    await AddProductStates.waiting_for_eng_author.set()


@dp.message_handler(state=AddProductStates.waiting_for_eng_author)
async def get_author_ask_price(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await state.update_data(author_en=message.text)
    await message.answer(langs[lang]['ask_price'])
    await AddProductStates.waiting_for_price.set()


@dp.message_handler(state=AddProductStates.waiting_for_price)
async def get_price_ask_description(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    try:
        price = int(message.text)
        await state.update_data(price=price)
        await message.answer(langs[lang]['ask_description'])
        await AddProductStates.waiting_for_description.set()
    except ValueError:
        await message.answer(langs[lang]['check_price'])


@dp.message_handler(state=AddProductStates.waiting_for_description)
async def get_description_on_russian(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await state.update_data(description_ru=message.text)
    await message.answer(langs[lang]['ask_description_en'])
    await AddProductStates.waiting_for_eng_description.set()


@dp.message_handler(state=AddProductStates.waiting_for_eng_description)
async def get_description_ask_image(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await state.update_data(description_en=message.text)
    await message.answer(langs[lang]['ask_image'])
    await AddProductStates.waiting_for_image.set()


@dp.message_handler(content_types=['photo'], state=AddProductStates.waiting_for_image)
async def get_image_and_confirm(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    photo = message.photo[-1]
    photo_file_id = photo.file_id
    await state.update_data(image=photo_file_id)

    file = await bot.get_file(photo_file_id)
    file_path = file.file_path

    file_url = f'https://api.telegram.org/file/bot{token}/{file_path}'
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                file_path_on_disk = f'D:/Новая папка/My projects/store_bot/media/xudoj_lit/{photo_file_id}.jpg'
                with open(file_path_on_disk, 'wb') as f:
                    f.write(await resp.read())
                await state.update_data(image=f'media/xudoj_lit/{photo_file_id}.jpg')

    data = await state.get_data()
    category_id = data['category_id']
    product_name_ru = data['product_name_ru']
    product_name_en = data['product_name_en']
    author_ru = data['author_ru']
    author_en = data['author_en']
    price = data['price']
    description_ru = data['description_ru']
    description_en = data['description_en']

    await bot.send_photo(chat_id=chat_id, photo=photo_file_id,
                         caption=f'''{product_name_ru if lang == 'ru' else product_name_en}

{langs[lang]['description']} : {description_ru if lang == 'ru' else description_en}
{langs[lang]['author']} : {author_ru if lang == 'ru' else author_en}
{langs[lang]['price']} : {price} {langs[lang]['currency']}''', reply_markup=generate_confirm_for_admin(lang))
    await AddProductStates.waiting_for_confirmation.set()


@dp.message_handler(state=AddProductStates.waiting_for_confirmation)
async def confirm_or_cancel(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    data = await state.get_data()
    category_id = data['category_id']
    product_name_ru = data['product_name_ru']
    product_name_en = data['product_name_en']
    author_ru = data['author_ru']
    author_en = data['author_en']
    price = data['price']
    description_ru = data['description_ru']
    description_en = data['description_en']
    image = data['image']
    if message.text == 'Confirm' or message.text == 'Подтвердить':
        db.add_new_product_for_admin(category_id, product_name_ru, author_ru, price, description_ru, image, product_name_en, author_en, description_en)
        if lang == 'en':
            await message.answer(f'Book "{product_name_en}" successfully added in category.',
                                 reply_markup=generate_admin_tools(lang))
        else:
            await message.answer(f'Книга "{product_name_ru}" успешно добавлена в категорию.',
                                 reply_markup=generate_admin_tools(lang))
    else:
        await message.answer(langs[lang]['not_save'], reply_markup=generate_admin_tools(lang))
    await state.finish()


@dp.callback_query_handler(lambda call: 'exiting' in call.data)
async def return_to_category_admin(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    _, category_id = call.data.split('_')
    category_id = int(category_id)
    await bot.delete_message(chat_id, message_id)
    await bot.send_message(chat_id, langs[lang]['change_product'],
                           reply_markup=generate_products_for_changes(category_id, lang))


@dp.message_handler(regexp='📊 Statistics|📊 Статистика')
async def ask_statistics(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    user_navigation_history[chat_id].append(admin)
    await message.answer(langs[lang]['period_stat'], reply_markup=generate_period_for_admin(lang))


@dp.message_handler(
    regexp='1️⃣ месяц|3️⃣ месяца|6️⃣ месяцев|1️⃣2️⃣ месяцев|1️⃣ month|3️⃣ months|6️⃣ months|1️⃣2️⃣ months')
async def show_statistics(message: Message):
    text = message.text
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)

    months_mapping = {
        '1️⃣ месяц': 1,
        '3️⃣ месяца': 3,
        '6️⃣ месяцев': 6,
        '1️⃣2️⃣ месяцев': 12,
        '1️⃣ month': 1,
        '3️⃣ months': 3,
        '6️⃣ months': 6,
        '1️⃣2️⃣ months': 12
    }

    months = months_mapping.get(text)

    if months:
        summary = db.get_orders_summary_for_last_months(months=months)
        total_orders = summary[0]
        total_sum = summary[1]
        if lang == 'ru':
            await message.answer(f'📊 Статистика за последние {months} месяц(ев):\n\n'
                                 f'Количество заказов: {total_orders}\n'
                                 f'Общая сумма заказов: {total_sum} сумм')
        else:
            await message.answer(f'📊 Statistics for the last {months} month(s):\n\n'
                                 f'Total orders: {total_orders}\n'
                                 f'Total order amount: {total_sum} sum')
    else:
        if lang == 'ru':
            await message.answer('Не удалось определить количество месяцев. Попробуйте еще раз.')
        else:
            await message.answer('Could not determine the number of months. Please try again.')


executor.start_polling(dp)
