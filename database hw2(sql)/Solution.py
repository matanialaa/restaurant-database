import decimal
from typing import List, Tuple
from psycopg2 import sql
from datetime import date, datetime
import Utility.DBConnector as Connector
from Utility.ReturnValue import ReturnValue
from Utility.Exceptions import DatabaseException
from Business.Customer import Customer, BadCustomer
from Business.Order import Order, BadOrder
from Business.Dish import Dish, BadDish
from Business.OrderDish import OrderDish


# ---------------------------------- CRUD API: ----------------------------------
# Basic database functions


def create_tables() -> None:
    conn = Connector.DBConnector()

    # CUSTOMERS TABLE:
    customers_query = """
    CREATE TABLE customers (
        customer_id INTEGER CHECK(customer_id >0) PRIMARY KEY,
        customer_name varchar(100) NOT NULL,
        customer_phone varchar(100) NOT NULL,
        customer_address varchar(100) NOT NULL
        );
        """
    try:
        conn.execute(customers_query)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # ORDER TABLE:
    orders_query = """
    CREATE TABLE orders (
        order_id INTEGER  CHECK(order_id>0) PRIMARY KEY,
        order_date TIMESTAMP  NOT NULL
        );
        """

    try:
        conn.execute(orders_query)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # DISHES TABLE:
    dish_query = """
    CREATE TABLE dishes(
       dish_id INTEGER NOT NULL CHECK(dish_id > 0) PRIMARY KEY,
       dish_name varchar(100) NOT NULL CHECK(CHAR_LENGTH(dish_name) >= 3),
       dish_price   DECIMAL CHECK(dish_price > 0) NOT NULL ,
       dish_is_active BOOLEAN NOT NULL
       );
       """

    try:
        conn.execute(dish_query)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # CUSTOMERS_ORDERS
    customer_order_query = """
    CREATE TABLE customers_orders_table(
      customer_id INTEGER ,
      order_id INTEGER NOT NULL PRIMARY KEY , 
      FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
      FOREIGN KEY (order_id) REFERENCES orders(order_id)  ON DELETE CASCADE
      );
       """

    try:
        conn.execute(customer_order_query)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # ORDER_DISH
    order_dish_query = """
    CREATE TABLE order_dish_table(
      dish_id INTEGER NOT NULL,
      order_id INTEGER NOT NULL, 
      amount INTEGER NOT NULL CHECK (amount > 0),
      price DECIMAL NOT NULL CHECK ( price > 0),
      PRIMARY KEY (dish_id,order_id),
      FOREIGN KEY (dish_id) REFERENCES dishes(dish_id)  ON DELETE CASCADE,
      FOREIGN KEY (order_id) REFERENCES orders(order_id)  ON DELETE CASCADE
      );
       """

    try:
        conn.execute(order_dish_query)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # CUSTOMER_DISHES
    customer_dish_query = """
    CREATE TABLE customer_dish_table(
      customer_id INTEGER NOT NULL,
      dish_id INTEGER NOT NULL,
      is_like BOOLEAN NOT NULL,
      PRIMARY KEY (customer_id, dish_id),
      FOREIGN KEY (customer_id) REFERENCES customers(customer_id)  ON DELETE CASCADE,
      FOREIGN KEY (dish_id) REFERENCES dishes(dish_id)  ON DELETE CASCADE
      );
      """

    try:
        conn.execute(customer_dish_query)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # Create the view for order total prices
    order_total_prices_view = """
    CREATE VIEW order_total_prices AS
    SELECT
        order_id,
        COALESCE(SUM(price*amount), 0) AS total_price
    FROM
        order_dish_table
    GROUP BY
        order_id;
    """
    try:
        conn.execute(order_total_prices_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # Create the view for most liked dished
    most_liked_dish_view = """
    CREATE VIEW most_liked_dish AS
    SELECT
        dish_id,
        SUM(CASE WHEN is_like THEN 1 ELSE 0 END ) AS total_likes
    FROM
        customer_dish_table
    WHERE is_like = TRUE 

    GROUP BY
        dish_id;


    """
    try:
        conn.execute(most_liked_dish_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # Create the view for most purchased dished
    most_purchased_dish_view = """
    CREATE VIEW most_purchased_dish AS
    SELECT
        dish_id,
        SUM(amount) AS total_purchase
    FROM
        order_dish_table
    GROUP BY
        dish_id;

    """
    try:
        conn.execute(most_purchased_dish_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # create the view for equal dish_id for most liked_mosr_purchased
    dish_comparison_view = """
    CREATE VIEW dish_comparison AS
    SELECT
         most_liked_dish.dish_id AS liked_dish_id,
        most_purchased_dish.dish_id AS purchased_dish_id
    FROM
        (SELECT dish_id
        FROM most_liked_dish
        ORDER BY total_likes DESC, dish_id ASC
        LIMIT 1) AS most_liked_dish
    JOIN
        (SELECT dish_id
        FROM most_purchased_dish
        ORDER BY total_purchase DESC , dish_id ASC
        LIMIT 1) AS most_purchased_dish
    ON most_liked_dish.dish_id = most_purchased_dish.dish_id;
    """
    try:
        conn.execute(dish_comparison_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # create a view for all the orders in the database
    total_orders_view = """
    CREATE VIEW total_orders AS
        SELECT 
            o.order_id,
            COALESCE(SUM(odt.price * odt.amount), 0) AS total_price, 
            co.customer_id
        FROM orders o
        LEFT JOIN customers_orders_table co ON o.order_id = co.order_id
        LEFT JOIN order_dish_table odt ON o.order_id = odt.order_id
        GROUP BY o.order_id, co.customer_id;
    """
    try:
        conn.execute(total_orders_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    anonymoes_view = """
    CREATE VIEW anonymoes AS
        SELECT 
            order_id,total_price
        FROM total_orders
        WHERE customer_id IS NULL

    """
    try:
        conn.execute(anonymoes_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # VIEWS FOR CUSTOMERS ORDERED TOP 5 DISHES
    most_liked_dish_1_view = """
    CREATE VIEW most_liked_dish_1 AS
    SELECT
        dishes.dish_id,
        SUM(CASE WHEN is_like THEN 1 ELSE 0 END ) AS total_likes
    FROM
        customer_dish_table
        RIGHT JOIN dishes ON customer_dish_table.dish_id = dishes.dish_id

    GROUP BY
         dishes.dish_id;


    """
    try:
        conn.execute(most_liked_dish_1_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    top_5_most_liked_dishes_view = """CREATE VIEW top_5_most_liked_dishes AS
        SELECT dish_id
        FROM most_liked_dish_1
        ORDER BY total_likes DESC, dish_id ASC
        LIMIT 5;"""
    try:
        conn.execute(top_5_most_liked_dishes_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    customers_ordered_top_5_dishes_view = """
        CREATE VIEW customers_ordered_top_5_dishes AS
        SELECT customer_id
        FROM (
            SELECT customer_id, dish_id
        FROM customers_orders_table co
        JOIN order_dish_table odt ON co.order_id = odt.order_id
        WHERE dish_id IN (SELECT dish_id FROM top_5_most_liked_dishes)
        GROUP BY customer_id, dish_id
        ) AS subquery
        GROUP BY customer_id
        HAVING COUNT(DISTINCT dish_id) = 5;"""

    try:
        conn.execute(customers_ordered_top_5_dishes_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # VIEWS_FOR_TOTAL_PROFIT_PER_MONTH
    order_monthly_profits_view = """ 
    CREATE VIEW order_monthly_profits AS
    SELECT
        EXTRACT(MONTH FROM order_date) AS month,
        EXTRACT(YEAR FROM order_date) AS year,
        SUM(price * amount) AS total_profit
    FROM
        orders o
    JOIN
        order_dish_table odt ON o.order_id = odt.order_id
    GROUP BY
        EXTRACT(YEAR FROM order_date), EXTRACT(MONTH FROM order_date);"""

    try:
        conn.execute(order_monthly_profits_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    months_view = """
    CREATE VIEW months AS
    SELECT generate_series(1, 12) AS month;"""

    try:
        conn.execute(months_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # create views for get_potential_dish_recommendations
    customer_liked_dishes_view = """
        CREATE VIEW customer_liked_dishes AS
    SELECT
    customer_id,
    dish_id
    FROM
    customer_dish_table
    WHERE
    is_like = TRUE;"""

    try:
        conn.execute(customer_liked_dishes_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    similar_customers_view = """
            CREATE VIEW similar_customers AS
    SELECT
    cld1.customer_id AS similar_customer_id,
    cld2.customer_id AS target_customer_id
    FROM
    customer_liked_dishes cld1
    JOIN
    customer_liked_dishes cld2 ON cld1.dish_id = cld2.dish_id
    WHERE
    cld1.customer_id != cld2.customer_id
    GROUP BY
    cld1.customer_id, cld2.customer_id
    HAVING
    COUNT(cld1.dish_id) >= 3;"""

    try:
        conn.execute(similar_customers_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    potential_recommendations_view = """
        CREATE VIEW potential_recommendations AS
        SELECT
        sc.target_customer_id,
        cld.dish_id
        FROM
        similar_customers sc
        JOIN
        customer_liked_dishes cld ON sc.similar_customer_id = cld.customer_id
        WHERE
        cld.dish_id NOT IN (
            SELECT
        dish_id
        FROM
        customer_liked_dishes
        WHERE
        customer_id = sc.target_customer_id
        )
        GROUP BY
        sc.target_customer_id, cld.dish_id;"""

    try:
        conn.execute(potential_recommendations_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    # VIEW FOR GET_NON_WORTH_PRICE_INCREASE

    active_dishes_view = """
    CREATE VIEW active_dishes AS
    SELECT dish_id, dish_price AS current_price
    FROM dishes
    WHERE dish_is_active = TRUE
    """

    try:
        conn.execute(active_dishes_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    order_dish_amounts_view = """
    CREATE VIEW order_dish_amounts AS
    SELECT dish_id, price, AVG(amount) AS avg_amount
    FROM order_dish_table
    GROUP BY dish_id, price"""

    try:
        conn.execute(order_dish_amounts_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    current_profits_view = """
    CREATE VIEW current_profits AS
    SELECT ad.dish_id, ad.current_price, oda.avg_amount * ad.current_price AS avg_profit
    FROM active_dishes ad
    JOIN order_dish_amounts oda ON ad.dish_id = oda.dish_id AND ad.current_price = oda.price
"""

    try:
        conn.execute(current_profits_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    previous_profits_view = """
    CREATE VIEW previous_profits AS
    SELECT ad.dish_id, oda.price AS previous_price, oda.avg_amount * oda.price AS avg_profit
    FROM active_dishes ad
    JOIN order_dish_amounts oda ON ad.dish_id = oda.dish_id AND ad.current_price > oda.price
"""

    try:
        conn.execute(previous_profits_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    comparison_view = """
    CREATE VIEW comparison AS
    SELECT cp.dish_id
    FROM current_profits cp
    JOIN previous_profits pp ON cp.dish_id = pp.dish_id
    WHERE cp.avg_profit < pp.avg_profit"""

    try:
        conn.execute(comparison_view)
    except Exception as e:
        print(f"An unexpected error occurred during createTables: {e}")

    conn.close()


def clear_tables() -> None:
    conn = Connector.DBConnector()
    query_customers = """DELETE FROM customers;"""
    query_orders = """DELETE FROM orders;"""
    query_dishes = """DELETE FROM dishes;"""
    query_customers_order = """DELETE FROM customers_orders_table;"""
    query_dish_order = """DELETE FROM order_dish_table;"""
    query = """DELETE FROM customer_dish_table;"""


    conn.execute(query_customers)
    conn.execute(query_orders)
    conn.execute(query_dishes)
    conn.execute(query_customers_order)
    conn.execute(query_dish_order)
    conn.execute(query)



    if conn is not None:
        conn.close()
    pass


def drop_tables() -> None:
    conn = Connector.DBConnector()

    drop_query = "DROP TABLE IF EXISTS customer_dish_table CASCADE;"
    drop_order_dish_query = "DROP TABLE IF EXISTS order_dish_table CASCADE;"
    drop_customers_orders_query = "DROP TABLE IF EXISTS customers_orders_table CASCADE;"
    drop_customers_query = "DROP TABLE IF EXISTS customers CASCADE;"
    drop_orders_query = "DROP TABLE IF EXISTS orders CASCADE;"
    drop_dishes_query = "DROP TABLE IF EXISTS dishes CASCADE;"

    drop_anonymous_query = "DROP VIEW IF EXISTS anonymous CASCADE;"
    drop_customer_ordered_top_5_dishes = "DROP VIEW IF EXISTS customers_ordered_top_5_dishes CASCADE;"
    drop_dish_comparison = "DROP VIEW IF EXISTS dish_comparison CASCADE;"
    drop_months = "DROP VIEW IF EXISTS months CASCADE;"
    drop_most_liked_dish = "DROP VIEW IF EXISTS most_liked_dish CASCADE;"
    drop_most_liked_dish_1 = "DROP VIEW IF EXISTS most_liked_dish_1 CASCADE;"
    drop_most_purchased_dish = "DROP VIEW IF EXISTS most_purchased_dish CASCADE;"
    drop_order_monthly_profit = "DROP VIEW IF EXISTS order_monthly_profit CASCADE;"
    drop_order_total_prices = "DROP VIEW IF EXISTS order_total_price CASCADE;"
    drop_5_most_liked_dishes = "DROP VIEW IF EXISTS top_5_most_liked_dishes CASCADE;"
    drop_total_orders = "DROP VIEW IF EXISTS total_orders CASCADE;"
    drop1 = "DROP VIEW IF EXISTS potential_recommendations CASCADE;"
    drop2 = "DROP VIEW IF EXISTS similar_customers CASCADE;"
    drop3 = "DROP VIEW IF EXISTS customer_liked_dishes CASCADE;"

    conn.execute(drop_customers_query)
    conn.execute(drop_orders_query)
    conn.execute(drop_dishes_query)
    conn.execute(drop_customers_orders_query)
    conn.execute(drop_order_dish_query)
    conn.execute(drop_query)

    conn.execute(drop_anonymous_query)
    conn.execute(drop_months)
    conn.execute(drop_most_liked_dish)
    conn.execute(drop_most_liked_dish_1)
    conn.execute(drop_most_purchased_dish)
    conn.execute(drop_5_most_liked_dishes)
    conn.execute(drop_total_orders)
    conn.execute(drop_customer_ordered_top_5_dishes)
    conn.execute(drop_dish_comparison)
    conn.execute(drop_order_monthly_profit)
    conn.execute(drop_order_total_prices)
    conn.execute(drop1)
    conn.execute(drop2)
    conn.execute(drop3)

    if conn is not None:
        conn.close()
        pass


# CRUD API
# "*******************************************CUSTOMERS*****************************************************************
def add_customer(customer: Customer) -> ReturnValue:
    conn = None
    # Extract values
    customer_id = customer.get_cust_id()
    customer_name = customer.get_full_name()
    customer_address = customer.get_address()
    customer_phone = customer.get_phone()

    if customer_id is None or customer_name is None or customer_address is None or customer_phone is None or len(
            customer_address) < 3 or customer_id <= 0:
        return ReturnValue.BAD_PARAMS

    # Add the customer to the database with ON CONFLICT clause
    add_query = f"""
        INSERT INTO customers (customer_id, customer_name, customer_phone, customer_address)
        VALUES ('{customer_id}', '{customer_name}','{customer_phone}','{customer_address}')
        ON CONFLICT (customer_id) DO NOTHING
    """
    try:
        conn = Connector.DBConnector()
        affected, result = conn.execute(add_query)
        if affected != 0:
            return ReturnValue.OK
        else:
            return ReturnValue.ALREADY_EXISTS
    except DatabaseException.database_ini_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.ConnectionInvalid:
        return ReturnValue.ERROR
    except DatabaseException.UNKNOWN_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.NOT_NULL_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.UNIQUE_VIOLATION:
        return ReturnValue.ALREADY_EXISTS

    finally:
        if conn is not None:
            conn.close()
    pass


def get_customer(customer_id: int) -> Customer:
    conn = None
    try:
        conn = Connector.DBConnector()
        query = f"""SELECT * FROM customers WHERE customer_id = '{customer_id}'"""
        affected_rows, result = conn.execute(query)
        if result and result.size() > 0:
            customer_object = Customer(result[0]['customer_id'], result[0]['customer_name'],
                                       result[0]['customer_phone'], result[0]['customer_address'])
            return customer_object
        else:
            # Owner not found
            return BadCustomer()

    except DatabaseException as e:
        # Handle any exceptions that might occur during the query
        print(f"Error getting owner: {e}")
        return BadCustomer()

    finally:
        if conn is not None:
            conn.close()
    pass


def delete_customer(customer_id: int) -> ReturnValue:
    conn = None
    if customer_id <= 0:
        return ReturnValue.NOT_EXISTS

    try:
        conn = Connector.DBConnector()
        delete_query = f"""
            DELETE FROM customers
            WHERE customer_id = {customer_id}
            RETURNING CASE WHEN EXISTS (SELECT 1 FROM customers WHERE customer_id = {customer_id})
                           THEN {customer_id}
                           ELSE NULL
                      END AS customer_id"""
        _, result = conn.execute(delete_query)
        if result and result.size() > 0:
            # Deletion successful
            return ReturnValue.OK
        else:
            # Customer does not exist
            return ReturnValue.NOT_EXISTS

    except DatabaseException as e:
        # Handle any exceptions that might occur during the query
        print(f"Error deleting customer: {e}")
        return ReturnValue.ERROR

    finally:
        if conn is not None:
            conn.close()
    pass


def add_order(order: Order) -> ReturnValue:
    conn = None
    if order is None or order.get_order_id() is None or order.get_datetime() is None or order.get_order_id() <= 0:
        return ReturnValue.BAD_PARAMS
    # Extract values
    order_id = order.get_order_id()

    if order.get_datetime().microsecond == 0:
        order_timespam = order.get_datetime()
    else:
        order_timespam = order.get_datetime().replace(microsecond=0)

    # Add the order to the database with ON CONFLICT clause
    add_query = f"""
        INSERT INTO orders (order_id, order_date)
        VALUES ('{order_id}', '{order_timespam}')
        ON CONFLICT (order_id) DO NOTHING
    """
    try:
        conn = Connector.DBConnector()
        affected, result = conn.execute(add_query)
        if affected != 0:
            return ReturnValue.OK
        else:
            return ReturnValue.ALREADY_EXISTS
    except DatabaseException.database_ini_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.ConnectionInvalid:
        return ReturnValue.ERROR
    except DatabaseException.UNKNOWN_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.NOT_NULL_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION:
        return ReturnValue.BAD_PARAMS

    finally:
        if conn is not None:
            conn.close()
    pass


# "*********************************************ORDERS*****************************************************************


def get_order(order_id: int) -> Order:
    conn = None
    try:
        # Assuming 'conn' is your database connection object
        conn = Connector.DBConnector()
        query = f"""SELECT * FROM orders WHERE order_id = '{order_id}'"""
        affected_rows, result = conn.execute(query)
        if result and result.size() > 0:
            order_object = Order(result[0]['order_id'], result[0]['order_date'])
            return order_object
        else:
            # Owner not found
            return BadOrder()

    except DatabaseException as e:
        # Handle any exceptions that might occur during the query
        print(f"Error getting owner: {e}")
        return BadOrder()

    finally:
        if conn is not None:
            conn.close()
    pass


def delete_order(order_id: int) -> ReturnValue:
    conn = None
    if order_id <= 0:
        return ReturnValue.NOT_EXISTS

    try:
        conn = Connector.DBConnector()
        delete_query = f"""
            DELETE FROM orders
            WHERE order_id = {order_id}
            RETURNING CASE WHEN EXISTS (SELECT 1 FROM orders WHERE order_id = {order_id})
                           THEN {order_id}
                           ELSE NULL
                      END AS customer_id"""
        _, result = conn.execute(delete_query)
        if result and result.size() > 0:
            # Deletion successful
            return ReturnValue.OK
        else:
            # Customer does not exist
            return ReturnValue.NOT_EXISTS

    except DatabaseException as e:
        # Handle any exceptions that might occur during the query
        print(f"Error deleting customer: {e}")
        return ReturnValue.ERROR

    finally:
        if conn is not None:
            conn.close()
    pass

    pass


# "***********************************************DISHES*****************************************************************

def add_dish(dish: Dish) -> ReturnValue:
    conn = None

    # Extract values
    dish_id = dish.get_dish_id()
    dish_name = dish.get_name()
    dish_price = dish.get_price()
    dish_is_active = dish.get_is_active()

    if dish_id is None or dish_name is None or dish_price is None or dish_is_active is None or dish_id <= 0 or len(
            dish_name) < 3:
        return ReturnValue.BAD_PARAMS

    # Add the order to the database with ON CONFLICT clause
    add_query = f"""
        INSERT INTO dishes (dish_id, dish_name, dish_price,dish_is_active)
        VALUES ('{dish_id}', '{dish_name}', '{dish_price}', '{dish_is_active}')
        ON CONFLICT (dish_id) DO NOTHING
    """
    try:
        conn = Connector.DBConnector()
        affected, result = conn.execute(add_query)
        if affected != 0:
            return ReturnValue.OK
        else:
            return ReturnValue.ALREADY_EXISTS
    except DatabaseException.database_ini_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.ConnectionInvalid:
        return ReturnValue.ERROR
    except DatabaseException.UNKNOWN_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.NOT_NULL_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION:
        return ReturnValue.BAD_PARAMS

    finally:
        if conn is not None:
            conn.close()
    pass


def get_dish(dish_id: int) -> Dish:
    conn = None
    try:
        # Assuming 'conn' is your database connection object
        conn = Connector.DBConnector()
        query = f"""SELECT * FROM dishes WHERE dish_id = '{dish_id}'"""
        affected_rows, result = conn.execute(query)
        if result and result.size() > 0:
            dish_object = Dish(result[0]['dish_id'], result[0]['dish_name'], result[0]['dish_price'],
                               result[0]['dish_is_active'])
            return dish_object
        else:
            # Owner not found
            return BadDish()

    except DatabaseException as e:
        # Handle any exceptions that might occur during the query
        print(f"Error getting owner: {e}")
        return BadDish()

    finally:
        if conn is not None:
            conn.close()
    pass


def update_dish_price(dish_id: int, price: float) -> ReturnValue:
    conn = None
    if price <= 0 or price is None:
        return ReturnValue.BAD_PARAMS

    try:
        conn = Connector.DBConnector()
        dish = get_dish(dish_id)
        if dish == BadDish() or dish_id <= 0 or dish_id is None or dish.get_is_active() == False:
            return ReturnValue.NOT_EXISTS

        update_query = f"""UPDATE dishes SET dish_price = '{price}' WHERE dish_id = '{dish_id}'"""
        affected, _ = conn.execute(update_query)

        if affected > 0:
            return ReturnValue.OK
    except (DatabaseException.database_ini_ERROR,
            DatabaseException.ConnectionInvalid,
            DatabaseException.UNKNOWN_ERROR):
        return ReturnValue.ERROR
    finally:
        if conn is not None:
            conn.close()


def update_dish_active_status(dish_id: int, is_active: bool) -> ReturnValue:
    conn = None
    try:
        conn = Connector.DBConnector()
        dish = get_dish(dish_id)
        if dish.get_dish_id() == -1 or dish_id <= 0 or dish_id is None:
            return ReturnValue.NOT_EXISTS

        update_query = f"""UPDATE dishes SET dish_is_active = '{is_active}' WHERE dish_id = '{dish_id}'"""
        affected, _ = conn.execute(update_query)

        if affected > 0:
            return ReturnValue.OK

    except (DatabaseException.database_ini_ERROR,
            DatabaseException.ConnectionInvalid,
            DatabaseException.UNKNOWN_ERROR):
        return ReturnValue.ERROR
    finally:
        if conn is not None:
            conn.close()


# *********************************************** customer - orders - relation *********************************************
def customer_placed_order(customer_id: int, order_id: int) -> ReturnValue:
    conn = None
    try:
        conn = Connector.DBConnector()

        # Validate parameters
        if (
                customer_id is None
                or order_id is None
                or customer_id <= 0
                or order_id <= 0
        ):
            return ReturnValue.NOT_EXISTS

        customer = get_customer(customer_id)
        if customer.get_cust_id() == -1:
            return ReturnValue.NOT_EXISTS

        order = get_order(order_id)
        if order.get_order_id() == -1:
            return ReturnValue.NOT_EXISTS

        # Check if the order is available
        customer_placed_order_add = f"""
            INSERT INTO customers_orders_table (customer_id, order_id)
            SELECT 
                {customer_id}, 
                {order_id}
            WHERE NOT EXISTS (
                SELECT 1
                FROM customers_orders_table
                WHERE order_id = {order_id}
            )
        """

        affected, _ = conn.execute(customer_placed_order_add)

        if affected > 0:
            return ReturnValue.OK
        else:
            return ReturnValue.ALREADY_EXISTS
    except DatabaseException.UNIQUE_VIOLATION:
        return ReturnValue.ERROR
    except (DatabaseException.database_ini_ERROR,
            DatabaseException.ConnectionInvalid,
            DatabaseException.UNKNOWN_ERROR):
        return ReturnValue.ERROR
    finally:
        if conn is not None:
            conn.close()

    pass


def get_customer_that_placed_order(order_id: int) -> Customer:
    conn = None
    try:
        if order_id is None or order_id <= 0:
            return BadCustomer()

        conn = Connector.DBConnector()

        # Query to get the customer_id associated with the given order_id
        query = f"""
            SELECT customer_id
            FROM customers_orders_table
            WHERE order_id = {order_id}
        """

        _, result = conn.execute(query)

        if result == None or result.size() == 0:
            return BadCustomer()

        customer_id = result[0]['customer_id']
        customer = get_customer(customer_id)

        if customer is None:
            return BadCustomer()

        return customer

    except (DatabaseException.database_ini_ERROR,
            DatabaseException.ConnectionInvalid,
            DatabaseException.UNKNOWN_ERROR) as e:
        print(f"An unexpected error occurred: {e}")
        return BadCustomer()
    finally:
        if conn is not None:
            conn.close()


def order_contains_dish(order_id: int, dish_id: int, amount: int) -> ReturnValue:
    conn = None
    try:
        conn = Connector.DBConnector()

        if amount < 0:
            return ReturnValue.BAD_PARAMS
        if dish_id <= 0 or order_id <= 0 or dish_id is None or order_id is None:
            return ReturnValue.NOT_EXISTS

        order = get_order(order_id)
        dish = get_dish(dish_id)
        if order.get_order_id() == -1 or dish.get_dish_id() == -1 or dish.get_is_active() == False:
            return ReturnValue.NOT_EXISTS

        price = dish.get_price()

        add_query = f"""
            INSERT INTO order_dish_table (dish_id, order_id,amount,price)
            SELECT 
                {dish_id}, 
                {order_id},
                {amount},
                {price}
            WHERE NOT EXISTS (
                SELECT 1
                FROM order_dish_table
                WHERE dish_id = {dish_id} AND order_id = {order_id}
            )
        """

        affected, result = conn.execute(add_query)
        if affected != 0:
            return ReturnValue.OK
        else:
            return ReturnValue.ALREADY_EXISTS
    except DatabaseException.database_ini_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.ConnectionInvalid:
        return ReturnValue.ERROR
    except DatabaseException.UNKNOWN_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.NOT_NULL_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.UNIQUE_VIOLATION:
        return ReturnValue.ALREADY_EXISTS


    finally:
        if conn is not None:
            conn.close()


def order_does_not_contain_dish(order_id: int, dish_id: int) -> ReturnValue:
    conn = None
    if order_id <= 0 or dish_id <= 0:
        return ReturnValue.NOT_EXISTS

    try:
        conn = Connector.DBConnector()
        delete_query = f"""
            DELETE FROM order_dish_table
            WHERE order_id = {order_id} AND dish_id = {dish_id}
        """
        affected, result = conn.execute(delete_query)

        if affected != 0:
            # If rows are affected, the dish was removed
            return ReturnValue.OK
        else:
            return ReturnValue.NOT_EXISTS

    except DatabaseException as e:
        print(f"Error processing request: {e}")
        return ReturnValue.ERROR

    finally:
        if conn is not None:
            conn.close()


def get_all_order_items(order_id: int) -> List[OrderDish]:
    conn = None
    if order_id <= 0:
        return []

    try:
        conn = Connector.DBConnector()
        # Query to get all dishes for the given order_id
        query = f"""
            SELECT order_dish_table.dish_id, order_dish_table.amount,order_dish_table.price
            FROM order_dish_table
            JOIN dishes ON order_dish_table.dish_id = dishes.dish_id
            WHERE order_dish_table.order_id = {order_id}
            ORDER BY order_dish_table.dish_id ASC
        """
        _, result = conn.execute(query)

        # Check if result is not empty
        order_dishes = []
        for row in result:
            # Extract apartment information and create Apartment objects
            dish_id = row['dish_id']
            amount = row['amount']
            price = row['price']

            order_dishes.append(OrderDish(dish_id, amount, price))

        return order_dishes


    except DatabaseException as e:
        print(f"Error processing request: {e}")
        return []

    finally:
        if conn is not None:
            conn.close()


def customer_likes_dish(cust_id: int, dish_id: int) -> ReturnValue:
    conn = None

    if cust_id <= 0 or dish_id <= 0 or get_dish(dish_id).get_dish_id() == -1 or get_customer(
            cust_id).get_cust_id() == -1:
        return ReturnValue.NOT_EXISTS
    try:
        conn = Connector.DBConnector()

        is_like = 1

        add_query = f"""
            INSERT INTO customer_dish_table (customer_id, dish_id, is_like)
            VALUES ('{cust_id}', '{dish_id}','{is_like}')
        """
        affected, result = conn.execute(add_query)

        if affected != 0:
            return ReturnValue.OK
        else:
            return ReturnValue.ALREADY_EXISTS

    except DatabaseException.database_ini_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.ConnectionInvalid:
        return ReturnValue.ERROR
    except DatabaseException.UNKNOWN_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.UNIQUE_VIOLATION:
        return ReturnValue.ALREADY_EXISTS
    finally:
        if conn is not None:
            conn.close()


def customer_dislike_dish(cust_id: int, dish_id: int) -> ReturnValue:
    conn = None

    if cust_id <= 0 or dish_id <= 0 or get_dish(dish_id) == -1 or get_customer(cust_id) == -1:
        return ReturnValue.NOT_EXISTS

    try:
        conn = Connector.DBConnector()
        is_like = 0
        like = 1
        update_query = f"""UPDATE customer_dish_Table SET is_like = '{is_like}' WHERE customer_dish_table.dish_id = '{dish_id}' AND customer_dish_table.customer_id = '{cust_id}' """

        affected, _ = conn.execute(update_query)

        if affected != 0:
            return ReturnValue.OK
        else:
            return ReturnValue.NOT_EXISTS

    except DatabaseException.database_ini_ERROR:
        return ReturnValue.ERROR
    except DatabaseException.ConnectionInvalid:
        return ReturnValue.ERROR
    except DatabaseException.UNKNOWN_ERROR:
        return ReturnValue.ERROR
    finally:
        if conn is not None:
            conn.close()


def get_all_customer_likes(cust_id: int) -> List[Dish]:
    conn = None
    if cust_id <= 0 or get_customer(cust_id) == -1:
        return []

    try:
        conn = Connector.DBConnector()

        query = f"""
            SELECT dishes.dish_id, dishes.dish_name, dishes.dish_price, dishes.dish_is_active
            FROM dishes
            JOIN customer_dish_table ON customer_dish_table.dish_id = dishes.dish_id
            WHERE customer_dish_table.customer_id = '{cust_id}' AND customer_dish_table.is_like = TRUE
            ORDER BY customer_dish_table.dish_id ASC
        """

        # Execute the query with parameterized input
        rows, result = conn.execute(query)

        dishes = []
        for row in result:
            # Extract apartment information and create Apartment objects
            dish_id = row['dish_id']
            dish_name = row['dish_name']
            dish_price = row['dish_price']
            dish_is_active = row['dish_is_active']

            dishes.append(Dish(dish_id, dish_name, dish_price, dish_is_active))

        return dishes




    except DatabaseException.database_ini_ERROR:
        return []
    except DatabaseException.ConnectionInvalid:
        return []
    except DatabaseException.UNKNOWN_ERROR:
        return []
    finally:
        if conn is not None:
            conn.close()


# ---------------------------------- BASIC API: ----------------------------------

# Basic API


def get_order_total_price(order_id: int) -> float:
    conn = None
    try:
        conn = Connector.DBConnector()
        query = f"""SELECT total_price FROM order_total_prices WHERE order_id = '{order_id}'"""

        rows, result = conn.execute(query)

        if rows == 0:
            return 0.0

        total_price = result[0]['total_price']
        return float(total_price)

    except (
            DatabaseException.ConnectionInvalid, DatabaseException.CHECK_VIOLATION,
            DatabaseException.NOT_NULL_VIOLATION,
            DatabaseException.UNKNOWN_ERROR):
        return 0.0

    finally:
        if conn is not None:
            conn.close()


def get_max_amount_of_money_cust_spent(cust_id: int) -> float:
    conn = None
    try:
        conn = Connector.DBConnector()

        max_amount_query = f"""
            SELECT COALESCE(MAX(otp.total_price), 0) AS max_spent
            FROM customers_orders_table cot
            JOIN order_total_prices otp ON cot.order_id = otp.order_id
            WHERE cot.customer_id = {cust_id};
        """

        _, result = conn.execute(max_amount_query)
        if result.size() <= 0:
            return 0.0

        max_spent = result[0]['max_spent']
        return float(max_spent)

    except DatabaseException.database_ini_ERROR:
        return 0.0
    except DatabaseException.ConnectionInvalid:
        return 0.0
    except DatabaseException.UNKNOWN_ERROR:
        return 0.0
    finally:
        if conn is not None:
            conn.close()


def get_most_expensive_anonymous_order() -> Order:
    conn = None
    try:
        is_null = None
        conn = Connector.DBConnector()
        max_amount_query = f"""
            SELECT anonymoes.order_id 
            FROM anonymoes 
            ORDER BY anonymoes.total_price DESC, anonymoes.order_id ASC
            LIMIT 1;          
          """

        row, result = conn.execute(max_amount_query)
        if row == 0:
            return None
        order_id = result[0]['order_id']
        return get_order(order_id)

    except DatabaseException.database_ini_ERROR:
        return 0.0
    except DatabaseException.ConnectionInvalid:
        return 0.0
    except DatabaseException.UNKNOWN_ERROR:
        return 0.0

    finally:
        conn.close()


def is_most_liked_dish_equal_to_most_purchased() -> bool:
    conn = None

    try:
        conn = Connector.DBConnector()
        query = f"""
        SELECT
            COUNT(*) > 0 AS are_equal
        FROM
            dish_comparison;
            """

        row, result = conn.execute(query)
        if row == 0:
            return None
        return result[0]['are_equal']

    except DatabaseException.database_ini_ERROR:
        return 0.0
    except DatabaseException.ConnectionInvalid:
        return 0.0
    except DatabaseException.UNKNOWN_ERROR:
        return 0.0

    finally:
        conn.close()


# ---------------------------------- ADVANCED API: ----------------------------------

# Advanced API


def get_customers_ordered_top_5_dishes() -> List[int]:
    conn = Connector.DBConnector()
    query = f"""
    SELECT customer_id
    FROM customers_ordered_top_5_dishes
    ORDER BY customer_id ASC;
    """
    try:

        rows, result = conn.execute(query)
        cust_i1d = []
        for row in result:
            cust_id = row['customer_id']
            cust_i1d.append(cust_id)

        return cust_i1d

    except Exception as e:
        return []
    finally:
        conn.close()


def get_non_worth_price_increase() -> List[int]:
    conn = Connector.DBConnector()
    query = f"""
    SELECT DISTINCT dish_id
    FROM comparison
    ORDER BY dish_id;
    """
    try:

        rows, result = conn.execute(query)
        dish_i1d = []
        for row in result:
            dish_id = row['dish_id']
            dish_i1d.append(dish_id)

        return dish_i1d

    except Exception as e:
        return []
    finally:
        conn.close()


def get_total_profit_per_month(year: int) -> List[Tuple[int, float]]:
    conn = Connector.DBConnector()
    query = f"""
    SELECT 
        m.month, 
        COALESCE(omp.total_profit, 0) AS total_profit
    FROM
        months m
    LEFT JOIN 
        order_monthly_profits omp
    ON 
        m.month = omp.month AND omp.year = {year}
    ORDER BY
        m.month DESC;
    """

    try:

        rows, result = conn.execute(query)

        month_profit = []

        # Update the list with the actual profit values from the result
        for row in result:
            month = row['month']
            profit = row['total_profit']
            month_profit.append((month, float(profit)))

        return month_profit

    except Exception as e:
        return []
    finally:
        conn.close()


def get_potential_dish_recommendations(cust_id: int) -> List[int]:
    conn = Connector.DBConnector()

    query = f"""
        SELECT 
            pr.dish_id
        FROM
            potential_recommendations pr
        WHERE
            pr.target_customer_id = {cust_id}
        ORDER BY
            pr.dish_id ASC;
        """

    try:
        rows, result = conn.execute(query)
        dishes_ids = []

        for row in result:
            dish_id = row['dish_id']
            dishes_ids.append(dish_id)

        return dishes_ids

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []


class Solution:
    pass