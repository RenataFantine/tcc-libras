/* ADMIN-LOGIN.JS — autenticação administrativa integrada ao Flask.
   O backend verifica as credenciais no PostgreSQL e controla a sessão.
*/

import { qs } from "./dom-utils.js";

export class AdminLogin {
  init() {
    this.form = qs("#adminForm");

    // Se não estiver na página administrativa, não faz nada.
    if (!this.form) return;

    this.user = qs("#adminUser");
    this.pass = qs("#adminPass");
    this.toggle = qs("#togglePass");
    this.submit = qs("#adminSubmit");
    this.alert = qs("#formAlert");
    this.panel = qs("#adminPanel");
    this.userErr = qs("#userError");
    this.passErr = qs("#passError");
    this.logout = qs("#adminLogout");

    // Verifica se os elementos necessários existem.
    if (
      !this.user ||
      !this.pass ||
      !this.toggle ||
      !this.submit ||
      !this.alert ||
      !this.panel ||
      !this.userErr ||
      !this.passErr ||
      !this.logout
    ) {
      console.error("Elementos do formulário administrativo não encontrados.");
      return;
    }

    this.toggle.addEventListener("click", () => {
      this.togglePassword();
    });

    this.form.addEventListener("submit", (event) => {
      this.handleSubmit(event);
    });

    this.logout.addEventListener("click", () => {
      this.handleLogout();
    });

    // Consulta o backend para verificar uma sessão existente.
    this.checkSession();
  }

  async request(url, options = {}) {
    const response = await fetch(url, {
      credentials: "same-origin",
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      }
    });

    let data = {};

    try {
      data = await response.json();
    } catch {
      data = {};
    }

    return { response, data };
  }

  togglePassword() {
    const show = this.pass.type === "password";

    this.pass.type = show ? "text" : "password";
    this.toggle.textContent = show ? "Ocultar" : "Mostrar";
    this.toggle.setAttribute("aria-pressed", String(show));
  }

  validate() {
    this.userErr.textContent = this.user.value.trim()
      ? ""
      : "Informe o usuário.";

    this.passErr.textContent = this.pass.value
      ? ""
      : "Informe a senha.";

    if (this.userErr.textContent) {
      this.user.focus();
      return false;
    }

    if (this.passErr.textContent) {
      this.pass.focus();
      return false;
    }

    return true;
  }

  async checkSession() {
    this.form.hidden = true;
    this.panel.hidden = true;

    try {
      const { response } = await this.request("/api/admin/sessao", {
        method: "GET",
        headers: {}
      });

      if (response.ok) {
        this.showPanel();
      } else {
        this.showForm();
      }
    } catch (error) {
      console.error("Erro ao verificar sessão administrativa:", error);

      this.showForm();
      this.showAlert(
        "Não foi possível conectar ao servidor. Verifique se o Flask está em execução."
      );
    }
  }

  async handleSubmit(event) {
    event.preventDefault();

    this.alert.hidden = true;

    if (!this.validate()) return;

    this.submit.disabled = true;
    this.submit.textContent = "Verificando…";

    try {
      const { response, data } = await this.request(
        "/api/admin/login",
        {
          method: "POST",
          body: JSON.stringify({
            usuario: this.user.value.trim(),
            senha: this.pass.value
          })
        }
      );

      if (!response.ok) {
        this.showAlert(
          data.erro ||
          data.mensagem ||
          "Usuário ou senha incorretos. Verifique os dados e tente novamente."
        );

        this.pass.value = "";
        this.pass.focus();
        return;
      }

      // O servidor confirmou a autenticação.
      this.showPanel();

    } catch (error) {
      console.error("Erro no login administrativo:", error);

      this.showAlert(
        "Não foi possível conectar ao servidor. Verifique se o Flask está em execução."
      );

    } finally {
      this.submit.disabled = false;
      this.submit.textContent = "Entrar";
    }
  }

  async handleLogout() {
    this.logout.disabled = true;

    try {
      const { response, data } = await this.request(
        "/api/admin/logout",
        {
          method: "POST",
          body: JSON.stringify({})
        }
      );

      if (!response.ok) {
        this.showAlert(
          data.erro || "Não foi possível encerrar a sessão."
        );
        return;
      }

      this.showForm();

    } catch (error) {
      console.error("Erro ao encerrar sessão:", error);

      this.showAlert(
        "Não foi possível conectar ao servidor para encerrar a sessão."
      );

    } finally {
      this.logout.disabled = false;
    }
  }

  showAlert(message) {
    this.alert.textContent = message;
    this.alert.hidden = false;
  }

  showPanel() {
    this.form.hidden = true;
    this.panel.hidden = false;

    const title = this.panel.querySelector("h2");

    if (title) {
      title.focus();
    }
  }

  showForm() {
    this.form.reset();

    this.userErr.textContent = "";
    this.passErr.textContent = "";
    this.alert.hidden = true;

    this.submit.disabled = false;
    this.submit.textContent = "Entrar";

    this.form.hidden = false;
    this.panel.hidden = true;
  }
}
