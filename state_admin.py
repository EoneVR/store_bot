from aiogram.dispatcher.filters.state import State, StatesGroup


class AddProductStates(StatesGroup):
    waiting_for_category_id = State()
    waiting_for_name = State()
    waiting_for_eng_name = State()
    waiting_for_author = State()
    waiting_for_eng_author = State()
    waiting_for_price = State()
    waiting_for_description = State()
    waiting_for_eng_description = State()
    waiting_for_image = State()
    waiting_for_confirmation = State()
