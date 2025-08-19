# Final Plan: Shopping Cart UI Update and Agent-Only Animation

**Objective:**
1.  Redesign the shopping cart UI from a modal to a **fixed left sidebar panel**. This panel will be persistently visible (or toggleable) and display cart contents.
2.  Implement an animation showing items visually moving **only when added via the agent widget** (currently bottom-right). The animation will show items moving from the agent widget area to the new left sidebar cart.
3.  Items added directly from product cards on the main page will update the cart without a flying animation.
4.  Ensure extensive logging is added.

**Relevant Files:**
*   `cymbal_home_garden_backend/templates/index.html`
*   `cymbal_home_garden_backend/static/style.css`
*   `cymbal_home_garden_backend/static/script.js`
*   `agents/customer-service/customer_service/tools/tools.py`
*   `agents/customer-service/streaming_server.py`
*   `cymbal_home_garden_backend/static/agent_widget.js`

---

## Phase 1: New Left Sidebar Cart UI (HTML & CSS)

**Goal:** Implement the new fixed left sidebar cart panel.

1.  **Modify `cymbal_home_garden_backend/templates/index.html`:**
    *   **Remove Old Cart UI:**
        *   Remove/comment out the existing cart modal: `<div id="cart-modal" class="modal">`.
        *   Remove/comment out the header cart toggle button: `<button id="cart-toggle">`.
    *   **Add New Left Sidebar Cart Element:**
        *   Place this new `div` as a direct child of `<body>`, likely before the `<header>` or `<main>` to ensure it's part of the main layout flow that can push content.
            ```html
            <!-- New Left Sidebar Cart -->
            <aside id="left-sidebar-cart" class="cart-sidebar">
                <div class="cart-sidebar-header">
                    <h3>Your Shopping Cart (<span id="cart-sidebar-item-count">0</span>)</h3>
                    <button id="cart-sidebar-toggle-btn" aria-label="Toggle Cart Sidebar" class="cart-sidebar-toggle">&lt;</button> 
                </div>
                <div id="cart-sidebar-items-container" class="cart-items-container">
                    <p>Your cart is empty.</p>
                </div>
                <div class="cart-sidebar-footer">
                    <p>Subtotal: $<span id="cart-sidebar-subtotal">0.00</span></p>
                    <button id="cart-sidebar-clear-btn">Clear Cart</button>
                    <button id="cart-sidebar-checkout-btn">Checkout</button>
                </div>
            </aside>
            ```
    *   **Agent Widget:** The agent widget (`{% raw %}{% include 'agent_widget.html' %}{% endraw %}`) and its launcher icon (`#agent-launcher-icon`) remain as they are, positioned in the bottom-right.

2.  **Modify `cymbal_home_garden_backend/static/style.css`:**
    *   **Remove Old Cart Modal Styles.**
    *   **Add Styles for New Left Sidebar Cart:**
        *   `.cart-sidebar`:
            *   `position: fixed; left: 0; top: 0; width: 300px; height: 100vh;`
            *   `background-color: var(--current-card-bg); border-right: 1px solid var(--current-card-border);`
            *   `box-shadow: 3px 0px 10px rgba(0,0,0,0.1); z-index: 1000; display: flex; flex-direction: column; padding: 15px;`
            *   `transform: translateX(0); transition: transform 0.3s ease-in-out;`
        *   `.cart-sidebar.collapsed`: `transform: translateX(-100%);` (Sidebar initially visible, can be collapsed)
        *   `.cart-sidebar-header`: `display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;`
        *   `.cart-sidebar-toggle`: Styles for the toggle button.
        *   `.cart-items-container` (within sidebar): `flex-grow: 1; overflow-y: auto; margin-bottom: 10px;`
        *   `.cart-sidebar-footer`: Styles for padding, text alignment.
    *   **Main Content Area Adjustment (when sidebar is expanded):**
        *   `body.cart-sidebar-expanded main, body.cart-sidebar-expanded header { margin-left: 300px; transition: margin-left 0.3s ease-in-out; }`
        *   `body main, body header { margin-left: 0; transition: margin-left 0.3s ease-in-out; }` (Default state)

---

## Phase 2: Cart Logic Update (JavaScript) - Animation Specificity

**Goal:** Update JavaScript for the new sidebar cart, ensuring animation *only* triggers for agent-initiated adds.

1.  **Modify `cymbal_home_garden_backend/static/script.js`:**
    *   **DOM References & Sidebar Toggle:** Update as per previous plan (new sidebar IDs, toggle logic).
    *   **`addToCart` Function (Product Card Clicks):**
        *   **Remove Animation Logic:** The existing animation code block within this function (which handles clicks on product card "Add to Cart" buttons) should be **removed or commented out**.
        *   The function should now *only* contain the API call to add the item and then call `fetchCart()` to update the sidebar.
            ```javascript
            async function addToCart(productId, event) { // event parameter might become unused
                console.log(`[Product Card Add] Adding product ${productId} to cart. NO ANIMATION.`);
                try {
                    await fetchAPI(`/api/cart/${DEFAULT_CUSTOMER_ID}/item`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ product_id: productId, quantity: 1 })
                    });
                    await fetchCart(); // Fetches cart and updates sidebar display
                    // Optionally, ensure sidebar is visible if it was collapsed
                    const sidebar = document.getElementById('left-sidebar-cart');
                    if (sidebar && sidebar.classList.contains('collapsed')) {
                        // Logic to expand sidebar, e.g., by simulating a toggle click or calling a function
                        document.getElementById('cart-sidebar-toggle-btn')?.click();
                    }
                } catch (error) { /* fetchAPI handles alerts */ }
            }
            ```
    *   **Animation Function (New or Adapted):** The animation logic previously in `addToCart` will now be triggered *only* by messages from the agent widget. It can be refactored into a new standalone function, e.g., `animateItemToCart(sourceElementRect, targetElementRect, imageUrl)`.
    *   **Message Listener (for Agent Adds):**
        *   When `event.data.type === "REFRESH_CART_DISPLAY"`:
            *   Call `fetchCart()` to update sidebar.
            *   **If `event.data.added_item_details` is present:**
                *   Extract `image_url`.
                *   Get `sourceRect` from the agent widget (`document.querySelector('.agent-widget')`).
                *   Get `targetRect` for the `leftSidebarCart`.
                *   Call the new/refactored animation function: `animateItemToCart(sourceRect, targetRect, event.data.added_item_details.image_url)`.
    *   **Logging:** Add/maintain logging for all cart operations and specifically for when the animation is triggered (or intentionally skipped).

---

## Phase 3: Animation Trigger from Agent Widget (Unchanged Logic, Path is Key)

1.  **Agent Tools (`agents/customer-service/customer_service/tools/tools.py`):**
    *   `modify_cart` returns `{"action": "refresh_cart", "added_item": {"product_id": ..., "name": ..., "image_url": ...}}`.

2.  **Streaming Server (`agents/customer-service/streaming_server.py`):**
    *   Relays `added_item` payload.

3.  **Agent Widget JS (`cymbal_home_garden_backend/static/agent_widget.js`):**
    *   `postMessage`: `{"type": "REFRESH_CART_DISPLAY", "added_item_details": {...}}`.

---

## Phase 4: Refinements

1.  **Sidebar Visibility on Add:** When an item is added (either via agent or product card), ensure the left cart sidebar becomes visible if it was collapsed.
2.  **Logging:** Confirm comprehensive logging is in place.

---

## Mermaid Diagram (Animation ONLY from Agent)

```mermaid
sequenceDiagram
    participant User
    participant ProductCardUI as Main Page Product Card
    participant AgentWidgetJS as Agent Widget JS (agent_widget.js)
    participant StreamingServer as Streaming Server (streaming_server.py)
    participant AgentTools as Agent Tools (tools.py)
    participant BackendAPI as Backend API (app.py)
    participant MainPageJS as Main Page JS (script.js)
    participant CartSidebarUI as Cart Sidebar UI (DOM)

    alt User clicks Product Card "Add to Cart"
        User->>ProductCardUI: Click "Add to Cart"
        ProductCardUI->>MainPageJS: Calls addToCart(productId)
        MainPageJS->>BackendAPI: POST /api/cart/.../item (add item)
        BackendAPI-->>MainPageJS: Success
        MainPageJS->>MainPageJS: fetchCart()
        MainPageJS->>CartSidebarUI: Updates cart content (NO animation)
    end

    alt User asks Agent to add item
        User->>AgentWidgetJS: "Add item X to cart"
        AgentWidgetJS->>StreamingServer: Sends user request
        StreamingServer->>AgentTools: Invokes modify_cart tool
        AgentTools->>BackendAPI: Updates cart in DB
        BackendAPI-->>AgentTools: Success + Item Details (image_url)
        AgentTools-->>StreamingServer: Returns {"action": "refresh_cart", "added_item": {...}}
        StreamingServer-->>AgentWidgetJS: WebSocket: {"type": "command", ..., "payload": {"added_item": {...}}}
        AgentWidgetJS-->>MainPageJS: postMessage: {"type": "REFRESH_CART_DISPLAY", "added_item_details": {...}}
        
        MainPageJS->>MainPageJS: fetchCart()
        MainPageJS->>CartSidebarUI: Updates cart content in sidebar
        MainPageJS->>MainPageJS: Create flying image (using image_url from agent payload)
        Note over MainPageJS,CartSidebarUI: Animate image from Agent Widget (bottom-right) to Cart Sidebar (left)
    end