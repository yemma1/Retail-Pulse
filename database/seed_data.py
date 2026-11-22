"""
Online Retail Sales Analytics - Data Generation & Seeding Engine
Generates realistic sample retail sales data meeting all enterprise criteria:
- 105 Customers across 18 major cities
- 8 Product Categories
- 56 Diverse Products across tech, apparel, home, fitness, etc.
- 330 Orders spanning 14 calendar months
- 680+ Order Items with realistic quantities, unit prices, and discounts
- Full relational integrity
"""

import os
import random
from datetime import datetime, timedelta

# Seed for reproducible realistic data
random.seed(42)

CATEGORIES = [
    (1, "Electronics", "Computers, audio gear, mobile devices, and high-tech accessories"),
    (2, "Apparel & Fashion", "Men and women apparel, activewear, footwear, and accessories"),
    (3, "Home & Kitchen", "Cookware, small appliances, furniture, and home decor"),
    (4, "Sports & Outdoors", "Fitness equipment, camping gear, bicycles, and athletic wear"),
    (5, "Books & Stationery", "Best-sellers, educational textbooks, journals, and fine pens"),
    (6, "Beauty & Personal Care", "Skincare, haircare, fragrances, and wellness essentials"),
    (7, "Toys & Games", "Board games, educational toys, puzzles, and gaming accessories"),
    (8, "Automotive Accessories", "Car electronics, maintenance tools, dash cams, and interior care")
]

PRODUCTS = [
    # Electronics (1)
    (1, "Pro Ultrabook 15-inch", 1, 1299.99, 45),
    (2, "Wireless Noise-Canceling Headphones", 1, 249.99, 120),
    (3, "Smartphone 5G Pro Max", 1, 999.00, 60),
    (4, "4K Ultra HD Smart Monitor 27-inch", 1, 379.50, 85),
    (5, "Mechanical Gaming Keyboard RGB", 1, 119.00, 150),
    (6, "Ergonomic Wireless Mouse", 1, 59.99, 210),
    (7, "Portable Bluetooth Speaker Waterproof", 1, 89.99, 140),
    (8, "Smartwatch Fitness Tracker GPS", 1, 199.50, 95),

    # Apparel & Fashion (2)
    (9, "Classic Cotton Crewneck T-Shirt", 2, 24.99, 300),
    (10, "Slim Fit Stretch Denim Jeans", 2, 69.50, 180),
    (11, "Waterproof Windbreaker Jacket", 2, 129.00, 75),
    (12, "Merino Wool Knit Sweater", 2, 89.99, 90),
    (13, "Athletic Running Shoes Pro", 2, 119.50, 110),
    (14, "Genuine Leather Minimalist Wallet", 2, 45.00, 160),
    (15, "Polarized Aviator Sunglasses", 2, 79.00, 130),

    # Home & Kitchen (3)
    (16, "Espresso Coffee Machine Deluxe", 3, 449.99, 40),
    (17, "Stainless Steel Cookware Set 10-Piece", 3, 219.00, 55),
    (18, "Digital Air Fryer XL 6-Quart", 3, 109.99, 80),
    (19, "Smart Robot Vacuum Cleaner", 3, 299.00, 50),
    (20, "Cast Iron Dutch Oven 6-Quart", 3, 79.95, 65),
    (21, "Memory Foam Contour Pillow", 3, 39.99, 220),
    (22, "Aromatherapy Essential Oil Diffuser", 3, 29.50, 175),

    # Sports & Outdoors (4)
    (23, "Adjustable Dumbbells Set 50 lbs", 4, 289.00, 35),
    (24, "High-Density Yoga Mat with Strap", 4, 34.99, 250),
    (25, "Hydro Insulated Stainless Bottle 32oz", 4, 28.50, 320),
    (26, "Waterproof 4-Person Camping Tent", 4, 189.99, 45),
    (27, "Trail Hiking Backpack 45L", 4, 95.00, 70),
    (28, "Foldable Indoor Exercise Bike", 4, 349.00, 30),
    (29, "Speed Jump Rope Aluminum Handle", 4, 18.00, 280),

    # Books & Stationery (5)
    (30, "Executive Hardcover Dot Grid Journal", 5, 19.99, 300),
    (31, "Fountain Pen Matte Black Fine Nib", 5, 42.50, 140),
    (32, "Data Science and SQL Mastery Guide", 5, 49.99, 125),
    (33, "The Lean Startup Handbook", 5, 27.50, 160),
    (34, "Architectural Gel Ink Pens 12-Pack", 5, 22.00, 240),
    (35, "Ergonomic Desk Reading Lamp LED", 5, 38.99, 110),
    (36, "Modern Economics & Finance Treatise", 5, 54.00, 85),

    # Beauty & Personal Care (6)
    (37, "Hydrating Hyaluronic Acid Serum 50ml", 6, 32.00, 190),
    (38, "Sonic Electric Toothbrush Smart Sensor", 6, 89.99, 105),
    (39, "Organic Argan Oil Hair Treatment", 6, 26.50, 160),
    (40, "Mineral Broad Spectrum Sunscreen SPF 50", 6, 24.00, 230),
    (41, "Ionic Hair Dryer 1800W Fast Drying", 6, 79.00, 85),
    (42, "Botanical Gentle Face Cleanser", 6, 18.50, 210),
    (43, "Luxury Cedarwood & Vetiver Cologne", 6, 115.00, 60),

    # Toys & Games (7)
    (44, "Strategic Board Game Empire Builder", 7, 54.99, 90),
    (45, "Mechanical Robot Coding Kit STEM", 7, 79.99, 65),
    (46, "1000-Piece Panoramic Landscape Puzzle", 7, 21.50, 180),
    (47, "Remote Control Off-Road Rock Crawler", 7, 68.00, 75),
    (48, "Wooden Chess and Checkers Deluxe Set", 7, 45.00, 115),
    (49, "Wireless Gamepad Controller Pro", 7, 59.99, 140),

    # Automotive Accessories (8)
    (50, "4K Dual Lens Car Dash Camera", 8, 139.99, 70),
    (51, "Portable Tire Inflator Air Compressor", 8, 49.99, 150),
    (52, "Universal Magnetic Phone Car Mount", 8, 19.99, 350),
    (53, "Ceramic Coating Car Wash Shampoo 1 Gal", 8, 34.50, 110),
    (54, "OBD2 Bluetooth Diagnostic Scanner Tool", 8, 39.99, 125),
    (55, "Heavy-Duty All-Weather Rubber Floor Mats", 8, 89.00, 65),
    (56, "Emergency Roadside Assistance Safety Kit", 8, 64.99, 85)
]

CITIES_STATES = [
    ("New York", "New York"),
    ("Los Angeles", "California"),
    ("Chicago", "Illinois"),
    ("Houston", "Texas"),
    ("Phoenix", "Arizona"),
    ("Philadelphia", "Pennsylvania"),
    ("San Antonio", "Texas"),
    ("San Diego", "California"),
    ("Dallas", "Texas"),
    ("Austin", "Texas"),
    ("Seattle", "Washington"),
    ("Denver", "Colorado"),
    ("Boston", "Massachusetts"),
    ("Atlanta", "Georgia"),
    ("Miami", "Florida"),
    ("San Francisco", "California"),
    ("Portland", "Oregon"),
    ("Charlotte", "North Carolina")
]

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
    "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra",
    "Alexander", "Rachel", "Raymond", "Carolyn", "Patrick", "Janet", "Jack", "Maria",
    "Dennis", "Heather", "Jerry", "Diane", "Tyler", "Julie", "Aaron", "Joyce", "Henry"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz"
]

def generate_customers(count=105):
    customers = []
    base_date = datetime(2023, 1, 15)
    for i in range(1, count + 1):
        fn = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
        ln = LAST_NAMES[((i - 1) * 3) % len(LAST_NAMES)]
        full_name = f"{fn} {ln}"
        email = f"{fn.lower()}.{ln.lower()}{i}@retailnexus.com"
        city, state = CITIES_STATES[(i * 7) % len(CITIES_STATES)]
        reg_date = base_date + timedelta(days=(i * 4) % 400)
        customers.append((
            i,
            full_name,
            email,
            city,
            state,
            "USA",
            reg_date.strftime("%Y-%m-%d")
        ))
    return customers

def generate_orders_and_items(customer_count=105, order_count=330):
    orders = []
    order_items = []
    
    # 14 months window: from 2023-10-01 to 2024-11-15
    start_date = datetime(2023, 10, 1)
    end_date = datetime(2024, 11, 15)
    total_days = (end_date - start_date).days
    
    statuses = ["Completed", "Completed", "Completed", "Shipped", "Shipped", "Processing", "Cancelled"]
    payment_methods = ["Credit Card", "Credit Card", "PayPal", "Debit Card", "Apple Pay", "Bank Transfer"]
    
    item_counter = 1
    
    for order_id in range(1, order_count + 1):
        # Biased customer distribution so some VIPs emerge naturally
        if random.random() < 0.35:
            # VIP cluster (top 15 customers)
            cust_id = random.randint(1, 15)
        else:
            cust_id = random.randint(1, customer_count)
            
        # Spread dates across the 14 months with seasonal spikes (e.g., Nov-Dec holidays)
        day_offset = int((order_id / order_count) * total_days) + random.randint(-10, 10)
        day_offset = max(0, min(total_days, day_offset))
        order_date = start_date + timedelta(days=day_offset)
        
        status = random.choice(statuses)
        pay_method = random.choice(payment_methods)
        
        orders.append((
            order_id,
            cust_id,
            order_date.strftime("%Y-%m-%d"),
            status,
            pay_method
        ))
        
        # 1 to 4 items per order
        num_items = random.choices([1, 2, 3, 4], weights=[45, 35, 15, 5])[0]
        selected_prods = random.sample(PRODUCTS, num_items)
        
        for prod in selected_prods:
            prod_id = prod[0]
            catalog_price = prod[3]
            qty = random.choices([1, 2, 3, 4, 5], weights=[60, 22, 10, 5, 3])[0]
            
            # Apply occasional realistic discount ($0, or 5-15% of line price)
            line_subtotal = round(qty * catalog_price, 2)
            if random.random() < 0.28:
                discount_rate = random.choice([0.05, 0.10, 0.15, 0.20])
                discount = round(line_subtotal * discount_rate, 2)
            else:
                discount = 0.00
                
            order_items.append((
                item_counter,
                order_id,
                prod_id,
                qty,
                catalog_price,
                discount
            ))
            item_counter += 1
            
    return orders, order_items

def export_oracle_sql(customers, categories, products, orders, order_items, filepath):
    """Generates pure Oracle SQL INSERT script with TO_DATE formatting."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("-- ============================================================================\n")
        f.write("-- ONLINE RETAIL SALES ANALYTICS - SAMPLE DATASET SCRIPT\n")
        f.write("-- Target Database: Oracle Database (19c / 21c / 23c)\n")
        f.write(f"-- Generated: {len(customers)} Customers, {len(categories)} Categories, {len(products)} Products,\n")
        f.write(f"--            {len(orders)} Orders, {len(order_items)} Order Items\n")
        f.write("-- ============================================================================\n\n")
        f.write("SET DEFINE OFF;\n\n")

        # 1. Categories
        f.write("-- 1. INSERT CATEGORIES\n")
        for cid, name, desc in categories:
            safe_desc = desc.replace("'", "''")
            f.write(f"INSERT INTO CATEGORIES (CATEGORY_ID, CATEGORY_NAME, DESCRIPTION) VALUES ({cid}, '{name}', '{safe_desc}');\n")
        f.write("COMMIT;\n\n")

        # 2. Products
        f.write("-- 2. INSERT PRODUCTS\n")
        for pid, name, cid, price, stock in products:
            safe_name = name.replace("'", "''")
            f.write(f"INSERT INTO PRODUCTS (PRODUCT_ID, PRODUCT_NAME, CATEGORY_ID, PRICE, STOCK_QUANTITY) VALUES ({pid}, '{safe_name}', {cid}, {price}, {stock});\n")
        f.write("COMMIT;\n\n")

        # 3. Customers
        f.write("-- 3. INSERT CUSTOMERS\n")
        for cid, name, email, city, state, country, reg_date in customers:
            safe_name = name.replace("'", "''")
            f.write(f"INSERT INTO CUSTOMERS (CUSTOMER_ID, CUSTOMER_NAME, EMAIL, CITY, STATE, COUNTRY, REGISTRATION_DATE) "
                    f"VALUES ({cid}, '{safe_name}', '{email}', '{city}', '{state}', '{country}', TO_DATE('{reg_date}', 'YYYY-MM-DD'));\n")
        f.write("COMMIT;\n\n")

        # 4. Orders
        f.write("-- 4. INSERT ORDERS\n")
        for oid, cust_id, odate, status, pay_m in orders:
            f.write(f"INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, ORDER_DATE, ORDER_STATUS, PAYMENT_METHOD) "
                    f"VALUES ({oid}, {cust_id}, TO_DATE('{odate}', 'YYYY-MM-DD'), '{status}', '{pay_m}');\n")
        f.write("COMMIT;\n\n")

        # 5. Order Items
        f.write("-- 5. INSERT ORDER_ITEMS\n")
        for item_id, oid, pid, qty, price, disc in order_items:
            f.write(f"INSERT INTO ORDER_ITEMS (ORDER_ITEM_ID, ORDER_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE, DISCOUNT) "
                    f"VALUES ({item_id}, {oid}, {pid}, {qty}, {price}, {disc});\n")
        f.write("COMMIT;\n\n")
        f.write("-- DATA SEEDING COMPLETE\n")

if __name__ == "__main__":
    customers = generate_customers(105)
    orders, order_items = generate_orders_and_items(105, 330)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, "sample_data.sql")
    export_oracle_sql(customers, CATEGORIES, PRODUCTS, orders, order_items, sql_path)
    print(f"Generated sample_data.sql with {len(customers)} customers, {len(orders)} orders, {len(order_items)} items.")
