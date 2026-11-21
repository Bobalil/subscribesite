(function () {
  const KEY = "preferred_currency";
  const current = localStorage.getItem(KEY) || "RUB";
  document.querySelectorAll("[data-currency-switcher]").forEach((el) => {
    el.value = current;
    el.addEventListener("change", async (e) => {
      const to = e.target.value;
      localStorage.setItem(KEY, to);
      await fetch(`/currency/rate`).then(r => r.json()).then(d => {
        document.querySelectorAll("[data-price-rub]").forEach((node) => {
          const rub = parseFloat(node.dataset.priceRub);
          if (to === "USD") {
            node.textContent = "$" + (rub / d.USD_RUB).toFixed(2);
          } else {
            node.textContent = rub.toFixed(2) + " ₽";
          }
        });
      });
    });
  });
})();