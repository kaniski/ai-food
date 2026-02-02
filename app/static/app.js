(function () {
  function onlyDigits(s) {
    return (s || "").replace(/\D+/g, "");
  }

  function formatPhoneBR(d) {
    if (!d) return "";
    if (d.length <= 2) return `(${d}`;
    const dd = d.slice(0, 2);
    const rest = d.slice(2);

    if (rest.length <= 4) return `(${dd}) ${rest}`;
    if (rest.length <= 8) return `(${dd}) ${rest.slice(0, 4)}-${rest.slice(4)}`;
    return `(${dd}) ${rest.slice(0, 5)}-${rest.slice(5, 9)}`;
  }

  document.querySelectorAll('[data-mask="phone"]').forEach((input) => {
    input.addEventListener("input", () => {
      const d = onlyDigits(input.value).slice(0, 13);
      input.value = formatPhoneBR(d);
    });
  });
})();
