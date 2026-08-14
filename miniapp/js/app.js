// ================================
// USTABOT MINI APP
// ================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("UstaBot Mini App ishga tushdi");

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
    }


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

});
