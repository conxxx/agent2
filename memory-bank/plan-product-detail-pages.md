# Plan for Product Detail Pages Implementation

**Objective:** Design and plan the implementation of individual product detail pages and update the product card links to point to these new pages, resolving the current 404 errors.

## Flow Diagram

```mermaid
graph TD
    A[User Clicks Product Card in Widget] --> B{Current Link: /SKU_PLANT_ROSEMARY_001};
    B --> C[Results in 404];

    D[Plan: New Product Detail Pages] --> E[Update Product Card Links];
    E --> F[User Clicks Product Card in Widget];
    F --> G{New Link: /products/SKU_PLANT_ROSEMARY_001};
    G --> H[Displays Product Detail Page];

    subgraph "Backend (app.py)"
        direction LR
        I1[Define New Flask Route: @app.route('/products/<string:product_id>')] --> I2[Function: product_detail_page(product_id)];
        I2 --> I3[Fetch Product from ecommerce.db by product_id];
        I3 -- Found --> I4[Render product_detail.html with product_data];
        I3 -- Not Found --> I5[Return 404 Error Page];
    end

    subgraph "Frontend (New: product_detail.html)"
        direction TB
        J1[Display Product Name (H1)];
        J2[Display Product Image];
        J3[Display Product Description];
        J4[Display Price];
        J5[Display 'Add to Cart' Button];
        J5 --> J6[JS to call /api/cart/modify/...];
        J7[Display Other Attributes];
        J8[Display Related Products (Placeholder/Basic)];
        J9[Inherit Layout/Style from index.html (Header, Footer)];
    end

    subgraph "Styling (style.css or new file)"
        direction TB
        K1[CSS for Product Detail Page Layout];
        K2[CSS for Product Information Sections];
        K3[CSS for 'Add to Cart' Button];
        K4[CSS for Related Products Section];
    end

    subgraph "Agent Tools (tools.py)"
        direction TB
        L1[Modify get_product_recommendations tool] --> L2[Construct product_url: f"/products/{product_id}"];
        L2 --> L3[Return this as product_url in payload];
    end

    subgraph "Image Handling"
        direction TB
        M1[Ensure image_url is /static/images/filename.png];
    end

    D --> I1;
    D --> J1;
    D --> K1;
    E --> L1;
    H --> M1;
```

## Detailed Plan

**1. Flask Route for Product Detail Page (`app.py`)**

*   **Route Definition:**
    *   A new Flask route will be defined:
        ```python
        @app.route('/products/<string:product_id>')
        def product_detail_page(product_id):
            # ... implementation ...
        ```
*   **Route Function Logic (`product_detail_page(product_id)`)**:
    1.  **Accept `product_id`**: The function will take `product_id` (a string) as a parameter from the URL.
    2.  **Fetch Product Details**:
        *   Connect to the `ecommerce.db` database using the existing `get_db()` helper function.
        *   Execute a SQL query to select all details for the product matching the given `product_id` from the `products` table. This will be similar to the logic in the existing `get_product_detail(product_id)` API endpoint but will be used for rendering an HTML page.
        *   Deserialize any JSON string attributes (e.g., `flower_color`, `landscape_use`, `recommended_soil_ids`) into Python lists, similar to how it's done in `get_product_detail(product_id)`.
    3.  **Render Template or 404**:
        *   **If Product Found**:
            *   Pass the fetched product details (as a dictionary or object) to a new HTML template, e.g., `product_detail.html`.
            *   The `render_template` function will be used: `return render_template('product_detail.html', product=product_data)`
        *   **If Product Not Found**:
            *   Return a 404 error. This can be achieved by rendering a dedicated `404.html` template or using `abort(404)`. For consistency with existing error handling, `return render_template('404.html'), 404` or a custom error page is preferable.

**2. HTML Template for Product Detail Page (New file: `cymbal_home_garden_backend/templates/product_detail.html`)**

*   **File Creation**: Create a new file named `product_detail.html` in the `cymbal_home_garden_backend/templates/` directory.
*   **Structure and Content**:
    *   **Extend Base Layout (Optional but Recommended)**: If a base template (`base.html` or similar) exists or can be created from `index.html` (sharing header, footer, common CSS/JS links), `product_detail.html` should extend it.
        ```html
        {% extends "base.html" %} <!-- Or appropriate base template -->
        {% block title %}{{ product.name }} - Cymbal Home Garden{% endblock %}
        {% block content %}
            <!-- Product detail content here -->
        {% endblock %}
        ```
    *   **Main Product Information Section**:
        ```html
        <div class="product-detail-container">
            <div class="product-image-column">
                <img src="{{ product.image_url if product.image_url else url_for('static', filename='images/placeholder.png') }}" alt="{{ product.name }}">
            </div>
            <div class="product-info-column">
                <h1>{{ product.name }}</h1>
                <p class="product-id-display">SKU: {{ product.id }}</p>
                <p class="price">{{ product.price | format_price }}</p> <!-- Assuming a Jinja filter for price formatting, or pass pre-formatted -->
                <div class="description">
                    <p>{{ product.description }}</p>
                </div>
                
                <!-- Display other attributes -->
                <div class="product-attributes">
                    <h3>Product Details:</h3>
                    <ul>
                        {% if product.plant_type %}<li><strong>Type:</strong> {{ product.plant_type }}</li>{% endif %}
                        {% if product.care_level %}<li><strong>Care Level:</strong> {{ product.care_level }}</li>{% endif %}
                        {% if product.light_requirements %}<li><strong>Light:</strong> {{ product.light_requirements }}</li>{% endif %}
                        {% if product.water_needs %}<li><strong>Water:</strong> {{ product.water_needs }}</li>{% endif %}
                        {% if product.soil_type %}<li><strong>Soil:</strong> {{ product.soil_type }}</li>{% endif %}
                        <!-- Add more attributes as needed, iterating through lists if applicable -->
                        {% if product.flower_color and product.flower_color|length > 0 %}
                            <li><strong>Flower Color:</strong> {{ product.flower_color|join(', ') }}</li>
                        {% endif %}
                        {% if product.attributes %} <!-- Generic attributes map -->
                            {% for key, value in product.attributes.items() %}
                                <li><strong>{{ key|replace("_", " ")|title }}:</strong> {{ value }}</li>
                            {% endfor %}
                        {% endif %}
                    </ul>
                </div>

                <button id="add-to-cart-pdp-btn" class="add-to-cart-btn" data-product-id="{{ product.id }}" data-product-name="{{ product.name }}">Add to Cart</button>
                <div id="add-to-cart-feedback" style="display:none; margin-top:10px;"></div>
            </div>
        </div>
        ```
    *   **"Add to Cart" Button Functionality**:
        *   The button will have `data-product-id` and `data-product-name` attributes.
        *   JavaScript (potentially in a new section in `cymbal_home_garden_backend/static/script.js` or a dedicated JS file for product pages) will handle the click event.
        *   On click, it will:
            1.  Get the `product_id` and `customer_id` (from `current-customer-id` span in header or a global JS variable).
            2.  Make a POST request to the `/api/cart/modify/<customer_id>` endpoint (or `/api/cart/<customer_id>/item`).
            3.  The payload should be: `{"items_to_add": [{"product_id": "THE_PRODUCT_ID", "quantity": 1}]}`.
            4.  Provide user feedback (e.g., "Added to cart!", update cart icon count).
    *   **Related Products Section (Placeholder/Basic)**:
        ```html
        <section class="related-products-section">
            <h2>Related Products</h2>
            <div class="product-grid recommended-grid" id="related-products-grid-pdp">
                <!-- Placeholder: Could be populated by JS if related product IDs are available in product_data -->
                <!-- Example: Iterate product.recommended_soil_ids, product.recommended_fertilizer_ids, product.companion_plants_ids -->
                <!-- For each ID, fetch minimal data via an API call or embed data if passed from Flask -->
                <p>Related products will be shown here.</p> 
            </div>
        </section>
        ```
        *   This could initially be a placeholder.
        *   Future enhancement: If `product_data` includes IDs for related items (e.g., `recommended_soil_ids`), JavaScript could fetch and display these, or Flask could pre-fetch and pass them to the template.

**3. CSS for Product Detail Page**

*   **File**: Rules can be added to `cymbal_home_garden_backend/static/style.css` or a new CSS file linked in `base.html` / `product_detail.html`.
*   **Key CSS Considerations**:
    *   **Layout**:
        *   `.product-detail-container`: Flexbox or Grid to arrange image and info columns.
            ```css
            .product-detail-container {
                display: flex;
                gap: 2rem;
                margin-top: 2rem;
                flex-wrap: wrap; /* Allow stacking on smaller screens */
            }
            .product-image-column {
                flex: 1 1 300px; /* Grow, shrink, base width */
                max-width: 400px;
            }
            .product-image-column img {
                width: 100%;
                height: auto;
                border-radius: 8px;
                border: 1px solid var(--current-card-border);
            }
            .product-info-column {
                flex: 2 1 400px; /* Grow more, shrink, base width */
            }
            ```
    *   **Typography & Spacing**:
        *   Styling for `h1` (product name), `.price`, `.description`, `.product-attributes ul/li`.
        *   Ensure clear visual hierarchy.
    *   **"Add to Cart" Button**: Style to be prominent, consistent with other buttons.
        ```css
        .product-info-column .add-to-cart-btn {
            padding: 0.8rem 1.5rem;
            font-size: 1.1rem;
            margin-top: 1.5rem;
        }
        ```
    *   **Related Products Section**: Style similar to the existing recommendations on `index.html`.
    *   **Responsiveness**: Ensure the layout adapts well to different screen sizes (e.g., image and info columns stack vertically on mobile).

**4. Update `product_url` Generation (`agents/customer-service/customer_service/tools/tools.py`)**

*   **Target Function**: `get_product_recommendations`
*   **Modification**:
    *   Currently, the tool fetches `product_data.get("product_uri")` and assigns it to `formatted_product['product_url']`.
    *   The key change is to ensure the value assigned to `formatted_product['product_url']` is the *actual path* to the new product detail page.
    *   If `product_data.get("id")` (which is the `product_id` like `SKU_PLANT_ROSEMARY_001`) is available, the URL should be constructed as:
        ```python
        # Inside the loop in get_product_recommendations
        product_id_for_url = product_data.get("id") # This should be the simple SKU
        if product_id_for_url:
            formatted_product["product_url"] = f"/products/{product_id_for_url}"
        else:
            formatted_product["product_url"] = "#" # Fallback if ID is missing
        ```
    *   The line `logger.info(f"Product ID {product_id} fetched product_uri: {formatted_product.get('product_url')}")` should reflect this new URL.
    *   The `product_uri` field from the database might still be the old SKU-only format, so we should rely on `product_data.get("id")` for constructing the new `/products/...` URL.

**5. Image URL Correction (Reiteration & Verification)**

*   **Backend Data**: Ensure that the `image_url` field in the `ecommerce.db` for each product, and consequently the `image_url` provided by the `/api/products/<product_id>` endpoint and used in `get_product_recommendations`, is a correctly resolvable path.
*   **Expected Format**: `/static/images/filename.png` (assuming images are stored in `cymbal_home_garden_backend/static/images/`).
*   **Action**: This is primarily a data integrity and backend API consistency check. The `product_detail.html` template will use `{{ product.image_url }}`. If this URL is incorrect, images will be broken. No specific code changes are planned for this point beyond ensuring the data source and API provide correct URLs.

**Plan Summary & Flow:**

1.  **Backend Route**: Create the `/products/<product_id>` Flask route in `app.py` to fetch product data and render `product_detail.html`.
2.  **HTML Template**: Develop `product_detail.html` to display all product information, including an "Add to Cart" button and potentially related products.
3.  **CSS Styling**: Add CSS rules to `style.css` for the new product detail page elements, ensuring consistency with the existing site theme.
4.  **Tool Update**: Modify `get_product_recommendations` in `tools.py` to generate `product_url` values in the format `/products/<product_id>`.
5.  **Image Path Verification**: Confirm that `image_url`s are correct throughout the system.