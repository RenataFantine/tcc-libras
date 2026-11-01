
/*
 * MAIN.JS — ponto de entrada do TraduLib.
 * Cada módulo é carregado de forma independente.
 * A versão evita o uso de arquivos antigos em cache.
 */

const VERSION = "6";

const MODULES = [
  ["navbar", "Navbar"],
  ["accessibility", "Accessibility"],
  ["site-content", "SiteContent"],
  ["admin-login", "AdminLogin"],
  ["admin-dashboard", "AdminDashboard"],
  ["translator", "Translator"]
];

async function start() {
  for (const [file, name] of MODULES) {
    try {
      const mod = await import(
        `./modules/${file}.js?v=${VERSION}`
      );

      if (!mod[name]) {
        console.error(
          `A classe ${name} não foi encontrada em ${file}.js`
        );
        continue;
      }

      new mod[name]().init();

    } catch (error) {
      console.error(
        `Falha ao iniciar ${file}:`,
        error
      );
    }
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", start);
} else {
  start();
}
