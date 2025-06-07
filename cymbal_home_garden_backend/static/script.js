document.addEventListener('DOMContentLoaded', () => {
    const productListing = document.getElementById('product-listing');
    const nightModeToggle = document.getElementById('night-mode-toggle');
    const recommendedProductsGrid = document.getElementById('recommended-products-grid');
    const currentCustomerIdSpan = document.getElementById('current-customer-id'); 

    // Cart DOM Elements (Old Modal - some might be repurposed or removed)
    // const cartModal = document.getElementById('cart-modal'); // Commented out, modal removed
    // const cartToggleBtn = document.getElementById('cart-toggle'); // Commented out, header button removed
    // const closeCartBtn = cartModal.querySelector('.close-button'); // Commented out
    // const cartItemsContainer = document.getElementById('cart-items-container'); // Old modal items container
    // const cartSubtotalEl = document.getElementById('cart-subtotal'); // Old modal subtotal
    // const cartCountEl = document.getElementById('cart-count'); // Old modal count

    // New Left Sidebar Cart DOM Elements
    const leftSidebarCart = document.getElementById('left-sidebar-cart');
    const cartSidebarToggleBtn = document.getElementById('cart-sidebar-toggle-btn');
    const cartSidebarItemsContainer = document.getElementById('cart-sidebar-items-container');
    const cartSidebarSubtotalEl = document.getElementById('cart-sidebar-subtotal');
    const cartSidebarItemCountEl = document.getElementById('cart-sidebar-item-count');
    const clearCartSidebarBtn = document.getElementById('cart-sidebar-clear-btn');
    // const cartSidebarCheckoutBtn = document.getElementById('cart-sidebar-checkout-btn'); // REMOVED
    
    console.log("[Cart Init] Sidebar cart elements:", { leftSidebarCart, cartSidebarToggleBtn, cartSidebarItemsContainer, cartSidebarSubtotalEl, cartSidebarItemCountEl, clearCartSidebarBtn }); // REMOVED cartSidebarCheckoutBtn from log

    // New Checkout Review Modal DOM Elements
    const checkoutReviewModal = document.getElementById('checkout-review-modal');
    const closeCheckoutReviewModalBtn = checkoutReviewModal ? checkoutReviewModal.querySelector('.checkout-modal-close-btn') : null;
    const checkoutModalItemsContainer = document.getElementById('checkout-modal-items-container');
    const checkoutModalSubtotalEl = document.getElementById('checkout-modal-subtotal');
    const checkoutModalModifyBtn = document.getElementById('checkout-modal-modify-btn');
    const checkoutModalProceedBtn = document.getElementById('checkout-modal-proceed-btn');

    // Shipping Modal DOM Elements
    const checkoutShippingModal = document.getElementById('checkout-shipping-modal');
    const closeCheckoutShippingModalBtn = checkoutShippingModal ? checkoutShippingModal.querySelector('.checkout-modal-close-btn') : null;
    const shippingHomeDeliveryOpt = document.getElementById('shipping-home-delivery');
    const shippingPickupPointOpt = document.getElementById('shipping-pickup-point');
    const shippingRadioHome = document.getElementById('shipping-radio-home');
    const shippingRadioPickup = document.getElementById('shipping-radio-pickup');
    const pickupLocationsListContainer = document.getElementById('pickup-locations-list');
    const shippingBackBtn = document.getElementById('shipping-back-btn');
    const shippingContinueBtn = document.getElementById('shipping-continue-btn');

    // Payment Modal DOM Elements
    const checkoutPaymentModal = document.getElementById('checkout-payment-modal');
    const closeCheckoutPaymentModalBtn = checkoutPaymentModal ? checkoutPaymentModal.querySelector('.checkout-modal-close-btn') : null;
    const paymentRadioSaved = document.getElementById('payment-radio-saved');
    const paymentRadioNew = document.getElementById('payment-radio-new');
    const savedCardDetailsDiv = document.getElementById('saved-card-details');
    const newCardFormDiv = document.getElementById('new-card-form');
    const saveCardBtn = document.getElementById('save-card-btn');
    const paymentBackBtn = document.getElementById('payment-back-btn');
    const paymentConfirmBtn = document.getElementById('payment-confirm-btn');
// Checkout Confirmation Modal DOM Elements
    const checkoutConfirmationModal = document.getElementById('checkout-confirmation-modal');
    const closeCheckoutConfirmationModalBtn = checkoutConfirmationModal ? checkoutConfirmationModal.querySelector('.checkout-modal-close-btn') : null;
    const confirmationCloseBtn = document.getElementById('confirmation-close-btn');


    // Checkout Modal (Sidebar) DOM Elements - REMOVED
    // const checkoutModalPh1 = document.getElementById('checkout-modal-ph1');
    // const checkoutModalTitlePh1 = document.getElementById('checkout-modal-title-ph1');
    // const checkoutModalBodyPh1 = document.getElementById('checkout-modal-body-ph1');
    // const closeCheckoutModalBtnPh1 = document.getElementById('checkout-modal-close-ph1');
    // const cancelCheckoutBtnPh1 = document.getElementById('checkout-cancel-btn-ph1');
    // const backCheckoutBtnPh1 = document.getElementById('checkout-back-btn-ph1');
    // const nextCheckoutBtnPh1 = document.getElementById('checkout-next-btn-ph1');

    const DEFAULT_CUSTOMER_ID = "123";
    if(currentCustomerIdSpan) currentCustomerIdSpan.textContent = DEFAULT_CUSTOMER_ID;

    let localProductCache = {};
    let currentCartItemsData = [];
    let currentCartItemIds = [];
    let cachedCartDataForModals = null; // To store cart data for reopening review modal

    const staticPickupLocations = [
        { name: 'Cymbal Store Downtown', address: '123 Main St, Anytown, USA' },
        { name: 'Cymbal Garden Center North', address: '789 Oak Ave, Anytown, USA' },
        { name: 'Partner Locker Hub', address: '456 Pine Rd, Anytown, USA' }
    ];
    let currentShippingSelection = {};


    // let checkoutProcessState = { ... }; // REMOVED
    // console.log("[Checkout] Initial checkoutProcessState:", JSON.parse(JSON.stringify(checkoutProcessState))); // REMOVED

    // --- Left Sidebar Cart Logic ---
    function toggleCartSidebar() {
        if (!leftSidebarCart) {
            console.error("[Cart Sidebar] Sidebar element not found for toggle.");
            return;
        }
        const isCollapsed = leftSidebarCart.classList.toggle('collapsed');
        document.body.classList.toggle('cart-sidebar-expanded', !isCollapsed);
        console.log(`[Cart Sidebar] Toggled. Now ${isCollapsed ? 'collapsed' : 'expanded'}. Body class 'cart-sidebar-expanded' is ${!isCollapsed}.`);
        if (cartSidebarToggleBtn) {
            cartSidebarToggleBtn.innerHTML = isCollapsed ? '>' : '<'; // Update button text/icon
        }
    }

    if (cartSidebarToggleBtn) {
        console.log("[Cart Init] Adding click listener to sidebar toggle button.");
        cartSidebarToggleBtn.addEventListener('click', toggleCartSidebar);
    } else {
        console.warn("[Cart Init] Sidebar toggle button not found.");
    }
    
    // --- Left Sidebar Cart Logic ---
    function toggleCartSidebar() {
        if (!leftSidebarCart) {
            console.error("[Cart Sidebar] Sidebar element not found for toggle.");
            return;
        }
        // This function is mainly for mobile now where the toggle button might be visible
        const isCurrentlyCollapsed = leftSidebarCart.classList.contains('collapsed');
        if (isCurrentlyCollapsed) {
            leftSidebarCart.classList.remove('collapsed');
            document.body.classList.add('cart-sidebar-expanded');
            if (cartSidebarToggleBtn) cartSidebarToggleBtn.innerHTML = '<';
            console.log(`[Cart Sidebar] Toggled. Now expanded.`);
        } else {
            leftSidebarCart.classList.add('collapsed');
            document.body.classList.remove('cart-sidebar-expanded');
            if (cartSidebarToggleBtn) cartSidebarToggleBtn.innerHTML = '>';
             console.log(`[Cart Sidebar] Toggled. Now collapsed.`);
        }
    }

    if (cartSidebarToggleBtn) {
        console.log("[Cart Init] Adding click listener to sidebar toggle button (for mobile).");
        cartSidebarToggleBtn.addEventListener('click', toggleCartSidebar);
    } else {
        console.warn("[Cart Init] Sidebar toggle button not found.");
    }
    
    // Ensure sidebar is expanded by default on DESKTOP.
    // On mobile, it will start collapsed due to CSS, and toggle button will be shown.
    if (window.innerWidth > 768) { // Assuming 768px is your mobile breakpoint
        if (leftSidebarCart) {
            leftSidebarCart.classList.remove('collapsed');
            document.body.classList.add('cart-sidebar-expanded');
            console.log("[Cart Init] Desktop: Sidebar forced to expanded state.");
        }
    } else {
         if (leftSidebarCart) {
             leftSidebarCart.classList.add('collapsed'); // Start collapsed on mobile
             document.body.classList.remove('cart-sidebar-expanded');
             if (cartSidebarToggleBtn) cartSidebarToggleBtn.innerHTML = '>';
             console.log("[Cart Init] Mobile: Sidebar initially collapsed.");
         }
    }


    // --- Night Mode ---
    const THEME_STORAGE_KEY = 'websiteTheme';
    function applyTheme(theme) {
        console.log(`Applying theme: ${theme}`);
        if (theme === 'night') {
            document.body.classList.add('night-mode');
            if(nightModeToggle) nightModeToggle.textContent = 'Light Mode';
        } else {
            document.body.classList.remove('night-mode');
            if(nightModeToggle) nightModeToggle.textContent = 'Night Mode';
        }
        try {
            localStorage.setItem(THEME_STORAGE_KEY, theme);
        } catch (error) {
            console.error("Error saving theme to localStorage:", error);
        }
    }
    try {
        const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
        if (savedTheme) applyTheme(savedTheme); else applyTheme('day');
    } catch (error) {
        console.error("Error loading theme from localStorage:", error);
        applyTheme('day'); 
    }
    if(nightModeToggle) {
        nightModeToggle.addEventListener('click', () => {
            applyTheme(document.body.classList.contains('night-mode') ? 'day' : 'night');
        });
    }

    // --- Cart Modal (Old - To be removed or commented out) ---
    // function openCartModal() { if(cartModal) cartModal.classList.add('show'); }
    // function closeCartModal() { if(cartModal) cartModal.classList.remove('show'); }
    // if(cartToggleBtn) cartToggleBtn.addEventListener('click', openCartModal);
    // if(closeCartBtn) closeCartBtn.addEventListener('click', closeCartModal);
    // window.addEventListener('click', (event) => {
    //     if (event.target === cartModal) closeCartModal();
    // });

    // --- API Helper ---
    async function fetchAPI(url, options = {}) {
        console.log(`AGENT ACTION: Calling ${options.method || 'GET'} ${url}`);
        if (options.body) {
            let payloadToLog = options.body;
            if (typeof options.body === 'string') {
                try { payloadToLog = JSON.parse(options.body); } catch (e) { /* ignore */ }
            }
            console.log("AGENT PAYLOAD:", payloadToLog);
        }
        try {
            const response = await fetch(url, options);
            const responseData = await response.json().catch(() => ({})); 
            console.log(`AGENT RESPONSE: Status ${response.status} from ${url}`, responseData);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}, message: ${responseData.message || response.statusText || 'Unknown error'}`);
            }
            return responseData;
        } catch (error) {
            console.error('API Error Details:', error);
            alert(`Error: ${error.message}`);
            throw error;
        }
    }

    // --- Cart Logic (Backend Integrated) ---
    async function fetchCart() {
        console.log("[Cart] Fetching cart data...");
        try {
            const data = await fetchAPI(`/api/cart/${DEFAULT_CUSTOMER_ID}`);
            console.log("[Cart] Cart data received:", data);
            currentCartItemsData = data.items || [];
            currentCartItemIds = currentCartItemsData.map(item => item.product_id);
            renderCartItems(currentCartItemsData); // Will now render to sidebar
            calculateSubtotal(currentCartItemsData); // Will now update sidebar subtotal
            updateCartCount(currentCartItemsData); // Will now update sidebar count
            displayRecommendedProducts();
            const subtotal = currentCartItemsData.reduce((sum, item) => sum + ((item.price_per_unit || 0) * item.quantity), 0);
            return { items: currentCartItemsData, subtotal: subtotal }; // Return the necessary data
        } catch (error) {
            console.error("[Cart] Error fetching cart:", error);
            if(cartSidebarItemsContainer) cartSidebarItemsContainer.innerHTML = '<p>Error loading cart. Please try again.</p>';
            throw error; // Re-throw error so it can be caught by caller
        }
    }

    // New animation function
    function animateItemToCart(sourceElementRect, targetElementRect, imageUrl) {
        console.log(`[Animation] Starting fly-to-cart. Source:`, sourceElementRect, `Target:`, targetElementRect, `Image: ${imageUrl}`);
        if (!imageUrl || !sourceElementRect || !targetElementRect) {
            console.error("[Animation] Missing data for animation:", {imageUrl, sourceElementRect, targetElementRect});
            return;
        }

        const flyingImage = document.createElement('div');
        flyingImage.classList.add('flying-item-animation'); // Use class from style.css
        flyingImage.style.backgroundImage = `url(${imageUrl})`;
        
        // Initial position and size (near source element, e.g., agent widget)
        const initialSize = 50; // px
        flyingImage.style.left = `${sourceElementRect.left + (sourceElementRect.width / 2) - (initialSize / 2)}px`;
        flyingImage.style.top = `${sourceElementRect.top + (sourceElementRect.height / 2) - (initialSize / 2)}px`;
        flyingImage.style.width = `${initialSize}px`;
        flyingImage.style.height = `${initialSize}px`;
        flyingImage.style.opacity = '1';
        
        document.body.appendChild(flyingImage);
        console.log("[Animation] Flying image appended to body:", flyingImage);

        // Target position and size (near cart sidebar icon or a specific point in sidebar)
        const finalSize = 20; // px, smaller as it "enters" the cart
        const targetX = targetElementRect.left + (targetElementRect.width / 4); // Adjust to target a specific part of the sidebar
        const targetY = targetElementRect.top + (targetElementRect.height / 4);

        // Force reflow to apply initial styles before transition
        void flyingImage.offsetWidth;

        // Apply target styles to trigger CSS transition
        flyingImage.style.left = `${targetX}px`;
        flyingImage.style.top = `${targetY}px`;
        flyingImage.style.width = `${finalSize}px`;
        flyingImage.style.height = `${finalSize}px`;
        flyingImage.style.opacity = '0';
        // transform: scale(0.1) could also be used if preferred over width/height transition for shrinking

        flyingImage.addEventListener('transitionend', () => {
            console.log("[Animation] Fly-to-cart animation ended. Removing element.");
            flyingImage.remove();
        }, { once: true });
    }

    async function addToCart(productId, event) { // event parameter might be null if called by agent
        console.log(`[Product Card Add] Adding product ${productId} to cart. Attempting animation.`);

        if (event && event.target) { // Ensure event and event.target are available for user clicks
            const sourceElementRect = event.target.getBoundingClientRect();
            const targetElement = document.getElementById('left-sidebar-cart');
            if (targetElement) {
                const targetElementRect = targetElement.getBoundingClientRect();
                let imageUrl = 'https://via.placeholder.com/150?text=No+Image'; // Default
                const product = localProductCache[productId];
                if (product && product.image_url) {
                    imageUrl = `/${product.image_url}`;
                } else {
                    // Fallback: Try to get image from the card DOM
                    const card = event.target.closest('.product-card');
                    if (card) {
                        const imgElement = card.querySelector('img');
                        if (imgElement && imgElement.src) {
                            imageUrl = imgElement.src;
                        }
                    }
                }
                animateItemToCart(sourceElementRect, targetElementRect, imageUrl);
            } else {
                console.warn("[Animation] Target cart element 'left-sidebar-cart' not found for user click animation.");
            }
        } else {
            console.log("[Product Card Add] Event or event.target not available, skipping user click animation (likely agent call or test).");
        }

        try {
            await fetchAPI(`/api/cart/${DEFAULT_CUSTOMER_ID}/item`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: productId, quantity: 1 })
            });
            await fetchCart(); // Fetches cart and updates sidebar display

            // Ensure sidebar is visible if it was collapsed
            if (leftSidebarCart && leftSidebarCart.classList.contains('collapsed')) {
                console.log("[Cart] Sidebar was collapsed, expanding it after item add.");
                toggleCartSidebar(); // Use the new toggle function
            }
        } catch (error) {
            console.error(`[Product Card Add] Error adding product ${productId}:`, error);
            // fetchAPI handles user-facing alerts
        }
    }

    function renderCartItems(items) {
        // Now targets the sidebar's item container
        if (!cartSidebarItemsContainer) {
            console.error("[Cart Render] Sidebar cart items container not found.");
            return;
        }
        console.log("[Cart Render] Rendering items in sidebar:", items);
        if (!items || items.length === 0) {
            cartSidebarItemsContainer.innerHTML = '<p>Your cart is empty.</p>';
        } else {
            cartSidebarItemsContainer.innerHTML = '';
            items.forEach(item => {
                const itemEl = document.createElement('div');
                itemEl.classList.add('cart-item');
                itemEl.innerHTML =
                    `<div class="cart-item-details">
                        <h4>${item.name || item.product_id}</h4>
                        <p class="product-id-display">ID: ${item.product_id}</p>
                        <p>Price: $${(item.price_per_unit || 0).toFixed(2)} x ${item.quantity}</p>
                    </div>
                    <div class="cart-item-actions">
                        <button class="remove-from-cart-btn" data-product-id="${item.product_id}">&times;</button>
                    </div>`;
                cartSidebarItemsContainer.appendChild(itemEl);
            });
            cartSidebarItemsContainer.querySelectorAll('.remove-from-cart-btn').forEach(btn => {
                btn.addEventListener('click', (e) => removeProductFromCart(e.target.dataset.productId));
            });
        }
    }

    function updateCartCount(items) {
        // Now targets the sidebar's count element
        if(!cartSidebarItemCountEl) {
            console.warn("[Cart Count] Sidebar item count element not found.");
            return;
        }
        const count = items.reduce((sum, item) => sum + item.quantity, 0);
        cartSidebarItemCountEl.textContent = count;
        console.log(`[Cart Count] Updated sidebar cart count to: ${count}`);
    }

    function calculateSubtotal(items) {
        // Now targets the sidebar's subtotal element
        if(!cartSidebarSubtotalEl) {
            console.warn("[Cart Subtotal] Sidebar subtotal element not found.");
            return;
        }
        const subtotal = items.reduce((sum, item) => sum + ((item.price_per_unit || 0) * item.quantity), 0).toFixed(2);
        cartSidebarSubtotalEl.textContent = subtotal;
        console.log(`[Cart Subtotal] Updated sidebar subtotal to: $${subtotal}`);
    }

    async function removeProductFromCart(productId) {
        console.log(`[Cart] Removing product ${productId} from cart.`);
        try {
            await fetchAPI(`/api/cart/${DEFAULT_CUSTOMER_ID}/item/${productId}`, { method: 'DELETE' });
            await fetchCart();
        } catch (error) {
            console.error(`[Cart] Error removing product ${productId}:`, error);
            /* Handled by fetchAPI */
        }
    }

    async function clearCart() {
        console.log("[Cart] Clearing all items from cart.");
        try {
            await fetchAPI(`/api/cart/${DEFAULT_CUSTOMER_ID}/clear`, { method: 'DELETE' });
            await fetchCart();
        } catch (error) {
            console.error("[Cart] Error clearing cart:", error);
        }
    }
    // Update to use the new sidebar clear button
    if(clearCartSidebarBtn) {
        console.log("[Cart Init] Adding click listener to sidebar clear cart button.");
        clearCartSidebarBtn.addEventListener('click', clearCart);
    } else {
        console.warn("[Cart Init] Sidebar clear cart button not found.");
    }

    // --- Product Display & Recommendations ---
    async function fetchInitialProducts() {
        try {
            const products = await fetchAPI('/api/products');
            localProductCache = {};
            products.forEach(p => localProductCache[p.id] = p);
            displayProducts(products);
        } catch (error) {
            if(productListing) productListing.innerHTML = '<p>Error loading products. Please try again later.</p>';
        }
    }

    function displayProducts(productsData) {
        if (!productListing || !productsData || productsData.length === 0) {
            if(productListing) productListing.innerHTML = '<p>No products found.</p>';
            return;
        }
        productListing.innerHTML = '';
        productsData.forEach(product => renderProductCard(product, productListing));
    }

    function displayRecommendedProducts() {
        if (!recommendedProductsGrid || !localProductCache) return;
        const allProducts = Object.values(localProductCache);
        if (allProducts.length === 0) {
            recommendedProductsGrid.innerHTML = '<p>No recommendations available yet.</p>'; return;
        }
        let recommendations = allProducts.filter(p => !currentCartItemIds.includes(p.id)).slice(0, 4);
        if (recommendations.length < 4) {
            recommendations = recommendations.concat(allProducts.filter(p => !recommendations.find(r => r.id === p.id)).slice(0, 4 - recommendations.length));
        }
        recommendations = [...new Map(recommendations.map(item => [item['id'], item])).values()].slice(0,4);
        recommendedProductsGrid.innerHTML = '';
        if (recommendations.length === 0 && allProducts.length > 0) recommendations = allProducts.slice(0,4);
        
        if (recommendations.length > 0) {
            recommendations.forEach(product => renderProductCard(product, recommendedProductsGrid, true));
        } else {
            recommendedProductsGrid.innerHTML = '<p>Explore our products!</p>';
        }
    }

    function renderProductCard(product, container, isRecommended = false) {
        const card = document.createElement('article');
        card.classList.add('product-card');
        if (isRecommended) card.classList.add('recommended-item');
        card.dataset.productId = product.id;
        const name = product.name || 'Unnamed Product';
        const price = product.price !== null && product.price !== undefined ? parseFloat(product.price).toFixed(2) : 'N/A';
        const description = product.description || 'No description available.';
        const imageUrl = product.image_url ? `/${product.image_url}` : 'https://picsum.photos/seed/productimg/300/300';
        let descSnippet = description.substring(0, isRecommended ? 50 : 100) + (description.length > (isRecommended ? 50 : 100) ? '...' : '');
        
        card.innerHTML =
            `<img src="${imageUrl}" alt="${name}">
            <h3>${name}</h3>
            <p class="product-id-display">ID: ${product.id}</p>
            <p class="price">$${price}</p>
            <p class="description">${descSnippet}</p>
            <button class="add-to-cart-btn" data-product-id="${product.id}">Add to Cart</button>`;
        container.appendChild(card);
        // Pass the event to addToCart
        card.querySelector('.add-to-cart-btn').addEventListener('click', (event) => addToCart(event.target.dataset.productId, event));
    }

    // Initial Load
    async function initialLoad() {
        await fetchInitialProducts();
        await fetchCart();
    }
    initialLoad();

    // --- Message Listener for Agent Widget ---
    window.addEventListener('message', (event) => {
        console.log("[Main Page DEBUG] Message event received. Origin:", event.origin, "Raw Data:", event.data);
        const expectedWidgetOrigin = 'http://localhost:5000';
        if (event.origin !== expectedWidgetOrigin) {
            console.warn(`[Main Page DEBUG] Message received from unexpected origin: ${event.origin}. Expected: ${expectedWidgetOrigin}. Ignoring message.`);
            return;
        }
        if (!event.data) {
            console.log("[Main Page DEBUG] Message data is null or undefined. Ignoring.");
            return;
        }

        console.log("[Main Page DEBUG] Processing message data:", event.data);

        if (event.data.type === "SET_WEBSITE_THEME" && typeof event.data.payload === 'string') {
            const newTheme = event.data.payload;
            console.log(`[Main Page DEBUG] Received SET_WEBSITE_THEME from widget with theme: ${newTheme}`);
            applyTheme(newTheme);
        } else if (event.data.type === "REFRESH_CART_DISPLAY") {
            console.log("[Main Page DEBUG] Received REFRESH_CART_DISPLAY from widget. Data:", event.data);
            fetchCart(); // This will update the sidebar cart display

            if (event.data.added_item_details && event.data.added_item_details.image_url) {
                console.log("[Main Page DEBUG] Item added via agent, attempting animation. Details:", event.data.added_item_details);
                const agentWidgetElement = document.querySelector('.agent-widget'); // Standard selector for agent widget
                const sidebarCartElement = document.getElementById('left-sidebar-cart');

                if (agentWidgetElement && sidebarCartElement) {
                    const sourceRect = agentWidgetElement.getBoundingClientRect();
                    const targetRect = sidebarCartElement.getBoundingClientRect(); // Or a specific element within the sidebar
                    
                    // Ensure sidebar is visible for animation target
                    if (leftSidebarCart && leftSidebarCart.classList.contains('collapsed')) {
                        console.log("[Main Page DEBUG Animation] Sidebar was collapsed, expanding it for animation target.");
                        toggleCartSidebar();
                    }
                    
                    animateItemToCart(sourceRect, targetRect, event.data.added_item_details.image_url);
                } else {
                    console.error("[Main Page DEBUG Animation] Could not find agent widget or sidebar cart element for animation.", {agentWidgetElement, sidebarCartElement});
                }
            } else {
                console.log("[Main Page DEBUG] REFRESH_CART_DISPLAY received, but no added_item_details with image_url for animation.");
            }
        } else if (event.data.type === "ui_command" && event.data.command_name) { // Changed to match agent_widget.js
            console.log(`[Main Page DEBUG] Received 'ui_command' for command: ${event.data.command_name}`, "Payload:", event.data.payload);
            handleDisplayUiComponent(event.data.command_name, event.data.payload); // Pass command_name as uiElement
        } else if (event.data.type === 'show_checkout_modal_command' && event.data.cart) {
            console.log("[Main Page DEBUG] Received 'show_checkout_modal_command' from widget. Cart data:", event.data.cart);
            openCheckoutReviewModal(event.data.cart);
        } else if (event.data.type === 'show_shipping_modal_command') {
            console.log("[Main Page DEBUG] Received 'show_shipping_modal_command' from widget.");
            openCheckoutShippingModal();
        } else if (event.data.type === 'show_payment_modal_command') {
            console.log("[Main Page DEBUG] Received 'show_payment_modal_command' from widget.");
            openCheckoutPaymentModal();
        } else if (event.data.type === 'ui_select_shipping_home_delivery') {
            console.log("[Main Page DEBUG] Received 'ui_select_shipping_home_delivery' from widget.");
            if(shippingRadioHome) shippingRadioHome.checked = true;
            updateShippingSelectionUI({ type: 'home_delivery' });
            hidePickupLocationsList();
        } else if (event.data.type === 'ui_show_pickup_locations') {
            console.log("[Main Page DEBUG] Received 'ui_show_pickup_locations' from widget.");
            if(shippingRadioPickup) shippingRadioPickup.checked = true;
            updateShippingSelectionUI({ type: 'pickup_initiated' });
            displayPickupLocationsList();
        } else if (event.data.type === 'ui_select_pickup_address' && event.data.address_index !== undefined) {
            console.log(`[Main Page DEBUG] Received 'ui_select_pickup_address' for index ${event.data.address_index} from widget.`);
            const selectedLocation = staticPickupLocations[event.data.address_index];
            if (selectedLocation) {
                updateShippingSelectionUI({ type: 'pickup_address', index: event.data.address_index, name: selectedLocation.name, address: selectedLocation.address });
                // Also visually check the radio button for the specific pickup location if they exist
                const pickupRadio = document.getElementById(`pickup-location-radio-${event.data.address_index}`);
                if (pickupRadio) pickupRadio.checked = true;
            }
        } else if (event.data.type === 'order_confirmed_refresh_cart_command') {
            console.log("[Main Page DEBUG] Received 'order_confirmed_refresh_cart_command' from widget. Data:", event.data.data);
            // Close any open checkout modals
            if (checkoutPaymentModal && checkoutPaymentModal.style.display !== 'none') {
                closeCheckoutPaymentModal();
            }
            if (checkoutShippingModal && checkoutShippingModal.style.display !== 'none') {
                closeCheckoutShippingModal();
            }
            if (checkoutReviewModal && checkoutReviewModal.style.display !== 'none') {
                closeCheckoutReviewModal();
            }
            // Refresh cart (will be empty as backend clears it)
            fetchCart();
            // Show custom success notification
            const notificationPopup = document.getElementById('order-success-notification');
            if (notificationPopup) {
                // Optionally, customize the message if needed, though "Order successfully submitted!" is generic.
                // const confirmationMessage = event.data.data?.message || "Order successfully submitted!";
                // notificationPopup.textContent = confirmationMessage; // If you want to use the message from backend
                
                notificationPopup.classList.add('show');
                setTimeout(() => {
                    notificationPopup.classList.remove('show');
                }, 3000); // Hide after 3 seconds
            }
            // Voice notification was removed.
            // The original alert that showed order ID was also removed.
        } else {
            console.log("[Main Page DEBUG] Received message not handled by current logic:", event.data);
        }
    });

    function handleDisplayUiComponent(uiElement, payload) { // uiElement here is actually command_name
        console.log(`[Main Page DEBUG] handleDisplayUiComponent called with command_name (as uiElement): ${uiElement}, payload:`, payload);
        // showCheckoutModalPh1(); // REMOVED - Checkout modal functionality is being removed

        switch (uiElement) { // uiElement here is actually command_name
            // case "checkout_item_selection": // REMOVED
            //     // renderCheckoutStep1ItemSelection(payload && payload.items ? payload.items : currentCartItemsData); // Function to be removed
            //     break;
            // case "shipping_options": // REMOVED
            //     // renderShippingStep(); // Function to be removed
            //     break;
            // case "pickup_locations": // REMOVED
            //     // checkoutProcessState.shippingInfo.previousPickupLocations = payload && payload.locations ? payload.locations : []; // State removed
            //     // renderPickupLocationsStep(checkoutProcessState.shippingInfo.previousPickupLocations); // Function to be removed
            //     console.log("[Main Page DEBUG] Received 'pickup_locations' UI command - functionality removed.");
            //     break;
            // case "payment_methods": // REMOVED
            //     // checkoutProcessState.paymentInfo.previousPaymentMethods = payload && payload.methods ? payload.methods : []; // State removed
            //     // renderPaymentStep(checkoutProcessState.paymentInfo.previousPaymentMethods); // Function to be removed
            //     console.log("[Main Page DEBUG] Received 'payment_methods' UI command - functionality removed.");
            //     break;
            // case "order_confirmation": // REMOVED
            //     // const orderId = payload && payload.details && payload.details.orderId ? payload.details.orderId : (payload && payload.details ? JSON.stringify(payload.details) : "N/A");
            //     // renderOrderConfirmationStep(orderId); // Function to be removed
            //     console.log("[Main Page DEBUG] Received 'order_confirmation' UI command - functionality removed.");
            //     break;
            default:
                console.error(`[Main Page DEBUG] Unknown/unhandled uiElement received in handleDisplayUiComponent: ${uiElement}`);
                // if (checkoutModalBodyPh1) { // checkoutModalBodyPh1 is already effectively removed
                //     // checkoutModalBodyPh1.innerHTML = `<p>Error: Received an unknown UI component name: ${uiElement}.</p>`;
                // }
        }
    }
    
    // --- Checkout Review Modal Functions ---
    function populateCheckoutModal(cartData) {
        console.log("[Checkout Modal DEBUG] Attempting to POPULATE review modal. Received Cart data:", JSON.stringify(cartData));
        if (!checkoutModalItemsContainer || !checkoutModalSubtotalEl) {
            console.error("[Checkout Modal DEBUG] Checkout modal item/subtotal elements not found for populate. Items El:", checkoutModalItemsContainer, "Subtotal El:", checkoutModalSubtotalEl);
            return;
        }
        cachedCartDataForModals = cartData; // Cache for reopening
        if (!cartData || !cartData.items || cartData.items.length === 0) {
            console.log("[Checkout Modal DEBUG] Cart is empty or invalid. Displaying empty message.");
            checkoutModalItemsContainer.innerHTML = '<p>Your cart is currently empty.</p>';
            checkoutModalSubtotalEl.textContent = '0.00';
            if(checkoutModalProceedBtn) checkoutModalProceedBtn.disabled = true;
            return;
        }

        checkoutModalItemsContainer.innerHTML = ''; // Clear previous items
        cartData.items.forEach(item => {
            const itemEl = document.createElement('div');
            itemEl.classList.add('checkout-modal-item');
            itemEl.innerHTML = `
                <span class="checkout-modal-item-name">${item.name || item.product_id}</span>
                <span class="checkout-modal-item-qty">Qty: ${item.quantity}</span>
                <span class="checkout-modal-item-price">$${(item.price_per_unit * item.quantity).toFixed(2)}</span>
            `;
            checkoutModalItemsContainer.appendChild(itemEl);
        });
        checkoutModalSubtotalEl.textContent = (cartData.subtotal || 0).toFixed(2);
        if(checkoutModalProceedBtn) checkoutModalProceedBtn.disabled = false;
        console.log("[Checkout Modal DEBUG] Review modal populated with items.");
    }

    function openCheckoutReviewModal(cartData) {
        console.log("[Checkout Modal DEBUG] Attempting to OPEN review modal. Received Cart data:", JSON.stringify(cartData));
        if (!checkoutReviewModal) {
            console.error("[Checkout Modal DEBUG] Checkout review modal element (#checkout-review-modal) NOT FOUND in DOM. Cannot open.");
            return;
        }
        console.log("[Checkout Modal DEBUG] checkoutReviewModal element found:", checkoutReviewModal, "Proceeding to populate and display.");
        populateCheckoutModal(cartData); // This will also cache cartData
        
        console.log("[Checkout Modal DEBUG] Applying 'popping-in' class and setting display to 'flex'. Current classes before change:", checkoutReviewModal.className);
        checkoutReviewModal.classList.remove('popping-out'); // Ensure popping-out is removed if it was stuck
        checkoutReviewModal.classList.add('popping-in');
        checkoutReviewModal.style.display = 'flex'; // Explicitly set display
        console.log("[Checkout Modal DEBUG] Review modal display style set to 'flex'. Final classes:", checkoutReviewModal.className);
        // Enhanced Debugging
        if (checkoutReviewModal) {
            const computedStyle = window.getComputedStyle(checkoutReviewModal);
            console.log("[Checkout Modal DEBUG] Computed display:", computedStyle.display);
            console.log("[Checkout Modal DEBUG] Computed visibility:", computedStyle.visibility);
            console.log("[Checkout Modal DEBUG] Computed opacity:", computedStyle.opacity);
            console.log("[Checkout Modal DEBUG] Computed z-index:", computedStyle.zIndex);
            console.log("[Checkout Modal DEBUG] OffsetWidth:", checkoutReviewModal.offsetWidth);
            console.log("[Checkout Modal DEBUG] OffsetHeight:", checkoutReviewModal.offsetHeight);
            console.log("[Checkout Modal DEBUG] BoundingClientRect:", JSON.stringify(checkoutReviewModal.getBoundingClientRect()));
            if (checkoutReviewModal.parentElement) {
                console.log("[Checkout Modal DEBUG] Parent element display:", window.getComputedStyle(checkoutReviewModal.parentElement).display);
            } else {
                console.log("[Checkout Modal DEBUG] Parent element not found.");
            }
        }
    }

    function closeCheckoutReviewModal() {
        console.log("[Checkout Modal DEBUG] Attempting to CLOSE review modal.");
        return new Promise((resolve) => {
            if (!checkoutReviewModal) {
                console.warn("[Checkout Modal DEBUG] closeCheckoutReviewModal: Modal element not found, resolving promise.");
                resolve();
                return;
            }
            console.log("[Checkout Modal DEBUG] Applying 'popping-out' class. Current classes before change:", checkoutReviewModal.className);
            checkoutReviewModal.classList.remove('popping-in');
            checkoutReviewModal.classList.add('popping-out');
            setTimeout(() => {
                checkoutReviewModal.style.display = 'none'; // Hide after animation
                checkoutReviewModal.classList.remove('popping-out'); // Clean up class
                console.log("[Checkout Modal DEBUG] Review modal display set to 'none' after timeout. Final classes:", checkoutReviewModal.className);
                resolve();
            }, 300); // Match CSS transition duration
        });
    }

    if (closeCheckoutReviewModalBtn) {
        closeCheckoutReviewModalBtn.addEventListener('click', () => {
            console.log("[Checkout Modal DEBUG] Close button clicked for review modal.");
            closeCheckoutReviewModal();
        });
    }
    if (checkoutModalModifyBtn) {
        checkoutModalModifyBtn.addEventListener('click', () => {
            console.log("[Checkout Modal DEBUG] Modify Cart button clicked in review modal.");
            closeCheckoutReviewModal();
        });
    }
    if (checkoutModalProceedBtn) {
        checkoutModalProceedBtn.addEventListener('click', async () => {
            console.log("[Checkout Modal DEBUG] Proceed button clicked in review modal. Opening shipping modal.");
            await closeCheckoutReviewModal();
            openCheckoutShippingModal(); // Transition to shipping modal
        });
    }

    // --- Shipping Modal Functions ---
    function resetShippingModalUI() {
        if(shippingRadioHome) shippingRadioHome.checked = false;
        if(shippingRadioPickup) shippingRadioPickup.checked = false;
        hidePickupLocationsList();
        // Clear visual selection cues
        document.querySelectorAll('.shipping-option.selected, .pickup-location-option.selected').forEach(el => {
            el.classList.remove('selected');
        });
        currentShippingSelection = {};
        if(shippingContinueBtn) shippingContinueBtn.disabled = true; // Disable continue until a choice is made
    }

    function updateShippingSelectionUI(selection) {
        currentShippingSelection = selection;
        console.log("[Shipping Modal DEBUG] Current selection updated:", currentShippingSelection);

        // Remove 'selected' class from all options first
        document.querySelectorAll('.shipping-option.selected, .pickup-location-option.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        if (selection.type === 'home_delivery' && shippingHomeDeliveryOpt) {
            shippingHomeDeliveryOpt.classList.add('selected');
        } else if (selection.type === 'pickup_initiated' && shippingPickupPointOpt) {
            shippingPickupPointOpt.classList.add('selected');
        } else if (selection.type === 'pickup_address' && selection.index !== undefined) {
            if(shippingPickupPointOpt) shippingPickupPointOpt.classList.add('selected'); // Keep main pickup option selected
            const selectedPickupEl = document.querySelector(`.pickup-location-option[data-index="${selection.index}"]`);
            if (selectedPickupEl) selectedPickupEl.classList.add('selected');
        }
        if(shippingContinueBtn) shippingContinueBtn.disabled = !(currentShippingSelection.type === 'home_delivery' || currentShippingSelection.type === 'pickup_address');
    }

    function displayPickupLocationsList() {
        if (!pickupLocationsListContainer) return;
        pickupLocationsListContainer.innerHTML = '<h4>Select a Pickup Location:</h4>'; // Title for the list
        staticPickupLocations.forEach((location, index) => {
            const locEl = document.createElement('div');
            locEl.classList.add('pickup-location-option');
            locEl.dataset.index = index;
            locEl.innerHTML = `
                <input type="radio" name="pickup_location_radio" value="${index}" id="pickup-location-radio-${index}" style="display:none;">
                <span class="location-name">${location.name}</span>
                <span class="location-address">${location.address}</span>
            `;
            locEl.addEventListener('click', () => {
                // Visually check the hidden radio for form semantics if ever needed, and for styling
                const radio = locEl.querySelector('input[type="radio"]');
                if(radio) radio.checked = true;
                
                updateShippingSelectionUI({ type: 'pickup_address', index: index, name: location.name, address: location.address });
                window.parent.postMessage({ type: 'pickup_address_chosen', address_text: `${location.name} - ${location.address}`, address_index: index }, '*');
            });
            pickupLocationsListContainer.appendChild(locEl);
        });
        pickupLocationsListContainer.style.display = 'block';
    }

    function hidePickupLocationsList() {
        if (pickupLocationsListContainer) {
            pickupLocationsListContainer.style.display = 'none';
            pickupLocationsListContainer.innerHTML = '<p>Loading pickup locations...</p>'; // Reset content
        }
    }

    function openCheckoutShippingModal() {
        if (!checkoutShippingModal) {
            console.error("Checkout shipping modal element not found.");
            return;
        }
        console.log("[Shipping Modal] Opening shipping modal.");
        resetShippingModalUI();
        checkoutShippingModal.classList.remove('popping-out');
        checkoutShippingModal.classList.add('popping-in');
        checkoutShippingModal.style.display = 'flex';
    }

    function closeCheckoutShippingModal() {
        return new Promise((resolve) => {
            if (!checkoutShippingModal) {
                resolve();
                return;
            }
            checkoutShippingModal.classList.remove('popping-in');
            checkoutShippingModal.classList.add('popping-out');
            setTimeout(() => {
                checkoutShippingModal.style.display = 'none';
                checkoutShippingModal.classList.remove('popping-out');
                resolve();
            }, 300);
        });
    }

    if (closeCheckoutShippingModalBtn) closeCheckoutShippingModalBtn.addEventListener('click', closeCheckoutShippingModal);

    if (shippingHomeDeliveryOpt) {
        shippingHomeDeliveryOpt.addEventListener('click', () => {
            if(shippingRadioHome) shippingRadioHome.checked = true; // Ensure radio is checked
            updateShippingSelectionUI({ type: 'home_delivery' });
            hidePickupLocationsList();
            window.parent.postMessage({ type: 'shipping_option_chosen', choice: 'home_delivery' }, '*');
        });
    }
    if (shippingPickupPointOpt) {
        shippingPickupPointOpt.addEventListener('click', () => {
            if(shippingRadioPickup) shippingRadioPickup.checked = true; // Ensure radio is checked
            updateShippingSelectionUI({ type: 'pickup_initiated' });
            displayPickupLocationsList();
            window.parent.postMessage({ type: 'shipping_option_chosen', choice: 'pickup_initiated' }, '*');
        });
    }

    if (shippingBackBtn) {
        console.log("[Init] shippingBackBtn element FOUND. Attaching listener.");
        shippingBackBtn.addEventListener('click', async () => {
            console.log("[Shipping Modal] Back to Cart Review button CLICKED. Starting process.");
            await closeCheckoutShippingModal();
            console.log("[Shipping Modal] closeCheckoutShippingModal awaited.");
            try {
                console.log("[Shipping Modal] cachedCartDataForModals before decision:", JSON.stringify(cachedCartDataForModals));
                let cartDataToDisplay;
                if (cachedCartDataForModals) {
                    cartDataToDisplay = cachedCartDataForModals;
                    console.log("[Shipping Modal] Using cachedCartDataForModals.");
                } else {
                    console.log("[Shipping Modal] No cached data, attempting to fetchCart().");
                    cartDataToDisplay = await fetchCart();
                    console.log("[Shipping Modal] fetchCart() result:", JSON.stringify(cartDataToDisplay));
                }
                console.log("[Shipping Modal] cartDataToDisplay before opening review modal:", JSON.stringify(cartDataToDisplay));
                openCheckoutReviewModal(cartDataToDisplay);
            } catch (error) {
                console.error("[Shipping Modal] Error in Back to Cart Review button logic:", error);
                openCheckoutReviewModal({ items: [], subtotal: 0 }); // Fallback
            }
            window.parent.postMessage({ type: 'shipping_flow_interrupted', reason: 'back_to_cart_review' }, '*');
        });
    } else {
        console.error("[Init] shippingBackBtn element NOT FOUND. Listener NOT attached.");
    }
    if (shippingContinueBtn) {
        shippingContinueBtn.addEventListener('click', async () => { // Made this function async
            console.log("[Shipping Modal] Continue to Payment button clicked. Current selection:", currentShippingSelection);
            if (!currentShippingSelection.type || (currentShippingSelection.type === 'pickup_initiated')) {
                alert("Please select a shipping option or a specific pickup location.");
                return;
            }
            // alert("Proceeding to payment is not yet implemented."); // Will be handled by opening payment modal
            await closeCheckoutShippingModal();
            openCheckoutPaymentModal();
        });
    }

    // --- Payment Modal Functions ---
    function resetPaymentModalUI() {
        if (paymentRadioSaved) paymentRadioSaved.checked = true;
        if (savedCardDetailsDiv) savedCardDetailsDiv.style.display = 'block';
        if (newCardFormDiv) {
            newCardFormDiv.style.display = 'none';
            const inputs = newCardFormDiv.querySelectorAll('input[type="text"]');
            inputs.forEach(input => input.value = '');
        }
        // Potentially disable confirm button until a valid state
        if(paymentConfirmBtn) paymentConfirmBtn.disabled = false; // Default to enabled if saved card is an option
    }

    function openCheckoutPaymentModal() {
        if (!checkoutPaymentModal) {
            console.error("Checkout payment modal element not found.");
            return;
        }
        console.log("[Payment Modal] Opening payment modal.");
        resetPaymentModalUI();
        checkoutPaymentModal.classList.remove('popping-out');
        checkoutPaymentModal.classList.add('popping-in');
        checkoutPaymentModal.style.display = 'flex';
    }

    function closeCheckoutPaymentModal() {
        return new Promise((resolve) => {
            if (!checkoutPaymentModal) {
                resolve();
                return;
            }
            checkoutPaymentModal.classList.remove('popping-in');
            checkoutPaymentModal.classList.add('popping-out');
            setTimeout(() => {
                checkoutPaymentModal.style.display = 'none';
                checkoutPaymentModal.classList.remove('popping-out');
                resolve();
            }, 300);
        });
    }

    if (closeCheckoutPaymentModalBtn) closeCheckoutPaymentModalBtn.addEventListener('click', closeCheckoutPaymentModal);

    if (paymentRadioSaved) {
        paymentRadioSaved.addEventListener('change', () => {
            if (paymentRadioSaved.checked) {
                if (savedCardDetailsDiv) savedCardDetailsDiv.style.display = 'block';
                if (newCardFormDiv) newCardFormDiv.style.display = 'none';
                if(paymentConfirmBtn) paymentConfirmBtn.disabled = false;
            }
        });
    }

    if (paymentRadioNew) {
        paymentRadioNew.addEventListener('change', () => {
            if (paymentRadioNew.checked) {
                if (savedCardDetailsDiv) savedCardDetailsDiv.style.display = 'none';
                if (newCardFormDiv) newCardFormDiv.style.display = 'block';
                // Could disable confirm button until card is "saved"
                if(paymentConfirmBtn) paymentConfirmBtn.disabled = true; 
            }
        });
    }

    if (saveCardBtn) {
        saveCardBtn.addEventListener('click', () => {
            // Simulate saving card
            const cardNumberInput = document.getElementById('card-number');
            if (cardNumberInput && cardNumberInput.value.trim() !== "") {
                alert("Card details saved (simulated). You can now confirm payment.");
                // Update saved card details display (optional, for more realism)
                // For now, just enable confirm button
                if(paymentConfirmBtn) paymentConfirmBtn.disabled = false;
                // Optionally, switch back to "Use Saved Card" view
                // if(paymentRadioSaved) paymentRadioSaved.checked = true;
                // if (savedCardDetailsDiv) savedCardDetailsDiv.style.display = 'block';
                // if (newCardFormDiv) newCardFormDiv.style.display = 'none';
            } else {
                alert("Please enter card details.");
            }
        });
    }

    if (paymentBackBtn) {
        paymentBackBtn.addEventListener('click', async () => {
            await closeCheckoutPaymentModal();
            openCheckoutShippingModal(); // Go back to shipping
        });
    }

    if (paymentConfirmBtn) {
        paymentConfirmBtn.addEventListener('click', async () => { // Make async
            console.log("[Payment Modal] Confirm Payment button clicked.");
            
            // Gather data for the order
            const customerId = DEFAULT_CUSTOMER_ID;
            const itemsToOrder = cachedCartDataForModals ? cachedCartDataForModals.items : [];
            const orderSubtotal = cachedCartDataForModals ? cachedCartDataForModals.subtotal : 0;

            // Construct shipping details from currentShippingSelection
            let shippingDetailsPayload = {
                type: currentShippingSelection.type || "N/A",
                address: "N/A",
                notes: "No specific shipping notes."
            };
            if (currentShippingSelection.type === 'home_delivery') {
                shippingDetailsPayload.address = "User's home address (placeholder)"; // Placeholder
            } else if (currentShippingSelection.type === 'pickup_address') {
                shippingDetailsPayload.address = `${currentShippingSelection.name}, ${currentShippingSelection.address}`;
            }

            const orderPayload = {
                customer_id: customerId,
                items: itemsToOrder,
                shipping_details: shippingDetailsPayload,
                total_amount: parseFloat(orderSubtotal) // Ensure it's a number
            };

            console.log("[Payment Modal] Order Payload for API:", orderPayload);

            try {
                const result = await fetchAPI('/api/checkout/place_order', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(orderPayload)
                });

                if (result.status === "success") {
                    // alert(`Order Submitted Successfully! Your Order ID: ${result.order_id}`); // Old alert
                    await closeCheckoutPaymentModal();
                    openCheckoutConfirmationModal(); // Open new confirmation modal
                    clearCart(false); // Clear UI cart, don't hit backend as order is placed
                    await fetchCart(); // Refresh cart display (will be empty)
                } else {
                    alert(`Order placement failed: ${result.message || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error placing order:', error);
                alert('There was an issue placing your order. Please try again.');
            }
        });
    } // End of if (paymentConfirmBtn)

    // --- Checkout Confirmation Modal Functions ---
    function openCheckoutConfirmationModal() {
        if (!checkoutConfirmationModal) {
            console.error("Checkout confirmation modal element not found.");
            return;
        }
        console.log("[Confirmation Modal] Opening confirmation modal.");
        checkoutConfirmationModal.classList.remove('popping-out');
        checkoutConfirmationModal.classList.add('popping-in');
        checkoutConfirmationModal.style.display = 'flex';
    }

    function closeCheckoutConfirmationModal() {
        return new Promise((resolve) => {
            if (!checkoutConfirmationModal) {
                resolve();
                return;
            }
            checkoutConfirmationModal.classList.remove('popping-in');
            checkoutConfirmationModal.classList.add('popping-out');
            setTimeout(() => {
                checkoutConfirmationModal.style.display = 'none';
                checkoutConfirmationModal.classList.remove('popping-out');
                resolve();
            }, 300); // Match CSS transition duration
        });
    }

    if (closeCheckoutConfirmationModalBtn) {
        closeCheckoutConfirmationModalBtn.addEventListener('click', async () => {
            await closeCheckoutConfirmationModal();
            // Optionally, redirect or perform other actions
        });
    }
    if (confirmationCloseBtn) { // The main button in the confirmation modal
        confirmationCloseBtn.addEventListener('click', async () => {
            await closeCheckoutConfirmationModal();
            // Optionally, redirect or perform other actions, e.g., back to main page
        });
    }
    
    // All checkout related functions, dummy data, and event listeners previously here are now removed.

    // Remove or comment out the OLD checkout modal logic if it's truly not needed elsewhere
    // For example, openCheckoutModal_OLD(), closeCheckoutModal_OLD(), etc.

    console.log("[Main Page] Script loaded.");
});
