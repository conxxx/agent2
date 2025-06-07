# Vertex AI Search for Commerce: Product Schema Guidelines

This document summarizes key guidelines for formatting product data for ingestion into Google Cloud Vertex AI Search for commerce, based on the official documentation.

**Source Documentation:**
*   URL: `https://cloud.google.com/retail/docs/upload-catalog`
*   Documentation Last Updated: 2025-05-05 UTC
*   Information Verified: 2025-05-10

## 1. Data Format for Import (via Cloud Storage)
*   **JSONL (JSON Lines):** Each product item must be a complete JSON object on a new line in the `.jsonl` file.

## 2. Minimum Required Product Fields
The following fields are mandatory for each product item:
*   `id`: (String) A unique identifier for the product.
*   `categories`: (String) The product category hierarchy. Example: `"Apparel & Accessories > Shoes"` or `"Home & Garden > Plants > Perennials"`.
*   `title`: (String) The name of the product.

## 3. Custom Attributes (`Product.attributes`)
Custom attributes allow for rich, product-specific data. They are defined within the `attributes` field, which is a map (object).
*   **Structure:** Each key in the `attributes` map is the custom attribute's name (e.g., `botanical_name`, `light_requirement`, `is_pet_friendly`).
*   **Value Format:** The value for each custom attribute *must* be an object containing either:
    *   `"text"`: An array of strings. Example: `{"vendor": {"text": ["vendor123", "vendor456"]}}`
    *   `"numbers"`: An array of numbers. Example: `{"npk_ratio": {"numbers": [10, 10, 10]}}`
*   **Boolean Custom Attributes:** There is no direct boolean type for custom attributes. They **must** be represented using the `"text"` format.
    *   Example for `true`: `{"is_pet_friendly": {"text": ["true"]}}`
    *   Example for `false`: `{"is_drought_tolerant": {"text": ["false"]}}`
    *   This is a critical formatting requirement.

## 4. Other Important Standard Fields (and their format from examples)
*   `name`: (String) The fully qualified product name. Example: `"projects/PROJECT_NUMBER/locations/global/catalogs/default_catalog/branches/0/products/PRODUCT_ID"` (Often auto-generated or can be set).
*   `description`: (String) A detailed description of the product.
*   `language_code`: (String) The language of the product information (e.g., `"en"`).
*   `tags`: (Array of Strings) Tags associated with the product (e.g., `["black-friday", "sale"]`).
*   `priceInfo`: (Object) Contains pricing details:
    *   `currencyCode`: (String) The currency code (e.g., `"USD"`).
    *   `price`: (Number) The current selling price.
    *   `originalPrice`: (Number, Optional) The original price before discounts.
    *   `cost`: (Number, Optional) The cost of the product.
*   `availableTime`: (String) The time the product becomes available, in ISO 8601 format. Example: `"2020-01-01T03:33:33.000001Z"`.
*   `expireTime`: (String) The time the product expires, in ISO 8601 format. Used for historical products. Example: `"2021-10-02T15:01:23Z"`.
*   `availableQuantity`: (String, as per documentation example) The quantity available. Example: `"1"`. While representing a number, the example uses a string.
*   `uri`: (String) The canonical URI of the product page on your website.
*   `images`: (Array of Objects) Each object represents an image and contains:
    *   `uri`: (String) Publicly accessible URI of the image.
    *   `height`: (Number) Height of the image in pixels.
    *   `width`: (Number) Width of the image in pixels.

## 5. General Best Practices
*   Keep catalog data up to date, ideally with daily imports.
*   Ensure high-quality data: avoid placeholder values and include as much optional information as possible.
*   Use a single currency per catalog if using Google Cloud console for revenue metrics.
*   Monitor import health and error reports.

This summary should serve as a quick reference for ensuring the `generate_vertex_ai_jsonl.py` script produces a compliant feed for Vertex AI Search for commerce.
