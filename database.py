import sqlite3


class Database:
    def __init__(self):
        self.database = sqlite3.connect('shop.db', check_same_thread=False)

    def manager(self, sql, *args,
                fetchone: bool = False,
                fetchall: bool = False,
                commit: bool = False):
        with self.database as db:
            cursor = db.cursor()
            if len(args) == 1:
                cursor.execute(sql, (args[0],))
            else:
                cursor.execute(sql, args)
            if commit:
                result = db.commit()
            if fetchone:
                result = cursor.fetchone()
            if fetchall:
                result = cursor.fetchall()
            return result
# ---------------------------------------------------------------------------------------------------------------------
    def create_users_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        phone TEXT,
        chat_id BIGINT NOT NULL UNIQUE,
        language TEXT
        )
        '''
        self.manager(sql, commit=True)

    def first_select_user(self, chat_id):
        sql = '''
        SELECT * FROM users WHERE chat_id = ?
        '''
        return self.manager(sql, chat_id, fetchone=True)

    def first_register_user(self, chat_id, full_name):
        sql = '''
        INSERT INTO users(chat_id, full_name) VALUES (?,?)
        '''
        self.manager(sql, chat_id, full_name, commit=True)

    def update_user_to_finish_register(self, chat_id, phone):
        sql = '''
        UPDATE users SET phone = ?
        WHERE chat_id = ?
        '''
        self.manager(sql, phone, chat_id, commit=True)

    def set_user_language(self, chat_id, lang):
        user = self.first_select_user(chat_id)
        if user:
            sql = '''
            UPDATE users SET language = ? WHERE chat_id = ?
            '''
            self.manager(sql, lang, chat_id, commit=True)
        else:
            sql = '''
            INSERT INTO users (chat_id, language) VALUES (?,?)
            '''
            self.manager(sql, chat_id, lang, commit=True)

    def get_user_language(self, chat_id):
        sql = '''
        SELECT language FROM users WHERE chat_id = ?
        '''
        result = self.manager(sql, chat_id, fetchone=True)
        if result:
            return result[0]
        return None
# ---------------------------------------------------------------------------------------------------------------------
    def create_table_locations(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS locations(
        location_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_name TEXT,
        location_latitude FLOAT,
        location_longitude FLOAT,
        chat_id INTEGER REFERENCES users(chat_id)
        )
        '''
        self.manager(sql, commit=True)

    def add_location(self, chat_id, location_name, latitude, longitude):
        sql = '''
        INSERT INTO locations(location_name, location_latitude, location_longitude, chat_id) VALUES (?, ?, ?, ?)
        '''
        self.manager(sql, location_name, latitude, longitude, chat_id, commit=True)

    def get_locations(self, chat_id):
        sql = '''
        SELECT location_name FROM locations
        WHERE chat_id = ?
        '''
        result = self.manager(sql, chat_id, fetchall=True)
        return result if result else None
# ---------------------------------------------------------------------------------------------------------------------
    def create_categories_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS categories(
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name VARCHAR(100) NOT NULL UNIQUE,
        category_name_en VARCHAR(100) NOT NULL UNIQUE
        )
        '''
        self.manager(sql, commit=True)

    def categories_table_empty(self):
        sql = '''
        SELECT COUNT(*) FROM categories
        '''
        result = self.manager(sql, fetchone=True)
        return result[0] == 0

    def insert_categories(self):
        if self.categories_table_empty():
            sql = '''
            INSERT INTO categories (category_name, category_name_en) VALUES
            ('Художественная литература', 'Fiction'),
            ('Литература на иностранных языках', 'Foreign Language Literature'),
            ('Бизнес-литература', 'Business Literature'),
            ('Учебная литература', 'Educational Literature'),
            ('Манга и комиксы', 'Manga and Comics'),
            ('Религиозные книги', 'Religious Books')
            '''
            self.manager(sql, commit=True)

    def get_all_categories(self):
        sql = '''
        SELECT * FROM categories
        '''
        return self.manager(sql, fetchall=True)
# ---------------------------------------------------------------------------------------------------------------------
    def create_products_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS products(
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name VARCHAR(100) NOT NULL,
        author VARCHAR(100), 
        price INTEGER NOT NULL,
        description TEXT,
        product_name_en VARCHAR(100) NOT NULL,
        author_en VARCHAR(100),
        description_en TEXT,
        image TEXT,
        category_id INTEGER NOT NULL,
        FOREIGN KEY(category_id) REFERENCES categories(category_id) ON DELETE CASCADE
        )
        '''
        self.manager(sql, commit=True)

    def products_table_empty(self):
        sql = '''
        SELECT COUNT(*) FROM products
        '''
        result = self.manager(sql, fetchone=True)
        return result[0] == 0

    def insert_products_table(self):
        if self.products_table_empty():
            sql = '''
            INSERT INTO products(
            category_id, product_name, author, price, description, image, 
            product_name_en, author_en, description_en
        ) VALUES 
        (1, 'Убийство в восточном экспрессе', 'Агата Кристи', 35000, 
        'Находившийся в Стамбуле великий сыщик Эркюль Пуаро возвращается в Англию на знаменитом "Восточном экспрессе"', 
        'media/xudoj_lit/murder on the oriental express.jpg',
        'Murder on the Orient Express', 'Agatha Christie', 
        'The famous detective Hercule Poirot, who was in Istanbul, returns to England on the famous "Orient Express"'),

        (1, 'Гордость и предубеждение', 'Джейн Остин', 40000, 
        'По соседству с бедной, но уважаемой семьей Беннет поселился богатый и загадочный мистер Дарси', 
        'media/xudoj_lit/pride and prejudice.jpg',
        'Pride and Prejudice', 'Jane Austen', 
        'A wealthy and mysterious Mr. Darcy has moved next door to the poor but respectable Bennet family'),

        (1, 'Великий Гэтсби', 'Ф.Скотт Фицджеральд', 45000, 
        '"Бурные" двадцатые годы прошлого века... Эпоха красивых тусовок, "сухого закона" и "легких" денег...', 
        'media/xudoj_lit/great getsby.jpg',
        'The Great Gatsby', 'F. Scott Fitzgerald', 
        'The "Roaring" twenties of the last century... An era of beautiful parties, "Prohibition," and "easy" money...')
        '''
            self.manager(sql, commit=True)

    def get_products_by_category_id(self, category_id):
        sql = '''
        SELECT * FROM products
        WHERE category_id = ? 
        '''
        return self.manager(sql, category_id, fetchall=True)

    def get_category_id_by_name(self, category_name):
        sql = '''
        SELECT category_id FROM categories 
        WHERE category_name = ?
        '''
        return self.manager(sql, (category_name,), fetchone=True)

    def get_product_detail(self, product_id):
        sql = '''
        SELECT * FROM products
        WHERE product_id = ?
        '''
        return self.manager(sql, product_id, fetchone=True)
# ---------------------------------------------------------------------------------------------------------------------
    def create_carts_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS carts(
        cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(user_id),
        total_price INTEGER DEFAULT 0,
        total_products INTEGER DEFAULT 0
        )
        '''
        self.manager(sql, commit=True)

    def insert_to_cart(self, chat_id):
        sql = '''
        INSERT INTO carts(user_id) VALUES
        (
        (SELECT user_id FROM users WHERE chat_id = ?)
        )
        '''
        self.manager(sql, chat_id, commit=True)

    def get_user_cart_id(self, chat_id):
        sql = '''
        SELECT cart_id FROM carts
        WHERE user_id = (SELECT user_id FROM users WHERE chat_id = ?)
        '''
        result = self.manager(sql, chat_id, fetchone=True)
        return result[0] if result else None
# ---------------------------------------------------------------------------------------------------------------------
    def create_cart_products_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS cart_products(
        cart_product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name VARCHAR(100) NOT NULL,
        quantity INTEGER NOT NULL,
        final_price INTEGER NOT NULL,
        cart_id INTEGER REFERENCES carts(cart_id),

        UNIQUE(product_name, cart_id)
        )
        '''
        self.manager(sql, commit=True)

    def insert_or_update_cart_product(self, cart_id, product_name, quantity, final_price):
        try:
            sql = '''
            INSERT INTO cart_products(cart_id, product_name, quantity, final_price)
            VALUES(?, ?, ?, ?)
            '''
            self.manager(sql, cart_id, product_name, quantity, final_price, commit=True)
            return True
        except:
            sql = '''
            UPDATE cart_products
            SET quantity = ?,
            final_price = ?
            WHERE product_name = ? AND cart_id = ?
            '''
            self.manager(sql, quantity, final_price, product_name, cart_id, commit=True)
            return False

    def get_quantity(self, cart_id, product):
        sql = '''
        SELECT quantity FROM cart_products
        WHERE cart_id = ? and product_name = ?
        '''
        return self.manager(sql, cart_id, product, fetchone=True)

    def update_total_product_price(self, cart_id):
        sql = '''
        UPDATE carts
        SET total_products = (
            SELECT SUM(quantity) FROM cart_products
            WHERE cart_id = ?
        ),
        total_price = (
            SELECT SUM(final_price) FROM cart_products
            WHERE cart_id = ?
        )
        WHERE cart_id = ?
        '''
        self.manager(sql, cart_id, cart_id, cart_id, commit=True)

    def get_cart_products(self, cart_id):
        sql = '''
        SELECT product_name, quantity, final_price
        FROM cart_products
        WHERE cart_id = ?
        '''
        return self.manager(sql, cart_id, fetchall=True)

    def get_total_products_price(self, cart_id):
        sql = '''
        SELECT total_products, total_price FROM carts
        WHERE cart_id = ?
        '''
        return self.manager(sql, cart_id, fetchone=True)

    def get_cart_products_for_delete(self, cart_id):
        sql = '''
        SELECT cart_product_id, product_name FROM cart_products
        WHERE cart_id = ?
        '''
        return self.manager(sql, cart_id, fetchall=True)

    def delete_cart_product_from(self, cart_product_id):
        sql = '''
        DELETE FROM cart_products 
        WHERE cart_product_id = ?
        '''
        self.manager(sql, cart_product_id, commit=True)
# ---------------------------------------------------------------------------------------------------------------------
    def order_total_price(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS orders_total_price(
        orders_total_price_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id INTEGER REFERENCES cards(cart_id),
        total_price DECIMAL (12, 2) DEFAULT 0,
        total_products INTEGER DEFAULT 0,
        time_now DATETIME,
        new_date DATE 
        )
        '''
        self.manager(sql, commit=True)

    def order(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS orders(
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        orders_total_price_id INTEGER REFERENCES orders_total_price(orders_total_price_id),
        product_name VARCHAR(100) NOT NULL,
        quantity INTEGER NOT NULL,
        final_price DECIMAL (12, 2) NOT NULL,
        type_payment TEXT
        )
        '''
        self.manager(sql, commit=True)

    def save_order_total(self, cart_id, total_products, total_price, time_now, new_date):
        sql = '''
        INSERT INTO orders_total_price(cart_id, total_products, total_price, time_now, new_date)
        VALUES (?,?,?,?,?)
        '''
        self.manager(sql, cart_id, total_products, total_price, time_now, new_date, commit=True)

    def orders_total_price_id(self, cart_id):
        sql = '''
        SELECT orders_total_price_id FROM orders_total_price
        WHERE cart_id = ? ORDER BY orders_total_price_id DESC LIMIT 1
        '''
        result = self.manager(sql, cart_id, fetchone=True)
        return result[0] if result else None

    def save_order(self, order_total_id, product_name, quantity, final_price, payment_type):
        sql = '''
        INSERT INTO orders(orders_total_price_id, product_name, quantity, final_price, type_payment)
        VALUES (?,?,?,?,?)
        '''
        self.manager(sql, order_total_id, product_name, quantity, final_price, payment_type, commit=True)

    def get_orders_total_price(self, cart_id):
        sql = '''
        SELECT * FROM orders_total_price
        WHERE cart_id = ?
        '''
        return self.manager(sql, cart_id, fetchall=True)

    def get_detail_product(self, id):
        sql = '''
        SELECT product_name, quantity, final_price FROM orders
        WHERE orders_total_price_id = ?
        '''
        return self.manager(sql, id, fetchall=True)

    def drop_cart_products_default(self, cart_id):
        sql = '''
        DELETE FROM cart_products
        WHERE cart_id = ?
        '''
        self.manager(sql, cart_id, commit=True)
#  ----------------------------------------- ADMIN SIDE --------------------------------------------------------------
    def get_new_category_from_admin(self, category_ru, category_en):
        sql = '''
        INSERT INTO categories(category_name, category_name_en) VALUES(?,?)
        '''
        self.manager(sql, category_ru, category_en, commit=True)

    def delete_category_for_admin(self, category_id):
        sql = '''
        DELETE FROM categories
        WHERE category_id = ?
        '''
        self.manager(sql, category_id, commit=True)

    def add_new_product_for_admin(self, category_id, product_name_ru, author_ru, price, description_ru, image,
                                  product_name_en, author_en, description_en):
        sql = '''
        INSERT INTO products(category_id, product_name, author, price, description, image, 
        product_name_en, author_en, description_en) VALUES(?,?,?,?,?,?,?,?,?)
        '''
        self.manager(sql, category_id, product_name_ru, author_ru, price, description_ru, image,
                     product_name_en, author_en, description_en, commit=True)

    def delete_product_for_admin(self, product_id):
        sql = '''
        DELETE FROM products
        WHERE product_id = ?
        '''
        self.manager(sql, product_id, commit=True)

    def get_orders_summary_for_last_months(self, months=1):
        sql = '''
        SELECT COUNT(*) AS total_orders,
               SUM(total_price) AS total_sum
        FROM orders_total_price
        WHERE strftime('%d.%m.%Y', new_date) >= strftime('%d.%m.%Y', date('now', ? || ' months'))
        '''
        return self.manager(sql, f'-{months}', fetchone=True)
