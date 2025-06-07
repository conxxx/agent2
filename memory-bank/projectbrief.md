# Project Brief: Cymbal Home Garden E-commerce Platform

## 1. Project Name
Cymbal Home Garden E-commerce Platform

## 2. Overall Goal
Develop an MVP (Minimum Viable Product) e-commerce application for a home and garden store. The platform will feature rich product details for a variety of items (plants, soil, tools, pots, fertilizers) and will integrate with Vertex AI Search for commerce to provide an advanced search experience.

## 3. Key Features for MVP
The initial focus for the MVP includes:
*   **Backend API:** A Flask-based API to serve product information, manage a shopping cart, and potentially handle user interactions in the future.
*   **SQLite Database:** A local SQLite database to store comprehensive product data, including detailed attributes specific to different product categories.
*   **Detailed Product Schema:** A well-defined database schema capable of storing rich information such as botanical names, care instructions, dimensions, material, NPK ratios, companion products, etc.
*   **JSONL Feed Generation:** The system must be capable of generating a JSONL (JSON Lines) feed from the product data, formatted according to the requirements of Vertex AI Search for commerce.
*   **Sample Data:** A robust set of sample data to populate the database for development and testing purposes.

## 4. Target User
Customers looking for home and garden supplies, ranging from beginners to experienced gardeners. The rich product information aims to help users make informed purchasing decisions.

## 5. Core Technologies (Initial)
*   **Backend:** Python, Flask
*   **Database:** SQLite
*   **Search Integration:** Vertex AI Search for commerce
*   **Data Interchange Format (for Search):** JSONL

## 6. Success Metrics (Conceptual for MVP)
*   Successfully populate the database with rich sample product data.
*   API endpoints correctly serve detailed product information, including deserialized list-like attributes.
*   Successfully generate a valid JSONL feed for Vertex AI Search from the database.
*   (Future) User can browse products and view their detailed information via a simple frontend.
*   (Future) User can add products to a cart.

## 7. Scope & Constraints
*   **MVP Focus:** The primary goal is to establish the backend data model, API, and the pipeline for Vertex AI Search. Frontend development is secondary for the initial MVP stages unless specified.
*   **SQLite for MVP:** SQLite is chosen for simplicity in local development. Data migration to a more robust production database will be considered post-MVP.
*   **JSON for List-like Attributes in SQLite:** Due to SQLite's limitations, fields representing lists (e.g., `flower_color`, `companion_plants_ids`) will be stored as JSON-encoded strings in `TEXT` columns. These will be parsed back into proper JSON arrays in API responses and during JSONL generation.
