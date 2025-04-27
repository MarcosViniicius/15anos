function toggleCamposOpcionais() {
  const confirmadoSelect = document.getElementById("confirmado");
  const presenteDiv = document.getElementById("presente-div");
  const escolhaDiv = document.getElementById("escolhaDiv");
  const quantidadePessoasDiv = document.getElementById(
    "quantidade-pessoas-div"
  );

  if (confirmadoSelect) {
    if (confirmadoSelect.value === "sim") {
      // Mostrar campos relacionados à presença
      escolhaDiv.style.display = "block";
      quantidadePessoasDiv.style.display = "block";
      presenteDiv.style.display = "none"; // Inicialmente ocultar o presente
    } else if (confirmadoSelect.value === "nao") {
      // Ocultar campos relacionados à presença
      escolhaDiv.style.display = "none";
      quantidadePessoasDiv.style.display = "none";
      presenteDiv.style.display = "none";
    } else {
      // Ocultar tudo se nenhuma opção for selecionada
      escolhaDiv.style.display = "none";
      quantidadePessoasDiv.style.display = "none";
      presenteDiv.style.display = "none";
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const confirmadoSelect = document.getElementById("confirmado");
  if (confirmadoSelect) {
    confirmadoSelect.addEventListener("change", toggleCamposOpcionais);
  }

  // Executa ao carregar para garantir o estado inicial correto
  toggleCamposOpcionais();
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
  const modal = bootstrap.Modal.getInstance(
    document.getElementById("listapresentesModal")
  );
  modal.hide();

  setTimeout(() => {
    document
      .getElementById("formConfirmacao")
      .scrollIntoView({ behavior: "smooth" });
  }, 300); // tempo suficiente para a modal sumir antes de rolar
}

function alternarFormaPresente(opcao) {
  const btnPresente = document.getElementById("btn-presente");
  const btnPix = document.getElementById("btn-pix");
  const presenteDiv = document.getElementById("presente-div");
  const formaPresenteInput = document.getElementById("forma_presente");
  const presenteSelect = document.getElementById("presente");
  const pixSelect = document.getElementById("pix-div");
  const submitButton = document.querySelector("button[type='submit']");

  // Resetar estilos dos botões
  btnPresente.classList.remove("active", "btn-primary");
  btnPix.classList.remove("active", "btn-success");

  // Mostrar ou ocultar campos conforme a opção selecionada
  if (opcao === "presente") {
    presenteDiv.style.display = "block";
    pixSelect.style.display = "none";
    btnPresente.classList.add("active", "btn-primary");
    btnPix.classList.add("btn-outline-success");
    formaPresenteInput.value = "presente";
    presenteSelect.setAttribute("required", "required"); // Torna obrigatório
    submitButton.textContent = "Confirmar Presença e Presente"; // Atualiza texto do botão
  } else if (opcao === "pix") {
    presenteDiv.style.display = "none";
    pixSelect.style.display = "block";
    btnPix.classList.add("active", "btn-success");
    btnPresente.classList.add("btn-outline-primary");
    formaPresenteInput.value = "pix";
    presenteSelect.removeAttribute("required"); // Remove obrigatoriedade
    submitButton.textContent = "Confirmar Presença e Prosseguir para Pagamento"; // Atualiza texto do botão
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
