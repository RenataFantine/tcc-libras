/* ==========================================================================
   DOM-UTILS.JS
   Helpers genéricos de manipulação de DOM, sem regra de negócio nenhuma.
   Qualquer módulo de interface (navbar, futuros componentes) pode reusar.
   ========================================================================== */

export const qs = (selector, scope = document) => scope.querySelector(selector);

export const qsa = (selector, scope = document) => [...scope.querySelectorAll(selector)];

export function toggleClass(element, className, force) {
  if (!element) return;
  element.classList.toggle(className, force);
}

export function setAttr(element, attribute, value) {
  if (!element) return;
  element.setAttribute(attribute, value);
}
