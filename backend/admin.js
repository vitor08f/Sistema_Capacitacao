(() => {
  "use strict";
  const mensagemStatus = document.querySelector("#mensagem-status");
  const chamarApi = async (url, opcoes = {}) => {
    const respostaHttp = await fetch(url, {
      ...opcoes,
      headers: { "Content-Type": "application/json", ...(opcoes.headers || {}) },
    });
    const resposta = await respostaHttp.json().catch(() => ({}));
    if (!respostaHttp.ok) throw new Error(resposta.detail || "N\u00e3o foi poss\u00edvel concluir a opera\u00e7\u00e3o.");
    return resposta;
  };
  const exibirStatus = (mensagem, ocorreuErro = false) => {
    mensagemStatus.textContent = mensagem;
    mensagemStatus.className = ocorreuErro ? "erro" : "";
  };
  const carregarDados = async () => {
    try {
      const [agendamentos, contatos] = await Promise.all([
        chamarApi("/api/v1/administracao/agendamentos"),
        chamarApi("/api/v1/administracao/contatos"),
      ]);
      const corpoTabela = document.querySelector("#agendamentos");
      corpoTabela.replaceChildren();
      agendamentos.forEach((agendamento) => {
        const linha = document.createElement("tr");
        const valores = [
          new Date(agendamento.data_hora_inicio).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" }),
          agendamento.nome_completo,
          `${agendamento.email} \u00b7 ${agendamento.telefone}`,
          agendamento.area_assunto,
          agendamento.status_agendamento,
        ];
        valores.forEach((valor) => {
          const celula = document.createElement("td");
          celula.textContent = valor;
          linha.append(celula);
        });
        const celulaAcao = document.createElement("td");
        const seletorStatus = document.createElement("select");
        [["solicitado", "Solicitado"], ["aprovado", "Aprovar"], ["cancelado", "Cancelar"]]
          .forEach(([valor, rotulo]) => {
            const opcao = document.createElement("option");
            opcao.value = valor;
            opcao.textContent = rotulo;
            opcao.selected = agendamento.status_agendamento === valor;
            seletorStatus.append(opcao);
          });
        seletorStatus.addEventListener("change", async () => {
          try {
            await chamarApi(`/api/v1/administracao/agendamentos/${agendamento.id_agendamento}`, {
              method: "PATCH",
              body: JSON.stringify({ status_agendamento: seletorStatus.value }),
            });
            exibirStatus("Status atualizado.");
            await carregarDados();
          } catch (erro) { exibirStatus(erro.message, true); }
        });
        celulaAcao.append(seletorStatus);
        linha.append(celulaAcao);
        corpoTabela.append(linha);
      });
      const seletorContato = document.querySelector("#contato_id");
      seletorContato.replaceChildren();
      contatos.forEach((contato) => {
        const opcao = document.createElement("option");
        opcao.value = contato.id_contato;
        opcao.textContent = `${contato.nome_completo} \u2014 ${contato.email}`;
        seletorContato.append(opcao);
      });
      const listaContatos = document.querySelector("#contatos");
      listaContatos.replaceChildren();
      contatos.forEach((contato) => {
        const itemContato = document.createElement("li");
        itemContato.textContent = `${contato.nome_completo} \u2014 ${contato.email} \u00b7 ${contato.telefone} \u00b7 ${contato.area_assunto}`;
        listaContatos.append(itemContato);
      });
    } catch (erro) {
      exibirStatus(`${erro.message} Verifique a autentica\u00e7\u00e3o administrativa.`, true);
    }
  };
  document.querySelector("#recarregar").addEventListener("click", carregarDados);
  document.querySelector("#formulario-bloqueio").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dadosFormulario = new FormData(evento.currentTarget);
    try {
      await chamarApi("/api/v1/administracao/bloqueios", {
        method: "POST",
        body: JSON.stringify({
          data_bloqueio: dadosFormulario.get("data_bloqueio"),
          hora_inicio: dadosFormulario.get("hora_inicio") || null,
          hora_fim: dadosFormulario.get("hora_fim") || null,
          motivo: dadosFormulario.get("motivo"),
        }),
      });
      exibirStatus("Bloqueio cadastrado.");
      evento.currentTarget.reset();
    } catch (erro) { exibirStatus(erro.message, true); }
  });
  document.querySelector("#formulario-agendamento").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dadosFormulario = new FormData(evento.currentTarget);
    try {
      await chamarApi("/api/v1/administracao/agendamentos", {
        method: "POST",
        body: JSON.stringify({
          contato_id: Number(dadosFormulario.get("contato_id")),
          data_agendamento: dadosFormulario.get("data_agendamento"),
          hora_agendamento: dadosFormulario.get("hora_agendamento"),
        }),
      });
      exibirStatus("Agendamento cadastrado.");
      evento.currentTarget.reset();
      await carregarDados();
    } catch (erro) { exibirStatus(erro.message, true); }
  });
  carregarDados();
})();
