(function () {
  const shell = document.querySelector(".shell");
  const applications = document.querySelector("#applications");
  const refreshSeconds = Number(shell?.dataset.refreshSeconds || 30);

  function valueOrNA(value, suffix) {
    if (value === null || value === undefined) return "N/A";
    return `${value}${suffix || ""}`;
  }

  function updateText(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  }

  function renderApplications(cards) {
    applications.replaceChildren();
    for (const card of cards) {
      const article = document.createElement("article");
      article.className = "app-card";
      article.dataset.status = card.status;

      const topline = document.createElement("div");
      topline.className = "card-topline";

      const category = document.createElement("span");
      category.className = "category";
      category.textContent = card.category;

      const status = document.createElement("span");
      status.className = "status";
      status.textContent = card.status;

      const title = document.createElement("h3");
      title.textContent = card.name;

      const description = document.createElement("p");
      description.textContent = card.description;

      const link = document.createElement("a");
      link.href = card.url;
      link.rel = "noreferrer";
      link.textContent = card.url;

      topline.append(category, status);
      article.append(topline, title, description, link);
      applications.append(article);
    }
  }

  async function refresh() {
    try {
      const response = await fetch("/api/status", { headers: { "Accept": "application/json" } });
      if (!response.ok) return;
      const payload = await response.json();
      updateText("server-name", payload.server.label);
      updateText("hostname", payload.system.hostname);
      updateText("uptime", payload.system.uptime_human);
      updateText("cpu", valueOrNA(payload.system.cpu_percent, "%"));
      updateText("load", payload.system.load_average ? payload.system.load_average.join(" / ") : "N/A");
      updateText("memory", valueOrNA(payload.system.memory.percent, "%"));
      updateText("disk", valueOrNA(payload.system.disk.percent, "%"));
      updateText("temperature", valueOrNA(payload.system.cpu_temperature_c, "°C"));
      updateText("docker", payload.docker.available ? "Online" : "Unavailable");
      renderApplications(payload.applications);
    } catch (error) {
      console.warn("Status refresh failed", error);
    }
  }

  if (applications) {
    window.setInterval(refresh, refreshSeconds * 1000);
  }
})();
