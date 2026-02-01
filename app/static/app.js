(function () {
  // Máscara simples de telefone BR (não é perfeita, mas ajuda bastante).
  const phone = document.getElementById("phone");
  if (phone) {
    const format = (digits) => {
      digits = (digits || "").replace(/\D+/g, "").slice(0, 13);

      // Formatos:
      // 10: (11) 9999-9999
      // 11: (11) 99999-9999
      if (digits.length <= 2) return digits;
      const ddd = digits.slice(0, 2);
      const rest = digits.slice(2);

      if (rest.length <= 4) return `(${ddd}) ${rest}`;
      if (rest.length <= 8) return `(${ddd}) ${rest.slice(0, 4)}-${rest.slice(4)}`;
      if (rest.length <= 9) return `(${ddd}) ${rest.slice(0, 5)}-${rest.slice(5)}`;

      // Se vier com 12-13 (ex. país), só deixa cru
      return digits;
    };

    const onInput = () => {
      const raw = phone.value;
      const digits = raw.replace(/\D+/g, "");
      // Só formata se parecer BR local (10-11)
      if (digits.length <= 11) {
        phone.value = format(digits);
      } else {
        phone.value = digits.slice(0, 13);
      }
    };

    phone.addEventListener("input", onInput);
  }
})();
