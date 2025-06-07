# Comprehensive Summary: Vertex AI Search for Commerce Documentation

This document provides a detailed summary of the Google Cloud Vertex AI Search for commerce documentation, intended to serve as a quick reference for development.

**Main Documentation URL:** `https://cloud.google.com/retail/docs/`

---

## 1. Overview and Implementation Steps
(Source: `https://cloud.google.com/retail/docs/overview`, Last Updated: 2025-04-21 UTC)

Vertex AI Search for commerce helps implement personalized search and recommendations using machine learning models. The same data (catalog and user events) is used for both search and recommendations.

**Key Implementation Phases:**

1.  **Project Setup:**
    *   Set up a Google Cloud project.
    *   Create authentication credentials (API key, OAuth token).

2.  **Data Ingestion:**
    *   **Product Catalog:**
        *   Can be imported via Google Merchant Center (for users with existing MC integration, though it has limitations like no facet support and no collections product type).
        *   Can be imported directly using `Products.create` (for individual items) or `Products.import` (for bulk, recommended for large catalogs). This offers more configurability.
    *   **User Events:**
        *   Track user actions (clicks, add-to-cart, purchases).
        *   Can be recorded using Google Tag Manager.
        *   Can be recorded by writing a custom tracking pixel and sending events in real-time.
        *   Events should be rejoined if uploaded before catalog import is complete.
    *   **Historical User Events:**
        *   Import past user events (from Google Analytics, Cloud Storage, BigQuery, or inline via `userEvents.import`) to accelerate model training.
        *   Sufficient training data is crucial for model accuracy.

3.  **Configuration and Modeling:**
    *   **Set up Monitoring and Alerts:** For data ingestion and service health.
    *   **Create Serving Configs, Models, and Controls:**
        *   A serving config associates a model and optional controls.
        *   For recommendations, choose a model type based on objectives (e.g., "Others you may like," "Frequently bought together") and tune options.
        *   For search, a default model is automatically created.
    *   **Model Training and Tuning:**
        *   Automatic for search once data thresholds are met.
        *   For recommendations, creating a model initiates training (2-5 days, longer for large datasets).

4.  **Testing and Evaluation:**
    *   **Preview and Test Serving Configs:** Ensure results are as expected. Use the "Evaluations" page in the console.
    *   **A/B Testing (Optional):** Compare performance with and without Vertex AI Search for commerce.
    *   **Evaluate Metrics:** Use the "Analytics" page to assess business impact.

**General Notes:**
*   Average integration time is in weeks, depending on data quality and quantity.
*   User event data requirements vary by model type and optimization objective.
    *   Terms of Service: Usage is under Google Cloud's T&Cs. Some data may be used for quality assurance with third-party vendors.

---

## 2. Product Catalog Import and Schema Guidelines
(Source: `https://cloud.google.com/retail/docs/upload-catalog`, Last Updated: 2025-05-05 UTC, Verified: 2025-05-10)

This section summarizes key guidelines for formatting product data for ingestion into Google Cloud Vertex AI Search for commerce.

### 2.1. Data Format for Import (via Cloud Storage)
*   **JSONL (JSON Lines):** Each product item must be a complete JSON object on a new line in the `.jsonl` file.

### 2.2. Minimum Required Product Fields
The following fields are mandatory for each product item:
*   `id`: (String) A unique identifier for the product.
*   `categories`: (String) The product category hierarchy. Example: `"Apparel & Accessories > Shoes"` or `"Home & Garden > Plants > Perennials"`.
*   `title`: (String) The name of the product.

### 2.3. Custom Attributes (`Product.attributes`)
Custom attributes allow for rich, product-specific data. They are defined within the `attributes` field, which is a map (object).
*   **Structure:** Each key in the `attributes` map is the custom attribute's name (e.g., `botanical_name`, `light_requirement`, `is_pet_friendly`).
*   **Value Format:** The value for each custom attribute *must* be an object containing either:
    *   `"text"`: An array of strings. Example: `{"vendor": {"text": ["vendor123", "vendor456"]}}`
    *   `"numbers"`: An array of numbers. Example: `{"npk_ratio": {"numbers": [10, 10, 10]}}`
*   **Boolean Custom Attributes:** There is no direct boolean type for custom attributes. They **must** be represented using the `"text"` format.
    *   Example for `true`: `{"is_pet_friendly": {"text": ["true"]}}`
    *   Example for `false`: `{"is_drought_tolerant": {"text": ["false"]}}`
    *   This is a critical formatting requirement.

### 2.4. Other Important Standard Fields (and their format from examples)
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

### 2.5. General Best Practices for Catalog Import
*   Keep catalog data up to date, ideally with daily imports.
*   Ensure high-quality data: avoid placeholder values and include as much optional information as possible.
*   Use a single currency per catalog if using Google Cloud console for revenue metrics.
*   Monitor import health and error reports.
*   For bulk import from Cloud Storage, each file must be 2 GB or smaller, up to 100 files per import request.
*   For inline import, max 5,000 items at a time (though the documentation also says "No more than 100 catalog items can be imported at a time" under "Inline import" limitations table - this might be a typo or context dependent, prefer the 5000 limit if using `ProductInlineSource` with multiple products).
*   Product levels (`primary` vs `variant`) are important and should be set carefully before initial import.
    *   Historical catalog data can be imported by setting the `expireTime` to a past timestamp and `availability` to `OUT_OF_STOCK`.

---

## 3. Record Real-Time User Events
(Source: `https://cloud.google.com/retail/docs/record-events`, Last Updated: 2025-04-24 UTC)

Real-time user events are crucial for generating personalized recommendations and search results. Recording many valid event types increases result quality.

### 3.1. Ways to Stream User Events
*   **JavaScript Pixel:** Embed a JS pixel on web pages.
*   **Google Analytics 4 (GA4) with Tag Manager:** Recommended method.
*   **Direct API Call (`userEvents.write`):** Send events from a backend server.
*   **Google Tag Manager (GTM):** Can be used standalone or with GA4.
*   **Server-Side Tagging:** Deploy a server-side GTM container.

### 3.2. Before You Begin
*   Google Cloud project set up with authentication.
*   Valid API key (for JS Pixel/GTM) or a service account with "Retail Editor" role (for direct API calls).
*   **Required Components:**
    *   **Attribution Token:** Captures first-time user interactions based on prior recommendations/search. See [Attribution Tokens](https://cloud.google.com/retail/docs/attribution-tokens).
    *   **Visitor IDs:** Required for all events. See [About user information](https://cloud.google.com/retail/docs/user-events#user-information).

### 3.3. Best Practices for Recording User Events
*   **Rejoin Events:** If events are recorded before catalog import completes, rejoin them using the API.
*   **Keep Catalog Up-to-Date:** Events for products not in the catalog are "unjoined" and not used for training.
*   **Provide Comprehensive Information:** Include as much detail as possible for each event type. Refer to [About user events](https://cloud.google.com/retail/docs/user-events) for schemas.
*   **Set Up Monitoring Alerts:** For event recording outages.
*   **Bulk Import Limits:** For user events, each file ≤ 2 GB, max 100 files per request. Import one day at a time.
*   **Accurate Timestamps:** Use `eventTime` in RFC 3339 format. Avoid identical timestamps for sequential events.
*   **Continuous Data:** Avoid gaps in user event data.
*   **Anonymize PII:** Use secure unique identifiers; redact PII like email/addresses.

### 3.4. Recording Methods Details

#### 3.4.1. JavaScript Pixel
*   Embed a script that pushes event data to `_gre` array.
*   Example provided for `detail-page-view`.
    ```javascript
    // Example structure
    var user_event = {
      "eventType" : "detail-page-view",
      "visitorId": "visitor-id", // Can be GA client ID
      "userInfo": { "userId": "user-id" },
      "attributionToken": "attribution-token",
      "productDetails": [ { "product": {"id": "123"} } ]
    };
    var _gre = _gre || [];
    _gre.push(['apiKey', 'your-api-key']);
    _gre.push(['logEvent', user_event]);
    _gre.push(['projectId', 'your-project-id']);
    // ... other config ...
    // Self-invoking function to load v2_event.js
    ```

#### 3.4.2. `userEvents.write` Method (Direct API)
*   Send a `POST` request to `https://retail.googleapis.com/v2/projects/PROJECT_ID/locations/global/catalogs/default_catalog/userEvents:write`.
*   Request body is the JSON `UserEvent` object.
*   Example `curl` command:
    ```bash
    curl -X POST \
         -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
         -H "Content-Type: application/json; charset=utf-8" \
         --data '{
             "eventType": "detail-page-view",
             "visitorId": "visitor0",
             "eventTime": "2020-01-01T03:33:33.000001Z",
             // ... other fields like productDetails, userInfo, attributes ...
        }' \
    "https://retail.googleapis.com/v2/projects/PROJECT_ID/locations/global/catalogs/default_catalog/userEvents:write"
    ```
*   Java client library example also available in docs.

#### 3.4.3. Google Analytics 4 (GA4)
*   Import GA4 user event data.
*   Ensure GA4 event reporting includes currency codes for purchase events and search queries for search events.
*   `search` events are constructed by combining `view_item_list` and `search_term` parameters from GA4.
*   Use `userEvents.collect` method with `prebuilt_rule=ga4_bq` and URL-encoded raw JSON data for the event.
    ```bash
    # Example GA4_EVENT JSON structure
    GA4_EVENT='{
         "event_timestamp": 1622994083878241,
         "event_name": "add_to_cart",
         "user_pseudo_id": "352499268.1622993559", // Maps to visitorId
         "items": [ { "item_id": "11", "price": 29.99, "quantity": 3 } ],
         "event_params": [ { "key": "currency", "value": { "string_value": "CAD" } } ],
         "user_id": "Alice"
    }'
    # API Call
    curl -G --data-urlencode "raw_json=${GA4_EVENT}" \
    "https://retail.googleapis.com/v2/projects/PROJECT_ID/locations/global/catalogs/default_catalog/userEvents:collect?key=API_KEY&prebuilt_rule=ga4_bq"
    ```

#### 3.4.4. Google Tag Manager (GTM)
*   Comprehensive setup involving:
    *   **Visitor ID Variable:** Create a GTM variable (e.g., from 1st party cookie `_ga` or custom JS) for `visitorId`.
    *   **Cloud Retail Tag:** Configure a "Cloud Retail" tag type in GTM.
        *   Provide API Key and Project Number.
        *   Select User Event Data Source (e.g., "Data Layer", "Variable, Cloud Retail", "Variable, Ecommerce").
        *   Overwrite `visitorId` field with the created variable.
    *   **Search Query Variable (if using search):** Create a GTM variable (URL, DOM element, or Custom JS) to capture search queries and attach it to the Cloud Retail tag.
    *   **Event Triggers:** Create triggers for all relevant user events (e.g., page views, add-to-cart clicks) and associate them with the Cloud Retail tag. Can reuse existing GA Ecommerce triggers.
    *   **Data Layer (`cloud_retail`):** If using "Variable, Cloud Retail" or "Data Layer" source, populate the `dataLayer` with a `cloud_retail` object matching the UserEvent schema.
        ```javascript
        // Example dataLayer push
        dataLayer.push({
          'cloud_retail': {
            'eventType': 'home-page-view',
            'visitorId': 'visitor_a', // Often overridden by GTM variable
            'userInfo': { 'userId': '789' },
            // ... other event details ...
          }
        });
        ```
*   **Preview and Debug:** Use GTM's preview mode and browser DevTools (Network tab, look for `userEvent:collect`) to test and debug tag firing and data.

#### 3.4.5. Server-Side Tagging
*   Deploy a server-side GTM container.
*   Cloud Retail server-side tag accepts similar parameters to the web tag.
*   Data source is a data stream from the Google tag in GA4 schema.

### 3.5. Monitoring and Viewing Events
*   Monitor event recording error rates via Cloud Monitoring alerts.
    *   View event integration metrics on the "Events" tab of the Search for commerce console "Data" page.

---

## 4. Setup Prerequisites
(Source: `https://cloud.google.com/retail/docs/setting-up`, Last Updated: 2025-04-17 UTC)

This section covers the initial setup steps for a new or existing Google Cloud project to use Vertex AI Search for commerce.

### 4.1. Project Creation and Billing
1.  **Create or Select a Google Cloud Project:**
    *   Use the Google Cloud console to create a new project or select an existing one.
2.  **Enable Billing:** Ensure billing is enabled for the Cloud project.

### 4.2. Enabling Vertex AI Search for Commerce API
1.  **Navigate to Vertex AI Search for commerce:** In the Google Cloud console.
2.  **Turn on API:**
    *   For new projects, click "Turn on API" on the "Set up Vertex AI Search for commerce" page.
    *   Both "Vertex AI Search for commerce" and "Recommendations AI" should show as "On".
3.  **Accept Data Use Terms:** Read and accept the "Vertex AI Search for Industry terms for data use".
4.  **Choose Services:**
    *   Decide if you want to use "recommendations only" or turn on "search" as well.
    *   Click "Get Started" to proceed.

### 4.3. Initial Configuration (Post-Enablement)
The console will display panels to guide initial configuration:
*   **Data > Catalog:** For importing product catalog.
*   **Data > Events:** For importing historical user events.
*   **Serving configs:** For creating and managing serving configurations.

#### 4.3.1. Importing Product Catalog (Initial)
Methods include:
*   **Merchant Center Sync:** Link an existing Merchant Center account.
*   **Cloud Storage:** Upload JSONL files to a GCS bucket.
*   **BigQuery:** Import from a BigQuery table.
    *   Detailed steps for each are provided in the "Import catalog information" documentation (summarized in Section 2 of this document).

#### 4.3.2. Importing Historical User Events (Initial)
Methods include:
*   **Cloud Storage:** Upload JSON files.
*   **BigQuery:** Import from a BigQuery table (supports GA4, GA360, or Retail User Events Schema).
    *   Detailed steps for each are provided in the "Importing historical user events" documentation.

#### 4.3.3. Creating a Serving Config (Initial)
*   A serving config associates a model and controls for search or recommendations.
*   Steps:
    1.  Click "Create serving config".
    2.  Choose the product (e.g., "Search").
    3.  Provide a name and optional ID.
    4.  Choose whether to enable dynamic faceting (for search).
    5.  Choose or create serving controls.

### 4.4. Creating an API Key
*   Required if using JavaScript pixel or GTM tag for capturing user events via `userEvents.Collect`.
*   Steps:
    1.  Go to Google Cloud console > Credentials page.
    2.  Select your project.
    3.  Click "Create credentials" > "API key".
    4.  **Important:** Do *not* add website application restrictions initially, as some privacy settings might not pass the referrer URL.
    5.  Note the generated API key.
    6.  For security, add an API restriction to the key, limiting its access to the Vertex AI Search for commerce service (`https://retail.googleapis.com/*`).

### 4.5. Turning Off Features
*   **Turn off Search Features:** Submit a support ticket (Category: Machine Learning, Component: Vertex AI Search for commerce: search & browse, Subcomponent: Account Administration & Billing).
*   **Turn off Vertex AI Search for commerce (entire service):**
    1.  Go to "Vertex AI Search for Retail API/Service Details" page in console.
    2.  Click "Disable API".

---

## 5. Create Recommendation Models
(Source: `https://cloud.google.com/retail/docs/create-models`, Last Updated: 2025-04-17 UTC)

This section details the process of creating, training, and managing recommendation models.

### 5.1. Introduction
*   New recommendation models are needed when you want to use a new recommendation type.
*   Sufficient user event data is required for training.
*   Serving configs are created for models to request predictions.
*   Up to 20 models per project, 10 active. Max 5 model operations (create, delete, pause, resume) per minute.

### 5.2. Before Creating a Model
*   Review [model types](https://cloud.google.com/retail/docs/models#model-types) (e.g., "Recommended for You", "Others You May Like", "Frequently Bought Together", "Page-Level Optimization", "Similar Items", "Buy it Again") and [business objectives](https://cloud.google.com/retail/docs/models#opt-obj) (e.g., Click-through rate (CTR), Conversion rate (CVR), Revenue per session).
*   Decide model tuning frequency (every three months or manual).
*   Ensure data requirements are met (varies by model type, see detailed table in docs).
*   For Page-Level Optimization models:
    *   Requires existing trained recommendation serving configs.
    *   Requires event recording for `detail-page-view` and the page type being optimized (e.g., `home-page-view`). `purchase` and `add-to-cart` also recommended. CVR objective requires `add-to-cart`.
    *   Continue querying the model post-creation for impressions to improve it.

### 5.3. Creating a Recommendation Model
Can be done via Google Cloud Console or `models.Create` API method.

**API `Models.create` Request Body Example:**
```json
{
  "name": "FULL_MODEL_NAME", // e.g., projects/PROJECT_NUMBER/locations/global/catalogs/default_catalog/models/my-fbt-model
  "displayName": "DISPLAY_NAME",
  "trainingState": "TRAINING_STATE", // e.g., "TRAINING", "PAUSED"
  "type": "MODEL_TYPE", // e.g., "frequently-bought-together", "others-you-may-like"
  "optimizationObjective": "OPTIMIZATION_OBJECTIVE", // e.g., "CTR", "CVR"
  "periodicTuningState": "TUNING_STATE", // e.g., "PERIODIC_TUNING_ENABLED", "PERIODIC_TUNING_DISABLED"
  "filteringOption": "FILTERING_STATE", // e.g., "RECOMMENDATIONS_FILTERING_ENABLED", "RECOMMENDATIONS_FILTERING_DISABLED" (Public Preview)
  "modelTypeConfig": { // Specific to model type, e.g., for FBT
    "contextProductsType": "CONTEXT_PRODUCTS_TYPE" // "SINGLE_CONTEXT_PRODUCT" or "MULTIPLE_CONTEXT_PRODUCTS"
  }
}
```
*   **Path for API call:** `https://retail.googleapis.com/v2beta/projects/PROJECT_NUMBER/locations/global/catalogs/default_catalog/models` (Note: `v2beta` might be used for newer features like `modelTypeConfig`). The main docs often refer to `v2`.

**Console Steps:**
1.  Go to Models page.
2.  Click "Create model".
3.  Enter name, choose recommendation type.
4.  For Page-Level Optimization: define page type, restriction for similar serving configs, panels (ID, selectable serving configs, default serving config).
5.  Choose business objective.
6.  For FBT: choose context products type.
7.  Review data requirements.
8.  Choose tuning frequency.
9.  Choose whether to auto-generate tags for filtering (Public Preview, increases training time/cost).
10. Click "Create".

### 5.4. Model Training
*   Initial training and tuning take 2-5 days (longer for large datasets).
*   Serving configs can be created before training completes but will serve "dry run" predictions.

### 5.5. Requirements for Creating a New Model (Process Summary)
1.  Import catalog and keep it updated.
2.  Record user events (follow best practices).
3.  Identify model type and optimization objective.
4.  Determine and meet user event data requirements.
5.  Import historical user events if needed.
6.  Create model and serving configs.
7.  Model training starts.
8.  Confirm model works using prediction preview.
9.  (Optional) Create A/B experiment.

### 5.6. Model Type Minimum Data Requirements (Examples)
(A detailed table is in the documentation. Below are a few key examples.)
*   **Recommended for You (CTR):**
    *   Events: `detail-page-view`, `home-page-view`.
    *   Min data: 7 days of `detail-page-view` events in last 90 days AND 10 occurrences/item avg. OR 60 days of `detail-page-view` events. 100 unique items for `detail-page-view`. 10,000 `detail-page-view` events. Similar for `home-page-view`.
    *   Window: 3 months.
*   **Frequently Bought Together (Revenue per session):**
    *   Events: `purchase-complete`.
    *   Min data: 10 occurrences/item avg. (1-year window) OR 90 days of `purchase-complete` events. 100 unique items for `purchase-complete`. 1,000 `purchase-complete` events.
    *   Window: 3 months (recommend daily event uploads).
*   **Similar Items:**
    *   Events: None required.
    *   Min data: 100 product SKUs in some branch.
*   **Page-Level Optimization:** Data requirements depend on the models selected as options for its panels.
*   **Buy it Again:**
    *   Events: `purchase-complete`.
    *   Min data: Similar to FBT but with a 90-day window for event counts. 100 product SKUs in branch.

**General Note on Data:** Use real user events and catalog data. Synthetic data doesn't build good models.

---

## 6. Get Recommendations (Predictions)
(Source: `https://cloud.google.com/retail/docs/predict`, Last Updated: 2025-05-05 UTC)

This section explains how to request product recommendations for users based on their events and activity.

### 6.1. Before You Begin
*   Ensure you have a trained and tuned recommendation model.
*   Have one or more active serving configs associated with the model.
*   New products and user events can take up to 48 hours to be reflected in the model.
*   **Important:** Never cache personalized results for one user and show them to another.

### 6.2. Evaluate Recommendations (Preview)
*   Before site integration, preview prediction results to confirm model and serving config behavior.
*   Use the **Evaluate** page in the Search for commerce console:
    1.  Select the "Recommendations" tab.
    2.  Choose the serving config to preview.
    3.  Optionally, enter a `visitorId` for user-specific previews.
    4.  If the model type requires context (e.g., "Others You May Like" based on a product view), add associated item IDs.
    5.  Click "Prediction preview".

### 6.3. Get a Recommendation (API Call)
*   Make a `POST` request to the `predict` REST method:
    `https://retail.googleapis.com/v2/projects/PROJECT_ID/locations/global/catalogs/default_catalog/servingConfigs/SERVING_CONFIG_ID:predict`
*   The service account needs "Retail Viewer" role or higher.
*   **Request Body Key Fields (`PredictRequest`):**
    *   `userEvent`: (Required) A `UserEvent` object representing the user action that initiated the recommendation request (e.g., `detail-page-view` if on a product page). This event is *not* recorded by this call; it's for context only. Record it separately.
        *   `eventType`: (String) e.g., "detail-page-view".
        *   `visitorId`: (String) Required.
        *   `userInfo`: (Object, Optional) Contains `userId`, `ipAddress`, `userAgent`.
        *   `productDetails`: (Array, if applicable) e.g., for `detail-page-view`, the product being viewed.
    *   `filter`: (String, Optional) A filter string to narrow down results. See [Filter recommendations](https://cloud.google.com/retail/docs/filter-recs).
    *   `params`: (Object, Optional) Key-value pairs for per-request settings.
        *   `priceRerankLevel`: (String) e.g., "price-rerank-enabled", "price-rerank-disabled". Overrides serving config setting.
        *   `diversityLevel`: (String) e.g., "diversity-low", "diversity-medium", "diversity-high". Overrides serving config setting.
    *   `validateOnly`: (Boolean, Optional) If true, validates the request without returning predictions.
    *   `pageSize`: (Integer, Optional) Number of recommendations to return.
    *   `pageToken`: (String, Optional) For pagination.
    *   `labels`: (Map, Optional) Key-value labels for the request, useful for analytics.

*   **Example `curl` for `predict`:**
    ```bash
    curl -X POST \
        -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
        -H "Content-Type: application/json; charset=utf-8" \
        --data '{
                  "userEvent": {
                      "eventType": "detail-page-view",
                      "visitorId": "VISITOR_ID",
                      "productDetails": [{"product": {"id": "PRODUCT_ID"}}]
                  }
                }' \
    https://retail.googleapis.com/v2/projects/PROJECT_ID/locations/global/catalogs/default_catalog/servingConfigs/SERVING_CONFIG_ID:predict
    ```

*   **Response (`PredictResponse`):**
    *   `results`: An array of `PredictResponse.PredictionResult` objects, each usually containing just the `id` of the recommended product.
        ```json
        {
          "results": [{"id": "sample-id-1"}, {"id": "sample-id-2"}],
          "attributionToken": "sample-atr-token"
        }
        ```
    *   `attributionToken`: (String) **Crucial.** This token must be associated with any URL served as a result of this prediction and returned with subsequent user events related to those recommendations. See [Attribution Tokens](https://cloud.google.com/retail/docs/attribution-tokens).
    *   `missingIds`: (Array of Strings, Optional) IDs of products in the request that were not found in the catalog.
    *   `validateOnly`: (Boolean) True if the request was a validation-only request.

### 6.4. Features

#### 6.4.1. Price Reranking
*   Orders recommended products with similar probability by price (highest first). Relevance is still a primary factor.
*   Can be set at the serving config level or per-prediction request via `PredictRequest.params.priceRerankLevel`.

#### 6.4.2. Recommendation Diversity
*   Affects whether results from a single request are from different product categories.
*   Can be set at the serving config level or per-prediction request via `PredictRequest.params.diversityLevel`.

#### 6.4.3. Recommendation Filters
*   Use the `filter` field in `PredictRequest` to narrow results based on product attributes (e.g., `filter="filterOutOfStock"`, `filter="tag=\"sale\""`).
*   Refer to [Filter recommendations](https://cloud.google.com/retail/docs/filter-recs) for syntax.

### 6.5. Prediction Calls with Page-Level Optimization Models
*   **Initial Call:** Make a prediction call to the serving config containing the Page-Level Optimization model. The response is a sorted list of serving config IDs (one for each panel defined in the PLO model).
*   **Subsequent Calls:** For each panel, make another prediction call using the serving config ID returned by the PLO model for that panel. This response will contain the actual product recommendations for that panel.
*   Price reranking, diversity, and filters are not available for the initial call to a PLO model serving config.

### 6.6. Monitoring and Troubleshooting
*   Set up alerts for prediction errors.
*   See [Monitor and troubleshoot](https://cloud.google.com/retail/docs/error-reporting).

---

## 7. Manage User Events
(Source: `https://cloud.google.com/retail/docs/manage-user-events`, Last Updated: 2025-05-05 UTC)

This section covers viewing, rejoining, and removing user events. For recording real-time events or importing historical events, see their respective documentation sections.

### 7.1. View Aggregated User Event Information
*   Event integration metrics can be viewed on the **Events** tab of the Search for commerce console **Data** page.
*   Shows events written or imported in the last year.
*   Metrics can take up to 24 hours to appear after ingestion.

### 7.2. Rejoin User Events
*   **Purpose:** Links specified user events with the latest version of the product catalog. This is particularly useful for "unjoined" events (events associated with a product not in the catalog at ingestion time) or to correct events joined with an outdated catalog.
*   **API Method:** `POST` request to `https://retail.googleapis.com/v2/projects/PROJECT_ID/locations/global/catalogs/default_catalog/userEvents:rejoin`
*   **Permissions:** Requires "Retail AI Admin" IAM role.
*   **Duration:** Can take hours or days to complete.
*   **Request Body (`RejoinUserEventsRequest`):**
    *   `userEventRejoinScope`: (String) Specifies which events to rejoin.
        *   `USER_EVENT_REJOIN_SCOPE_UNSPECIFIED`: Default. Rejoins both joined and unjoined events.
        *   `JOINED_EVENTS`: Rejoins only events that were previously joined.
        *   `UNJOINED_EVENTS`: Rejoins only unjoined events.
*   **Example `curl` for rejoining unjoined events:**
    ```bash
    curl -X POST \
        -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
        -H "Content-Type: application/json; charset=utf-8" \
        --data '{
         "userEventRejoinScope": "UNJOINED_EVENTS"
         }' \
        "https://retail.googleapis.com/v2/projects/PROJECT_ID/locations/global/catalogs/default_catalog/userEvents:rejoin"
    ```
*   **Response:** An operation object. The status can be checked by GETting the operation URL. A successful rejoin response includes `rejoinedUserEventsCount`.

### 7.3. Remove User Events (Purge)
*   **General Recommendation:** Generally, leave user events in place. Purging is not recommended. Consider creating a new project for a full reset.
*   **Purpose:** To remove improperly recorded user events.
*   **API Method:** `POST` request to `https://retail.googleapis.com/v2/projects/PROJECT_ID/locations/global/catalogs/default_catalog/userEvents:purge`
*   **Duration:** Can take several days.
*   **Request Body (`PurgeUserEventsRequest`):**
    *   `filter`: (String) A filter string to specify which events to remove. Supports filtering on `eventTime`, `eventType`, `visitorID`, and `userID`.
    *   `force`: (Boolean)
        *   `false` (default): Dry run. Returns the count of events that *would* be deleted without actually deleting them.
        *   `true`: Actually deletes the events. **Use with caution as this cannot be undone.**
*   **Filter String Syntax:**
    *   `eventTime > "YYYY-MM-DDTHH:MM:SSZ"` or `eventTime < "YYYY-MM-DDTHH:MM:SSZ"` (RFC 3339 Zulu time). Can be specified once or twice for a contiguous block.
    *   `eventType = "event-type-name"`
    *   `visitorID = "some-visitor-id"`
    *   `userID = "some-user-id"`
    *   Multiple restrictions are ANDed.
    *   Example: `filter="eventTime > \"2019-12-23T18:25:43.511Z\" eventTime < \"2019-12-23T18:30:43.511Z\" eventType = add-to-cart"`
*   **Example `curl` for dry run:**
    ```bash
    curl -X POST \
      -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
      -H "Content-Type: application/json; charset=utf-8" \
      --data '{
        "filter":"eventTime > \"2019-12-23T18:25:43.511Z\" eventTime < \"2019-12-23T18:30:43.511Z\"",
        "force":"false"
      }' \
      "https://retail.googleapis.com/v2/projects/PROJECT_ID/locations/global/catalogs/default_catalog/userEvents:purge"
    ```
    *   **Response:** An operation object. A successful purge response includes `purgedEventsCount`.

---

## 8. Manage Catalog Information
(Source: `https://cloud.google.com/retail/docs/manage-catalog`, Last Updated: 2025-05-01 UTC)

This section describes how to manage product information after the initial catalog import. While full catalog re-imports are common for updates, individual product management is also possible.

### 8.1. CRUD Operations for Individual Products
These operations are typically done via the REST API.

#### 8.1.1. Create a Product
*   **Method:** `POST` to `https://retail.googleapis.com/v2/projects/PROJECT_NUMBER/locations/global/catalogs/default_catalog/branches/0/products?productId=PRODUCT_ID`
*   **Request Body:** A `Product` JSON object (e.g., `{"title": "PRODUCT_TITLE", "categories": "CATEGORY"}`).
*   **Response:** The created `Product` object.
*   **API Reference:** `products.create`

#### 8.1.2. Retrieve (Get) a Product
*   **Method:** `GET` to `https://retail.googleapis.com/v2/projects/PROJECT_NUMBER/locations/global/catalogs/default_catalog/branches/0/products/PRODUCT_ID`
*   **Response:** The `Product` object.
*   **API Reference:** `products.get` (though the doc shows the endpoint for `list` or `get` by name)

#### 8.1.3. Update a Product
*   **Method:** `PATCH` to `https://retail.googleapis.com/v2/projects/PROJECT_NUMBER/locations/global/catalogs/default_catalog/branches/0/products/PRODUCT_ID?updateMask=title,description`
*   **Request Body:** A partial `Product` JSON object containing fields to update.
*   `updateMask`: (Query parameter) Comma-separated list of fields to update (e.g., `title`, `priceInfo.price`).
*   **Response:** The updated `Product` object.
*   **API Reference:** `products.patch`

#### 8.1.4. Delete a Product
*   **Method:** `DELETE` to `https://retail.googleapis.com/v2/projects/PROJECT_NUMBER/locations/global/catalogs/default_catalog/branches/0/products/PRODUCT_ID`
*   **Recommendation:** Instead of deleting, set product `availability` to `OUT_OF_STOCK` to preserve historical data for model quality. Deleting products referenced by user events can cause issues.
*   **API Reference:** `products.delete`

### 8.2. View Aggregated Catalog Information
*   Use the **Catalog** tab on the **Data** page in the Search for commerce console.
*   Allows viewing aggregated information and previewing uploaded products.

### 8.3. Assess Catalog Data Quality
*   Use the **Data quality** page in the Search for commerce console.
*   Helps identify if catalog data needs updates to improve search results and unlock performance tiers.
*   Refer to [Unlock search performance tiers](https://cloud.google.com/retail/docs/data-quality) and [Catalog quality metrics](https://cloud.google.com/retail/docs/catalog#quality-metrics).

### 8.4. Change Product Types
*   Product types: `TYPE_UNSPECIFIED`, `PRIMARY`, `VARIANT`, `COLLECTION`.
*   If a product's type changes or was incorrect, it must be deleted and then re-created with the updated type.

### 8.5. Change Product Level Configuration (Primary/Variant for Merchant Center Imports)
*   Applies when product levels (primary/variant) for Merchant Center imports need correction.
*   Requires "Retail Admin" IAM role.
*   **Process:**
    1.  Ensure no imports are active.
    2.  Delete all product items from the catalog branch (`products.delete`). The catalog must be empty.
    3.  Re-import data, correctly setting the product level configuration during the import process (refer to "Import Catalog Information" docs).
    4.  Finish importing the new catalog.
    5.  Tune all existing models manually via the Models page in the console.

---

## 9. Monitor and Troubleshoot (Error Reporting)
(Source: `https://cloud.google.com/retail/docs/error-reporting`, Last Updated: 2025-04-17 UTC)

This section describes how to monitor errors from data imports, API operations, and how to troubleshoot them.

### 9.1. See Aggregated Integration Errors
*   **Monitoring Page:** Use the **Monitoring** page in the Search for commerce console to see aggregated errors for catalog, user events, predictions, search, and models.
*   Displays up to 100 errors per import file.
*   Filter by time period and error type.
*   Click individual errors to see logs in Cloud Logging, including request/response payloads.

### 9.2. See Status for Specific Integration Operations
*   **Activity Status Window:**
    1.  Go to the **Data** page in the console.
    2.  Click **Activity status**.
    *   Shows status of long-running operations (catalog, user events, controls).
    *   Click "View logs" for an operation to inspect its logs in Cloud Logging.

### 9.3. View Logs in Cloud Logging
*   **Direct Access:** Go to Logs Explorer in Google Cloud console.
    *   Requires "Logs Viewer" (`roles/logging.viewer`) IAM role.
    *   Select your project.
    *   Filter by Resource: "Consumed API" > "Cloud Retail".
*   Provides detailed logs for API requests and responses.

### 9.4. Configure Logging (`LoggingConfig`)
*   Control which service logs are written to Cloud Logging (severity levels, on/off, overrides for specific services).
*   Requires "Vertex AI Search for commerce editor" role.
*   Can be configured via Console (**Monitoring** page > **Logging configuration**) or API (`LoggingConfig` resource).

#### 9.4.1. Logging Levels
*   `LOGGING_DISABLED`: No logs.
*   `LOG_ERRORS_AND_ABOVE`: Errors only.
*   `LOG_WARNINGS_AND_ABOVE`: (Default) Errors and warnings.
*   `LOG_ALL`: All logs, including `INFO` (successful requests).

#### 9.4.2. Sampling Rate for Successful Logs
*   If `logging_level` is `LOG_ALL`, `info_log_sample_rate` (float >0 to <=1) can be set to sample successful logs instead of logging all of them. Default is 1 (log all).

#### 9.4.3. Service-Level Configurations
*   Override global logging settings for specific services (e.g., `CatalogService`, `UserEventService`, `PredictionService`).
*   API method: `loggingConfig.Patch`
    *   `default_log_generation_rule`: Sets global rule.
    *   `service_log_generation_rules`: Array to specify rules for individual services.
    ```json
    // Example PATCH request body
    {
      "name": "projects/PROJECT_ID/loggingConfig",
      "default_log_generation_rule": {"logging_level": "LOG_ERRORS_AND_ABOVE"},
      "service_log_generation_rules": [
        {
          "service_name": "UserEventService",
          "log_generation_rule": {
            "logging_level": "LOG_ALL", "info_log_sample_rate": "0.1"
          }
        }
      ]
    }
    ```

### 9.5. Common Error Types
*   `MISSING_FIELD`: Required field not set (e.g., catalog item missing title).
*   `INVALID_TIMESTAMP`: Timestamp invalid or wrongly formatted.
*   `INCORRECT_JSON_FORMAT`: Malformed JSON.
*   `INVALID_LANGUAGE_CODE`: Incorrect language code format.
*   `INVALID_RESOURCE_ID`: Non-existent ID in resource name (e.g., `catalog_id`).
*   `RESOURCE_ALREADY_EXISTS`: Tried to create an existing resource.
*   `INVALID_API_KEY`: API key doesn't match project.
*   `INSUFFICIENT_PERMISSIONS`: Missing IAM permission.
*   `UNJOINED_WITH_CATALOG`: Request includes a product ID not in the catalog.
*   `BATCH_ERROR`: Multiple errors in a batch request.
*   `INACTIVE_RECOMMENDATION_MODEL`: Queried an inactive model.
*   `ABUSIVE_ENTITY`: Visitor/User ID sent too many events in a short time.
*   `FILTER_TOO_STRICT`: Prediction filter blocked all results. May return generic popular items unless `strictFiltering: false`.

### 9.6. View Data Load Metrics
*   **Monitoring Page:** Error metrics for catalog and user event ingestion.
*   **Data Page (Catalog & Event tabs):** Aggregated stats, preview products, visualize user event metrics (total, unjoined, period comparisons).
*   **Data Quality Page:** Metrics on product/event data quality for search, helps unlock performance tiers.

### 9.7. Unjoined Events
*   Events/requests referring to products not in the catalog at the time of ingestion/request.
*   Logged but not used for model enhancement. Aim for a very low percentage.
*   View unjoined user event percentage in the **Event** tab on the **Data** page.

### 9.8. API Errors and Activity
    *   **Monitoring Page:** Graph of API errors over time by method name. Visualizations of traffic, errors, latency by API method.

---

## 11. REST API Reference Overview
(Source: `https://cloud.google.com/retail/docs/reference/rest`, Last Updated: 2025-03-08 UTC)

This section provides an overview of the Vertex AI Search for commerce REST API structure. The API allows for direct interaction with the service for managing resources and operations.

### 11.1. API Versions and Discovery
*   The API is versioned, with `v2`, `v2alpha`, and `v2beta` being common.
    *   `v2` is generally the stable version.
    *   `v2alpha` and `v2beta` offer access to newer features that might still be under development or subject to change.
*   **Service Endpoint:** `https://retail.googleapis.com`
*   **Discovery Documents:** Available for each version (e.g., `https://retail.googleapis.com/$discovery/rest?version=v2`) for machine-readable API specification.

### 11.2. Key Resource Categories
The REST API is organized around resources. Common high-level resources include:
*   **`projects`**: Top-level project configuration (e.g., `alertConfig`, `loggingConfig`).
*   **`projects.locations.catalogs`**: Manages catalogs, default branches, attribute configurations, completion configurations, and analytics.
    *   **`projects.locations.catalogs.branches.products`**: Core resource for managing products within a catalog branch (create, get, list, patch, delete, import, export, setInventory, add/remove local inventories).
    *   **`projects.locations.catalogs.userEvents`**: For managing user events (collect, import, write, purge, rejoin).
    *   **`projects.locations.catalogs.models`**: For creating and managing recommendation models (create, get, list, patch, pause, resume, tune).
    *   **`projects.locations.catalogs.servingConfigs`**: For managing serving configurations that link models/controls to placements (create, get, list, patch, delete, predict, search, add/remove controls).
    *   **`projects.locations.catalogs.controls`**: For managing controls that influence search/recommendation results.
    *   **`projects.locations.catalogs.operations` / `projects.locations.catalogs.branches.operations`**: For checking the status of long-running operations.
    *   **`projects.locations.catalogs.placements`**: Alternative endpoint for `predict` and `search` using a placement ID (often tied to a serving config).

### 11.3. Common API Interaction Patterns
*   **Resource Names:** Resources are identified by a path, e.g., `projects/PROJECT_ID/locations/global/catalogs/default_catalog/branches/0/products/PRODUCT_ID`.
*   **Standard Methods:**
    *   `GET`: Retrieve a resource.
    *   `POST`: Create a resource or invoke a custom method (like `import`, `predict`, `search`, `rejoin`).
    *   `PATCH`: Update a resource (often with an `updateMask` to specify fields).
    *   `DELETE`: Delete a resource.
    *   `LIST`: List resources under a parent.
*   **Long-Running Operations (LROs):** Many operations like import, export, model tuning are LROs. The initial API call returns an operation name, which can then be polled (e.g., via `projects.locations.catalogs.operations.get`) until `done: true`.

### 11.4. Navigating the Full Reference
*   The main REST reference page (`https://cloud.google.com/retail/docs/reference/rest`) provides direct links to the detailed documentation for each resource and method under each API version (`v2`, `v2alpha`, `v2beta`).
*   Developers should consult these detailed pages for specific request/response bodies, query parameters, and field descriptions when implementing API calls. For example, to find details for creating a product, one would navigate to the `v2.projects.locations.catalogs.branches.products` resource and look for the `create` method.

This overview serves as a map to the extensive REST API. For specific endpoint details, always refer to the linked pages for the relevant API version.

---

## 12. RPC API Reference Overview
(Source: `https://cloud.google.com/retail/docs/reference/rpc`, Last Updated: 2025-03-08 UTC)

This section provides an overview of the Vertex AI Search for commerce RPC (Remote Procedure Call) API structure, typically used with gRPC.

### 12.1. Service Name
*   The primary service name for creating RPC client stubs is `retail.googleapis.com`.

### 12.2. API Versions
*   The RPC reference also covers multiple API versions, primarily `v2`, `v2alpha`, and `v2beta`.
*   Developers should choose the version appropriate for their needs (stability vs. access to newer features).

### 12.3. Key Services
The RPC API is organized into services, each grouping related methods. The main services correspond closely to the functionalities offered by the platform:

*   **`google.cloud.retail.v2.AnalyticsService`**: For exporting analytics metrics.
*   **`google.cloud.retail.v2.CatalogService`**: Manages catalogs, attributes configuration, completion configuration, and default branches.
*   **`google.cloud.retail.v2.CompletionService`**: For autocompletion features (e.g., `CompleteQuery`, `ImportCompletionData`).
*   **`google.cloud.retail.v2.ControlService`**: Manages controls for search and recommendations.
*   **`google.cloud.retail.v2.ModelService`**: For creating, managing, and tuning recommendation models.
*   **`google.cloud.retail.v2.PredictionService`**: For getting recommendation predictions (`Predict` method).
*   **`google.cloud.retail.v2.ProductService`**: For managing individual products (CRUD operations, inventory updates, import/export).
*   **`google.cloud.retail.v2.SearchService`**: For performing searches (`Search` method).
*   **`google.cloud.retail.v2.ServingConfigService`**: Manages serving configurations.
*   **`google.cloud.retail.v2.UserEventService`**: For ingesting and managing user events.
*   **`google.cloud.retail.v2alpha.*` and `google.cloud.retail.v2beta.*`**: These namespaces contain services and methods for alpha and beta features, respectively. They often mirror the `v2` services but may include additional or modified functionalities (e.g., `BranchService`, `ConversationalSearchService`, `MerchantCenterAccountLinkService` in `v2alpha`).
*   **`google.longrunning.Operations`**: Standard service for managing long-running operations (like imports, model tuning).
*   **`google.cloud.location.Locations`**: For getting and listing supported locations.

### 12.4. Using the RPC Reference
*   The main RPC reference page (`https://cloud.google.com/retail/docs/reference/rpc`) lists each service and its methods for each API version.
*   Unlike the REST reference which links to detailed pages for each resource, the RPC reference page itself contains the list of methods for each service.
*   For detailed message definitions (request/response protobufs) and specific gRPC service definitions, developers would typically refer to the `.proto` files provided by Google or the generated code from client libraries.

This overview provides a structural understanding of the RPC API. For specific method signatures and message types, developers using gRPC would consult the relevant `.proto` definitions or the client library documentation for their chosen language.

---

## 13. Pricing
(Source: `https://cloud.google.com/retail/docs/pricing`)

This section outlines the pricing structure for Vertex AI Search for commerce. Prices are listed in USD.

### 13.1. Search Charges
*   **Charged Operations:** Only requests for search or browse results via the `SearchService.Search` method incur charges.
*   **No Charge For:** Importing/managing user events or catalog information, using the pretrained Recommendations LLM.
*   **Rate:** $2.50 per 1000 search and browse queries.

**Example Calculation:**
*   15 million search queries + 10 million browse queries = 25 million total queries.
*   Cost = 25,000 (thousand queries) * $2.50/thousand = $62,500.

### 13.2. Recommendations Charges
*   **Free Trial:** $600 free credits, expiring six months after signup. Credits apply to the billing account.
*   **Charged Operations:**
    *   Training (per node per hour): Charged daily if model is actively training or resumed. No charge if paused/deleted.
    *   Tuning (per node per hour): Charged after successful tune completion. Partial charge if paused/deleted during tuning.
    *   Prediction requests via `PredictionService.Predict` method.
*   **No Charge For:** Importing/managing user events or catalog information.

**Prediction Request Pricing (per 1000 predictions, per month):**
*   Up to 20,000,000: $0.27
*   Next 280,000,000: $0.18
*   After 300,000,000: $0.10

**Training and Tuning Pricing:**
*   Rate: $2.50 per node per hour.

**Example Calculation (High Volume):**
*   1 billion prediction requests:
    *   20M @ $0.27/k = $5,400
    *   280M @ $0.18/k = $50,400
    *   700M @ $0.10/k = $70,000
    *   Subtotal Predictions: $125,800
*   Training: 500 node hours * $2.50 = $1,250
*   Tuning (monthly avg.): 100 node hours * $2.50 = $250
*   Total: $127,300

### 13.3. Google Cloud Observability Charges
*   Vertex AI Search for commerce logs errors to Google Cloud Observability (formerly Stackdriver).
*   Charges are by GiB of logs stored (retained for one month).
*   **Free Tier:** First 50 GiB of logs per month per project is free.
*   **Rate:** $0.50 per GiB after the free tier.
*   A GiB is approximately 200,000 recommendations errors (depends on JSON payload size).

### 13.4. General
*   If paying in a currency other than USD, prices on Cloud Platform SKUs apply.
*   A pricing calculator is available on the Google Cloud website.
    *   Custom quotes can be requested from Google Cloud sales.

---

## 14. Quotas and Limits
(Source: `https://cloud.google.com/retail/docs/quotas`, Last Updated: 2025-04-17 UTC)

This section provides information about default quotas and operational limits for Vertex AI Search for commerce.

### 14.1. Default Quotas (Per Project)
These are some key default quotas. For a full list, refer to the documentation.
*   **User Event Writes per minute:** 60,000
*   **User Event Imports per minute:** 100
*   **User Event Writes per user per minute:** 240
*   **Product Writes per minute:** 12,000
*   **Product Imports per minute:** 100
*   **Predictions per minute:** 60,000
*   **Searches per minute:** 300
*   **Total User Events:** 40,000,000,000
*   **Total Products (search not enabled):** 40,000,000
*   **Total Products (search enabled):** 4,000,000
*   **Total Tags (sum of per-product tag counts):** 100,000,000
*   **Pending Cloud Storage import LROs:** 300
*   **Pending BigQuery import LROs:** 100
*   **Concurrent Active Models:** 10
*   **Total Models (active and paused):** 20
*   **Total Placements:** 100
*   **Total Controls:** 100

### 14.2. Checking Your Quotas
*   Go to the **Quotas** page in the Google Cloud console.
*   Select **Vertex AI Search for Retail API** in the "Services" dropdown.
*   Recent usage can be viewed on the **API Dashboard** > select API > **Quotas** tab.

### 14.3. Editing Your Quotas
*   If increased quotas are needed, request them a few days in advance.
1.  On the **Quotas** page, select the "Vertex AI Search for Retail API".
2.  Select the quotas to change.
3.  Click **EDIT QUOTAS**.
4.  Fill out the form and submit the request.
*   A response is typically received within 48 hours.

### 14.4. Limits (Hard Limits)
These are enforced limits:
*   **Model Operations:** Up to five model operations (create, delete, pause, resume) per minute.
*   **User Event Writes per ID:** Up to 250,000 user event writes per `visitorId` or `userId` per week.
*   **Product Writes per Product ID:**
    *   Up to 10,000 product writes per product ID per week.
    *   One product write per product ID per second. Frequent updates to the same product might be rejected with `RESOURCE_EXHAUSTED`.

---

## 17. Getting Support
(Source: `https://cloud.google.com/retail/docs/getting-support`, Last Updated: 2025-04-17 UTC)

This section outlines avenues for obtaining support for Vertex AI Search for commerce.

### 17.1. Google Support Packages
*   Google Cloud offers various support packages (24/7 coverage, phone support, Technical Account Manager).
*   Details at [Google Cloud Support](https://cloud.google.com/support).

### 17.2. Community Support
*   **Stack Overflow:**
    *   Ask questions using the tag `google-cloud-recommendations`.
*   **Google Group:**
    *   Join the [cloud-recommendations-users](https://groups.google.com/forum/#!forum/cloud-recommendations-users) Google group for discussions, announcements, and updates.
*   **Slack Community:**
    *   Visit the Google Cloud [Slack community](https://googlecloud-community.slack.com/) (requires signup).

### 17.3. File Bugs or Feature Requests
*   File a support ticket.
*   When creating a ticket, select the appropriate category and component:
    *   **For Recommendations:**
        *   Category: Machine Learning
        *   Component: Vertex AI Search for commerce: recommendations
        *   Subcomponent: Choose the relevant one (e.g., API, Quality of Results, Feature Request).
    *   **For Search:**
        *   Category: Machine Learning
        *   Component: Vertex AI Search for commerce: search & browse
    *   Subcomponent: Choose the relevant one (e.g., API, Indexing, Quality/Modeling, Feature Request).

---

## 18. Billing Questions
(Source: `https://cloud.google.com/retail/docs/billing-questions`, Last Updated: 2025-04-17 UTC)

This page provides resources for billing-related questions.

*   **Cloud Billing Documentation:** For general information, refer to the [Cloud Billing documentation](https://cloud.google.com/billing/docs).
*   **Billing Concerns Troubleshooter:** Use the [billing concerns troubleshooter](https://support.google.com/cloud/troubleshooter/7279311?ref_topic=6288636).
*   **Billing Support Form:** Request help via the [billing support form](https://support.google.com/cloud/contact/cloud_platform_billing).
*   **Change/Disable Billing on a Project:**
    *   Go to the **Billing** page in the Google Cloud console.
    *   See [Modify a Project's Billing Settings](https://support.google.com/cloud/answer/6293499) in Google Cloud console Help.

---

## 16. Frequently Asked Questions (FAQ)
(Source: `https://cloud.google.com/retail/docs/faq`, Last Updated: 2025-04-17 UTC)

This section summarizes common questions about Vertex AI Search for commerce.

### 16.1. General
*   **Client Libraries & Sample Code:** Yes, client libraries are available (see Section 10). Google API Discovery Service can also be used.
*   **Model Personalization:** "Recommended for You," "Others You May Like," and "Buy it Again" models are personalized if user history is provided. "Frequently Bought Together" and "Similar Items" are not.
*   **Personalization Immediacy:** Recommendations improve with more user history. Models start taking user behavior into account immediately if real-time events are sent. Batch-uploaded events are less effective for immediate personalization.
*   **Demographic Data:** Models use only catalog and user event data you provide. Demographic data can be included as custom attributes (anonymized, no PII).
*   **Group Recommendations:** Currently based on single visitor/user ID. For group recommendations, make individual requests and combine, or use group IDs as user IDs if common metadata exists.
*   **Product Images:** Image URLs in catalog are for metadata retrieval and rendering, not currently used by models for recommendations.
*   **Non-Retail Use Cases:** While designed for retail, some customers use it for content, video, gaming. However, features are retail-focused.
*   **Placement of Recommendations:** Models are designed for specific pages (e.g., FBT on add-to-cart, OYML on product detail, RFY on home page).
*   **Email Newsletters:** Yes, by calling the API with a visitor/user ID and incorporating results into email templates. Dynamic loading at read-time requires an intermediary (e.g., Cloud Function).
*   **Non-Web Use Cases (Mobile, Kiosks):** Yes, by setting up an endpoint (e.g., Cloud Function) to get results and send events.
*   **Insufficient Event Data:** "Similar Items" model doesn't require event data. Other models can be trained with recent real-time events if historical data is lacking, but quality improves with more data (ideally 3+ months of views/adds-to-cart, 1-2 years of purchases for FBT).
*   **Category Recommendations:** Only product recommendations are returned, but categories for each product can be included in results.
*   **Data Integrations (SQL, BigQuery):** Yes, sample code exists for reading from BigQuery. GA sample dataset for BigQuery is available.
*   **Cookies:** Vertex AI Search for commerce itself doesn't use cookies, but requires a `visitorId` which is often a session ID from a cookie.
*   **Dedicated Project:** Not required; can enable in an existing project.
*   **Credential Issues (Cloud Shell):** Ensure proper authentication setup with a service account.
*   **Comparing Solutions:** Use A/B tests.
*   **Feature Requests:** Submit via account team, Google Support, or issue tracker.

### 16.2. Catalogs and Products
*   **Cold Starts (New Products):** Recommendations based on similar products (good titles, categories, descriptions are important). For cold-start users, popular products are shown initially, personalizing as events come in.
*   **Merchant Center Catalog:** Can be used by exporting to BigQuery via MC Data Transfer Service.
*   **Other Catalog Import Methods:** BigQuery, Cloud Storage (JSONL), Inline API call, `Products.create` method.
*   **Keeping Catalog Updated:** Daily updates recommended (full or incremental). Real-time price/availability updates are ideal. Cloud Scheduler can automate imports.
*   **Catalog Size:** No minimum, but <100 items may see little benefit. Max is 40 million items (check quotas for specifics if search is enabled).
*   **Multiple Countries/Websites:**
    *   Usually best to have one catalog if significant product overlap. Use "entities" or filter tags for site-specific results.
    *   Separate projects if catalogs/languages are very different or if traffic is low on secondary sites (to ensure enough events for model quality on main site).
    *   Consistent item IDs across sites are crucial for a single catalog.
*   **Multiple Currencies:** Not supported per catalog. All events must use a single currency. Convert before uploading if using console revenue metrics.
*   **Cross-Site Recommendations (Shared Catalog):** Recommended if significant overlap. Use entities or filter tags. Separate projects for dissimilar catalogs.
*   **Metadata for Model Improvement:** Primary fields: ID, title, category hierarchy, price, URL. Custom key-value attributes in `Product.attributes[]` can also be used. Image URLs are mainly for rendering/preview.
*   **Supported Languages:**
    *   Recommendations: Most languages (auto-detects).
    *   Search: Specific list of world languages.
    *   Catalog should be in one language; queries in the same language.
*   **Primary/Variant SKUs:** Supported (similar to `item_group_id` in MC). Define product level (parent/child) before sending data. Changing levels requires rejoining/retuning. See [Product levels](https://cloud.google.com/retail/docs/catalog#product-levels).
*   **Deleting Unavailable Products:** Recommended to set `availability` to `OUT_OF_STOCK` instead of deleting, to preserve historical event data.

### 16.3. User Events
*   **Required Event Types:** See [About user events](https://cloud.google.com/retail/docs/user-events) and [User event data requirements](https://cloud.google.com/retail/docs/create-models#import-reqs).
*   **Troubleshooting Data Quality:** Use **Data Quality** page in the console.
*   **Google Analytics 360 Integration:** Historical data via BigQuery export. Real-time via GTM pixel recommended due to GA360 delays.
*   **GA360 Event Coverage:** Natively supports most events except `search` (which is constructed from queries and impressions).
*   **Feeding Events:** Cloud Storage, API inline import, JS Pixel, GTM, API `write` method.
*   **Missing Event Types/Values:** Refer to minimum requirements per model. More events/item generally better. Default quantity to 1 if unknown. `displayPrice` should always be set.
*   **Limited Event Types:** Check minimum data requirements for specific models.

### 16.4. Search Results
*   **Personalization:** Yes, based on `visitorId`.
*   **Context (e.g., Store ID):** Send as product attributes and use in search request parameters for filtering/ranking.
*   **Hiding Products:** Use `filter` parameter with tags.
*   **Ranking on Multiple Criteria:** Yes, `boostSpec` allows complex ranking rules.
*   **Grouping Attributes (Facets):** Product attributes are not hierarchical. Use multiple custom attributes (e.g., country_of_production, city_of_production).
*   **Suggestions (Autocomplete):** Combination of user queries, rewritten queries, product names. Requires sufficient search events and catalog.

### 16.5. Prediction Results
*   **Limit on Predictions Returned:** Default 20. Max 100 via `pageSize` parameter. More requires Google Support (can increase latency).
*   **Reasons for Recommendations:** Not provided.
*   **Caching Predictions:** Not recommended due to real-time improvements and daily model retraining.
*   **Re-ranking Results (Business Rules):** Supported, but can reduce model effectiveness. Price reranking is a built-in option.
*   **Filter Tag Limits:** No hard limit on unique tags. Recommended max 10 tags/item. Total tags limit 100M (sum of all per-item tag counts).
*   **Diversification:** Yes, via serving config or predict request params. Balances category diversity and relevance.
*   **Prioritize by Price:** Yes, "Price reranking" feature.

### 16.6. Models
*   **"Model not ready" Error:** Usually means model hasn't finished training. Contact support if >10 days.
*   **Training Time:** Initial: 2-5 days (longer for large datasets). Retrains daily unless disabled.
*   **Download/Export Model:** No.
*   **Use Models in New Project:** No, must recreate and retrain.
*   **Category Page Recommendations:** Yes, use "Recommended for You" model with filter tags for the specific category. Disable diversity.
*   **Disable Personalization:** Not recommended. Possible by sending random unique `visitorId` for specific serving configs.

### 16.7. Console Usage
*   **Purged Events Still Showing in Dashboard:** Expected. Dashboard shows ingested events over time, not current count.
*   **Identifying Catalog/Event Errors:** API calls return errors. Dashboard shows unjoined event percentage. Use Cloud Monitoring/Logging.
*   **Inactive Recommendation Serving Configs:** Model needs to be trained with catalog/event data first.
*   **Revenue Metrics Currency:** Reported in the currency used in uploaded data. Single currency per catalog recommended.

---

## 15. Release Notes (Recent Highlights)
(Source: `https://cloud.google.com/retail/docs/release-notes`, Page Last Updated: 2025-04-21 UTC, but individual notes have their own dates)

This section highlights recent key updates and features. For a full history, refer to the source.

*   **March 11, 2025: Conversational Commerce (Private Preview)**
    *   Introduces LLM and conversational product filtering for real-time conversational experiences.
    *   Functions as part of the Guided Search package.
    *   See docs for [Conversational commerce](https://cloud.google.com/retail/docs/conversational-search) and [Conversational product filtering](https://cloud.google.com/retail/docs/conversational-filtering).

*   **February 03, 2025: Pinning Control for Search**
    *   Allows specifying an exact position (1-120) in search results for an item.
    *   Created by adding a rule with `pin_action` in the Retail API.
    *   Not supported for recommendations.
    *   See [Pinning controls](https://cloud.google.com/retail/docs/serving-control-rules#pinning).

*   **January 31, 2025: Merchandising Console**
    *   New user-friendly console for site merchants/business users to manage rules and controls.
    *   Admins can grant Creator or Approver roles.
    *   Accessible via a tab in the main Search for commerce console Controls section.
    *   See [Console options for creating controls](https://cloud.google.com/retail/docs/create-controls#console-options).

*   **January 10, 2025: Product Rename**
    *   "Vertex AI Search for retail" officially renamed to "Vertex AI Search for commerce" in console and documentation.

*   **September 27, 2024: Conversational Search API & Tile Navigation**
    *   **Conversational Search API:** Part of Guided Search. Uses `ConversationalSearchSpec` and `followup_conversation_requested` flag. LLM generates questions for catalog attributes where `allowed_in_conversation` is enabled.
    *   **Tile Navigation:** Part of Guided Search. Shows tiles for likely dynamic facets to speed up filtering.

*   **March 29, 2024: Search Analytics v2 Improvements**
    *   Enhanced Looker-based dashboard for search/browse performance.
    *   Granular per-search/browse metrics and visit-tied metrics.
    *   Full funnel reporting (page-views, add-to-cart, purchases, revenue).
    *   Filtering by date ranges and device types.

*   **December 15, 2023: Export Analytics Metrics to BigQuery**
    *   Allows retaining metrics and writing custom SQL for analysis.
    *   See [Export your analytics metrics into BigQuery](https://cloud.google.com/retail/docs/export-analytics-metrics).

*   **December 12, 2023: Retail Search with LLM (Public Preview)**
    *   Improves ranking with AI-driven relevance grading.
    *   Uses a Giant Relevance LLM distilled into smaller, retailer-specific LLMs.
    *   Access criteria include being fully onboarded to Retail Search, stable usage, no major data quality issues, and >5M searches/day.

*   **November 02, 2023: Configure Logging**
    *   Ability to set severity levels for logs, turn logging on/off, and override defaults for specific services.
    *   See [Configure Logging](https://cloud.google.com/retail/docs/error-reporting#log-config).

*   **October 03, 2023: Facet Controls**
    *   Create controls for search/browse facets (ignore/replace values, set numerical intervals, remove/force facets).
    *   Improved numerical facets with customizable intervals.
    *   See [Facets for search](https://cloud.google.com/retail/docs/facets-overview).

*   **August 04, 2023: View Search Performance Tiers**
    *   Retail console **Data Quality** page shows if data requirements for different search performance tiers are met.
    *   See [Unlock search performance tiers](https://cloud.google.com/retail/docs/data-quality).

*   **June 26, 2023: Data Export GA, Entities, Data Quality Page**
    *   Exporting retail data to BigQuery is Generally Available (GA).
    *   **Entities:** Subdivide retail organization (e.g., by region, brand) for tailored results. See [Entities](https://cloud.google.com/retail/docs/entities).
    *   **Data Quality Page:** Replaces Data Quality panel for assessing product/event data quality.

*   **Earlier Key Milestones:**
    *   **Feb 06, 2023:** Korean, Polish, Turkish catalog support GA.
    *   **Jan 12, 2023:** Browse search GA; Automatic personalization for text/browse search GA; Page-Level Optimization model GA.
    *   **Dec 22, 2022:** On-sale recommendation model introduced.
    *   **Oct 27, 2022:** GA4 user event recording to Retail API GA.
    *   **Oct 12, 2022:** Autocompletion for Retail Search GA; Buy It Again model GA; Revenue per session optimization for OYML & FBT models; Diversification options for serving configs.
    *   **Apr 05, 2022:** Retail Search GA. New data use terms introduced.
    *   **Jan 21, 2022:** Retail console unified Recommendations AI and Retail Search.
    *   **Jan 15, 2021:** Recommendations AI GA (migrated to Retail API from Recommendations Engine API).

---

## 10. Client Libraries
(Source: `https://cloud.google.com/retail/docs/libraries`, Last Updated: 2025-05-05 UTC)

This section provides information on using Cloud Client Libraries to interact with the Vertex AI Search for commerce API.

### 10.1. Overview
*   Client libraries simplify accessing Google Cloud APIs from supported languages.
*   They reduce the amount of code needed compared to making raw HTTP requests.
*   Supported languages include: C++, C#, Go, Java, Node.js, PHP, Python, Ruby.

### 10.2. Installation
*   Each language has specific installation instructions and dependency requirements.
*   The documentation page provides links to:
    *   GitHub READMEs or PyPI pages for installation details (e.g., `pip install google-cloud-retail` for Python).
    *   General setup guides for each language's development environment on Google Cloud.

**Example for Python (from PyPI link):**
```bash
pip install google-cloud-retail
```

### 10.3. Authentication
*   Client libraries support **Application Default Credentials (ADC)**.
*   ADC allows credentials to be available in various environments (local development, production) without code changes.
*   **Production Environments:** ADC setup depends on the service and context (e.g., service accounts on Compute Engine, GKE). Refer to [Set up Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc).
*   **Local Development Environment:**
    1.  Install Google Cloud CLI: `gcloud init` (if not already done).
    2.  Create local authentication credentials for your user account: `gcloud auth application-default login`. This stores credentials in a local file used by ADC.
        *   Not needed if using Cloud Shell.
        *   If using an external IdP, sign in to gcloud CLI with federated identity first.

### 10.4. Additional Resources
*   The documentation page lists links for each language to:
    *   API reference documentation.
    *   Client libraries best practices.
    *   Issue trackers (GitHub).
    *   Stack Overflow tags (though many are `tbd` - to be determined).
    *   Source code repositories (GitHub).

---
