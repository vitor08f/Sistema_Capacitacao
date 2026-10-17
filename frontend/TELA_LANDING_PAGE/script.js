(() => {
  "use strict";

  const elementoAno = document.getElementById("ano");
  if (elementoAno) {
    const anoAtual = new Date().getFullYear();
    elementoAno.textContent = String(anoAtual);
    elementoAno.dateTime = String(anoAtual);
  }

  const perguntasFrequentes = document.querySelectorAll("#perguntas-frequentes details");
  perguntasFrequentes.forEach((pergunta) => pergunta.addEventListener("toggle", () => {
    if (pergunta.open) perguntasFrequentes.forEach((outraPergunta) => {
      if (outraPergunta !== pergunta) outraPergunta.open = false;
    });
  }));

  const linksNavegacao = document.querySelectorAll('nav a[href^="#"]');
  const secoesAlvo = [...linksNavegacao]
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);
  if ("IntersectionObserver" in window) {
    const observador = new IntersectionObserver((entradas) => entradas.forEach((entrada) => {
      if (!entrada.isIntersecting) return;
      linksNavegacao.forEach((link) => {
        if (link.getAttribute("href") === `#${entrada.target.id}`) link.setAttribute("aria-current", "true");
        else link.removeAttribute("aria-current");
      });
    }), { rootMargin: "-40% 0px -55% 0px" });
    secoesAlvo.forEach((secao) => observador.observe(secao));
  }

  const formulario = document.getElementById("form-contato");
  if (!formulario) return;

  const urlApi = window.location.port && window.location.port !== "8000"
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : "";
  const etapas = [...formulario.querySelectorAll(".step")];
  const marcadoresEtapa = formulario.querySelector(".crumbs");
  const botoesEtapa = [...marcadoresEtapa.querySelectorAll("button")];
  const botaoVoltar = formulario.querySelector("[data-back]");
  const botaoEnviar = formulario.querySelector(".cta");
  const mensagemFeedback = formulario.querySelector("#form-feedback");
  const campoData = formulario.elements.data_agendamento;
  const seletorHorario = formulario.elements.hora_agendamento;
  const campoNome = formulario.elements.nome_completo;
  const campoEmail = formulario.elements.email;
  const campoTelefone = formulario.elements.telefone;
  let etapaAtual = 0;
  let carregandoDisponibilidade = false;
  let numeroConsultaDisponibilidade = 0;

  const limparFeedback = () => {
    mensagemFeedback.textContent = "";
    mensagemFeedback.className = "form-feedback";
  };
  const exibirFeedback = (mensagem, tipo = "erro") => {
    mensagemFeedback.textContent = mensagem;
    mensagemFeedback.className = `form-feedback ${tipo}`;
  };
  const obterMensagemErroApi = (detalhe, mensagemPadrao) => {
    if (typeof detalhe === "string") return detalhe;
    if (Array.isArray(detalhe)) {
      return detalhe.map((erro) => erro.msg).filter(Boolean).join(" ") || mensagemPadrao;
    }
    return mensagemPadrao;
  };
  const formatarDataLocal = (data) => {
    const ano = data.getFullYear();
    const mes = String(data.getMonth() + 1).padStart(2, "0");
    const dia = String(data.getDate()).padStart(2, "0");
    return `${ano}-${mes}-${dia}`;
  };
  const dataAtual = formatarDataLocal(new Date());
  campoData.min = dataAtual;

  const domingoDePascoa = (ano) => {
    const a = ano % 19;
    const b = Math.floor(ano / 100);
    const c = ano % 100;
    const d = Math.floor(b / 4);
    const e = b % 4;
    const f = Math.floor((b + 8) / 25);
    const g = Math.floor((b - f + 1) / 3);
    const h = (19 * a + b - d - g + 15) % 30;
    const i = Math.floor(c / 4);
    const k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7;
    const m = Math.floor((a + 11 * h + 22 * l) / 451);
    const valor = h + l - 7 * m + 114;
    return new Date(Date.UTC(ano, Math.floor(valor / 31) - 1, valor % 31 + 1));
  };
  const diaTemExpediente = (dataISO) => {
    if (!dataISO || dataISO < dataAtual) return false;
    const [ano, mes, dia] = dataISO.split("-").map(Number);
    const dataSelecionada = new Date(ano, mes - 1, dia, 12);
    if (dataSelecionada.getDay() === 0 || dataSelecionada.getDay() === 6) return false;
    const feriadosFixos = new Set(["01-01", "01-25", "04-21", "05-01", "07-09", "09-07", "10-12", "11-02", "11-15", "11-20", "12-25"]);
    if (feriadosFixos.has(dataISO.slice(5))) return false;
    const pascoa = domingoDePascoa(ano);
    const diasAposPascoa = Math.round((Date.UTC(ano, mes - 1, dia) - pascoa.getTime()) / 86400000);
    return diasAposPascoa !== -2 && diasAposPascoa !== 60;
  };

  const carregarDisponibilidade = async () => {
    const numeroConsulta = ++numeroConsultaDisponibilidade;
    const dataConsultada = campoData.value;
    seletorHorario.replaceChildren(new Option("Carregando hor\u00e1rios...", ""));
    seletorHorario.disabled = true;
    carregandoDisponibilidade = true;
    try {
        const respostaHttp = await fetch(`${urlApi}/api/v1/disponibilidade?data=${encodeURIComponent(dataConsultada)}`, {        headers: { Accept: "application/json" },
      });
      const resposta = await respostaHttp.json();
      if (numeroConsulta !== numeroConsultaDisponibilidade || dataConsultada !== campoData.value) return;
      if (!respostaHttp.ok) throw new Error(resposta.detail || "N\u00e3o foi poss\u00edvel consultar a agenda.");
      const horariosDisponiveis = resposta.horarios ?? resposta.horarios_disponiveis ?? [];
      if (horariosDisponiveis.length === 0) {
        seletorHorario.replaceChildren(new Option("Nenhum hor\u00e1rio dispon\u00edvel para esta data", ""));
        seletorHorario.disabled = true;
        exibirFeedback("N\u00e3o h\u00e1 hor\u00e1rios livres nesta data. Escolha outro dia \u00fatil.");
      } else {
        seletorHorario.replaceChildren(new Option("Selecione", ""));
        horariosDisponiveis.forEach((horario) => seletorHorario.add(new Option(horario, horario)));
        seletorHorario.disabled = false;
      }
    } catch (erro) {
      if (numeroConsulta !== numeroConsultaDisponibilidade) return;
      seletorHorario.replaceChildren(new Option("Falha ao consultar", ""));
      exibirFeedback(erro.message || "N\u00e3o foi poss\u00edvel consultar os hor\u00e1rios. Tente novamente.");
    } finally {
      if (numeroConsulta === numeroConsultaDisponibilidade) {
        carregandoDisponibilidade = false;
        atualizarEstadoEnvio();
      }
    }
  };

  campoData.addEventListener("change", () => {
    limparFeedback();
    numeroConsultaDisponibilidade += 1;
    carregandoDisponibilidade = false;
    seletorHorario.value = "";
    seletorHorario.disabled = true;
    if (!campoData.value) {
      seletorHorario.replaceChildren(new Option("Selecione uma data primeiro", ""));
      atualizarEstadoEnvio();
      return;
    }
    if (!diaTemExpediente(campoData.value)) {
      seletorHorario.replaceChildren(new Option("Selecione uma data v\u00e1lida", ""));
      exibirFeedback("Por favor, selecione um dia \u00fatil futuro para o agendamento.");
      atualizarEstadoEnvio();
      return;
    }
    carregarDisponibilidade();
  });
  seletorHorario.addEventListener("change", () => { limparFeedback(); atualizarEstadoEnvio(); });

  const atualizarValidadeNome = () => {
    campoNome.setCustomValidity(campoNome.value.trim().length >= 3 ? "" : "Informe seu nome completo com pelo menos 3 caracteres.");
  };
  const atualizarValidadeEmail = () => {
    const emailValido = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(campoEmail.value.trim());
    campoEmail.setCustomValidity(!campoEmail.value || emailValido ? "" : "Informe um e-mail v\u00e1lido.");
  };
  const formatarTelefone = (valor) => {
    const digitos = valor.replace(/\D/g, "").slice(0, 11);
    if (digitos.length <= 2) return digitos ? `(${digitos}` : "";
    const codigoArea = `(${digitos.slice(0, 2)}) `;
    const numeroLocal = digitos.slice(2);
    const tamanhoInicial = digitos.length > 10 ? 5 : 4;
    const parteInicial = numeroLocal.slice(0, tamanhoInicial);
    const parteFinal = numeroLocal.slice(tamanhoInicial);
    return `${codigoArea}${parteInicial}${parteFinal ? `-${parteFinal}` : ""}`;
  };
  const atualizarValidadeTelefone = () => {
    const digitos = campoTelefone.value.replace(/\D/g, "");
    campoTelefone.setCustomValidity([10, 11].includes(digitos.length) ? "" : "Informe telefone com DDD e 10 ou 11 d\u00edgitos.");
  };
  campoNome.addEventListener("input", () => { atualizarValidadeNome(); atualizarEstadoEnvio(); });
  campoEmail.addEventListener("input", () => { atualizarValidadeEmail(); atualizarEstadoEnvio(); });
  campoTelefone.addEventListener("input", () => {
    campoTelefone.value = formatarTelefone(campoTelefone.value);
    atualizarValidadeTelefone();
    atualizarEstadoEnvio();
  });

  const validarEtapa = (indice) => {
    if (indice === 1) {
      if (!campoData.value || !campoData.checkValidity() || !diaTemExpediente(campoData.value)) {
        exibirFeedback("Por favor, selecione um dia \u00fatil futuro para o agendamento.");
        campoData.focus();
        return false;
      }
      if (carregandoDisponibilidade) {
        exibirFeedback("Aguarde a consulta dos hor\u00e1rios dispon\u00edveis.");
        return false;
      }
      if (!seletorHorario.value || seletorHorario.disabled) {
        exibirFeedback("Selecione um hor\u00e1rio dispon\u00edvel antes de continuar.");
        seletorHorario.focus();
        return false;
      }
    }
    let primeiroCampoInvalido = null;
    etapas[indice].querySelectorAll("input,select,textarea").forEach((campo) => {
      if (campo === campoNome) atualizarValidadeNome();
      if (campo === campoEmail) atualizarValidadeEmail();
      if (campo === campoTelefone) atualizarValidadeTelefone();
      if (!campo.willValidate) return;
      if (!campo.checkValidity() && !primeiroCampoInvalido) primeiroCampoInvalido = campo;
    });
    if (primeiroCampoInvalido) {
      exibirFeedback(primeiroCampoInvalido.validationMessage || "Revise os campos destacados.");
      primeiroCampoInvalido.focus();
    }
    return !primeiroCampoInvalido;
  };

  function atualizarEstadoEnvio() {
    if (etapaAtual !== etapas.length - 1) { botaoEnviar.disabled = false; return; }
    atualizarValidadeNome();
    atualizarValidadeEmail();
    atualizarValidadeTelefone();
    const agendaValida = Boolean(campoData.value && diaTemExpediente(campoData.value) && seletorHorario.value && !seletorHorario.disabled);
    botaoEnviar.disabled = !formulario.checkValidity() || !agendaValida || carregandoDisponibilidade;
  }
  const validarAntesDoEnvio = () => {
    const area = formulario.elements.area_assunto.value.trim();
    const formato = formulario.querySelector('input[name="formato_atendimento"]:checked')?.value.trim() || "";
    const data = campoData.value.trim();
    const hora = seletorHorario.value.trim();
    const consentimento = formulario.elements.consentimento_lgpd.checked === true;
    const telefoneDigitos = campoTelefone.value.replace(/\D/g, "");
    const email = campoEmail.value.trim();

    const erros = [
      { valido: campoNome.value.trim().length >= 3, mensagem: "Por favor, preencha seu nome completo com pelo menos 3 caracteres.", campo: campoNome, etapa: 2 },
      { valido: /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email), mensagem: "Informe um endereço de e-mail válido.", campo: campoEmail, etapa: 2 },
      { valido: telefoneDigitos.length >= 10 && telefoneDigitos.length <= 11, mensagem: "Informe um número de telefone/WhatsApp válido.", campo: campoTelefone, etapa: 2 },
      { valido: Boolean(area), mensagem: "Selecione o assunto do atendimento.", campo: formulario.elements.area_assunto, etapa: 0 },
      { valido: Boolean(formato), mensagem: "Selecione o formato do atendimento (Online ou Presencial).", campo: formulario.querySelector('input[name="formato_atendimento"]'), etapa: 0 },
      { valido: Boolean(data), mensagem: "Selecione uma data para a consulta.", campo: campoData, etapa: 1 },
      { valido: Boolean(hora), mensagem: "Selecione um horário disponível para o atendimento.", campo: seletorHorario, etapa: 1 },
      { valido: consentimento, mensagem: "Você precisa aceitar os termos de privacidade para prosseguir.", campo: formulario.elements.consentimento_lgpd, etapa: 2 },
    ];
    const erro = erros.find((item) => !item.valido);
    if (erro) {
      if (etapaAtual !== erro.etapa) mostrarEtapa(erro.etapa, true);
      exibirFeedback(erro.mensagem);
      erro.campo?.focus();
      return false;
    }
    if (!diaTemExpediente(data)) {
      mostrarEtapa(1, true);
      exibirFeedback("Por favor, selecione um dia útil futuro para o agendamento.");
      campoData.focus();
      return false;
    }
    if (seletorHorario.disabled || carregandoDisponibilidade) {
      mostrarEtapa(1, true);
      exibirFeedback("Selecione um horário disponível para o atendimento.");
      seletorHorario.focus();
      return false;
    }
    return true;
  };
  const mostrarEtapa = (indice, moverFoco = false) => {
    etapaAtual = indice;
    etapas.forEach((etapa, indiceEtapa) => { etapa.hidden = indiceEtapa !== indice; });
    botoesEtapa.forEach((botao, indiceBotao) => {
      botao.disabled = indiceBotao > indice;
      if (indiceBotao === indice) botao.setAttribute("aria-current", "step");
      else botao.removeAttribute("aria-current");
    });
    botaoVoltar.hidden = indice === 0;
    botaoEnviar.textContent = indice === etapas.length - 1 ? "Enviar solicita\u00e7\u00e3o" : "Continuar";
    limparFeedback();
    if (indice === 1 && campoData.value && diaTemExpediente(campoData.value)) carregarDisponibilidade();
    atualizarEstadoEnvio();
    if (moverFoco) etapas[indice].querySelector("legend").focus();
  };

  marcadoresEtapa.hidden = false;
  mostrarEtapa(0);
  botaoVoltar.addEventListener("click", () => mostrarEtapa(etapaAtual - 1, true));
  botoesEtapa.forEach((botao, indice) => botao.addEventListener("click", () => mostrarEtapa(indice, true)));
  formulario.elements.consentimento_lgpd.addEventListener("change", atualizarEstadoEnvio);
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparFeedback();
    if (etapaAtual === etapas.length - 1 && !validarAntesDoEnvio()) return;
    if (!validarEtapa(etapaAtual)) return;
    if (etapaAtual < etapas.length - 1) { mostrarEtapa(etapaAtual + 1, true); return; }
    if (formulario.elements.site.value) return;

    const valoresFormulario = new FormData(formulario);
    const dadosAgendamento = {
      nome: String(valoresFormulario.get("nome_completo") || "").trim(),
      email: String(valoresFormulario.get("email") || "").trim(),
      telefone: String(valoresFormulario.get("telefone") || "").trim(),
      area: String(valoresFormulario.get("area_assunto") || "").trim(),
      formato: String(valoresFormulario.get("formato_atendimento") || "").trim(),
      data: String(valoresFormulario.get("data_agendamento") || "").trim(),
      hora: String(valoresFormulario.get("hora_agendamento") || "").trim(),
      mensagem: valoresFormulario.get("mensagem") || null,
      consentimento_lgpd: valoresFormulario.get("consentimento_lgpd") === "on",
    };
    botaoEnviar.disabled = true;
    exibirFeedback("Enviando sua solicita\u00e7\u00e3o...", "info");
    try {
      const respostaHttp = await fetch(`${urlApi}/api/v1/agendamentos`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(dadosAgendamento),
      });
      const resposta = await respostaHttp.json();
      if (respostaHttp.status === 409) {
        mostrarEtapa(1, true);
        exibirFeedback("Este hor\u00e1rio acabou de ser ocupado. Escolha outro hor\u00e1rio dispon\u00edvel.");
        return;
      }
      if (!respostaHttp.ok) {
        throw new Error(obterMensagemErroApi(resposta.detail, "N\u00e3o foi poss\u00edvel enviar sua solicita\u00e7\u00e3o."));
      }
      formulario.reset();
      campoData.min = dataAtual;
      seletorHorario.replaceChildren(new Option("Selecione uma data primeiro", ""));
      seletorHorario.disabled = true;
      mostrarEtapa(0);
      exibirFeedback("Solicita\u00e7\u00e3o recebida! O escrit\u00f3rio entrar\u00e1 em contato para confirmar o hor\u00e1rio.", "sucesso");
    } catch (erro) {
      exibirFeedback(erro.message || "Falha de conex\u00e3o. Tente novamente.");
    } finally {
      atualizarEstadoEnvio();
    }
  });
})();
