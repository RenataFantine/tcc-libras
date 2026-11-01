/* ACCESSIBILITY.JS — botão e painel de acessibilidade (tamanho do texto, tema, fonte para dislexia).
   Preferências ficam só no navegador (localStorage, chave tradulib_a11y). Sem dados pessoais.
   O mesmo estado é aplicado antes da pintura por um pequeno script no <head> de cada página (evita "piscar"). */
import { qs } from "./dom-utils.js";

const KEY = "tradulib_a11y";
const SCALES = [0.875, 1, 1.125, 1.25, 1.375];
const DEFAULT_LEVEL = 1;
const ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="4.5" r="1.8"/><path d="M5 8.5l7 1.5 7-1.5M12 10v5l-3 5M12 15l3 5"/></svg>';
const FONT_URL = "https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap";

const store = {
  read() { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch { return {}; } },
  write(data) { try { localStorage.setItem(KEY, JSON.stringify(data)); } catch { /* sem storage */ } },
};

export class Accessibility {
  init() {
    const host = qs(".navbar__container");
    if (!host) return;
    const saved = store.read();
    this.level = Number.isInteger(saved.level) && SCALES[saved.level] ? saved.level : DEFAULT_LEVEL;
    this.userTheme = saved.theme === "dark" || saved.theme === "light";
    const systemDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    this.theme = this.userTheme ? saved.theme : systemDark ? "dark" : "light";
    this.dyslexia = saved.dyslexia === true;
    this.open = false;
    this.build(host);
    this.bind();
    this.apply();
  }

  build(host) {
    this.wrap = document.createElement("div");
    this.wrap.className = "a11y";
    const size = (action, hidden, label) => `<button type="button" class="a11y__control" data-action="${action}"><span aria-hidden="true">${label}</span><span class="visually-hidden">${hidden}</span></button>`;
    this.wrap.innerHTML = `
      <button type="button" class="a11y__button" aria-expanded="false" aria-controls="a11yPanel" aria-haspopup="dialog">${ICON}<span class="a11y__label">Acessibilidade</span></button>
      <div class="a11y__panel" id="a11yPanel" role="dialog" aria-labelledby="a11yTitle" hidden>
        <h2 class="a11y__title" id="a11yTitle">Acessibilidade</h2>
        <section class="a11y__group" aria-labelledby="a11yText">
          <h3 class="a11y__heading" id="a11yText">Tamanho do texto</h3>
          <div class="a11y__row a11y__row--3">${size("size-down", "Diminuir fonte", "A−")}${size("size-reset", "Restaurar tamanho padrão", "Padrão")}${size("size-up", "Aumentar fonte", "A+")}</div>
          <p class="a11y__status" aria-live="polite"></p>
        </section>
        <section class="a11y__group" aria-labelledby="a11yTheme">
          <h3 class="a11y__heading" id="a11yTheme">Tema da interface</h3>
          <div class="a11y__row"><button type="button" class="a11y__control" data-action="theme-light">Tema claro</button><button type="button" class="a11y__control" data-action="theme-dark">Tema escuro</button></div>
        </section>
        <section class="a11y__group" aria-labelledby="a11yRead">
          <h3 class="a11y__heading" id="a11yRead">Leitura acessível</h3>
          <button type="button" class="a11y__control a11y__switch" role="switch" data-action="dyslexia"><span>Fonte adaptada para dislexia</span><span class="a11y__state"></span></button>
          <p class="a11y__hint">Adaptação visual que pode ajudar alguns leitores; o efeito varia de pessoa para pessoa.</p>
        </section>
      </div>`;
    host.appendChild(this.wrap);
    this.button = qs(".a11y__button", this.wrap);
    this.panel = qs(".a11y__panel", this.wrap);
  }

  bind() {
    this.button.addEventListener("click", () => this.toggle());
    this.panel.addEventListener("click", (e) => {
      const el = e.target.closest("[data-action]");
      if (el) this.act(el.dataset.action);
    });
    document.addEventListener("click", (e) => { if (this.open && !this.wrap.contains(e.target)) this.close(); });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && this.open) { this.close(); this.button.focus(); }
    });
  }

  toggle() { this.open ? this.close() : this.openPanel(); }
  openPanel() { this.open = true; this.panel.hidden = false; this.button.setAttribute("aria-expanded", "true"); }
  close() { this.open = false; this.panel.hidden = true; this.button.setAttribute("aria-expanded", "false"); }

  act(action) {
    if (action === "size-down" && this.level > 0) this.level--;
    else if (action === "size-up" && this.level < SCALES.length - 1) this.level++;
    else if (action === "size-reset") this.level = DEFAULT_LEVEL;
    else if (action === "theme-light" || action === "theme-dark") { this.theme = action.slice(6); this.userTheme = true; }
    else if (action === "dyslexia") this.dyslexia = !this.dyslexia;
    this.apply();
    store.write({ level: this.level, theme: this.userTheme ? this.theme : undefined, dyslexia: this.dyslexia });
  }

  apply() {
    const root = document.documentElement;
    root.style.setProperty("--font-scale", String(SCALES[this.level]));
    root.dataset.theme = this.theme;
    if (this.dyslexia) { root.dataset.dyslexia = "on"; this.loadFont(); } else delete root.dataset.dyslexia;

    const q = (a) => qs(`[data-action="${a}"]`, this.panel);
    qs(".a11y__status", this.panel).textContent = `Tamanho atual: ${Math.round(SCALES[this.level] * 100)}%`;
    q("size-down").setAttribute("aria-disabled", String(this.level === 0));
    q("size-up").setAttribute("aria-disabled", String(this.level === SCALES.length - 1));
    q("theme-light").setAttribute("aria-pressed", String(this.theme === "light"));
    q("theme-dark").setAttribute("aria-pressed", String(this.theme === "dark"));
    q("dyslexia").setAttribute("aria-checked", String(this.dyslexia));
    qs(".a11y__state", this.panel).textContent = this.dyslexia ? "Ativada" : "Desativada";
  }

  loadFont() {
    if (document.getElementById("a11y-font")) return;
    const link = document.createElement("link");
    link.id = "a11y-font";
    link.rel = "stylesheet";
    link.href = FONT_URL;
    document.head.appendChild(link);
  }
}