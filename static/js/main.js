// ==========================================================
// Desenvolvido por Marcos Vinicius - github.com/MarcosViniicius
// ==========================================================

// Mapeamento de presentes para imagem e referência
const presentesInfo = {
  "Jansport Mini Mochila Misty Rose": {
    imagem: "../static/img/mochila-half-pint-jansport-TDH67N8-1.png",
    referencia: "Referência: JDJ-12345",
  },
  "Zara Tênis Hello Kitty TAM. 36": {
    imagem: "../static/img/tenis_hello_kitty.png",
    referencia: "Referência: ZTK-67890",
  },
  "Cartão presente C&A": {
    imagem: "../static/img/cia_cartao.webp",
    referencia:
      "Link de compra: https://www.cea.com.br/cartao-presente---arcos-3001701-arcos/p",
  },
  // Adicione aqui outros presentes no futuro:
  // "Nome do Presente": { imagem: "url", referencia: "texto" }
};

const presentesImagens = {
  "Papete Branca TAM. 36": "https://i.imgur.com/IxWjkp4.jpeg",
  // ...outras entradas...
};

function toggleCamposOpcionais() {
  const confirmadoSelect = document.getElementById("confirmado");
  const escolhaDiv = document.getElementById("escolhaDiv");
  const presenteDiv = document.getElementById("presente-div");
  const pixDiv = document.getElementById("pix-div");
  const quantidadeDiv = document.getElementById("quantidade-pessoas-div");
  const quantidadeInput = document.getElementById("quantidade_pessoas");
  const presenteSelect = document.getElementById("presente");
  const formaPresenteInput = document.getElementById("forma_presente");

  if (!confirmadoSelect) return;

  if (confirmadoSelect.value === "sim") {
    // mostra apenas quantidade e escolha de forma, mas esconde lista
    quantidadeDiv.style.display = "block";
    quantidadeInput.required = true;
    escolhaDiv.style.display = "block";

    // mantém ambas ocultas até o usuário clicar em "Escolher Presente" ou "Pix"
    presenteDiv.style.display = "none";
    pixDiv.style.display = "none";
    presenteSelect.required = false;

    // Resetar o valor do campo forma_presente para forçar uma nova escolha
    formaPresenteInput.value = "";

    // Resetar os estilos dos botões
    const btnPresente = document.getElementById("btn-presente");
    const btnPix = document.getElementById("btn-pix");

    if (btnPresente) {
      btnPresente.classList.remove("active", "btn-primary");
      btnPresente.classList.add("btn-outline-primary");
    }

    if (btnPix) {
      btnPix.classList.remove("active", "btn-success");
      btnPix.classList.add("btn-outline-success");
    }
  } else {
    // caso "não", oculta tudo e remove required
    quantidadeDiv.style.display = "none";
    quantidadeInput.required = false;
    escolhaDiv.style.display = "none";
    presenteDiv.style.display = "none";
    pixDiv.style.display = "none";
    presenteSelect.required = false;
    formaPresenteInput.value = ""; // Limpar o campo quando não for comparecer
  }
}

// liga ao evento change do select e inicializa
document.addEventListener("DOMContentLoaded", () => {
  const confirmadoSelect = document.getElementById("confirmado");
  if (confirmadoSelect) {
    confirmadoSelect.addEventListener("change", toggleCamposOpcionais);
    toggleCamposOpcionais();
  }
});

document.addEventListener("DOMContentLoaded", function () {
  // Código para garantir que o modal seja acionado pelo botão
  const btnMostrarExemplo = document.getElementById("btnMostrarExemplo");
  const exemploDressCodeModal = new bootstrap.Modal(
    document.getElementById("exemploDressCodeModal")
  );

  if (btnMostrarExemplo) {
    btnMostrarExemplo.addEventListener("click", function () {
      exemploDressCodeModal.show();
    });
  }
});

function fecharEMover() {
  // Fecha o modal de presentes
  var modal = bootstrap.Modal.getInstance(
    document.getElementById("listapresentesModal")
  );
  if (modal) modal.hide();
  // Aguarda o modal fechar antes de rolar
  setTimeout(function () {
    // Rola suavemente até o formulário de confirmação
    var form = document.getElementById("formConfirmacao");
    if (form) {
      form.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, 400); // tempo suficiente para o modal fechar
}

function alternarFormaPresente(opcao) {
  const btnPresente = document.getElementById("btn-presente");
  const btnPix = document.getElementById("btn-pix");
  const presenteDiv = document.getElementById("presente-div");
  const formaPresenteInput = document.getElementById("forma_presente");
  const presenteSelect = document.getElementById("presente");
  const pixSelect = document.getElementById("pix-div");
  const submitButton = document.querySelector("button[type='submit']");
  const imagemDiv = document.getElementById("imagemPresente");
  const referenciaDiv = document.getElementById("referenciaPresente");

  // Resetar estilos dos botões
  btnPresente.classList.remove("active", "btn-primary");
  btnPresente.classList.add("btn-outline-primary");
  btnPix.classList.remove("active", "btn-success");
  btnPix.classList.add("btn-outline-success");

  if (opcao === "presente") {
    presenteDiv.style.display = "block";
    pixSelect.style.display = "none";
    btnPresente.classList.add("active", "btn-primary");
    btnPresente.classList.remove("btn-outline-primary");
    formaPresenteInput.value = "presente"; // Garantir que o valor esteja definido
    presenteSelect.setAttribute("required", "required");
    submitButton.textContent = "Confirmar Presença e Presente";
  } else if (opcao === "pix") {
    presenteDiv.style.display = "none";
    pixSelect.style.display = "block";
    btnPix.classList.add("active", "btn-success");
    btnPix.classList.remove("btn-outline-success");
    formaPresenteInput.value = "pix"; // Garantir que o valor esteja definido
    presenteSelect.removeAttribute("required");
    submitButton.textContent = "Confirmar Presença e Prosseguir para Pagamento";
    // Limpa seleção e oculta imagem/referência
    presenteSelect.value = "";
    if (imagemDiv) imagemDiv.style.display = "none";
    if (referenciaDiv) referenciaDiv.style.display = "none";
  }
}

window.addEventListener("scroll", function () {
  const navbar = document.querySelector(".custom-navbar");
  const hero = document.querySelector(".hero");
  if (!navbar || !hero) return;

  // Ativa navbar-fixa quando o scroll passa do final da hero
  if (window.scrollY >= hero.offsetTop + hero.offsetHeight) {
    navbar.classList.add("navbar-fixa");
  } else {
    navbar.classList.remove("navbar-fixa");
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const navbar = document.querySelector(".custom-navbar");
  const trigger = document.getElementById("nav-trigger");
  if (!navbar || !trigger) return;

  const observer = new IntersectionObserver(
    ([entry]) => {
      if (!entry.isIntersecting) {
        navbar.classList.add("navbar-fixa");
      } else {
        navbar.classList.remove("navbar-fixa");
      }
    },
    { threshold: 0 }
  );

  observer.observe(trigger);
});

window.addEventListener("DOMContentLoaded", function () {
  const navbar = document.querySelector(".custom-navbar");
  if (navbar) navbar.classList.remove("navbar-fixa");
});

// Função para atualizar a imagem do presente selecionado
function atualizarImagemPresente(presente) {
  const imagemDiv = document.getElementById("imagemPresente");
  const imagem = document.getElementById("imagemPresenteSelecionado");
  const presenteSelect = document.getElementById("presente");
  if (!imagem || !imagemDiv || !presenteSelect) return;

  // Busca a opção selecionada
  const selectedOption = presenteSelect.options[presenteSelect.selectedIndex];
  const imgUrl = selectedOption.getAttribute("data-img");

  if (imgUrl) {
    imagem.src = imgUrl;
    imagemDiv.style.display = "block";
    imagem.style.maxWidth = "200px";
    imagem.style.maxHeight = "200px";
  } else {
    imagem.src = "";
    imagemDiv.style.display = "none";
  }
}

// Função para atualizar a referência do presente selecionado
function atualizarReferenciaPresente(presente) {
  const referenciaDiv = document.getElementById("referenciaPresente");
  if (presentesInfo[presente]) {
    referenciaDiv.textContent = presentesInfo[presente].referencia;
    referenciaDiv.style.display = "block";
  } else {
    referenciaDiv.textContent = "";
    referenciaDiv.style.display = "none";
  }
}

// Garante que ao enviar como Pix, o campo presente não será enviado
document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form");
  form.addEventListener("submit", function () {
    const formaPresenteInput = document.getElementById("forma_presente");
    const presenteSelect = document.getElementById("presente");
    if (formaPresenteInput.value === "pix") {
      presenteSelect.value = "";
    }
  });
});

function atualizarReferenciaPresente(presente) {
  // ...código existente...
  var linkCompra = "";
  if (presentesInfo[presente] && presentesInfo[presente].link_compra) {
    linkCompra = `<br><b>Recomendação de compra:</b> <a href="${presentesInfo[presente].link_compra}" target="_blank" style="color:#7c43bd; text-decoration:underline;">${presentesInfo[presente].link_compra}</a><br><span style="font-size:0.9em;color:#555;">(A compra pelo site é opcional, serve apenas como indicação para facilitar sua escolha.)</span>`;
  }
  document.getElementById("linkCompraPresente").innerHTML = linkCompra;
}

document.addEventListener("DOMContentLoaded", function () {
  var closeBtn = document.querySelector("#floating-alert .btn-close");
  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      var alert = document.getElementById("floating-alert");
      if (alert) alert.style.display = "none";
    });
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form[action]");
  if (!form) return;

  form.addEventListener("submit", function (event) {
    const confirmadoSelect = document.getElementById("confirmado");
    const formaPresenteInput = document.getElementById("forma_presente");
    const presenteSelect = document.getElementById("presente");

    // Se confirmou presença, verificar se selecionou forma de presente
    if (confirmadoSelect && confirmadoSelect.value === "sim") {
      // Verificar se uma forma de presente foi selecionada
      if (!formaPresenteInput.value || formaPresenteInput.value === "") {
        event.preventDefault();
        alert(
          "Por favor, selecione como deseja presentear (Escolher um presente ou Fazer um Pix)"
        );
        return false;
      }

      // Se escolheu presente físico, verificar se selecionou um presente específico
      if (formaPresenteInput.value === "presente") {
        if (!presenteSelect.value || presenteSelect.value === "") {
          event.preventDefault();
          alert("Por favor, selecione um presente da lista disponível");
          return false;
        }
      }
    }
  });
});
