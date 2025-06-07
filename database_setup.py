# cymbal_home_garden_backend/database_setup.py

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Drop existing products table if it exists, to apply new schema
    # Be CAREFUL with this in a production environment or if you have important data.
    # For MVP development, it's often useful to start fresh with schema changes.
    cursor.execute("DROP TABLE IF EXISTS products")
    logger.info("Dropped existing products table (if any).")
    cursor.execute("DROP TABLE IF EXISTS cart_items") # Also drop cart_items due to foreign key
    logger.info("Dropped existing cart_items table (if any).")


    # Products table with richer details
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,                      -- Unique product SKU
        name TEXT NOT NULL,                       -- Common Name
        description TEXT,                         -- Detailed description
        price REAL NOT NULL,
        original_price REAL,                      -- Optional: For showing discounts
        stock INTEGER NOT NULL DEFAULT 0,
        category TEXT,                            -- e.g., "Plants", "Soil", "Tools", "Pots", "Fertilizers"
        image_url TEXT,
        product_uri TEXT,                         -- Canonical URL for the product page
        language_code TEXT DEFAULT 'en',          -- Language code, e.g., "en"

        -- Plant-Specific Attributes (can be NULL for non-plant products)
        botanical_name TEXT,
        plant_type TEXT,                          -- e.g., "Perennial", "Annual", "Houseplant", "Herb", "Vegetable"
        mature_height_cm INTEGER,
        mature_width_cm INTEGER,
        light_requirement TEXT,                   -- e.g., "Full Sun", "Partial Shade", "Bright Indirect Light"
        water_needs TEXT,                         -- e.g., "Low", "Moderate", "High"
        watering_frequency_notes TEXT,
        soil_preference TEXT,                     -- e.g., "Well-draining", "Acidic", "Loamy"
        soil_ph_preference TEXT,                  -- e.g., "6.0-7.0"
        hardiness_zone TEXT,                      -- e.g., "5-9" (USDA Hardiness Zone)
        flower_color TEXT,                        -- Store as JSON string array: '["Purple", "Blue"]'
        flowering_season TEXT,                    -- Store as JSON string array: '["Late Spring", "Summer"]'
        fragrance TEXT,                           -- e.g., "None", "Slight", "Strong"
        fruit_bearing BOOLEAN DEFAULT FALSE,
        harvest_time TEXT,                        -- Store as JSON string array for edibles
        care_level TEXT,                          -- e.g., "Beginner", "Intermediate", "Expert"
        pet_safe BOOLEAN,                         -- True if safe, False if toxic, NULL if unknown/not applicable
        toxicity_notes TEXT,                      -- Details if not pet_safe
        attracts_pollinators BOOLEAN,
        pollinator_types TEXT,                    -- Store as JSON string array: '["Bees", "Butterflies"]'
        deer_resistant BOOLEAN,
        drought_tolerant BOOLEAN,
        landscape_use TEXT,                       -- Store as JSON string array: '["Border", "Container"]'
        indoor_outdoor TEXT,                      -- "Indoor", "Outdoor", "Both"
        
        -- Relationship / Recommendation Attributes (store as JSON string array of product IDs)
        companion_plants_ids TEXT,                -- '["SKU_OTHER_PLANT_1", "SKU_OTHER_PLANT_2"]'
        recommended_soil_ids TEXT,                -- '["SKU_SOIL_1", "SKU_SOIL_2"]'
        recommended_fertilizer_ids TEXT,          -- '["SKU_FERT_1"]'

        -- Seed Specific Attributes (can be NULL for non-seed products)
        seed_quantity_grams REAL,
        seed_planting_depth_cm REAL,
        seed_spacing_cm REAL,
        seed_days_to_germination TEXT,
        seed_days_to_maturity TEXT,
        
        -- Soil/Fertilizer Specific Attributes
        volume_liters REAL,                       -- For soil bags, liquid fertilizers
        npk_ratio TEXT,                           -- For fertilizers (e.g., "10-10-10")
        organic BOOLEAN,
        application_method TEXT,                  -- For fertilizers
        application_frequency TEXT,               -- For fertilizers
        
        -- Pot Specific Attributes
        pot_material TEXT,
        pot_diameter_cm INTEGER,
        pot_height_cm INTEGER,
        pot_drainage_holes BOOLEAN
    )
    ''')
    logger.info("Products table with new schema created or already exists.")

    # Cart Items table (recreate after dropping products)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    logger.info("Cart items table created or already exists.")

    conn.commit()
    conn.close()
    logger.info(f"Database '{DATABASE_NAME}' and tables initialized successfully with new schema.")

if __name__ == '__main__':
    create_tables()
