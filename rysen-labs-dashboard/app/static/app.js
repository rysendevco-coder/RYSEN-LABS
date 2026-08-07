(function () {
  const shell = document.querySelector(".shell");
  const applications = document.querySelector("#applications");
  const repositories = document.querySelector("#repositories");
  const sprintProjects = document.querySelector("#sprint-projects");
  const needsAttention = document.querySelector("#needs-attention");
  const emptyState = document.querySelector("#empty-state");
  const repositoriesEmptyState = document.querySelector("#repositories-empty-state");
  const configErrors = document.querySelector("#config-errors");
  const updateIntervalSeconds = Number(shell?.dataset.updateIntervalSeconds || 30);
  let eventSource = null;
  let pollingTimer = null;
  let staleTimer = null;

  function valueOrNA(value, suffix) {
    if (value === null || value === undefined) return "N/A";
    return `${value}${suffix || ""}`;
  }

  function updateText(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  }

  function setConnection(state) {
    updateText("connection-state", state);
    const pulse = document.getElementById("connection-pulse");
    if (pulse) pulse.dataset.state = state.toLowerCase();
  }

  function formatTime(value) {
    try {
      return new Intl.DateTimeFormat(undefined, {
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
      }).format(new Date(value));
    } catch {
      return value;
    }
  }

  function createTextElement(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = text;
    return node;
  }

  function renderApplications(cards) {
    applications.replaceChildren();
    emptyState.hidden = cards.length > 0;
    for (const card of cards) {
      const article = document.createElement("article");
      article.className = "app-card";
      article.dataset.status = card.health.state;

      const topline = document.createElement("div");
      topline.className = "card-topline";
      topline.append(
        createTextElement("span", "category", card.category),
        createTextElement("span", "status", card.health.state.replaceAll("_", " ")),
      );

      const details = document.createElement("dl");
      details.className = "health-details";
      for (const [label, value] of [
        ["Latency", card.health.latency_ms === null ? "N/A" : `${card.health.latency_ms} ms`],
        ["Source", card.health.source],
      ]) {
        const group = document.createElement("div");
        group.append(createTextElement("dt", "", label), createTextElement("dd", "", value));
        details.append(group);
      }

      const link = document.createElement("a");
      link.href = card.url;
      link.rel = "noreferrer";
      link.textContent = card.url;

      article.append(
        topline,
        createTextElement("h3", "", card.name),
        createTextElement("p", "", card.description),
        details,
        link,
      );
      applications.append(article);
    }
  }

  function renderRepositories(items) {
    if (!repositories) return;
    repositories.replaceChildren();
    if (repositoriesEmptyState) repositoriesEmptyState.hidden = items.length > 0;
    for (const repo of items) {
      const article = document.createElement("article");
      article.className = "repo-card";
      article.dataset.status = repo.status_class;

      const topline = document.createElement("div");
      topline.className = "card-topline";
      topline.append(
        createTextElement("span", "category", repo.category),
        createTextElement("span", "status", repo.status_class.replaceAll("_", " ")),
      );

      const details = document.createElement("dl");
      details.className = "health-details";
      for (const [label, value] of [
        ["Branch", repo.detached_head ? "Detached" : (repo.current_branch || "N/A")],
        ["Commit", repo.short_commit_sha || "N/A"],
        ["Remote", repo.remote_url || "N/A"],
        ["Changes", `${repo.staged_files} staged / ${repo.modified_files} modified / ${repo.untracked_files} untracked`],
        ["Ahead/Behind", `${repo.ahead_count ?? "?"}/${repo.behind_count ?? "?"}`],
        ["Upstream", repo.upstream_branch || "N/A"],
      ]) {
        const group = document.createElement("div");
        group.append(createTextElement("dt", "", label), createTextElement("dd", "", value));
        details.append(group);
      }

      article.append(
        topline,
        createTextElement("h3", "", repo.repository_name),
        createTextElement("p", "", repo.warning || repo.latest_commit_message || repo.path),
        details,
      );
      repositories.append(article);
    }
  }

  function renderSprint(sprint) {
    if (!sprint || !sprintProjects) return;
    updateText("sprint-name", sprint.name);
    updateText("sprint-objective", sprint.primary_objective);
    updateText("revenue-goal-name", sprint.revenue_goal.name);
    updateText("revenue-goal-description", sprint.revenue_goal.description);
    updateText("sprint-progress-label", `${sprint.progress.progress_percentage}%`);
    const sprintBar = document.getElementById("sprint-progress-bar");
    if (sprintBar) sprintBar.style.width = `${sprint.progress.progress_percentage}%`;

    sprintProjects.replaceChildren();
    for (const project of sprint.projects) {
      const article = document.createElement("article");
      article.className = "sprint-card";
      article.dataset.status = project.status;

      const topline = document.createElement("div");
      topline.className = "card-topline";
      topline.append(
        createTextElement("span", "category", project.short_name),
        createTextElement("span", "status", project.status),
      );

      const track = document.createElement("div");
      track.className = "progress-track";
      const bar = document.createElement("span");
      bar.style.width = `${project.progress.progress_percentage}%`;
      track.append(bar);

      const details = document.createElement("dl");
      details.className = "health-details";
      for (const [label, value] of [
        ["Progress", `${project.progress.progress_percentage}%`],
        ["Points", `${project.progress.completed_points} / ${project.progress.total_points}`],
      ]) {
        const group = document.createElement("div");
        group.append(createTextElement("dt", "", label), createTextElement("dd", "", value));
        details.append(group);
      }

      article.append(
        topline,
        createTextElement("h3", "", project.name),
        createTextElement("p", "", project.current_focus),
        track,
        details,
      );
      sprintProjects.append(article);
    }

    if (!needsAttention) return;
    needsAttention.replaceChildren();
    if (sprint.needs_attention.length === 0) {
      needsAttention.append(createTextElement("p", "quiet-state", "No active blockers"));
      return;
    }
    for (const task of sprint.needs_attention) {
      const item = document.createElement("article");
      item.className = "attention-item";
      item.dataset.status = task.status;
      item.append(
        createTextElement("span", "status", task.status.replaceAll("_", " ")),
        createTextElement("strong", "", task.name),
        createTextElement("p", "", task.blocker || task.description),
      );
      needsAttention.append(item);
    }
  }

  function renderConfigErrors(errors) {
    configErrors.replaceChildren();
    configErrors.hidden = errors.length === 0;
    for (const error of errors) {
      configErrors.append(createTextElement("p", "", error));
    }
  }

  function render(payload) {
    updateText("server-name", payload.server.label);
    updateText("safe-mode", payload.server.safe_mode ? "On" : "Off");
    updateText("hostname", payload.system.hostname);
    updateText("uptime", payload.system.uptime_human);
    updateText("cpu", valueOrNA(payload.system.cpu_percent, "%"));
    updateText("load", payload.system.load_average ? payload.system.load_average.join(" / ") : "N/A");
    updateText("memory", valueOrNA(payload.system.memory.percent, "%"));
    updateText("disk", valueOrNA(payload.system.disk.percent, "%"));
    updateText("temperature", valueOrNA(payload.system.cpu_temperature_c, "°C"));
    updateText("docker", payload.docker.available ? "Online" : (payload.docker.enabled ? "Unavailable" : "Disabled"));
    updateText("service-count", String(payload.applications.length));
    updateText("repository-count", String((payload.repositories || []).length));
    updateText("last-updated", formatTime(payload.generated_at));
    renderConfigErrors(payload.config_errors || []);
    renderSprint(payload.sprint);
    renderApplications(payload.applications);
    renderRepositories(payload.repositories || []);
    window.clearTimeout(staleTimer);
    staleTimer = window.setTimeout(() => setConnection("Stale"), updateIntervalSeconds * 2500);
  }

  async function pollOnce() {
    try {
      const response = await fetch("/api/status", { headers: { "Accept": "application/json" } });
      if (!response.ok) return;
      render(await response.json());
      setConnection("Polling");
    } catch {
      setConnection("Disconnected");
    }
  }

  function startPolling() {
    if (pollingTimer) return;
    pollOnce();
    pollingTimer = window.setInterval(pollOnce, updateIntervalSeconds * 1000);
  }

  function startEvents() {
    if (!window.EventSource) {
      startPolling();
      return;
    }
    eventSource = new EventSource("/api/events");
    eventSource.addEventListener("open", () => {
      setConnection("Live");
      if (pollingTimer) {
        window.clearInterval(pollingTimer);
        pollingTimer = null;
      }
    });
    eventSource.addEventListener("status", (event) => {
      render(JSON.parse(event.data));
      setConnection("Live");
    });
    eventSource.addEventListener("error", () => {
      setConnection("Disconnected");
      startPolling();
    });
  }

  if (applications) startEvents();
  window.addEventListener("beforeunload", () => {
    if (eventSource) eventSource.close();
    if (pollingTimer) window.clearInterval(pollingTimer);
    if (staleTimer) window.clearTimeout(staleTimer);
  });
})();
