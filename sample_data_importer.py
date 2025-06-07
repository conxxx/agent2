# cymbal_home_garden_backend/sample_data_importer.py

import sqlite3
import logging
import json # For encoding lists as JSON strings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_NAME = 'ecommerce.db'

# Define SKUs for cross-referencing
SKU_LAVENDER = "SKU_PLANT_LAVENDER_001"
SKU_TOMATO = "SKU_PLANT_TOMATO_CELEBRITY_001"
SKU_MONSTERA = "SKU_PLANT_MONSTERA_D_001"
SKU_ROSEMARY = "SKU_PLANT_ROSEMARY_001"
SKU_BASIL = "SKU_PLANT_BASIL_GENOVESE_001"

SKU_SOIL_WELLDRAIN = "SKU_SOIL_WELLDRAIN_PREMIUM_001"
SKU_SOIL_ORGANIC_VEG = "SKU_SOIL_ORGANIC_VEG_001"
SKU_SOIL_HOUSEPLANT = "SKU_SOIL_HOUSEPLANT_PREMIUM_001"

SKU_FERT_BLOOM = "SKU_FERT_BLOOMBOOSTER_001"
SKU_FERT_VEGGIE = "SKU_FERT_ORGANIC_VEG_001"
SKU_FERT_ALLPURPOSE_LIQUID = "SKU_FERT_ALLPURPOSE_LIQUID_001"

SKU_POT_TERRACOTTA_MED = "SKU_POT_TERRACOTTA_MED_001"
SKU_POT_CERAMIC_LG = "SKU_POT_CERAMIC_LG_INDOOR_001"

SKU_TOOL_TROWEL = "SKU_TOOL_TROWEL_ERGO_001"
SKU_TOOL_PRUNERS = "SKU_TOOL_PRUNERS_BYPASS_001"

# New SKUs for additional products - Batch 1
SKU_PEPPER_BELL_GREEN = "SKU_PLANT_PEPPER_BELL_GREEN_001"
SKU_CUCUMBER_MARKETMORE = "SKU_PLANT_CUCUMBER_MARKETMORE_001"
SKU_STRAWBERRY_EARLIBELLE = "SKU_PLANT_STRAWBERRY_EARLIBELLE_001"
SKU_MINT_SPEARMINT = "SKU_PLANT_MINT_SPEARMINT_001"
SKU_SAGE_COMMON = "SKU_PLANT_SAGE_COMMON_001" # Actual definition for placeholder
SKU_MARIGOLD_CRACKERJACK = "SKU_PLANT_MARIGOLD_CRACKERJACK_001" # Actual definition for placeholder
SKU_SUNFLOWER_MAMMOTH = "SKU_PLANT_SUNFLOWER_MAMMOTH_001"
SKU_ECHINACEA_PURPLE = "SKU_PLANT_ECHINACEA_PURPLE_001" # Actual definition for placeholder
SKU_SOIL_SEED_START = "SKU_SOIL_SEED_START_MIX_001"
SKU_TOOL_WATERING_CAN_PLASTIC = "SKU_TOOL_WATERING_CAN_PLASTIC_1GAL_001"
SKU_TOOL_GARDEN_GLOVES_L = "SKU_TOOL_GARDEN_GLOVES_L_001"
SKU_SEED_CARROT_DANVERS = "SKU_SEED_CARROT_DANVERS_001"
SKU_SEED_LETTUCE_BUTTERCRUNCH = "SKU_SEED_LETTUCE_BUTTERCRUNCH_001"
SKU_PEST_NEEM_OIL_CONCENTRATE = "SKU_PEST_NEEM_OIL_CONCENTRATE_001"
SKU_PEST_INSECTICIDAL_SOAP = "SKU_PEST_INSECTICIDAL_SOAP_RTU_001"
SKU_FERN_BOSTON = "SKU_PLANT_FERN_BOSTON_001"


SAMPLE_PRODUCTS = [
    # --- PLANTS ---
    {
        "id": SKU_LAVENDER, "name": "English Lavender 'Munstead'", "category": "Plants",
        "description": "Aromatic perennial with deep purple-blue flowers, compact growth. Excellent for borders, rock gardens, and attracting bees and butterflies. Drought-tolerant once established.",
        "price": 5.99, "original_price": 6.99, "stock": 75, "image_url": "static/images/lavender_munstead.png", "product_uri": "/products/SKU_PLANT_LAVENDER_001", "language_code": "en",
        "botanical_name": "Lavandula angustifolia 'Munstead'", "plant_type": "Perennial Shrub",
        "mature_height_cm": 45, "mature_width_cm": 60, "light_requirement": "Full Sun",
        "water_needs": "Low", "watering_frequency_notes": "Water deeply but infrequently, allow soil to dry out between waterings.",
        "soil_preference": "Well-draining, Alkaline", "soil_ph_preference": "6.5-7.5", "hardiness_zone": "5-9",
        "flower_color": json.dumps(["Purple", "Blue"]), "flowering_season": json.dumps(["Late Spring", "Summer"]),
        "fragrance": "Strong", "fruit_bearing": False,
        "care_level": "Beginner", "pet_safe": True, "attracts_pollinators": True,
        "pollinator_types": json.dumps(["Bees", "Butterflies"]), "deer_resistant": True, "drought_tolerant": True,
        "landscape_use": json.dumps(["Border", "Container", "Herb Garden", "Rock Garden", "Mass Planting"]),
        "indoor_outdoor": "Outdoor",
        "companion_plants_ids": json.dumps([SKU_ROSEMARY, SKU_ECHINACEA_PURPLE]),
        "recommended_soil_ids": json.dumps([SKU_SOIL_WELLDRAIN]),
        "recommended_fertilizer_ids": json.dumps([SKU_FERT_BLOOM]),
    },
    {
        "id": SKU_TOMATO, "name": "Tomato 'Celebrity'", "category": "Plants",
        "description": "Vigorous determinate tomato plant producing medium-sized, flavorful red fruits. Good disease resistance. Ideal for slicing and salads.",
        "price": 4.50, "original_price": 4.50, "stock": 100, "image_url": "static/images/tomato_celebrity.png", "product_uri": "/products/SKU_PLANT_TOMATO_CELEBRITY_001", "language_code": "en",
        "botanical_name": "Solanum lycopersicum 'Celebrity'", "plant_type": "Vegetable (Annual)",
        "mature_height_cm": 120, "mature_width_cm": 60, "light_requirement": "Full Sun",
        "water_needs": "Moderate to High", "watering_frequency_notes": "Water consistently, especially during fruit development. Aim for 1-2 inches per week.",
        "soil_preference": "Well-draining, Loamy, Rich in organic matter", "soil_ph_preference": "6.0-6.8", "hardiness_zone": "3-11 (grown as annual)",
        "flower_color": json.dumps(["Yellow"]), "flowering_season": json.dumps(["Summer"]),
        "fruit_bearing": True, "harvest_time": json.dumps(["Mid Summer", "Late Summer"]),
        "care_level": "Intermediate", "pet_safe": False, "toxicity_notes": "Leaves and stems are toxic to most pets.",
        "landscape_use": json.dumps(["Vegetable Garden", "Container (Large)"]), "indoor_outdoor": "Outdoor",
        "companion_plants_ids": json.dumps([SKU_BASIL, SKU_MARIGOLD_CRACKERJACK]),
        "recommended_soil_ids": json.dumps([SKU_SOIL_ORGANIC_VEG]),
        "recommended_fertilizer_ids": json.dumps([SKU_FERT_VEGGIE]),
    },
    {
        "id": SKU_MONSTERA, "name": "Monstera Deliciosa (Swiss Cheese Plant)", "category": "Plants",
        "description": "Iconic houseplant with large, fenestrated leaves. Adds a tropical touch to any indoor space. Relatively easy to care for.",
        "price": 29.99, "original_price": 32.00, "stock": 30, "image_url": "static/images/monstera_deliciosa.png", "product_uri": "/products/SKU_PLANT_MONSTERA_D_001", "language_code": "en",
        "botanical_name": "Monstera deliciosa", "plant_type": "Houseplant (Tropical Perennial)",
        "mature_height_cm": 300, "mature_width_cm": 150, # Indoors, can be kept smaller
        "light_requirement": "Bright Indirect Light", "water_needs": "Moderate",
        "watering_frequency_notes": "Water when top 1-2 inches of soil are dry. Avoid overwatering.",
        "soil_preference": "Well-draining, Peat-based potting mix", "soil_ph_preference": "5.5-7.0",
        "care_level": "Beginner", "pet_safe": False, "toxicity_notes": "Contains calcium oxalate crystals, toxic to pets and humans if ingested.",
        "indoor_outdoor": "Indoor",
        "recommended_soil_ids": json.dumps([SKU_SOIL_HOUSEPLANT]),
        "recommended_fertilizer_ids": json.dumps([SKU_FERT_ALLPURPOSE_LIQUID]),
    },
     {
        "id": SKU_ROSEMARY, "name": "Rosemary 'Arp'", "category": "Plants",
        "description": "Upright, aromatic herb with needle-like leaves. Excellent for culinary use and attracts pollinators. More cold-hardy variety.",
        "price": 6.50, "original_price": 6.50, "stock": 60, "image_url": "static/images/rosemary_arp.png", "product_uri": "/products/SKU_PLANT_ROSEMARY_001", "language_code": "en",
        "botanical_name": "Rosmarinus officinalis 'Arp'", "plant_type": "Perennial Herb/Shrub",
        "mature_height_cm": 120, "mature_width_cm": 90, "light_requirement": "Full Sun",
        "water_needs": "Low", "soil_preference": "Well-draining, Sandy", "hardiness_zone": "6-10",
        "flower_color": json.dumps(["Blue", "Lavender"]), "flowering_season": json.dumps(["Spring", "Early Summer"]),
        "fragrance": "Strong", "care_level": "Beginner", "pet_safe": True, "attracts_pollinators": True, "fruit_bearing": False,
        "pollinator_types": json.dumps(["Bees"]), "deer_resistant": True, "drought_tolerant": True,
        "landscape_use": json.dumps(["Herb Garden", "Border", "Container", "Xeriscaping"]), "indoor_outdoor": "Outdoor",
        "companion_plants_ids": json.dumps([SKU_LAVENDER, SKU_SAGE_COMMON]),
        "recommended_soil_ids": json.dumps([SKU_SOIL_WELLDRAIN]),
    },
    {
        "id": SKU_BASIL, "name": "Basil 'Genovese'", "category": "Plants",
        "description": "Classic Italian sweet basil with large, fragrant leaves. Perfect for pesto, salads, and tomato dishes. Best grown as an annual.",
        "price": 3.99, "original_price": 3.99, "stock": 80, "image_url": "static/images/basil_genovese.png", "product_uri": "/products/SKU_PLANT_BASIL_GENOVESE_001", "language_code": "en",
        "botanical_name": "Ocimum basilicum 'Genovese'", "plant_type": "Annual Herb",
        "mature_height_cm": 60, "mature_width_cm": 45, "light_requirement": "Full Sun",
        "water_needs": "Moderate", "watering_frequency_notes": "Keep soil consistently moist, but not waterlogged.",
        "soil_preference": "Well-draining, Rich in organic matter", "soil_ph_preference": "6.0-7.0", "hardiness_zone": "10+ (grown as annual elsewhere)",
        "care_level": "Beginner", "pet_safe": True, "fruit_bearing": False,
        "landscape_use": json.dumps(["Herb Garden", "Container", "Vegetable Garden Companion"]), "indoor_outdoor": "Outdoor",
        "companion_plants_ids": json.dumps([SKU_TOMATO]),
        "recommended_soil_ids": json.dumps([SKU_SOIL_ORGANIC_VEG]),
    },

    # --- SOIL ---
    {
        "id": SKU_SOIL_WELLDRAIN, "name": "Premium Well-Draining Potting Mix", "category": "Soil",
        "description": "Specially formulated for plants requiring excellent drainage, such as lavender, succulents, and Mediterranean herbs. Prevents root rot.",
        "price": 12.99, "original_price": 13.99, "stock": 50, "image_url": "static/images/soil_welldrain.png", "product_uri": "/products/SKU_SOIL_WELLDRAIN_PREMIUM_001", "language_code": "en",
        "volume_liters": 20, "organic": False, "fruit_bearing": False,
    },
    {
        "id": SKU_SOIL_ORGANIC_VEG, "name": "Organic Vegetable & Herb Garden Soil", "category": "Soil",
        "description": "Rich, organic soil blend perfect for growing robust vegetables and herbs. Enriched with compost and natural nutrients.",
        "price": 15.99, "original_price": 15.99, "stock": 40, "image_url": "static/images/soil_organic_veg.png", "product_uri": "/products/SKU_SOIL_ORGANIC_VEG_001", "language_code": "en",
        "volume_liters": 25, "organic": True, "fruit_bearing": False,
    },
    {
        "id": SKU_SOIL_HOUSEPLANT, "name": "Premium Houseplant Potting Mix", "category": "Soil",
        "description": "Lightweight and airy mix ideal for a wide variety of indoor houseplants. Promotes healthy root growth and provides essential nutrients.",
        "price": 10.99, "original_price": 11.50, "stock": 60, "image_url": "static/images/soil_houseplant.png", "product_uri": "/products/SKU_SOIL_HOUSEPLANT_PREMIUM_001", "language_code": "en",
        "volume_liters": 10, "organic": False, "fruit_bearing": False,
    },

    # --- FERTILIZERS ---
    {
        "id": SKU_FERT_BLOOM, "name": "Bloom Booster Flower Fertilizer", "category": "Fertilizers",
        "description": "High phosphorus formula to promote vibrant and abundant blooms in flowering plants.",
        "price": 9.99, "original_price": 10.99, "stock": 70, "image_url": "static/images/fert_bloom.png", "product_uri": "/products/SKU_FERT_BLOOMBOOSTER_001", "language_code": "en",
        "npk_ratio": "10-30-10", "organic": False, "application_method": "Granular, mix with soil or sprinkle on top.", "application_frequency": "Every 4-6 weeks during blooming season.", "fruit_bearing": False,
        "volume_liters": 0.5,
    },
    {
        "id": SKU_FERT_VEGGIE, "name": "Organic Vegetable & Tomato Fertilizer", "category": "Fertilizers",
        "description": "OMRI listed organic fertilizer, specially formulated for vegetables and tomatoes. Promotes healthy growth and bountiful harvests.",
        "price": 13.49, "original_price": 13.49, "stock": 55, "image_url": "static/images/fert_veggie.png", "product_uri": "/products/SKU_FERT_ORGANIC_VEG_001", "language_code": "en",
        "npk_ratio": "3-4-4", "organic": True, "application_method": "Granular, mix into soil.", "application_frequency": "At planting and mid-season.", "fruit_bearing": False,
    },
    {
        "id": SKU_FERT_ALLPURPOSE_LIQUID, "name": "All-Purpose Liquid Plant Food", "category": "Fertilizers",
        "description": "Concentrated liquid fertilizer for all indoor and outdoor plants. Easy to mix and apply for quick nutrient absorption.",
        "price": 7.99, "original_price": 8.99, "stock": 90, "image_url": "static/images/fert_allpurpose_liquid.png", "product_uri": "/products/SKU_FERT_ALLPURPOSE_LIQUID_001", "language_code": "en",
        "npk_ratio": "10-10-10", "organic": False, "application_method": "Liquid, dilute with water.", "application_frequency": "Every 2-4 weeks during growing season.", "fruit_bearing": False,
        "volume_liters": 0.5,
    },

    # --- POTS ---
    {
        "id": SKU_POT_TERRACOTTA_MED, "name": "Terracotta Pot - Medium (8 inch)", "category": "Pots",
        "description": "Classic porous terracotta pot, promotes healthy root growth by allowing air and moisture exchange. Includes drainage hole.",
        "price": 7.50, "original_price": 7.50, "stock": 120, "image_url": "static/images/pot_terracotta_medium.png", "product_uri": "/products/SKU_POT_TERRACOTTA_MED_001", "language_code": "en",
        "pot_material": "Terracotta", "pot_diameter_cm": 20, "pot_height_cm": 18, "pot_drainage_holes": True, "fruit_bearing": False,
    },
     {
        "id": SKU_POT_CERAMIC_LG, "name": "Large Ceramic Indoor Planter with Saucer (12 inch)", "category": "Pots",
        "description": "Elegant glazed ceramic planter, perfect for statement houseplants. Includes attached saucer to protect surfaces.",
        "price": 24.99, "original_price": 26.99, "stock": 45, "image_url": "static/images/pot_ceramic_large.png", "product_uri": "/products/SKU_POT_CERAMIC_LG_INDOOR_001", "language_code": "en",
        "pot_material": "Ceramic", "pot_diameter_cm": 30, "pot_height_cm": 28, "pot_drainage_holes": True, "fruit_bearing": False,
    },

    # --- TOOLS ---
    {
        "id": SKU_TOOL_TROWEL, "name": "Ergonomic Hand Trowel", "category": "Tools",
        "description": "Durable stainless steel hand trowel with a comfortable, non-slip ergonomic grip. Ideal for planting and weeding.",
        "price": 11.99, "original_price": 11.99, "stock": 60, "image_url": "static/images/trowel_ergo.png", "product_uri": "/products/SKU_TOOL_TROWEL_ERGO_001", "language_code": "en", "fruit_bearing": False,
    },
    {
        "id": SKU_TOOL_PRUNERS, "name": "Bypass Pruning Shears", "category": "Tools",
        "description": "Sharp bypass pruning shears for clean cuts on live stems and branches up to 3/4 inch. Hardened steel blades.",
        "price": 18.75, "original_price": 19.99, "stock": 50, "image_url": "static/images/pruners_bypass.png", "product_uri": "/products/SKU_TOOL_PRUNERS_BYPASS_001", "language_code": "en", "fruit_bearing": False,
    },

    # --- NEW PRODUCTS START HERE ---
    # Plants - Vegetables
    {
        "id": SKU_PEPPER_BELL_GREEN, "name": "Green Bell Pepper Plant", "category": "Plants",
        "description": "Produces large, blocky green bell peppers. Sweet and crisp, perfect for salads, stuffing, or grilling.",
        "price": 4.75, "original_price": 4.75, "stock": 90, "image_url": "static/images/pepper_bell_green.png", "product_uri": "/products/SKU_PLANT_PEPPER_BELL_GREEN_001", "language_code": "en",
        "botanical_name": "Capsicum annuum 'Green Bell'", "plant_type": "Vegetable (Annual)",
        "mature_height_cm": 70, "mature_width_cm": 50, "light_requirement": "Full Sun",
        "water_needs": "Moderate", "watering_frequency_notes": "Keep soil consistently moist. Water 1-2 times per week.",
        "soil_preference": "Well-draining, Rich in organic matter", "soil_ph_preference": "6.0-7.0", "hardiness_zone": "3-11 (grown as annual)",
        "flower_color": json.dumps(["White"]), "flowering_season": json.dumps(["Summer"]),
        "fruit_bearing": True, "harvest_time": json.dumps(["Mid Summer", "Late Summer"]),
        "care_level": "Intermediate", "pet_safe": True,
        "landscape_use": json.dumps(["Vegetable Garden", "Container"]), "indoor_outdoor": "Outdoor",
        "companion_plants_ids": json.dumps([SKU_TOMATO, SKU_BASIL]),
        "recommended_soil_ids": json.dumps([SKU_SOIL_ORGANIC_VEG]),
        "recommended_fertilizer_ids": json.dumps([SKU_FERT_VEGGIE]),
    },
    {
        "id": SKU_CUCUMBER_MARKETMORE, "name": "Cucumber 'Marketmore 76'", "category": "Plants",
        "description": "Reliable and productive slicing cucumber. Dark green, straight fruits about 8 inches long. Disease resistant.",
        "price": 3.99, "original_price": 3.99, "stock": 110, "image_url": "static/images/cucumber_marketmore.png", "product_uri": "/products/SKU_PLANT_CUCUMBER_MARKETMORE_001", "language_code": "en",
        "botanical_name": "Cucumis sativus 'Marketmore 76'", "plant_type": "Vegetable (Annual Vine)",
        "mature_height_cm": 200, "mature_width_cm": 60, "light_requirement": "Full Sun", # Vine length
        "water_needs": "High", "watering_frequency_notes": "Needs consistent moisture, especially during fruiting. Water deeply.",
        "soil_preference": "Well-draining, Rich, Fertile", "soil_ph_preference": "6.0-7.0", "hardiness_zone": "4-11 (grown as annual)",
        "flower_color": json.dumps(["Yellow"]), "flowering_season": json.dumps(["Summer"]),
        "fruit_bearing": True, "harvest_time": json.dumps(["Summer"]),
        "care_level": "Beginner", "pet_safe": True,
        "landscape_use": json.dumps(["Vegetable Garden", "Trellis", "Container (Large with support)"]), "indoor_outdoor": "Outdoor",
        "recommended_soil_ids": json.dumps([SKU_SOIL_ORGANIC_VEG]),
        "recommended_fertilizer_ids": json.dumps([SKU_FERT_VEGGIE]),
    },
    {
        "id": SKU_STRAWBERRY_EARLIBELLE, "name": "Strawberry 'Earlibelle' (June-bearing)", "category": "Plants",
        "description": "Popular June-bearing strawberry variety. Produces large, sweet, red berries in late spring/early summer. Great for fresh eating or preserves.",
        "price": 7.99, "original_price": 8.50, "stock": 60, "image_url": "static/images/strawberry_earlibelle.png", "product_uri": "/products/SKU_PLANT_STRAWBERRY_EARLIBELLE_001", "language_code": "en", # Price for a pack of plants
        "botanical_name": "Fragaria × ananassa 'Earlibelle'", "plant_type": "Perennial Fruit",
        "mature_height_cm": 20, "mature_width_cm": 30, "light_requirement": "Full Sun",
        "water_needs": "Moderate", "watering_frequency_notes": "Keep soil consistently moist, especially during fruiting.",
        "soil_preference": "Well-draining, Sandy Loam, Rich in organic matter", "soil_ph_preference": "5.5-6.5", "hardiness_zone": "4-8",
        "flower_color": json.dumps(["White"]), "flowering_season": json.dumps(["Spring"]),
        "fruit_bearing": True, "harvest_time": json.dumps(["Late Spring", "Early Summer"]),
        "care_level": "Intermediate", "pet_safe": True,
        "landscape_use": json.dumps(["Fruit Patch", "Ground Cover", "Container", "Hanging Basket"]), "indoor_outdoor": "Outdoor",
        "recommended_soil_ids": json.dumps([SKU_SOIL_ORGANIC_VEG]),
        "recommended_fertilizer_ids": json.dumps([SKU_FERT_ALLPURPOSE_LIQUID]), # Or a fruit-specific one
    },

    # Plants - Herbs
    {
        "id": SKU_MINT_SPEARMINT, "name": "Spearmint Plant", "category": "Plants",
        "description": "Classic spearmint with a refreshing, sweet flavor. Spreads vigorously. Ideal for teas, desserts, and garnishes.",
        "price": 4.25, "original_price": 4.25, "stock": 70, "image_url": "static/images/mint_spearmint.png", "product_uri": "/products/SKU_PLANT_MINT_SPEARMINT_001", "language_code": "en",
        "botanical_name": "Mentha spicata", "plant_type": "Perennial Herb",
        "mature_height_cm": 60, "mature_width_cm": 90, "light_requirement": "Full Sun to Part Shade", # Spreading
        "water_needs": "Moderate to High", "watering_frequency_notes": "Prefers consistently moist soil.",
        "soil_preference": "Rich, Moist, Well-draining", "soil_ph_preference": "6.0-7.5", "hardiness_zone": "4-9",
        "flower_color": json.dumps(["Lilac", "Pink", "White"]), "flowering_season": json.dumps(["Summer"]),
        "fragrance": "Strong, Minty", "fruit_bearing": False,
        "care_level": "Beginner", "pet_safe": True, # Generally, but large quantities can be an issue for some pets
        "landscape_use": json.dumps(["Herb Garden", "Container (recommended to control spread)", "Ground Cover"]), "indoor_outdoor": "Outdoor",
    },
    {
        "id": SKU_SAGE_COMMON, "name": "Common Sage Plant", "category": "Plants",
        "description": "Aromatic culinary herb with gray-green leaves. Used in stuffings, sausages, and savory dishes. Drought-tolerant once established.",
        "price": 5.50, "original_price": 5.99, "stock": 50, "image_url": "static/images/sage_common.png", "product_uri": "/products/SKU_PLANT_SAGE_COMMON_001", "language_code": "en",
        "botanical_name": "Salvia officinalis", "plant_type": "Perennial Herb/Shrub",
        "mature_height_cm": 75, "mature_width_cm": 60, "light_requirement": "Full Sun",
        "water_needs": "Low", "watering_frequency_notes": "Allow soil to dry between waterings.",
        "soil_preference": "Well-draining", "soil_ph_preference": "6.0-7.0", "hardiness_zone": "4-8",
        "flower_color": json.dumps(["Purple", "Blue"]), "flowering_season": json.dumps(["Early Summer"]),
        "fragrance": "Strong, Earthy", "fruit_bearing": False,
        "care_level": "Beginner", "pet_safe": True, "attracts_pollinators": True, "deer_resistant": True,
        "landscape_use": json.dumps(["Herb Garden", "Border", "Container", "Rock Garden"]), "indoor_outdoor": "Outdoor",
        "companion_plants_ids": json.dumps([SKU_ROSEMARY, SKU_LAVENDER]),
        "recommended_soil_ids": json.dumps([SKU_SOIL_WELLDRAIN]),
    },

    # Plants - Flowers
    {
        "id": SKU_MARIGOLD_CRACKERJACK, "name": "Marigold 'Crackerjack Mix'", "category": "Plants",
        "description": "Tall marigolds with large, fluffy blooms in shades of yellow, gold, and orange. Excellent for cutting and deterring garden pests.",
        "price": 3.50, "original_price": 3.50, "stock": 120, "image_url": "static/images/marigold_crackerjack.png", "product_uri": "/products/SKU_PLANT_MARIGOLD_CRACKERJACK_001", "language_code": "en", # Price for a 6-pack
        "botanical_name": "Tagetes erecta 'Crackerjack'", "plant_type": "Annual Flower",
        "mature_height_cm": 90, "mature_width_cm": 45, "light_requirement": "Full Sun",
        "water_needs": "Moderate", "watering_frequency_notes": "Water regularly, especially in dry weather.",
        "soil_preference": "Well-draining, Tolerates poor soil", "soil_ph_preference": "6.0-7.5", "hardiness_zone": "2-11 (grown as annual)",
        "flower_color": json.dumps(["Yellow", "Orange", "Gold"]), "flowering_season": json.dumps(["Summer", "Fall"]),
        "fragrance": "Pungent (leaves)", "fruit_bearing": False,
        "care_level": "Beginner", "pet_safe": True, "attracts_pollinators": True, "deer_resistant": True,
        "landscape_use": json.dumps(["Bedding Plant", "Border", "Container", "Vegetable Garden Companion"]), "indoor_outdoor": "Outdoor",
        "companion_plants_ids": json.dumps([SKU_TOMATO, SKU_PEPPER_BELL_GREEN]),
    },
    {
        "id": SKU_SUNFLOWER_MAMMOTH, "name": "Sunflower 'Mammoth Grey Stripe'", "category": "Plants",
        "description": "Classic giant sunflower with huge yellow heads and edible seeds. Can grow over 10 feet tall!",
        "price": 4.99, "original_price": 5.49, "stock": 80, "image_url": "static/images/sunflower_mammoth.png", "product_uri": "/products/SKU_PLANT_SUNFLOWER_MAMMOTH_001", "language_code": "en", # Price for a seedling or small plant
        "botanical_name": "Helianthus annuus 'Mammoth Grey Stripe'", "plant_type": "Annual Flower",
        "mature_height_cm": 300, "mature_width_cm": 60, "light_requirement": "Full Sun", # Can reach 300-400 cm
        "water_needs": "Moderate to High", "watering_frequency_notes": "Needs regular watering, especially during growth spurts.",
        "soil_preference": "Well-draining, Fertile", "soil_ph_preference": "6.0-7.5", "hardiness_zone": "2-11 (grown as annual)",
        "flower_color": json.dumps(["Yellow"]), "flowering_season": json.dumps(["Summer"]),
        "fragrance": "None", "fruit_bearing": True, "harvest_time": json.dumps(["Late Summer", "Fall"]), # For seeds
        "care_level": "Beginner", "pet_safe": True, "attracts_pollinators": True,
        "landscape_use": json.dumps(["Background Plant", "Screen", "Children's Garden"]), "indoor_outdoor": "Outdoor",
    },
    {
        "id": SKU_ECHINACEA_PURPLE, "name": "Purple Coneflower (Echinacea)", "category": "Plants",
        "description": "Popular prairie native with large, daisy-like purple-pink flowers. Attracts pollinators and is great for cutting. Drought-tolerant.",
        "price": 8.99, "original_price": 8.99, "stock": 65, "image_url": "static/images/echinacea_purple.png", "product_uri": "/products/SKU_PLANT_ECHINACEA_PURPLE_001", "language_code": "en",
        "botanical_name": "Echinacea purpurea", "plant_type": "Perennial Flower",
        "mature_height_cm": 90, "mature_width_cm": 60, "light_requirement": "Full Sun to Part Shade",
        "water_needs": "Low to Moderate", "watering_frequency_notes": "Drought-tolerant once established.",
        "soil_preference": "Well-draining, Tolerates various soils", "soil_ph_preference": "6.0-7.0", "hardiness_zone": "3-8",
        "flower_color": json.dumps(["Purple", "Pink"]), "flowering_season": json.dumps(["Summer", "Fall"]),
        "fragrance": "Mild", "fruit_bearing": False,
        "care_level": "Beginner", "pet_safe": True, "attracts_pollinators": True, "deer_resistant": True,
        "landscape_use": json.dumps(["Perennial Border", "Cutting Garden", "Prairie Garden", "Mass Planting"]), "indoor_outdoor": "Outdoor",
        "companion_plants_ids": json.dumps([SKU_LAVENDER, "SKU_PLANT_RUDBECKIA_001"]),
        "recommended_soil_ids": json.dumps([SKU_SOIL_WELLDRAIN]),
    },
    {
        "id": SKU_FERN_BOSTON, "name": "Boston Fern", "category": "Plants",
        "description": "Classic lush fern with arching fronds. Perfect for hanging baskets or as a graceful houseplant. Prefers humidity.",
        "price": 15.99, "original_price": 17.99, "stock": 40, "image_url": "static/images/fern_boston.png", "product_uri": "/products/SKU_PLANT_FERN_BOSTON_001", "language_code": "en",
        "botanical_name": "Nephrolepis exaltata 'Bostoniensis'", "plant_type": "Houseplant (Fern)",
        "mature_height_cm": 60, "mature_width_cm": 90,
        "light_requirement": "Bright Indirect Light, Partial Shade", "water_needs": "High",
        "watering_frequency_notes": "Keep soil consistently moist. Loves humidity, mist frequently.",
        "soil_preference": "Rich, Peat-based, Well-draining", "soil_ph_preference": "5.0-5.5",
        "care_level": "Intermediate", "pet_safe": True, "fruit_bearing": False,
        "indoor_outdoor": "Indoor",
        "recommended_soil_ids": json.dumps([SKU_SOIL_HOUSEPLANT]),
    },

    # Soil - Specialty
    {
        "id": SKU_SOIL_SEED_START, "name": "Seed Starting Mix", "category": "Soil",
        "description": "Fine, lightweight mix ideal for germinating seeds and nurturing young seedlings. Promotes strong root development.",
        "price": 8.99, "original_price": 8.99, "stock": 70, "image_url": "static/images/soil_seed_start.png", "product_uri": "/products/SKU_SOIL_SEED_START_MIX_001", "language_code": "en",
        "volume_liters": 8, "organic": True, "fruit_bearing": False, # Often organic
    },

    # Tools - Variety
    {
        "id": SKU_TOOL_WATERING_CAN_PLASTIC, "name": "Plastic Watering Can (1 Gallon)", "category": "Tools",
        "description": "Lightweight and durable 1-gallon plastic watering can with a detachable sprinkler rose.",
        "price": 9.75, "original_price": 10.25, "stock": 85, "image_url": "static/images/watering_can_plastic_1gal.png", "product_uri": "/products/SKU_TOOL_WATERING_CAN_PLASTIC_1GAL_001", "language_code": "en", "fruit_bearing": False,
    },
    {
        "id": SKU_TOOL_GARDEN_GLOVES_L, "name": "Durable Garden Gloves - Large", "category": "Tools",
        "description": "Comfortable and durable garden gloves with reinforced palms and fingertips. Size Large.",
        "price": 12.50, "original_price": 12.50, "stock": 100, "image_url": "static/images/garden_gloves_l.png", "product_uri": "/products/SKU_TOOL_GARDEN_GLOVES_L_001", "language_code": "en", "fruit_bearing": False,
    },

    # Seeds - Vegetables
    {
        "id": SKU_SEED_CARROT_DANVERS, "name": "Carrot Seeds 'Danvers 126'", "category": "Seeds",
        "description": "Packet of 'Danvers 126' carrot seeds. A popular heirloom variety, producing sweet, orange, 6-7 inch roots. Good for storage.",
        "price": 2.99, "original_price": 2.99, "stock": 200, "image_url": "static/images/seed_carrot_danvers.png", "product_uri": "/products/SKU_SEED_CARROT_DANVERS_001", "language_code": "en",
        "seed_quantity_grams": 2, "seed_planting_depth_cm": 1, "seed_spacing_cm": 5, "seed_days_to_germination": "10-21", "seed_days_to_maturity": "70-80", "fruit_bearing": False, # The plant is, not the seed packet
    },
    {
        "id": SKU_SEED_LETTUCE_BUTTERCRUNCH, "name": "Lettuce Seeds 'Buttercrunch'", "category": "Seeds",
        "description": "Packet of 'Buttercrunch' lettuce seeds. Forms small, tender heads with a buttery texture. Slow to bolt.",
        "price": 2.79, "original_price": 2.79, "stock": 180, "image_url": "static/images/seed_lettuce_buttercrunch.png", "product_uri": "/products/SKU_SEED_LETTUCE_BUTTERCRUNCH_001", "language_code": "en",
        "seed_quantity_grams": 0.5, "seed_planting_depth_cm": 0.5, "seed_spacing_cm": 20, "seed_days_to_germination": "7-14", "seed_days_to_maturity": "55-65", "fruit_bearing": False,
    },

    # Pest Control
    {
        "id": SKU_PEST_NEEM_OIL_CONCENTRATE, "name": "Neem Oil Concentrate (Fungicide/Insecticide/Miticide)", "category": "Pest Control",
        "description": "Concentrated neem oil for organic gardening. Controls common pests like aphids, mites, whiteflies, and fungal diseases. Must be diluted.",
        "price": 14.99, "original_price": 15.99, "stock": 60, "image_url": "static/images/pest_neem_oil_concentrate.png", "product_uri": "/products/SKU_PEST_NEEM_OIL_CONCENTRATE_001", "language_code": "en",
        "volume_liters": 0.25, "organic": True, "application_method": "Liquid, dilute with water and spray.", "fruit_bearing": False, # Product itself
    },
    {
        "id": SKU_PEST_INSECTICIDAL_SOAP, "name": "Insecticidal Soap Spray (Ready-to-Use)", "category": "Pest Control",
        "description": "Ready-to-use insecticidal soap spray. Effective against soft-bodied insects like aphids, mealybugs, and spider mites. Safe for organic gardening.",
        "price": 10.99, "original_price": 10.99, "stock": 75, "image_url": "static/images/pest_insecticidal_soap_rtu.png", "product_uri": "/products/SKU_PEST_INSECTICIDAL_SOAP_RTU_001", "language_code": "en",
        "volume_liters": 0.75, "organic": True, "application_method": "Liquid, spray directly on pests.", "fruit_bearing": False,
    },
]

def insert_sample_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    for product_data in SAMPLE_PRODUCTS:
        # Prepare a list of columns and a list of corresponding values
        # This handles cases where some products don't have all optional fields
        columns = []
        values = []
        for key, value in product_data.items():
            columns.append(key)
            values.append(value)
        
        # Create the INSERT statement dynamically
        # e.g., INSERT INTO products (id, name, ...) VALUES (?, ?, ...)
        placeholders = ', '.join(['?'] * len(columns))
        sql = f"INSERT INTO products ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT(id) DO NOTHING"
        
        try:
            cursor.execute(sql, values)
        except sqlite3.Error as e:
            logger.error(f"Error inserting product {product_data.get('id', 'Unknown ID')}: {e}")
            logger.error(f"SQL: {sql}")
            logger.error(f"Values: {values}")

    conn.commit()
    conn.close()
    logger.info("Sample product data insertion process completed using new schema.")

if __name__ == '__main__':
    # First, ensure tables are created with the new schema
    from database_setup import create_tables
    logger.info("Re-creating tables with the new schema...")
    create_tables() 
    
    logger.info("Inserting new sample data...")
    insert_sample_data()
    
    logger.info("Please create/update the 'static/images/' directory in your backend project root with placeholder images for the new sample products if you want to see them in the frontend.")
    logger.info("Example image names: lavender_munstead.png, tomato_celebrity.png, soil_welldrain.png, etc.")
