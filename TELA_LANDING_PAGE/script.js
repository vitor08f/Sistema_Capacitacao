(() => {
  "use strict";

  // Ano atual no rodapé
  const ano = document.getElementById("ano");
  if (ano) {
    const y = new Date().getFullYear();
    ano.textContent = y;
    ano.dateTime = y;
  }

  // FAQ: mantém apenas uma pergunta aberta por vez
  const faq = document.querySelectorAll("#perguntas-frequentes details");
  faq.forEach((item) =>
    item.addEventListener("toggle", () => {
      if (item.open) faq.forEach((o) => o !== item && (o.open = false));
    })
  );

  // Destaca no menu a seção visível
  const links = document.querySelectorAll('nav a[href^="#"]');
  const alvos = [...links]
    .map((a) => document.querySelector(a.getAttribute("href")))
    .filter(Boolean);
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entradas) =>
        entradas.forEach((e) => {
          if (!e.isIntersecting) return;
          links.forEach((a) =>
            a.getAttribute("href") === "#" + e.target.id ? a.setAttribute("aria-current", "true") : a.removeAttribute("aria-current")
          );
        }),
      { rootMargin: "-40% 0px -55% 0px" }
    );
    alvos.forEach((s) => io.observe(s));
  }

  // Formulário em etapas (breadcrumb)
  const form = document.getElementById("form-contato");
  if (form) {
    const steps = [...form.querySelectorAll(".step")];
    const crumbs = form.querySelector(".crumbs");
    const crumbBtns = [...crumbs.querySelectorAll("button")];
    const back = form.querySelector("[data-back]");
    const cta = form.querySelector(".cta");
    const status = document.getElementById("status");
    const data = form.elements.data;
    let atual = 0;

    // Datas: de amanhã em diante, só dias úteis
    const amanha = new Date();
    amanha.setDate(amanha.getDate() + 1);
    data.min = amanha.toISOString().slice(0, 10);
    data.addEventListener("input", () => {
      const dia = data.valueAsDate ? data.valueAsDate.getUTCDay() : 1;
      data.setCustomValidity(dia === 0 || dia === 6 ? "Escolha um dia útil, de segunda a sexta." : "");
    });

    const validar = (i) => {
      let primeiro = null;
      steps[i].querySelectorAll("input,select,textarea").forEach((el) => {
        if (!el.willValidate) return;
        const ok = el.checkValidity();
        el.setAttribute("aria-invalid", ok ? "false" : "true");
        if (!ok && !primeiro) primeiro = el;
      });
      if (primeiro) {
        status.className = "erro";
        status.textContent = primeiro.validationMessage || "Revise os campos destacados.";
        primeiro.focus();
      }
      return !primeiro;
    };

    const ir = (i, foco) => {
      atual = i;
      steps.forEach((s, n) => (s.hidden = n !== i));
      crumbBtns.forEach((b, n) => {
        b.disabled = n > i;
        n === i ? b.setAttribute("aria-current", "step") : b.removeAttribute("aria-current");
      });
      back.hidden = i === 0;
      cta.textContent = i === steps.length - 1 ? "Agendar minha consulta" : "Continuar";
      status.className = "";
      status.textContent = "";
      if (foco) steps[i].querySelector("legend").focus();
    };

    crumbs.hidden = false;
    ir(0, false);
    back.addEventListener("click", () => ir(atual - 1, true));
    crumbBtns.forEach((b, n) => b.addEventListener("click", () => ir(n, true)));

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (!validar(atual)) return;
      if (atual < steps.length - 1) return ir(atual + 1, true);
      if (form.elements.site.value) return; // anti-spam

      const f = new FormData(form);
      const [a, m, d] = f.get("data").split("-");
      const corpo = [
        "Nome: " + f.get("nome"),
        "E-mail: " + f.get("email"),
        "Telefone: " + f.get("telefone"),
        "Área: " + f.get("area"),
        "Data e horário preferidos: " + d + "/" + m + "/" + a + " às " + f.get("hora"),
        "Formato: " + f.get("formato"),
        "Resumo: " + (f.get("mensagem") || "não informado"),
      ].join("\n");
      window.location.href =
        "mailto:contato@pereiramonteiro.adv.br?subject=" +
        encodeURIComponent("Pedido de horário - " + f.get("nome")) +
        "&body=" + encodeURIComponent(corpo);
      status.textContent = "Quase lá: envie o e-mail que abrimos para concluir o pedido.";
    });
  }
})();