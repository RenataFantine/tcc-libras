
/* TRANSLATOR.JS — interface integrada ao Flask. */

export class Translator {
  init() {
    this.container = document.querySelector("#tradutor-app-container");

    if (!this.container) {
      return;
    }

    this.polling = null;

    this.render();
    this.bindEvents();
    this.checkStatus();
  }

  // ==================================================
  // CONSTRUIR INTERFACE
  // ==================================================

  render() {
    this.container.innerHTML = `
      <div class="translator">

        <div class="translator__header">
          <h3>Reconhecimento de Libras</h3>
          <p>
            Posicione as mãos diante da câmera para iniciar
            o reconhecimento dos sinais.
          </p>
        </div>

        <div class="translator__camera">

          <img
            id="translator-camera-feed"
            alt="Imagem da câmera com detecção dos movimentos das mãos"
            hidden
          />

          <span
            class="translator__camera-icon"
            id="translator-camera-icon"
            aria-hidden="true"
          >📷</span>

          <p
            id="translator-camera-message"
            aria-live="polite"
          >
            A câmera ainda não foi iniciada.
          </p>

        </div>

        <!-- INDICADOR DE DETECÇÃO DAS MÃOS -->
        <div
          id="translator-hand-indicator"
          class="hand-indicator hand-indicator--waiting"
          role="status"
          aria-live="polite"
        >
          Nenhuma mão detectada
        </div>

        <div class="translator__result">

          <h4>Resultado do reconhecimento</h4>

          <p>
            <strong>Sinal identificado:</strong>
            <span id="translator-sign">Nenhum sinal</span>
          </p>

          <p>
            <strong>Tradução:</strong>
            <span id="translator-translation">
              Aguardando sinal...
            </span>
          </p>

          <p>
            <strong>Confiança:</strong>
            <span id="translator-confidence">—</span>
          </p>

        </div>

        <p
          id="translator-status"
          class="translator__status"
          role="status"
          aria-live="polite"
        >
          Verificando conexão com o servidor...
        </p>

        <div class="translator__actions">

          <button
            type="button"
            class="btn btn--primary"
            id="translator-start"
            disabled
          >
            Iniciar reconhecimento
          </button>

          <button
            type="button"
            class="btn btn--secondary"
            id="translator-stop"
            disabled
          >
            Parar reconhecimento
          </button>

        </div>

      </div>
    `;
  }

  // ==================================================
  // EVENTOS DOS BOTÕES
  // ==================================================

  bindEvents() {
    this.startButton =
      this.container.querySelector("#translator-start");

    this.stopButton =
      this.container.querySelector("#translator-stop");

    this.startButton.addEventListener("click", () => {
      this.startRecognition();
    });

    this.stopButton.addEventListener("click", () => {
      this.stopRecognition();
    });
  }

  // ==================================================
  // VERIFICAR CONEXÃO COM O SERVIDOR
  // ==================================================

  async checkStatus() {
    try {
      const response = await fetch("/api/status");

      if (!response.ok) {
        throw new Error("Servidor indisponível.");
      }

      const data = await response.json();

      this.setStatus(
        `Servidor ${data.servidor}: ${data.sistema}.`
      );

      this.startButton.disabled = false;

      await this.updateRecognitionState();

    } catch (error) {

      this.setStatus(
        "Não foi possível conectar ao servidor Tradulib."
      );

      console.error("Erro ao verificar servidor:", error);
    }
  }

  // ==================================================
  // INICIAR RECONHECIMENTO
  // ==================================================

  async startRecognition() {
    this.startButton.disabled = true;
    this.stopButton.disabled = true;

    this.setStatus("Iniciando reconhecimento...");

    try {
      const response = await fetch(
        "/api/reconhecimento/iniciar",
        {
          method: "POST"
        }
      );

      const data = await response.json();

      if (!response.ok && response.status !== 409) {
        throw new Error(
          data.mensagem || "Não foi possível iniciar."
        );
      }

      this.startPolling();

      await this.updateRecognitionState();

    } catch (error) {

      this.setStatus(
        `Erro ao iniciar: ${error.message}`
      );

      console.error("Erro ao iniciar reconhecimento:", error);

      this.startButton.disabled = false;
      this.stopButton.disabled = true;
    }
  }

  // ==================================================
  // PARAR RECONHECIMENTO
  // ==================================================

  async stopRecognition() {
    this.stopButton.disabled = true;

    this.setStatus("Encerrando reconhecimento...");

    try {
      const response = await fetch(
        "/api/reconhecimento/parar",
        {
          method: "POST"
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.mensagem || "Não foi possível parar."
        );
      }

      await this.updateRecognitionState();

    } catch (error) {

      this.setStatus(
        `Erro ao parar: ${error.message}`
      );

      console.error("Erro ao parar reconhecimento:", error);
    }
  }

  // ==================================================
  // CONSULTAR ESTADO DO RECONHECIMENTO
  // ==================================================

  async updateRecognitionState() {
    try {
      const response = await fetch(
        "/api/reconhecimento/estado"
      );

      if (!response.ok) {
        throw new Error(
          "Não foi possível consultar o reconhecimento."
        );
      }

      const state = await response.json();

      // ----------------------------------------------
      // ATUALIZAR INDICADOR DE MÃOS
      // ----------------------------------------------

      const handIndicator = this.container.querySelector(
        "#translator-hand-indicator"
      );

      if (handIndicator) {
        if (state.running && state.maos_detectadas) {
          handIndicator.textContent = "Mãos detectadas";
          handIndicator.className =
            "hand-indicator hand-indicator--detected";
        } else {
          handIndicator.textContent = "Nenhuma mão detectada";
          handIndicator.className =
            "hand-indicator hand-indicator--waiting";
        }
      }

      // ----------------------------------------------
      // ATUALIZAR RESULTADOS
      // ----------------------------------------------

      this.container.querySelector(
        "#translator-sign"
      ).textContent = state.sinal || "Nenhum sinal";

      this.container.querySelector(
        "#translator-translation"
      ).textContent =
        state.traducao || "Aguardando sinal...";

      const confidence = Number(state.confianca || 0);

      this.container.querySelector(
        "#translator-confidence"
      ).textContent =
        state.sinal && state.sinal !== "Sinal incerto"
          ? `${(confidence * 100).toFixed(1)}%`
          : "—";

      // ----------------------------------------------
      // ATUALIZAR CÂMERA E MENSAGENS
      // ----------------------------------------------

      const cameraMessage = this.container.querySelector(
        "#translator-camera-message"
      );

      if (state.running) {

        this.startCameraFeed();

        if (state.maos_detectadas) {

          cameraMessage.textContent =
            `Mãos detectadas! Pode realizar o sinal. ` +
            `${state.frames}/${state.total_frames} frames.`;

        } else {

          cameraMessage.textContent =
            "Mãos não detectadas. Posicione suas mãos diante da câmera.";
        }

      } else {

        this.stopCameraFeed();

        if (state.erro) {

          cameraMessage.textContent =
            "Não foi possível iniciar a câmera.";

        } else if (
          state.status &&
          state.status.startsWith("Sinal reconhecido")
        ) {

          cameraMessage.textContent =
            "Sinal reconhecido! Clique em iniciar para reconhecer outro.";

        } else {

          cameraMessage.textContent =
            "Reconhecimento encerrado. Clique em iniciar para tentar novamente.";
        }
      }

      // ----------------------------------------------
      // ATUALIZAR BOTÕES
      // ----------------------------------------------

      this.startButton.disabled = state.running;
      this.stopButton.disabled = !state.running;

      // ----------------------------------------------
      // ATUALIZAR STATUS
      // ----------------------------------------------

      if (state.erro) {

        this.setStatus(`Erro: ${state.erro}`);

      } else {

        this.setStatus(
          `Reconhecimento: ${state.status}.`
        );
      }

      // ----------------------------------------------
      // CONTROLAR CONSULTAS AUTOMÁTICAS
      // ----------------------------------------------

      if (state.running) {

        this.startPolling();

      } else {

        this.stopPolling();
      }

      return state;

    } catch (error) {

      this.setStatus(
        `Erro ao consultar estado: ${error.message}`
      );

      console.error(
        "Erro ao consultar reconhecimento:",
        error
      );

      return null;
    }
  }

  // ==================================================
  // TRANSMISSÃO DA CÂMERA
  // ==================================================

  startCameraFeed() {
    const cameraFeed = this.container.querySelector(
      "#translator-camera-feed"
    );

    const cameraIcon = this.container.querySelector(
      "#translator-camera-icon"
    );

    if (!cameraFeed) return;

    cameraFeed.hidden = false;

    if (cameraIcon) {
      cameraIcon.hidden = true;
    }

    if (!cameraFeed.getAttribute("src")) {
      cameraFeed.src =
        "/api/reconhecimento/video";
    }
  }

  // ==================================================
  // ENCERRAR TRANSMISSÃO DA CÂMERA
  // ==================================================

  stopCameraFeed() {
    const cameraFeed = this.container.querySelector(
      "#translator-camera-feed"
    );

    const cameraIcon = this.container.querySelector(
      "#translator-camera-icon"
    );

    if (!cameraFeed) return;

    cameraFeed.removeAttribute("src");
    cameraFeed.hidden = true;

    if (cameraIcon) {
      cameraIcon.hidden = false;
    }
  }

  // ==================================================
  // CONSULTA AUTOMÁTICA DO ESTADO
  // ==================================================

  startPolling() {
    if (this.polling) return;

    this.polling = setInterval(() => {
      this.updateRecognitionState();
    }, 1000);
  }

  stopPolling() {
    if (!this.polling) return;

    clearInterval(this.polling);
    this.polling = null;
  }

  // ==================================================
  // MENSAGENS DA INTERFACE
  // ==================================================

  setStatus(message) {
    const statusElement = this.container.querySelector(
      "#translator-status"
    );

    if (statusElement) {
      statusElement.textContent = message;
    }
  }
}
