/* КР №2: небольшое дополнение к Bootstrap, без корзины и backend.
   Bootstrap Bundle отвечает за modal, navbar, tabs и accordion. */
const form = document.getElementById("order-form");
const product = document.getElementById("product");
const requestedProduct = new URLSearchParams(window.location.search).get(
  "product",
);

// Принимаем из URL только значение, существующее среди вариантов select.
if (
  requestedProduct &&
  [...product.options].some((option) => option.value === requestedProduct)
) {
  product.value = requestedProduct;
}

form.addEventListener("submit", (event) => {
  // Браузер выполняет required/type/pattern до события submit.
  // При недоступном Bootstrap работает обычный переход на резервную страницу.
  if (!window.bootstrap?.Modal) return;
  event.preventDefault();
  document.getElementById("request-product").textContent =
    `Ваш выбор: ${product.selectedOptions[0].textContent}`;
  const modalElement = document.getElementById("requestModal");
  bootstrap.Modal.getOrCreateInstance(modalElement).show();
});

// При программном открытии Bootstrap не знает кнопку-инициатор.
// Возвращаем фокус после закрытия результата самостоятельно.
document
  .getElementById("requestModal")
  .addEventListener("hidden.bs.modal", () => {
    form.querySelector('[type="submit"]').focus();
  });
