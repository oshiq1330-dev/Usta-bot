// ================================
// USTABOT MINI APP
// ================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("UstaBot Mini App ishga tushdi");
    alert("🔥 USTABOT JS ISHLADI");

    // Telegram Mini App
    if (window.Telegram && Telegram.WebApp) {

        const tg = Telegram.WebApp;

        tg.ready();
        tg.expand();

        console.log("Telegram Mini App ulandi");

        console.log(
            "Telegram user:",
            tg.initDataUnsafe?.user
        );

        console.log("Telegram initData:", tg.initData);

        console.log("INIT DATA BOR:", !!tg.initData);
        console.log("USER ID:", tg.initDataUnsafe?.user?.id);
    }

    // ================================
    // API
    // ================================

    const API_URL = "https://rough-colorado-amendment-brick.trycloudflare.com";

    async function loadProducts() {
        alert("🔥 LOADPRODUCTS FUNKSIYAGA KIRDI");
        console.log("🔥 loadProducts() ishladi");

        try {
            const tg = Telegram.WebApp;

            alert(
                "initData: " + (tg.initData ? "BOR ✅" : "YO‘Q ❌") +
                "\nuser: " + (tg.initDataUnsafe?.user?.id || "YO‘Q ❌") +
                "\nplatform: " + (tg.platform || "noma'lum")
            );

            if (!tg.initData) {
                console.error("❌ Telegram initData mavjud emas");
                return;
            }

            const response = await fetch(
                `${API_URL}/api/products`,
                {
                    headers: {
                        "X-Telegram-Init-Data": tg.initData
                    }
                }
            );

            const data = await response.json();

            console.log("📦 API PRODUCTS:", data);
            alert(
                "API javobi:\n" +
                JSON.stringify(data, null, 2)
            );

            // ================================
            // MAHSULOTLARNI EKRANGA CHIQARISH
            // ================================

            const productsList = document.getElementById("productsList");

            if (!productsList) {
                console.error("❌ productsList topilmadi");
                return;
            }

            productsList.innerHTML = "";

            if (!Array.isArray(data) || data.length === 0) {
                productsList.innerHTML = `
                    <div class="empty-products">
                        <div class="empty-icon">📦</div>
                        <h3>Hali mahsulotlar yo‘q</h3>
                        <p>Do‘koningizga mahsulot qo‘shishni boshlang.</p>
                    </div>
                `;

                return;
            }

            data.forEach(product => {

                const card = document.createElement("div");

                card.className = "product-card";

                card.innerHTML = `
                    <div class="product-icon">📦</div>

                    <div class="product-info">
                        <h3>${product.name}</h3>

                        <p class="product-category">
                            ${product.category || ""}
                        </p>

                        <p class="product-price">
                            ${Number(product.price).toLocaleString("uz-UZ")} so‘m
                            / ${product.unit || "dona"}
                        </p>

                        <p class="product-quantity">
                            Mavjud: ${product.quantity}
                        </p>
                    </div>
                `;

                productsList.appendChild(card);
            });

        } catch (error) {
            console.error("❌ API ERROR:", error);
        }
    }

    console.log("🔥 LOAD PRODUCTS START");
    loadProducts();

    // ================================
    // ADD PRODUCT
    // ================================

    const addProductModal = document.getElementById("addProductModal");
    const closeProductModal = document.getElementById("closeProductModal");
    const saveProduct = document.getElementById("saveProduct");

    const addButtons = document.querySelectorAll(
        ".action-card.add, .primary-btn"
    );

    addButtons.forEach(button => {
        button.addEventListener("click", () => {
            addProductModal.classList.remove("hidden");
        });
    });

    closeProductModal.addEventListener("click", () => {
        addProductModal.classList.add("hidden");
    });

    addProductModal.addEventListener("click", (event) => {
        if (event.target === addProductModal) {
            addProductModal.classList.add("hidden");
        }
    });

    saveProduct.addEventListener("click", () => {

        const name = document.getElementById("productName").value.trim();
        const category = document.getElementById("productCategory").value;
        const price = document.getElementById("productPrice").value;
        const unit = document.getElementById("productUnit").value;
        const quantity = document.getElementById("productQuantity").value;

        if (!name) {
            alert("❌ Mahsulot nomini kiriting");
            return;
        }

        if (!category) {
            alert("❌ Kategoriyani tanlang");
            return;
        }

        if (!price) {
            alert("❌ Mahsulot narxini kiriting");
            return;
        }

        if (!quantity) {
            alert("❌ Mavjud miqdorni kiriting");
            return;
        }

        console.log("Yangi mahsulot:", {
            name,
            category,
            price,
            unit,
            quantity
        });

        const productData = {
            action: "add_product",
            name: name,
            category: category,
            price: price,
            unit: unit,
            quantity: quantity
        };

        if (window.Telegram && Telegram.WebApp) {
            Telegram.WebApp.sendData(
                JSON.stringify(productData)
            );
        } else {
            alert("❌ Telegram Mini App topilmadi");
        }

        addProductModal.classList.add("hidden");
     });

    // Pastki menyu
    const navButtons = document.querySelectorAll(
        ".bottom-nav button"
    );

    navButtons.forEach(button => {

        button.addEventListener("click", () => {

            navButtons.forEach(item => {
                item.classList.remove("active");
            });

            button.classList.add("active");

            const name =
                button.querySelector("span")?.textContent;

            console.log(
                "Tanlangan bo‘lim:",
                name
            );
        });

    });

        // =====================================
    // PRODUCTS WINDOW
    // =====================================

    const productsModal =
        document.getElementById("productsModal");

    const closeProductsModal =
        document.getElementById("closeProductsModal");

    const productsButton =
        document.querySelector(
            ".bottom-nav button:nth-child(2)"
        );

    const seeAllButton =
        document.querySelector(".see-all");

    function openProductsModal() {
        if (productsModal) {
            productsModal.classList.remove("hidden");
        }
    }

    function closeProductsWindow() {
        if (productsModal) {
            productsModal.classList.add("hidden");
        }
    }

    if (productsButton) {
        productsButton.addEventListener(
            "click",
            openProductsModal
        );
    }

    if (seeAllButton) {
        seeAllButton.addEventListener(
            "click",
            openProductsModal
        );
    }

    if (closeProductsModal) {
        closeProductsModal.addEventListener(
            "click",
            closeProductsWindow
        );
    }

    if (productsModal) {
        productsModal.addEventListener(
            "click",
            (event) => {

                if (event.target === productsModal) {
                    closeProductsWindow();
                }

            }
        );
    }

});
