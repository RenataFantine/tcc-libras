/* NAVBAR.JS — comportamento da navbar: menu mobile acessível e sombra ao rolar.
   Só UI; a página atual é marcada no HTML com aria-current="page". */
import { qs, qsa, toggleClass, setAttr } from "./dom-utils.js";

export class Navbar {
  constructor({
    headerSelector = ".navbar",
    toggleSelector = "#navToggle",
    menuSelector = "#navMenu",
    linkSelector = ".navbar__link",
    desktopQuery = "(min-width: 769px)",
    scrollThreshold = 8,
  } = {}) {
    this.header = qs(headerSelector);
    this.toggleButton = qs(toggleSelector);
    this.menu = qs(menuSelector);
    this.links = qsa(linkSelector);
    this.desktopMedia = window.matchMedia(desktopQuery);
    this.scrollThreshold = scrollThreshold;
    this.isOpen = false;
  }

  init() {
    this.initScrollState();
    if (!this.toggleButton || !this.menu) return;

    this.toggleButton.addEventListener("click", () => this.toggleMenu());
    this.links.forEach((link) => link.addEventListener("click", () => this.closeMenu()));

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && this.isOpen) {
        this.closeMenu();
        this.toggleButton.focus();
      }
    });
    document.addEventListener("click", (event) => this.handleOutsideClick(event));
    this.desktopMedia.addEventListener("change", (event) => {
      if (event.matches) this.closeMenu();
    });
  }

  initScrollState() {
    if (!this.header) return;
    let ticking = false;
    const update = () => {
      toggleClass(this.header, "is-scrolled", window.scrollY > this.scrollThreshold);
      ticking = false;
    };
    window.addEventListener(
      "scroll",
      () => {
        if (!ticking) {
          requestAnimationFrame(update);
          ticking = true;
        }
      },
      { passive: true }
    );
    update();
  }

  toggleMenu() {
    this.isOpen ? this.closeMenu() : this.openMenu();
  }

  openMenu() {
    this.isOpen = true;
    toggleClass(this.menu, "is-open", true);
    setAttr(this.toggleButton, "aria-expanded", "true");
    setAttr(this.toggleButton, "aria-label", "Fechar menu de navegação");
  }

  closeMenu() {
    if (!this.isOpen) return;
    this.isOpen = false;
    toggleClass(this.menu, "is-open", false);
    setAttr(this.toggleButton, "aria-expanded", "false");
    setAttr(this.toggleButton, "aria-label", "Abrir menu de navegação");
  }

  handleOutsideClick(event) {
    if (!this.isOpen) return;
    const inside = this.menu.contains(event.target) || this.toggleButton.contains(event.target);
    if (!inside) this.closeMenu();
  }
}