const totalProductsElement = document.getElementById("total-products");
const deadStockCountElement = document.getElementById("dead-stock-count");
const totalValueElement = document.getElementById("total-value");
const productGridElement = document.getElementById("product-grid");
const resultsCountElement = document.getElementById("results-count");
const refreshButton = document.getElementById("refresh-button");
const filtersElement = document.getElementById("category-filters");

const CATEGORY_FILTERS = [
    "All",
    "Grocery",
    "Dairy",
    "Cold Drinks",
    "Namkeen",
];

let allProducts = [];
let activeCategory = "All";

async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed: ${url}`);
    }
    return response.json();
}

function canonicalCategory(value) {
    const category = String(value || "").trim().toLowerCase();
    if (!category) return "Other";
    
    if (category === "grocery" || category.includes("kirana")) return "Grocery";
    if (category === "dairy" || category.includes("milk")) return "Dairy";
    if (category === "cold_drinks" || category.includes("beverage")) return "Cold Drinks";
    if (category === "namkeen" || category.includes("snack")) return "Namkeen";
    
    // Fallback title-case for unknown categories
    return category.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function getStockLabel(stockQuantity) {
    if (stockQuantity <= 0) {
        return { label: "Out of Stock", className: "stock-out" };
    }
    if (stockQuantity <= 20) {
        return { label: "Low Stock", className: "stock-low" };
    }
    return { label: "In Stock", className: "stock-good" };
}

function formatPrice(value) {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2,
    }).format(Number(value) || 0);
}

function formatDaysUnsold(daysUnsold) {
    if (daysUnsold === null || daysUnsold === undefined) {
        return "N/A";
    }
    if (daysUnsold === 0) return "Today";
    return `${daysUnsold} days`;
}

function formatExpiryCountdown(daysToExpire) {
    if (daysToExpire === null || daysToExpire === undefined) {
        return "⏳ Expiry date unavailable";
    }
    if (daysToExpire < 0) {
        return `⏳ Expired ${Math.abs(daysToExpire)} days ago`;
    }
    if (daysToExpire === 0) {
        return "⏳ Expires today";
    }
    return `⏳ Expires in ${daysToExpire} days`;
}

function getUrgencyFromExpiry(daysToExpire) {
    const safeDays = Number(daysToExpire);
    if (!Number.isFinite(safeDays)) {
        return { label: "Low", className: "urgency-low" };
    }
    if (safeDays <= 3) {
        return { label: "Critical", className: "urgency-critical" };
    }
    if (safeDays <= 7) {
        return { label: "High", className: "urgency-high" };
    }
    if (safeDays <= 15) {
        return { label: "Medium", className: "urgency-medium" };
    }
    return { label: "Low", className: "urgency-low" };
}

function formatOfferDisplay(offerType, message, isExpired) {
    if (isExpired) {
        return {
            label: "Sale Status",
            text: "❌ Cannot sell",
            className: "offer-blocked",
        };
    }

    switch (offerType) {
        case "BUY_1_GET_1":
            return {
                label: "Smart Offer",
                text: "🎯 Buy 1 Get 1 Free",
                className: "offer-buy1get1",
            };
        case "FLAT_40_OFF":
            return {
                label: "Smart Offer",
                text: "⚡ 40% Discount",
                className: "offer-flat40",
            };
        case "BUY_2_GET_1":
            return {
                label: "Smart Offer",
                text: "🎁 Buy 2 Get 1 Free",
                className: "offer-buy2get1",
            };
        case "BUNDLE":
            return {
                label: "Smart Offer",
                text: `🤝 ${message || "Bundle with related product for better sales"}`,
                className: "offer-bundle",
            };
        case "NO_ACTION":
            return {
                label: "Status",
                text: "✅ No action needed",
                className: "offer-noaction",
            };
        default:
            return {
                label: "Smart Offer",
                text: formatSuggestionText(message || "No action needed"),
                className: "offer-noaction",
            };
    }
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function formatSuggestionText(suggestion) {
    if (!suggestion) return "";
    const normalized = String(suggestion).trim();

    const discountMatch =
        normalized.match(/offer\s+(\d+%?)\s+discount/i) ||
        normalized.match(/(\d+%?)\s+discount/i);
    if (discountMatch) {
        return `${discountMatch[1]} Discount`;
    }

    const bundleMatch =
        normalized.match(/bundle\s+(.+?)\s+with\s+(.+)/i) ||
        normalized.match(/bundle\s+with\s+(.+)/i);
    if (bundleMatch) {
        const target =
            bundleMatch[2] || bundleMatch[1] || normalized.replace(/^bundle\s+/i, "");
        return `Bundle with ${target.trim()}`;
    }

    return normalized;
}

function renderStats(products) {
    const total = products.length;
    const dead = products.filter((product) => product.status === "Dead Stock").length;
    const totalValue = products.reduce((sum, product) => {
        return sum + (Number(product.price) || 0) * (Number(product.stockQuantity) || 0);
    }, 0);

    totalProductsElement.textContent = String(total);
    deadStockCountElement.textContent = String(dead);
    totalValueElement.textContent = formatPrice(totalValue);
}

function formatPricingBreakdown(product) {
    const original  = formatPrice(product.originalPrice);
    const effective = formatPrice(product.effectivePrice);
    const savings   = formatPrice(product.savings);
    const pct       = product.discountPct;

    if (pct === 0) {
        return `
            <div class="pricing-row">
                <span class="pricing-label">Price</span>
                <span class="pricing-value">${original}</span>
            </div>`;
    }

    const offerType = product.offerType;
    let offerNote = "";
    if (offerType === "BUY_1_GET_1") {
        offerNote = "<span class=\"pricing-note\">Buy 1, get 1 free</span>";
    } else if (offerType === "BUY_2_GET_1") {
        offerNote = "<span class=\"pricing-note\">Buy 2, get 1 free</span>";
    } else if (offerType === "FLAT_40_OFF") {
        offerNote = "<span class=\"pricing-note\">Flat 40% off</span>";
    } else if (offerType === "BUNDLE") {
        offerNote = "<span class=\"pricing-note\">Bundle deal</span>";
    }

    return `
        <div class="pricing-row">
            <span class="pricing-label">Original</span>
            <span class="pricing-value pricing-original">${original}</span>
        </div>
        <div class="pricing-row">
            <span class="pricing-label">Discount</span>
            <span class="pricing-value pricing-discount">−${pct}%</span>
        </div>
        <div class="pricing-row">
            <span class="pricing-label">Effective Price</span>
            <span class="pricing-value pricing-final">${effective} ${offerNote}</span>
        </div>
        <div class="pricing-row">
            <span class="pricing-label">You Save</span>
            <span class="pricing-value pricing-savings">🏷 ${savings} per unit</span>
        </div>`;
}

function createProductCard(product) {
    const article = document.createElement("article");
    const isDeadStock = product.status === "Dead Stock";
    const isExpired = Number(product.daysToExpire) < 0;
    article.className = `product-card ${isDeadStock ? "card-dead" : "card-active"} ${isExpired ? "card-disabled" : ""}`;

    const stockClass = product.stock.className;
    const statusClass = isDeadStock ? "status-dead" : "status-active";
    const urgency = getUrgencyFromExpiry(product.daysToExpire);
    const offerDisplay = formatOfferDisplay(product.offerType, product.suggestion, isExpired);

    article.innerHTML = `
        <div class="card-top">
            <h3>${escapeHtml(product.name)}</h3>
            <div class="card-badges">
                <span class="pill ${statusClass}">${escapeHtml(product.status)}</span>
                <span class="pill urgency-pill ${urgency.className}">
                    🔥 ${escapeHtml(urgency.label)} Urgency
                </span>
                ${
                    isExpired
                        ? '<span class="pill expiry-expired">Expired</span>'
                        : ""
                }
            </div>
        </div>
        <div class="meta">
            <div class="meta-row">
                <span class="meta-label">Category</span>
                <span class="meta-value">${escapeHtml(product.category)}</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Price</span>
                <span class="meta-value">${formatPrice(product.price)}</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Stock Status</span>
                <span class="meta-value ${stockClass}">${product.stock.label}</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Days Unsold</span>
                <span class="meta-value">${formatDaysUnsold(product.daysUnsold)}</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Expiry</span>
                <span class="meta-value expiry-countdown ${isExpired ? "expiry-text-expired" : ""}">
                    ${escapeHtml(formatExpiryCountdown(product.daysToExpire))}
                </span>
            </div>
        </div>
        <div class="pricing-breakdown">
            <p class="pricing-breakdown-title">💰 Pricing Breakdown</p>
            ${formatPricingBreakdown(product)}
        </div>
        <div class="suggestion offer-box ${offerDisplay.className}">
            <p class="suggestion-label">${escapeHtml(offerDisplay.label)}</p>
            <p class="suggestion-text">${escapeHtml(offerDisplay.text)}</p>
        </div>
    `;

    return article;
}

function renderEmpty(message) {
    updateGridContent(() => {
        productGridElement.innerHTML = `<article class="state-card">${message}</article>`;
    });
}

function renderError(message) {
    updateGridContent(() => {
        productGridElement.innerHTML = `<article class="state-card error">${message}</article>`;
    });
}

function renderLoading() {
    updateGridContent(() => {
        productGridElement.innerHTML = `
            <article class="state-card loading-state">
                <span class="loader" aria-hidden="true"></span>
                <p>Fetching latest products...</p>
            </article>
        `;
    });
}

function setRefreshLoading(isLoading) {
    refreshButton.disabled = isLoading;
    refreshButton.classList.toggle("is-loading", isLoading);
    refreshButton.textContent = isLoading ? "Refreshing..." : "Refresh Data";
}

function updateGridContent(renderFn) {
    productGridElement.classList.add("is-updating");
    window.requestAnimationFrame(() => {
        renderFn();
        window.requestAnimationFrame(() => {
            productGridElement.classList.remove("is-updating");
        });
    });
}

function getFilteredProducts() {
    if (activeCategory === "All") {
        return allProducts;
    }
    return allProducts.filter((product) => product.category === activeCategory);
}

function syncFilterButtons() {
    const buttons = filtersElement.querySelectorAll(".filter-btn");
    buttons.forEach((button) => {
        const isActive = button.dataset.category === activeCategory;
        button.classList.toggle("active", isActive);
        button.setAttribute("aria-pressed", String(isActive));
    });
}

function renderProducts() {
    const filteredProducts = getFilteredProducts();

    resultsCountElement.textContent = `${filteredProducts.length} items`;

    updateGridContent(() => {
        if (filteredProducts.length === 0) {
            productGridElement.innerHTML = `<article class="state-card">No products in this category.</article>`;
            return;
        }

        productGridElement.innerHTML = "";
        const fragment = document.createDocumentFragment();

        filteredProducts.forEach((product) => {
            fragment.appendChild(createProductCard(product));
        });

        productGridElement.appendChild(fragment);
    });
}

function setActiveFilter(category) {
    activeCategory = CATEGORY_FILTERS.includes(category) ? category : "All";
    syncFilterButtons();
    renderProducts();
}

function normalizeProducts(products) {
    return products
        .map((product) => {
            const status = product.status || "Active";
            const category = canonicalCategory(product.category);
            const stock = getStockLabel(product.stock_quantity);
            const defaultSuggestion =
                status === "Dead Stock"
                    ? "Offer 10% discount"
                    : "Bundle with a top-selling product";
            const suggestion = product.message || product.suggestion || defaultSuggestion;

            return {
                name: product.name,
                category,
                price: product.price,
                stockQuantity: product.stock_quantity,
                stock,
                status,
                offerType: product.offer_type || "",
                daysUnsold: product.days_unsold ?? null,
                daysToExpire: product.days_to_expire ?? null,
                suggestion,
                // Pricing breakdown
                originalPrice:  product.original_price  ?? product.price,
                discountPct:    product.discount_pct    ?? 0,
                finalPrice:     product.final_price     ?? product.price,
                effectivePrice: product.effective_price ?? product.price,
                savings:        product.savings         ?? 0,
            };
        })
        .sort((left, right) => {
            if (left.status !== right.status) {
                return left.status === "Dead Stock" ? -1 : 1;
            }
            const leftDays = Number(left.daysUnsold ?? -1);
            const rightDays = Number(right.daysUnsold ?? -1);
            return rightDays - leftDays;
        });
}

async function loadDashboard() {
    setRefreshLoading(true);
    renderLoading();

    try {
        const products = await fetchJson("/products");

        allProducts = normalizeProducts(products);
        renderStats(allProducts);
        renderProducts();
    } catch (error) {
        renderError("Could not fetch dashboard data. Please try again.");
    } finally {
        setRefreshLoading(false);
    }
}

filtersElement.addEventListener("click", (event) => {
    const targetButton = event.target.closest(".filter-btn");
    if (!targetButton) return;

    const selectedCategory = targetButton.dataset.category || "All";
    setActiveFilter(selectedCategory);
});

refreshButton.addEventListener("click", loadDashboard);
syncFilterButtons();
loadDashboard();
