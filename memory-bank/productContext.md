# Product Context: Cymbal Home Garden E-commerce Platform

## 1. Problem Statement
Traditional online plant and garden shopping experiences can be frustrating for users due to:
*   **Lack of Detailed Information:** Customers often struggle to find comprehensive details about plants (e.g., specific care needs, mature size, pet safety, hardiness zones) or other gardening products (e.g., soil composition, fertilizer NPK ratios, pot drainage). This makes it difficult to choose the right products for their specific needs and environment.
*   **Poor Product Discovery:** Finding suitable companion plants, or the right soil and fertilizer for a specific plant, can be a cumbersome process involving multiple searches or external research.
*   **Generic Search Results:** Standard e-commerce search often fails to understand the nuanced queries of gardeners (e.g., "drought-tolerant perennials for full sun in zone 7").

Cymbal Home Garden aims to solve these problems by providing a platform with rich, structured product data and an intelligent search experience.

## 2. Solution: Rich Data & Intelligent Search
The core solution revolves around two main pillars:
*   **Comprehensive Product Data:** The platform will store and present detailed attributes for all products. This includes:
    *   **For Plants:** Botanical name, plant type, mature dimensions, light/water/soil needs, hardiness zone, flower details, fragrance, fruit-bearing information, care level, pet safety, pollinator attraction, deer resistance, drought tolerance, landscape use, and indoor/outdoor suitability.
    *   **For Soil/Fertilizers:** Volume, NPK ratio, organic status, application methods, and frequency.
    *   **For Pots:** Material, dimensions, and drainage information.
    *   **Relationships:** Explicitly linking companion plants, recommended soil, and recommended fertilizers to plant products.
*   **Advanced Search (via Vertex AI Search for Commerce):** By feeding this rich, structured data into Vertex AI Search, the platform will enable users to:
    *   Perform complex, natural language queries.
    *   Receive highly relevant search results based on specific plant needs and gardening scenarios.
    *   Discover products more effectively.

## 3. User Experience Goals
*   **Informed Purchasing Decisions:** Users should feel confident that they have all the necessary information to select the right products for their garden and skill level.
*   **Ease of Use:** The platform (both local API and future frontend) should be intuitive to navigate. Product information should be clearly presented.
*   **Efficient Product Discovery:** Users should be able to easily find not only individual products but also related items (e.g., the best soil for a lavender plant they are viewing).
*   **Trust and Authority:** The depth and accuracy of product information should establish Cymbal Home Garden as a trusted resource.

## 4. How It Should Work (MVP Focus)
*   **Data Storage:** A SQLite database will house the detailed product information, with list-like attributes stored as JSON strings.
*   **API Access:** A Flask API will expose endpoints to retrieve:
    *   A list of all products (with filtering capabilities).
    *   Detailed information for a single product.
    *   The API will handle deserializing JSON string attributes into proper arrays in its responses.
*   **Data Feed for Search:** A mechanism (likely a Python script) will extract data from the SQLite database, transform it (including parsing JSON strings), and format it into a JSONL file suitable for ingestion by Vertex AI Search for commerce. This feed will map SQLite columns to the appropriate Vertex AI Search product schema fields (e.g., `title`, `description`, `priceInfo`, `attributes`).

## 5. Product Categories (Initial)
*   Plants (Perennials, Annuals, Houseplants, Herbs, Vegetables, Shrubs)
*   Soil (Potting mixes, Garden soil)
*   Fertilizers (Bloom boosters, Vegetable fertilizers, All-purpose)
*   Pots (Terracotta, Ceramic)
*   Tools (Hand trowels, Pruners)

This detailed product context, driven by the rich data model, is key to achieving the project's goals of empowering users and providing a superior shopping experience.
