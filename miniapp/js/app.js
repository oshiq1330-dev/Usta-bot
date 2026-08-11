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
    }


    // Mahsulot qo‘shish tugmalari
    const addButtons = document.querySelectorAll(
        ".action-card.add, .primary-btn"
    );

    addButtons.forEach(button => {

        button.addEventListener("click", () => {

            alert(
                "➕ Mahsulot qo‘shish bo‘limi tez orada ishlaydi."
            );

        });

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
