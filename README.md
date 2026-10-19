[README.md](https://github.com/user-attachments/files/33675541/README.md)
# Restaurant Delivery Database & Analytics

**The database design and Python data access layer for "Yummy," a restaurant delivery app, built on PostgreSQL.**

Customers can place orders and save favorite dishes, and managers can update the menu, change prices, and track profits. All filtering, aggregation, and calculation happens inside the database: every API function runs a single SQL query, with views doing the heavy lifting.

## Highlights

- **6-table relational schema** with primary keys, foreign keys, check constraints, and cascading delete rules
- **26 API functions** for customers, orders, dishes, likes, and analytics
- **Analytics views** for monthly profit, order totals, and top spenders
- **Price-change analysis** that flags dishes whose price increase lowered average profit
- **Dish recommendations** based on customers with similar tastes

## Tech Stack

PostgreSQL · SQL · Python · psycopg2

## Database Schema

| Table | Purpose | Key Constraints |
|---|---|---|
| `customers` | Customer details | `customer_id` > 0, name, phone, and address required |
| `orders` | Orders and timestamps | `order_id` > 0 |
| `dishes` | Menu items | Name at least 3 characters, price > 0, active flag |
| `customers_orders` | Which customer placed each order | One customer per order; set to NULL if the customer is deleted |
| `order_dish` | Dishes in each order, with amount and price at order time | Primary key (`dish_id`, `order_id`); cascades on delete |
| `customer_dish` | Dishes each customer likes | Primary key (`customer_id`, `dish_id`); cascades on delete |

Storing the **price at order time** keeps past order totals correct even after a dish's price changes. Setting `customer_id` to NULL when a customer is deleted keeps their orders in the profit reports as anonymous orders.

## API Overview

**CRUD:** add, get, and delete customers, orders, and dishes; update dish price and active status; link orders to customers; add and remove dishes from orders; like and unlike dishes.

**Basic analytics**
- `get_order_total_price` – total cost of an order
- `get_max_amount_of_money_cust_spent` – a customer's most expensive order
- `get_most_expensive_anonymous_order` – top order from deleted customers
- `is_most_liked_dish_equal_to_most_purchased`

**Advanced analytics**
- `get_customers_ordered_top_5_dishes` – customers who ordered all five most-liked dishes
- `get_non_worth_price_increase` – dishes where raising the price reduced average profit
- `get_total_profit_per_month` – profit for each month of a year, including months with no sales
- `get_potential_dish_recommendations` – dishes liked by customers who share at least 3 liked dishes with you

## Example: Recommendations

The recommendation feature is built from three views:

1. `customer_liked_dishes` – every dish each customer likes
2. `similar_customers` – pairs of different customers who share at least 3 liked dishes
3. `potential_recommendations` – dishes that similar customers like and the target customer hasn't liked yet

## Running Locally

1. Install PostgreSQL and create a database.
2. Install the Python driver:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your database connection details in the connector configuration.
4. Call `create_tables()` to build the schema, then use the API functions.

## About

A course project for Database Systems (236363) at the Technion, built with a partner. The `Utility` connector package and business object classes were provided by the course staff.

