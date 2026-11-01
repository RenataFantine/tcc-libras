/* SITE-CONTENT.JS — renderiza vídeo de demonstração e integrantes a partir de js/config.js. */
import { SITE } from "../config.js?v=4";
import { qsa } from "./dom-utils.js";

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const ghLabel = (url) => url.replace(/^https?:\/\//, "");

export class SiteContent {
  init() {
    this.renderVideos();
    this.renderMembers();
  }

  renderVideos() {
    qsa("[data-demo-video]").forEach((box) => {
      if (!SITE.videoSrc) {
        box.innerHTML = '<p class="placeholder">Espaço reservado para o vídeo de demonstração em Libras. Defina <code>videoSrc</code> em js/config.js.</p>';
        return;
      }
      const src = esc(SITE.videoSrc);
      box.innerHTML = `<video controls preload="metadata" aria-label="Vídeo de demonstração em Libras"><source src="${src}">Seu navegador não suporta vídeos. <a href="${src}">Baixe o vídeo aqui</a>.</video>`;
    });
  }

  renderMembers() {
    qsa('[data-members="cards"]').forEach((list) => {
      list.innerHTML = SITE.members.map((m) => {
        const photo = m.photo
          ? `<img class="member__photo" src="${esc(m.photo)}" alt="Foto de ${esc(m.name)}" loading="lazy" />`
          : `<div class="member__photo" role="img" aria-label="Espaço reservado para a foto de ${esc(m.name)}">Espaço para foto</div>`;
        const bio = m.bio ? `<p>${esc(m.bio)}</p>` : "";
        return `<li class="card contact-card member">${photo}<h3>${esc(m.name)}</h3>${bio}<ul><li>E-mail: <a href="mailto:${esc(m.email)}">${esc(m.email)}</a></li><li>GitHub: <a href="${esc(m.github)}" target="_blank" rel="noopener">${esc(ghLabel(m.github))}</a></li></ul></li>`;
      }).join("");
    });
    qsa('[data-members="footer"]').forEach((list) => {
      list.innerHTML = SITE.members.map((m) => `<li>${esc(m.name)}: <a href="mailto:${esc(m.email)}">${esc(m.email)}</a> · <a href="${esc(m.github)}" target="_blank" rel="noopener">GitHub</a></li>`).join("");
    });
  }
}