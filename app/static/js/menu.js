(function () {
  const modal = document.getElementById("mealModal");
  const closeBtn = document.getElementById("closeModal");

  const mLabel = document.getElementById("mLabel");
  const mTitle = document.getElementById("mTitle");
  const mIngredients = document.getElementById("mIngredients");
  const mPrep = document.getElementById("mPrep");
  const mTips = document.getElementById("mTips");
  const tipsWrap = document.getElementById("tipsWrap");

  function openModal(data) {
    if (!modal) return;

    mLabel.textContent = data.label || "";
    mTitle.textContent = data.title || "";
    mIngredients.textContent = data.ingredients || "—";
    mPrep.textContent = data.prep || "—";

    const tips = (data.tips || "").trim();
    if (tips) {
      tipsWrap.style.display = "block";
      mTips.textContent = tips;
    } else {
      tipsWrap.style.display = "none";
      mTips.textContent = "";
    }

    modal.classList.add("show");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  document.querySelectorAll(".meal-card").forEach((btn) => {
    btn.addEventListener("click", () => {
      openModal({
        label: btn.dataset.label,
        title: btn.dataset.title,
        ingredients: btn.dataset.ingredients,
        prep: btn.dataset.prep,
        tips: btn.dataset.tips
      });
    });
  });

  if (closeBtn) closeBtn.addEventListener("click", closeModal);

  // clicar no fundo fecha
  if (modal) {
    modal.addEventListener("click", (e) => {
      const target = e.target;
      if (target && target.dataset && target.dataset.close) closeModal();
    });
  }

  // ESC fecha
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
})();
