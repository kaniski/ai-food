(function () {
  const bar = document.getElementById("progressBar");
  let pct = 0;

  const tick = setInterval(() => {
    pct += 4; // vai chegar perto de 100 em ~2.5s
    if (pct > 100) pct = 100;
    if (bar) bar.style.width = pct + "%";
    if (pct === 100) clearInterval(tick);
  }, 100);

  // 3 segundos cravados, depois manda pro cardápio
  setTimeout(() => {
    window.location.href = "/menu";
  }, 3000);
})();
