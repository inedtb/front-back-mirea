/* Единственная JavaScript-логика проекта: открытие и закрытие <dialog>.
   Навигация, формы, раскрывающиеся ответы и категории работают без JavaScript. */
document.querySelectorAll("[data-dialog-open]").forEach((link) => {
  link.addEventListener("click", (event) => {
    const dialog = document.getElementById(link.dataset.dialogOpen);
    if (dialog && typeof dialog.showModal === "function") {
      event.preventDefault();
      dialog.showModal();
    }
  });
});
document.querySelectorAll("[data-dialog-close]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});
// Escape, удержание фокуса и возврат фокуса выполняет сам браузер.
