/**
 * ==============================================================================
 * ONLINE RETAIL SALES ANALYTICS DASHBOARD - CORE JAVASCRIPT
 * Handles REST API integrations, dynamic Chart.js visualizations,
 * data tables rendering, filter state management, and real-time business insights.
 * ==============================================================================
 */

// Application State
const state = {
    filters: {
        startDate: "",
        endDate: "",
        category: "all",
        city: "all",
        status: "all_active"
    },
    charts: {
        monthlyTrend: null,
        categoryShare: null,
        topProducts: null,
        cities: null
    },
    currentSortProducts: "quantity",
    cachedCustomers: []
};

// Currency Formatter
const formatUSD = (val) => {
    const num = Number(val) || 0;
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2
    }).format(num);
};

// Number Formatter
const formatInt = (val) => {
    const num = Number(val) || 0;
    return new Intl.NumberFormat("en-US").format(num);
};

// Helper: Build Query String
const buildQueryString = () => {
    const params = new URLSearchParams();
    if (state.filters.startDate) params.append("startDate", state.filters.startDate);
    if (state.filters.endDate) params.append("endDate", state.filters.endDate);
    if (state.filters.category && state.filters.category !== "all") params.append("category", state.filters.category);
    if (state.filters.city && state.filters.city !== "all") params.append("city", state.filters.city);
    if (state.filters.status) params.append("status", state.filters.status);
    return params.toString() ? `?${params.toString()}` : "";
};

// ==============================================================================
// 1. INITIALIZATION & EVENT LISTENERS
// ==============================================================================
document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initFilterControls();
    loadFilterOptions();
    fetchAllData();
    fetchSqlQueriesCatalog();
});

// Sidebar Navigation & Section Switching
function initNavigation() {
    const menuItems = document.querySelectorAll(".sidebar-menu .menu-item");
    const heading = document.getElementById("currentPageHeading");
    const sidebar = document.getElementById("sidebar");
    const toggleBtn = document.getElementById("sidebarToggleBtn");
    const closeBtn = document.getElementById("sidebarCloseBtn");

    menuItems.forEach((item) => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const targetSectionId = item.getAttribute("data-target");
            const label = item.querySelector("span").textContent;

            menuItems.forEach((m) => m.classList.remove("active"));
            item.classList.add("active");

            switchSection(targetSectionId);
            if (heading) heading.textContent = label;

            // Close sidebar on mobile
            if (window.innerWidth < 992 && sidebar) {
                sidebar.classList.remove("show");
            }
        });
    });

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => sidebar.classList.toggle("show"));
    }
    if (closeBtn && sidebar) {
        closeBtn.addEventListener("click", () => sidebar.classList.remove("show"));
    }
}

function switchSection(sectionId) {
    document.querySelectorAll(".app-section").forEach((sec) => sec.classList.remove("active"));
    const target = document.getElementById(sectionId);
    if (target) {
        target.classList.add("active");
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    // Sync menu active state
    document.querySelectorAll(".sidebar-menu .menu-item").forEach((m) => {
        if (m.getAttribute("data-target") === sectionId) {
            m.classList.add("active");
            const label = m.querySelector("span").textContent;
            const heading = document.getElementById("currentPageHeading");
            if (heading) heading.textContent = label;
        } else {
            m.classList.remove("active");
        }
    });
}

// Global Filter Setup
function initFilterControls() {
    const btnApply = document.getElementById("btnApplyFilters");
    const btnReset = document.getElementById("btnResetFilters");
    const btnRefresh = document.getElementById("btnRefreshAll");

    if (btnApply) {
        btnApply.addEventListener("click", () => {
            state.filters.startDate = document.getElementById("filterStartDate").value;
            state.filters.endDate = document.getElementById("filterEndDate").value;
            state.filters.category = document.getElementById("filterCategory").value;
            state.filters.city = document.getElementById("filterCity").value;
            state.filters.status = document.getElementById("filterStatus").value;
            fetchAllData();
        });
    }

    if (btnReset) {
        btnReset.addEventListener("click", () => {
            document.getElementById("filterStartDate").value = "";
            document.getElementById("filterEndDate").value = "";
            document.getElementById("filterCategory").value = "all";
            document.getElementById("filterCity").value = "all";
            document.getElementById("filterStatus").value = "all_active";

            state.filters = {
                startDate: "",
                endDate: "",
                category: "all",
                city: "all",
                status: "all_active"
            };
            fetchAllData();
        });
    }

    if (btnRefresh) {
        btnRefresh.addEventListener("click", () => {
            const icon = document.getElementById("refreshIcon");
            if (icon) icon.classList.add("fa-spin");
            fetchAllData().finally(() => {
                setTimeout(() => {
                    if (icon) icon.classList.remove("fa-spin");
                }, 600);
            });
        });
    }

    // Best Selling Products sort toggle
    const btnSortQty = document.getElementById("btnSortByQty");
    const btnSortRev = document.getElementById("btnSortByRev");
    if (btnSortQty && btnSortRev) {
        btnSortQty.addEventListener("click", () => {
            btnSortQty.classList.add("active");
            btnSortRev.classList.remove("active");
            state.currentSortProducts = "quantity";
            fetchBestSellingProducts();
        });
        btnSortRev.addEventListener("click", () => {
            btnSortRev.classList.add("active");
            btnSortQty.classList.remove("active");
            state.currentSortProducts = "revenue";
            fetchBestSellingProducts();
        });
    }

    // Customer client-side search filter
    const custSearch = document.getElementById("customerSearchInput");
    if (custSearch) {
        custSearch.addEventListener("input", (e) => {
            const term = e.target.value.toLowerCase().trim();
            filterCustomerTable(term);
        });
    }
}

// Fetch filter options to populate dropdowns
async function loadFilterOptions() {
    try {
        const res = await fetch("/api/filters");
        const json = await res.json();
        if (json.status === "success" && json.data) {
            const { categories, cities, date_range } = json.data;

            // Categories
            const catSelect = document.getElementById("filterCategory");
            if (catSelect && categories) {
                catSelect.innerHTML = `<option value="all">All Categories</option>`;
                categories.forEach((cat) => {
                    catSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
                });
            }

            // Cities
            const citySelect = document.getElementById("filterCity");
            if (citySelect && cities) {
                citySelect.innerHTML = `<option value="all">All Cities</option>`;
                cities.forEach((city) => {
                    citySelect.innerHTML += `<option value="${city}">${city}</option>`;
                });
            }

            // Min and Max dates
            if (date_range) {
                const sDate = document.getElementById("filterStartDate");
                const eDate = document.getElementById("filterEndDate");
                if (sDate && !sDate.value) sDate.min = date_range.min_date;
                if (eDate && !eDate.value) eDate.max = date_range.max_date;
            }
        }
    } catch (err) {
        console.error("Failed to load filter metadata:", err);
    }
}

// Master Fetcher
async function fetchAllData() {
    await Promise.allSettled([
        fetchDashboardKpis(),
        fetchMonthlySalesData(),
        fetchCategoryData(),
        fetchBestSellingProducts(),
        fetchCitiesData(),
        fetchRevenueBreakdown(),
        fetchTopCustomers(),
        fetchBusinessInsights()
    ]);
}

// ==============================================================================
// 2. MAIN KPI CARDS (DYNAMIC FROM DATABASE)
// ==============================================================================
async function fetchDashboardKpis() {
    try {
        const res = await fetch(`/api/dashboard${buildQueryString()}`);
        const json = await res.json();
        if (json.status === "success" && json.data) {
            const d = json.data;
            document.getElementById("kpiTotalRevenue").textContent = formatUSD(d.total_revenue);
            document.getElementById("kpiTotalOrders").textContent = formatInt(d.total_orders);
            document.getElementById("kpiTotalProductsSold").textContent = formatInt(d.total_products_sold);
            document.getElementById("kpiTotalCustomers").textContent = formatInt(d.total_customers);
            document.getElementById("kpiAverageOrderValue").textContent = formatUSD(d.average_order_value);
            document.getElementById("kpiTotalCategories").textContent = formatInt(d.total_categories);

            // Update Database Engine info pill
            if (json.database) {
                const pill = document.getElementById("engineStatusText");
                const sbDb = document.getElementById("sidebarDbName");
                const sbMode = document.getElementById("sidebarDbMode");
                if (pill) pill.textContent = json.database.database_name;
                if (sbDb) sbDb.textContent = json.database.is_oracle ? "Oracle Database" : "SQLite Local Engine";
                if (sbMode) sbMode.textContent = json.database.is_oracle ? "Oracle 19c/21c/23c Connected" : "Embedded Local Mode";
            }
        }
    } catch (err) {
        console.error("Error fetching KPI cards:", err);
    }
}

// ==============================================================================
// 3. FEATURE 1: REVENUE ANALYSIS
// ==============================================================================
async function fetchRevenueBreakdown() {
    try {
        const res = await fetch(`/api/revenue${buildQueryString()}`);
        const json = await res.json();
        if (json.status === "success" && json.data) {
            const { revenue_by_product, revenue_by_category, revenue_by_city } = json.data;

            // Product table
            const tbodyProd = document.getElementById("tbodyRevByProduct");
            if (tbodyProd) {
                tbodyProd.innerHTML = revenue_by_product.map((item, idx) => `
                    <tr>
                        <td><span class="text-muted fw-bold">${idx + 1}</span></td>
                        <td class="fw-semibold text-dark">${item.PRODUCT_NAME}</td>
                        <td><span class="badge bg-light text-secondary border">${item.CATEGORY_NAME}</span></td>
                        <td class="text-end fw-bold">${formatInt(item.QUANTITY_SOLD)}</td>
                        <td class="text-end text-primary fw-bold">${formatUSD(item.REVENUE)}</td>
                    </tr>
                `).join("") || `<tr><td colspan="5" class="text-center text-muted py-4">No revenue data available</td></tr>`;
            }

            // Category table
            const tbodyCat = document.getElementById("tbodyRevByCategory");
            if (tbodyCat) {
                tbodyCat.innerHTML = revenue_by_category.map((cat) => `
                    <tr>
                        <td class="fw-bold text-dark">${cat.CATEGORY_NAME}</td>
                        <td class="text-end">${formatInt(cat.TOTAL_ORDERS)}</td>
                        <td class="text-end">${formatInt(cat.QUANTITY_SOLD)}</td>
                        <td class="text-end text-success fw-bold">${formatUSD(cat.REVENUE)}</td>
                    </tr>
                `).join("") || `<tr><td colspan="4" class="text-center text-muted py-4">No category data available</td></tr>`;
            }

            // City table
            const tbodyCity = document.getElementById("tbodyRevByCity");
            if (tbodyCity) {
                tbodyCity.innerHTML = revenue_by_city.map((city) => `
                    <tr>
                        <td class="fw-bold text-dark">${city.CITY}</td>
                        <td><span class="text-muted">${city.STATE}</span></td>
                        <td class="text-end">${formatInt(city.TOTAL_ORDERS)}</td>
                        <td class="text-end">${formatInt(city.QUANTITY_SOLD)}</td>
                        <td class="text-end text-primary fw-bold">${formatUSD(city.REVENUE)}</td>
                    </tr>
                `).join("") || `<tr><td colspan="5" class="text-center text-muted py-4">No city data available</td></tr>`;
            }
        }
    } catch (err) {
        console.error("Error fetching revenue breakdown:", err);
    }
}

// ==============================================================================
// 4. FEATURE 2: BEST-SELLING PRODUCTS
// ==============================================================================
async function fetchBestSellingProducts() {
    try {
        const url = `/api/best-selling-products${buildQueryString()}${buildQueryString() ? "&" : "?"}sortBy=${state.currentSortProducts}&limit=10`;
        const res = await fetch(url);
        const json = await res.json();
        if (json.status === "success" && json.data) {
            const { products, chart_data } = json.data;

            // Render Table
            const tbody = document.getElementById("tbodyBestSellingProducts");
            if (tbody) {
                tbody.innerHTML = products.map((p, idx) => {
                    const rankClass = idx === 0 ? "rank-gold" : idx === 1 ? "rank-silver" : idx === 2 ? "rank-bronze" : "rank-default";
                    const stockBadge = p.STOCK_QUANTITY <= 40 
                        ? `<span class="badge bg-warning text-dark"><i class="fa-solid fa-triangle-exclamation me-1"></i>Low (${p.STOCK_QUANTITY})</span>`
                        : `<span class="badge bg-soft-success text-success"><i class="fa-solid fa-circle-check me-1"></i>In Stock</span>`;

                    return `
                        <tr>
                            <td><span class="rank-badge ${rankClass}">${p.RANK || (idx + 1)}</span></td>
                            <td class="fw-semibold text-dark">${p.PRODUCT_NAME}</td>
                            <td><span class="badge bg-light text-secondary border">${p.CATEGORY_NAME}</span></td>
                            <td class="text-end">${formatUSD(p.UNIT_PRICE)}</td>
                            <td class="text-end fw-bold text-dark">${formatInt(p.TOTAL_QUANTITY_SOLD)}</td>
                            <td class="text-end text-primary fw-bold">${formatUSD(p.TOTAL_REVENUE)}</td>
                            <td class="text-end text-muted">${formatInt(p.STOCK_QUANTITY)}</td>
                            <td class="text-center">${stockBadge}</td>
                        </tr>
                    `;
                }).join("") || `<tr><td colspan="8" class="text-center text-muted py-4">No products found</td></tr>`;
            }

            // Render Chart
            renderTopProductsChart(chart_data);
        }
    } catch (err) {
        console.error("Error fetching best-selling products:", err);
    }
}

function renderTopProductsChart(chartData) {
    const canvas = document.getElementById("topProductsChart");
    if (!canvas || !chartData) return;

    if (state.charts.topProducts) {
        state.charts.topProducts.destroy();
    }

    const ctx = canvas.getContext("2d");
    state.charts.topProducts = new Chart(ctx, {
        type: "bar",
        data: {
            labels: chartData.labels.map(l => l.length > 20 ? l.slice(0, 18) + "..." : l),
            datasets: [
                {
                    label: "Quantity Sold",
                    data: chartData.quantities,
                    backgroundColor: "rgba(59, 130, 246, 0.85)",
                    hoverBackgroundColor: "rgba(30, 64, 175, 1)",
                    borderRadius: 6,
                    yAxisID: "y"
                },
                {
                    label: "Revenue ($)",
                    data: chartData.revenues,
                    backgroundColor: "rgba(16, 185, 129, 0.4)",
                    borderColor: "rgba(16, 185, 129, 1)",
                    borderWidth: 1.5,
                    type: "line",
                    yAxisID: "y1"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { position: "top", labels: { font: { family: "Plus Jakarta Sans", size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            if (context.dataset.yAxisID === "y1") {
                                return `Revenue: ${formatUSD(context.raw)}`;
                            }
                            return `Units Sold: ${formatInt(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                y: {
                    type: "linear",
                    position: "left",
                    title: { display: true, text: "Units Sold", font: { size: 11 } },
                    grid: { color: "#f1f5f9" }
                },
                y1: {
                    type: "linear",
                    position: "right",
                    title: { display: true, text: "Revenue ($)", font: { size: 11 } },
                    grid: { display: false },
                    ticks: { callback: (v) => `$${v >= 1000 ? (v/1000).toFixed(0) + 'k' : v}` }
                }
            }
        }
    });
}

// ==============================================================================
// 5. FEATURE 3: MONTHLY SALES ANALYSIS
// ==============================================================================
async function fetchMonthlySalesData() {
    try {
        const res = await fetch(`/api/monthly-sales${buildQueryString()}`);
        const json = await res.json();
        if (json.status === "success" && json.data) {
            const { monthly_data, peak_month, chart_data } = json.data;

            // Highlight Peak Month in Executive Overview
            if (peak_month) {
                const badge = document.getElementById("overviewPeakMonthBadge");
                if (badge) badge.textContent = `Peak: ${peak_month.month} (${formatUSD(peak_month.revenue)})`;
            }

            // Render Table
            const tbody = document.getElementById("tbodyMonthlySales");
            if (tbody) {
                tbody.innerHTML = monthly_data.map((m) => {
                    const momVal = Number(m.MOM_GROWTH_PERCENT) || 0;
                    const momBadge = momVal > 0 
                        ? `<span class="text-success fw-bold"><i class="fa-solid fa-arrow-trend-up me-1"></i>+${momVal.toFixed(2)}%</span>`
                        : momVal < 0
                        ? `<span class="text-danger fw-bold"><i class="fa-solid fa-arrow-trend-down me-1"></i>${momVal.toFixed(2)}%</span>`
                        : `<span class="text-muted">--</span>`;

                    const isPeak = m.STATUS_FLAG === "Peak Month";
                    const statusTag = isPeak 
                        ? `<span class="badge bg-primary"><i class="fa-solid fa-star me-1"></i>Highest Month</span>`
                        : `<span class="badge bg-light text-muted border">Normal</span>`;

                    return `
                        <tr class="${isPeak ? 'table-primary bg-opacity-10' : ''}">
                            <td class="fw-bold text-dark">${m.SALES_MONTH}</td>
                            <td class="text-end">${formatInt(m.ORDER_COUNT)}</td>
                            <td class="text-end">${formatInt(m.UNITS_SOLD)}</td>
                            <td class="text-end text-primary fw-bold">${formatUSD(m.MONTHLY_REVENUE)}</td>
                            <td class="text-end text-muted">${formatUSD(m.MONTHLY_AOV)}</td>
                            <td class="text-end">${momBadge}</td>
                            <td class="text-center">${statusTag}</td>
                        </tr>
                    `;
                }).join("") || `<tr><td colspan="7" class="text-center text-muted py-4">No monthly records available</td></tr>`;
            }

            // Render Line Chart
            renderMonthlyTrendChart(chart_data);
        }
    } catch (err) {
        console.error("Error fetching monthly sales:", err);
    }
}

function renderMonthlyTrendChart(chartData) {
    const canvas = document.getElementById("monthlyTrendChart");
    if (!canvas || !chartData) return;

    if (state.charts.monthlyTrend) {
        state.charts.monthlyTrend.destroy();
    }

    const ctx = canvas.getContext("2d");
    state.charts.monthlyTrend = new Chart(ctx, {
        type: "line",
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: "Monthly Revenue ($)",
                    data: chartData.revenues,
                    borderColor: "#1e40af",
                    backgroundColor: "rgba(30, 64, 175, 0.08)",
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: "#1e40af",
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    yAxisID: "y"
                },
                {
                    label: "Orders Fulfilled",
                    data: chartData.orders,
                    type: "bar",
                    backgroundColor: "rgba(59, 130, 246, 0.25)",
                    hoverBackgroundColor: "rgba(59, 130, 246, 0.5)",
                    borderRadius: 4,
                    yAxisID: "y1"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { position: "top", labels: { font: { family: "Plus Jakarta Sans", size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            if (context.dataset.yAxisID === "y") {
                                return `Revenue: ${formatUSD(context.raw)}`;
                            }
                            return `Orders: ${formatInt(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                y: {
                    type: "linear",
                    position: "left",
                    title: { display: true, text: "Revenue ($)", font: { size: 11 } },
                    grid: { color: "#f1f5f9" },
                    ticks: { callback: (v) => `$${v >= 1000 ? (v/1000).toFixed(0) + 'k' : v}` }
                },
                y1: {
                    type: "linear",
                    position: "right",
                    title: { display: true, text: "Order Count", font: { size: 11 } },
                    grid: { display: false }
                }
            }
        }
    });
}

// ==============================================================================
// 6. FEATURE 4: TOP CUSTOMERS
// ==============================================================================
async function fetchTopCustomers() {
    try {
        const res = await fetch(`/api/top-customers${buildQueryString()}&limit=10`);
        const json = await res.json();
        if (json.status === "success" && json.data) {
            state.cachedCustomers = json.data.customers || [];
            renderCustomerTable(state.cachedCustomers);
        }
    } catch (err) {
        console.error("Error fetching top customers:", err);
    }
}

function renderCustomerTable(customers) {
    const tbody = document.getElementById("tbodyTopCustomers");
    if (!tbody) return;

    tbody.innerHTML = customers.map((c, idx) => {
        const rankClass = idx === 0 ? "rank-gold" : idx === 1 ? "rank-silver" : idx === 2 ? "rank-bronze" : "rank-default";
        const tierBadge = c.VIP_TIER === "Platinum Elite"
            ? `<span class="badge bg-primary"><i class="fa-solid fa-crown me-1"></i>Platinum</span>`
            : c.VIP_TIER === "Gold VIP"
            ? `<span class="badge bg-warning text-dark"><i class="fa-solid fa-gem me-1"></i>Gold</span>`
            : `<span class="badge bg-secondary">Silver</span>`;

        return `
            <tr>
                <td><span class="rank-badge ${rankClass}">${c.RANK || (idx + 1)}</span></td>
                <td class="fw-bold text-dark">${c.CUSTOMER_NAME}</td>
                <td><span class="text-muted">${c.EMAIL}</span></td>
                <td><span class="text-secondary">${c.CITY}, ${c.STATE}</span></td>
                <td class="text-end fw-semibold">${formatInt(c.TOTAL_ORDERS)}</td>
                <td class="text-end">${formatInt(c.TOTAL_ITEMS_BOUGHT)}</td>
                <td class="text-end text-primary fw-bold">${formatUSD(c.TOTAL_SPENDING)}</td>
                <td class="text-end text-success">${formatUSD(c.AVERAGE_ORDER_VALUE)}</td>
                <td class="text-center">${tierBadge}</td>
            </tr>
        `;
    }).join("") || `<tr><td colspan="9" class="text-center text-muted py-4">No matching customers found</td></tr>`;
}

function filterCustomerTable(searchTerm) {
    if (!searchTerm) {
        renderCustomerTable(state.cachedCustomers);
        return;
    }
    const filtered = state.cachedCustomers.filter(c => 
        c.CUSTOMER_NAME.toLowerCase().includes(searchTerm) ||
        c.EMAIL.toLowerCase().includes(searchTerm) ||
        c.CITY.toLowerCase().includes(searchTerm) ||
        c.STATE.toLowerCase().includes(searchTerm)
    );
    renderCustomerTable(filtered);
}

// ==============================================================================
// 7. FEATURE 5: PRODUCT CATEGORY COMPARISON
// ==============================================================================
async function fetchCategoryData() {
    try {
        const res = await fetch(`/api/category-analysis${buildQueryString()}`);
        const json = await res.json();
        if (json.status === "success" && json.data) {
            const { categories, chart_data } = json.data;

            // Render Table
            const tbody = document.getElementById("tbodyCategories");
            if (tbody) {
                tbody.innerHTML = categories.map((cat, idx) => {
                    const rankClass = idx === 0 ? "rank-gold" : idx === 1 ? "rank-silver" : idx === 2 ? "rank-bronze" : "rank-default";
                    const isTop = idx === 0;
                    return `
                        <tr class="${isTop ? 'table-success bg-opacity-10' : ''}">
                            <td><span class="rank-badge ${rankClass}">${cat.CATEGORY_RANK || (idx + 1)}</span></td>
                            <td class="fw-bold text-dark">${cat.CATEGORY_NAME}</td>
                            <td class="text-end">${formatInt(cat.DISTINCT_PRODUCTS)}</td>
                            <td class="text-end">${formatInt(cat.TOTAL_ORDERS)}</td>
                            <td class="text-end">${formatInt(cat.TOTAL_QUANTITY_SOLD)}</td>
                            <td class="text-end text-primary fw-bold">${formatUSD(cat.TOTAL_REVENUE)}</td>
                            <td class="text-end fw-bold text-success">${cat.REVENUE_SHARE_PERCENT}%</td>
                            <td class="text-center">
                                ${isTop ? '<span class="badge bg-success">Top Category</span>' : '<span class="badge bg-light text-muted border">Standard</span>'}
                            </td>
                        </tr>
                    `;
                }).join("") || `<tr><td colspan="8" class="text-center text-muted py-4">No categories found</td></tr>`;
            }

            // Render Doughnut Chart
            renderCategoryShareChart(chart_data);
        }
    } catch (err) {
        console.error("Error fetching category analysis:", err);
    }
}

function renderCategoryShareChart(chartData) {
    const canvas = document.getElementById("categoryShareChart");
    if (!canvas || !chartData) return;

    if (state.charts.categoryShare) {
        state.charts.categoryShare.destroy();
    }

    const colorPalette = [
        "#1e40af", "#3b82f6", "#10b981", "#f59e0b",
        "#8b5cf6", "#ec4899", "#06b6d4", "#64748b"
    ];

    const ctx = canvas.getContext("2d");
    state.charts.categoryShare = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    data: chartData.revenues,
                    backgroundColor: colorPalette,
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { boxWidth: 12, font: { family: "Plus Jakarta Sans", size: 10 } }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const val = context.raw;
                            return ` ${context.label}: ${formatUSD(val)}`;
                        }
                    }
                }
            },
            cutout: "65%"
        }
    });
}

// ==============================================================================
// 8. FEATURE 6: HIGH-REVENUE CITIES
// ==============================================================================
async function fetchCitiesData() {
    try {
        const res = await fetch(`/api/city-analysis${buildQueryString()}&limit=12`);
        const json = await res.json();
        if (json.status === "success" && json.data) {
            const { cities, chart_data } = json.data;

            // Render Table
            const tbody = document.getElementById("tbodyCities");
            if (tbody) {
                tbody.innerHTML = cities.map((c, idx) => {
                    const rankClass = idx === 0 ? "rank-gold" : idx === 1 ? "rank-silver" : idx === 2 ? "rank-bronze" : "rank-default";
                    return `
                        <tr>
                            <td><span class="rank-badge ${rankClass}">${c.RANK || (idx + 1)}</span></td>
                            <td class="fw-bold text-dark">${c.CITY}</td>
                            <td><span class="text-muted">${c.STATE}</span></td>
                            <td class="text-end">${formatInt(c.CUSTOMER_COUNT)}</td>
                            <td class="text-end">${formatInt(c.TOTAL_ORDERS)}</td>
                            <td class="text-end">${formatInt(c.TOTAL_UNITS_SOLD)}</td>
                            <td class="text-end text-primary fw-bold">${formatUSD(c.TOTAL_REVENUE)}</td>
                            <td class="text-end text-success">${formatUSD(c.AOV_PER_CITY)}</td>
                        </tr>
                    `;
                }).join("") || `<tr><td colspan="8" class="text-center text-muted py-4">No cities found</td></tr>`;
            }

            // Render Horizontal Bar Chart
            renderCitiesChart(chart_data);
        }
    } catch (err) {
        console.error("Error fetching city analysis:", err);
    }
}

function renderCitiesChart(chartData) {
    const canvas = document.getElementById("citiesChart");
    if (!canvas || !chartData) return;

    if (state.charts.cities) {
        state.charts.cities.destroy();
    }

    const ctx = canvas.getContext("2d");
    state.charts.cities = new Chart(ctx, {
        type: "bar",
        data: {
            labels: chartData.labels.slice(0, 8),
            datasets: [
                {
                    label: "Revenue ($)",
                    data: chartData.revenues.slice(0, 8),
                    backgroundColor: "rgba(30, 64, 175, 0.8)",
                    borderRadius: 4
                }
            ]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` Revenue: ${formatUSD(ctx.raw)}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: "#f1f5f9" },
                    ticks: { callback: (v) => `$${v >= 1000 ? (v/1000).toFixed(0) + 'k' : v}` }
                },
                y: { grid: { display: false }, ticks: { font: { size: 10 } } }
            }
        }
    });
}

// ==============================================================================
// 9. FEATURE 7: BUSINESS INSIGHTS GENERATOR (DYNAMIC SQL DRIVEN)
// ==============================================================================
async function fetchBusinessInsights() {
    try {
        const container = document.getElementById("insightsContainer");
        const recContainer = document.getElementById("recommendationsContainer");
        if (!container) return;

        const res = await fetch(`/api/business-insights${buildQueryString()}`);
        const json = await res.json();
        if (json.status === "success" && json.data) {
            const { core_insights, strategic_recommendations } = json.data;

            // Render Insights Cards
            if (core_insights && core_insights.length > 0) {
                container.innerHTML = core_insights.map((ins) => `
                    <div class="col-md-6 col-lg-6">
                        <div class="insight-card card-${ins.type || 'primary'}">
                            <i class="fa-solid ${ins.icon || 'fa-chart-pie'} insight-icon"></i>
                            <div>
                                <div class="insight-header">
                                    <span class="insight-badge bg-soft-${ins.type || 'primary'}">${ins.badge || 'Insight'}</span>
                                    <h6 class="insight-title">${ins.title}</h6>
                                </div>
                                <p class="insight-description">${ins.description}</p>
                            </div>
                        </div>
                    </div>
                `).join("");
            } else {
                container.innerHTML = `<div class="col-12 text-center text-muted py-4">No business insights generated for selected criteria.</div>`;
            }

            // Render Strategic Recommendations
            if (recContainer && strategic_recommendations && strategic_recommendations.length > 0) {
                recContainer.innerHTML = strategic_recommendations.map((rec) => `
                    <div class="recommendation-item">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="badge bg-soft-primary text-primary fw-bold text-xs">${rec.category}</span>
                            <span class="text-xs text-muted"><i class="fa-solid fa-lightbulb text-warning me-1"></i>Actionable Strategy</span>
                        </div>
                        <h6 class="fw-bold text-dark mb-1">${rec.title}</h6>
                        <p class="text-secondary small mb-0">${rec.action}</p>
                    </div>
                `).join("");
            }
        }
    } catch (err) {
        console.error("Error generating business insights:", err);
    }
}

// ==============================================================================
// 10. ORACLE SQL WORKBENCH / QUERY CATALOG
// ==============================================================================
async function fetchSqlQueriesCatalog() {
    try {
        const container = document.getElementById("sqlQueriesContainer");
        if (!container) return;

        const res = await fetch("/api/sql-queries");
        const json = await res.json();
        if (json.status === "success" && json.queries) {
            container.innerHTML = json.queries.map((q) => `
                <div class="sql-query-card shadow-sm">
                    <div class="sql-query-header">
                        <div>
                            <h6 class="sql-query-title"><i class="fa-solid fa-code text-info me-2"></i>${q.title}</h6>
                            <span class="sql-query-meta">Features: ${q.features_used}</span>
                        </div>
                        <button class="btn btn-sm btn-outline-light" onclick="copySqlCode('${q.id}')">
                            <i class="fa-solid fa-copy me-1"></i> Copy SQL
                        </button>
                    </div>
                    <pre class="sql-query-code" id="sql_code_${q.id}">${escapeHtml(q.query)}</pre>
                </div>
            `).join("");
        }
    } catch (err) {
        console.error("Error loading SQL queries catalog:", err);
    }
}

function copySqlCode(queryId) {
    const el = document.getElementById(`sql_code_${queryId}`);
    if (el) {
        navigator.clipboard.writeText(el.innerText).then(() => {
            alert("Oracle SQL Query copied to clipboard!");
        });
    }
}

function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
