
/* ADMIN-DASHBOARD.JS — painel administrativo do TraduLib. */

import { qs } from "./dom-utils.js";

export class AdminDashboard {

init() {
  this.root = qs("#adminDashboard");

  if (!this.root) return;

  this.period = qs("#dashboardPeriod");
  this.refreshButton = qs("#dashboardRefresh");
  this.status = qs("#dashboardStatus");

  this.bindEvents();

  window.addEventListener("tradulib:admin-auth", (event) => {
    if (event.detail?.authenticated) {
      this.load();
    } else {
      this.clear();
    }
  });

  // Verifica a sessão mesmo quando o evento de login
  // aconteceu antes da inicialização deste módulo.
  this.checkSession();
}

async checkSession() {
  try {
    const response = await fetch("/api/admin/sessao", {
      method: "GET",
      credentials: "same-origin"
    });

    if (response.ok) {
      await this.load();
    }
  } catch (error) {
    console.error("Erro ao verificar sessão do dashboard:", error);
    this.setStatus("Não foi possível verificar a sessão administrativa.");
  }
}


  bindEvents() {
    this.period?.addEventListener("change", () => this.load());

    this.refreshButton?.addEventListener("click", () => this.load());

    window.addEventListener("resize", () => {
      if (this.data) this.drawCharts();
    });
  }

  async load() {
    const periodo = this.period?.value || "30";

    this.setStatus("Atualizando indicadores…");
    this.refreshButton && (this.refreshButton.disabled = true);

    try {
      const response = await fetch(
        `/api/admin/dashboard?periodo=${encodeURIComponent(periodo)}`,
        {
          method: "GET",
          credentials: "same-origin",
          headers: { "Accept": "application/json" }
        }
      );

      const data = await response.json();

      if (response.status === 401) {
        this.setStatus("Sua sessão expirou. Entre novamente.");
        return;
      }

      if (!response.ok) {
        throw new Error(data.erro || "Não foi possível carregar os dados.");
      }

      this.data = data;
      this.render();
      this.setStatus("Dados atualizados com sucesso.");

    } catch (error) {
      console.error("Erro ao carregar dashboard:", error);
      this.setStatus(error.message || "Erro ao carregar o dashboard.");
    } finally {
      if (this.refreshButton) {
        this.refreshButton.disabled = false;
      }
    }
  }

  render() {
    const indicadores = this.data.indicadores;

    this.setText("#metricRecognitions", this.formatNumber(
      indicadores.total_reconhecimentos
    ));

    this.setText("#metricAccesses", this.formatNumber(
      indicadores.total_acessos
    ));

    this.setText("#metricUsage", this.formatDuration(
      indicadores.tempo_total_segundos
    ));

    this.setText("#metricConfidence", (
      Number(indicadores.confianca_media) * 100
    ).toFixed(1).replace(".", ",") + "%");

    this.setText("#metricErrors", this.formatNumber(
      indicadores.total_erros
    ));

    this.renderRanking();
    this.renderRecognitions();
    this.renderAccesses();
    this.drawCharts();
  }

  renderRanking() {
    const container = qs("#rankingList");
    if (!container) return;

    container.replaceChildren();

    const ranking = this.data.ranking_sinais || [];
    const max = Math.max(
      1,
      ...ranking.map(item => Number(item.quantidade))
    );

    if (!ranking.length) {
      container.textContent = "Nenhum sinal registrado neste período.";
      return;
    }

    ranking.forEach((item) => {
      const row = document.createElement("div");
      row.className = "dashboard-ranking__item";

      const heading = document.createElement("div");
      heading.className = "dashboard-ranking__heading";

      const name = document.createElement("span");
      name.textContent = item.sinal;

      const count = document.createElement("strong");
      count.textContent = this.formatNumber(item.quantidade);

      heading.append(name, count);

      const track = document.createElement("div");
      track.className = "dashboard-ranking__track";

      const bar = document.createElement("div");
      bar.className = "dashboard-ranking__bar";
      bar.style.width = `${(Number(item.quantidade) / max) * 100}%`;

      track.append(bar);
      row.append(heading, track);
      container.append(row);
    });
  }

  renderRecognitions() {
    const body = qs("#recognitionsTable");
    if (!body) return;

    body.replaceChildren();

    const items = this.data.reconhecimentos_recentes || [];

    if (!items.length) {
      this.emptyRow(body, 3, "Nenhum reconhecimento registrado.");
      return;
    }

    items.forEach((item) => {
      const row = document.createElement("tr");

      this.addCell(row, item.sinal);
      this.addCell(
        row,
        `${(Number(item.confianca) * 100).toFixed(1).replace(".", ",")}%`
      );
      this.addCell(row, this.formatDate(item.data_hora));

      body.append(row);
    });
  }

  renderAccesses() {
    const body = qs("#accessesTable");
    if (!body) return;

    body.replaceChildren();

    const items = this.data.acessos_recentes || [];

    if (!items.length) {
      this.emptyRow(body, 3, "Nenhum acesso registrado.");
      return;
    }

    items.forEach((item) => {
      const row = document.createElement("tr");

      this.addCell(row, `#${item.id}`);
      this.addCell(row, this.formatDate(item.inicio));
      this.addCell(
        row,
        item.tempo_uso_segundos === null
          ? "Em andamento"
          : this.formatDuration(item.tempo_uso_segundos)
      );

      body.append(row);
    });
  }

  drawCharts() {
    this.drawEvolutionChart();
  }

  drawEvolutionChart() {
    const canvas = qs("#evolutionChart");
    if (!canvas) return;

    const context = canvas.getContext("2d");
    const values = this.data.evolucao_diaria || [];

    const width = Math.max(300, canvas.clientWidth);
    const height = 260;
    const ratio = window.devicePixelRatio || 1;

    canvas.width = width * ratio;
    canvas.height = height * ratio;
    canvas.style.height = `${height}px`;

    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, width, height);

    const padding = { top: 20, right: 18, bottom: 35, left: 38 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const numbers = values.map(item => Number(item.quantidade));
    const maxValue = Math.max(4, ...numbers);
    const step = Math.ceil(maxValue / 4);

    context.font = "11px Poppins, sans-serif";
    context.fillStyle = "#8993a5";
    context.strokeStyle = "rgba(140, 150, 170, 0.2)";
    context.lineWidth = 1;

    for (let i = 0; i <= 4; i++) {
      const value = step * i;
      const y = padding.top + chartHeight -
        (value / (step * 4)) * chartHeight;

      context.beginPath();
      context.moveTo(padding.left, y);
      context.lineTo(width - padding.right, y);
      context.stroke();

      context.fillText(
        String(value),
        5,
        y + 4
      );
    }

    if (!values.length) {
      context.fillText(
        "Sem dados para exibir.",
        padding.left + 10,
        padding.top + 25
      );
      return;
    }

    const points = values.map((item, index) => {
      const x = padding.left + (
        values.length === 1
          ? chartWidth / 2
          : index / (values.length - 1) * chartWidth
      );

      const y = padding.top + chartHeight -
        (Number(item.quantidade) / (step * 4)) * chartHeight;

      return { x, y };
    });

    if (points.length > 1) {
      context.beginPath();
      context.moveTo(points[0].x, points[0].y);

      points.slice(1).forEach(point => {
        context.lineTo(point.x, point.y);
      });

      context.strokeStyle = "#3977e8";
      context.lineWidth = 3;
      context.lineJoin = "round";
      context.stroke();

      const gradient = context.createLinearGradient(
        0, padding.top, 0, height - padding.bottom
      );

      gradient.addColorStop(0, "rgba(57, 119, 232, 0.22)");
      gradient.addColorStop(1, "rgba(57, 119, 232, 0)");

      context.beginPath();
      context.moveTo(points[0].x, height - padding.bottom);
      points.forEach(point => context.lineTo(point.x, point.y));
      context.lineTo(points[points.length - 1].x, height - padding.bottom);
      context.closePath();
      context.fillStyle = gradient;
      context.fill();
    }

    points.forEach(point => {
      context.beginPath();
      context.arc(point.x, point.y, 3.5, 0, Math.PI * 2);
      context.fillStyle = "#3977e8";
      context.fill();
    });

    const labelIndexes = [
      0,
      Math.floor((values.length - 1) / 2),
      values.length - 1
    ];

    [...new Set(labelIndexes)].forEach(index => {
      const label = values[index].data.slice(5).split("-").reverse().join("/");
      const point = points[index];

      context.textAlign = index === 0
        ? "left"
        : index === values.length - 1
          ? "right"
          : "center";

      context.fillStyle = "#8993a5";
      context.fillText(
        label,
        point.x,
        height - 10
      );
    });

    context.textAlign = "left";
  }

  addCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = value ?? "—";
    row.append(cell);
  }

  emptyRow(body, columns, message) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");

    cell.colSpan = columns;
    cell.textContent = message;
    cell.className = "dashboard-empty";

    row.append(cell);
    body.append(row);
  }

  setText(selector, value) {
    const element = qs(selector);
    if (element) element.textContent = value;
  }

  setStatus(message) {
    if (this.status) this.status.textContent = message;
  }

  formatNumber(value) {
    return Number(value || 0).toLocaleString("pt-BR");
  }

  formatDuration(seconds) {
    const total = Math.max(0, Number(seconds) || 0);
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const remainingSeconds = total % 60;

    if (hours > 0) return `${hours}h ${minutes}min`;
    if (minutes > 0) return `${minutes}min ${remainingSeconds}s`;
    return `${remainingSeconds}s`;
  }

  formatDate(value) {
    if (!value) return "—";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) return "—";

    return date.toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  clear() {
    this.data = null;

    [
      "#metricRecognitions",
      "#metricAccesses",
      "#metricUsage",
      "#metricConfidence",
      "#metricErrors"
    ].forEach(selector => this.setText(selector, "—"));

    ["#rankingList", "#recognitionsTable", "#accessesTable"].forEach(
      selector => {
        const element = qs(selector);
        if (element) element.replaceChildren();
      }
    );

    const canvas = qs("#evolutionChart");

    if (canvas) {
      const context = canvas.getContext("2d");
      context.clearRect(0, 0, canvas.width, canvas.height);
    }
  }
}
