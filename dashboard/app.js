const API_BASE = "/api/v1";
const TOKEN_KEY = "endpoint_console_token";

const $ = (id) => document.getElementById(id);

let authToken = sessionStorage.getItem(TOKEN_KEY);

function setMessage(message, isError = false) {
  const element = $("app-message");
  element.textContent = message || "";
  element.classList.toggle("error", isError);
}

function showLogin() {
  $("login-view").classList.remove("hidden");
  $("app-view").classList.add("hidden");
}

function showApp() {
  $("login-view").classList.add("hidden");
  $("app-view").classList.remove("hidden");
}

function escapeText(value) {
  return value === null || value === undefined || value === ""
    ? "—"
    : String(value);
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function makeCell(value) {
  const cell = document.createElement("td");
  cell.textContent = escapeText(value);
  return cell;
}

function renderTable(containerId, headings, rows) {
  const container = $(containerId);
  container.replaceChildren();

  if (!Array.isArray(rows) || rows.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No records available.";
    container.append(empty);
    return;
  }

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");

  headings.forEach((heading) => {
    const th = document.createElement("th");
    th.textContent = heading;
    headerRow.append(th);
  });

  thead.append(headerRow);
  table.append(thead);

  const tbody = document.createElement("tbody");

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((value) => tr.append(makeCell(value)));
    tbody.append(tr);
  });

  table.append(tbody);
  container.append(table);
}

async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});

  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 || response.status === 403) {
    if (response.status === 401) logout();
    throw new Error(response.status === 401
      ? "Your session has expired. Please sign in again."
      : "You are not authorized to perform this action.");
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Keep the HTTP status message if the response isn't JSON.
    }
    throw new Error(detail);
  }

  return response;
}

async function getJson(path) {
  const response = await apiRequest(path);
  return response.json();
}

function getArray(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.reports)) return payload.reports;
  if (Array.isArray(payload?.devices)) return payload.devices;
  if (Array.isArray(payload?.events)) return payload.events;
  if (Array.isArray(payload?.files)) return payload.files;
  return [];
}

async function login(event) {
  event.preventDefault();
  $("login-error").textContent = "";

  const username = $("username").value.trim();
  const password = $("password").value;

  const body = new URLSearchParams();
  body.set("username", username);
  body.set("password", password);

  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    });

    if (!response.ok) {
      let message = "Login failed. Check your credentials.";
      try {
        const data = await response.json();
        message = data.detail || message;
      } catch {
        // Use the default message.
      }
      throw new Error(message);
    }

    const data = await response.json();

    if (!data.access_token) {
      throw new Error("The server did not return an access token.");
    }

    authToken = data.access_token;
    sessionStorage.setItem(TOKEN_KEY, authToken);

    $("password").value = "";
    showApp();
    await loadDashboard();
  } catch (error) {
    $("login-error").textContent = error.message;
  }
}

function logout() {
  authToken = null;
  sessionStorage.removeItem(TOKEN_KEY);
  showLogin();
}

function showSection(name) {
  document.querySelectorAll(".page-section").forEach((section) => {
    section.classList.add("hidden");
  });

  const target = $(`section-${name}`);
  if (target) target.classList.remove("hidden");

  document.querySelectorAll(".nav-link").forEach((button) => {
    button.classList.toggle("active", button.dataset.section === name);
  });

  const titles = {
    overview: "Overview",
    devices: "Devices",
    monitoring: "Monitoring",
    events: "Security events",
    files: "Managed files",
  };

  $("page-title").textContent = titles[name] || "Dashboard";

  if (name === "files") loadFiles();
}

function deviceName(report) {
  return report.device_name ||
    report.device?.device_name ||
    report.device?.name ||
    report.device_uid ||
    report.device_id ||
    "Unknown device";
}

async function loadOverview() {
  const [devicesResult, reportsResult, eventsResult] = await Promise.allSettled([
    getJson("/devices"),
    getJson("/monitoring/reports"),
    getJson("/security/events"),
  ]);

  const devices = devicesResult.status === "fulfilled"
    ? getArray(devicesResult.value) : [];
  const reports = reportsResult.status === "fulfilled"
    ? getArray(reportsResult.value) : [];
  const events = eventsResult.status === "fulfilled"
    ? getArray(eventsResult.value) : [];

  $("stat-devices").textContent =
    devicesResult.status === "fulfilled" ? devices.length : "Unavailable";
  $("stat-reports").textContent =
    reportsResult.status === "fulfilled" ? reports.length : "Unavailable";
  $("stat-events").textContent =
    eventsResult.status === "fulfilled" ? events.length : "Unavailable";

  const recent = [...reports]
    .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
    .slice(0, 8);

  renderTable("overview-reports",
    ["Device", "CPU", "Memory", "Disk", "Received"],
    recent.map((report) => [
      deviceName(report),
      report.cpu_percent == null ? "—" : `${report.cpu_percent}%`,
      report.memory_percent == null ? "—" : `${report.memory_percent}%`,
      report.disk_percent == null ? "—" : `${report.disk_percent}%`,
      formatDate(report.created_at),
    ])
  );

  const failures = [devicesResult, reportsResult, eventsResult]
    .filter((result) => result.status === "rejected");

  if (failures.length) {
    setMessage("Some dashboard data could not be loaded. Check the relevant API endpoint.", true);
  }
}

async function loadDevices() {
  const payload = await getJson("/devices");
  const devices = getArray(payload);

  renderTable("devices-table",
    ["Device", "Device ID", "Operating system", "Last seen", "Status"],
    devices.map((device) => [
      device.device_name || device.name || "Unnamed device",
      device.device_uid || device.id,
      device.os_name || device.platform || device.operating_system,
      formatDate(device.last_seen),
      device.is_active === false || device.is_revoked
        ? "Revoked"
        : "Registered",
    ])
  );
}

async function loadMonitoring() {
  const payload = await getJson("/monitoring/reports");
  const reports = getArray(payload);

  renderTable("monitoring-table",
    ["Device", "CPU", "Memory", "Disk", "Network sent", "Network received", "Time"],
    reports.map((report) => [
      deviceName(report),
      report.cpu_percent == null ? "—" : `${report.cpu_percent}%`,
      report.memory_percent == null ? "—" : `${report.memory_percent}%`,
      report.disk_percent == null ? "—" : `${report.disk_percent}%`,
      report.network_bytes_sent ?? "—",
      report.network_bytes_recv ?? "—",
      formatDate(report.created_at),
    ])
  );
}

async function loadEvents() {
  const payload = await getJson("/security/events");
  const events = getArray(payload);

  renderTable("events-table",
    ["Event", "Severity", "Device", "Description", "Time"],
    events.map((event) => [
      event.event_type || event.title || event.type,
      event.severity,
      event.device_name || event.device_id,
      event.description || event.message,
      formatDate(event.created_at),
    ])
  );
}

async function loadFiles() {
  const path = $("current-path").value.trim();
  const query = new URLSearchParams({ path });

  try {
    const payload = await getJson(`/files?${query.toString()}`);
    const files = getArray(payload);
    const container = $("files-list");
    container.replaceChildren();

    if (!files.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "This folder is empty, or no files were returned.";
      container.append(empty);
      return;
    }

    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const header = document.createElement("tr");

    ["Name", "Type", "Size", "Action"].forEach((name) => {
      const th = document.createElement("th");
      th.textContent = name;
      header.append(th);
    });

    thead.append(header);
    table.append(thead);

    const tbody = document.createElement("tbody");

    files.forEach((file) => {
      const tr = document.createElement("tr");
      tr.append(makeCell(file.name));
      tr.append(makeCell(file.is_dir || file.is_directory ? "Folder" : "File"));
      tr.append(makeCell(file.size == null ? "—" : `${file.size} bytes`));

      const actionCell = document.createElement("td");

      if (!file.is_dir && !file.is_directory) {
        const downloadButton = document.createElement("button");
        downloadButton.className = "file-action";
        downloadButton.textContent = "Download";
        downloadButton.addEventListener("click", () => downloadFile(file.path || file.name));
        actionCell.append(downloadButton);
      } else {
        actionCell.textContent = "—";
      }

      tr.append(actionCell);
      tbody.append(tr);
    });

    table.append(tbody);
    container.append(table);
  } catch (error) {
    setMessage(`Could not load managed files: ${error.message}`, true);
  }
}

async function downloadFile(path) {
  try {
    const query = new URLSearchParams({ path });
    const response = await apiRequest(`/files/download?${query.toString()}`);
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = objectUrl;
    link.download = path.split("/").pop() || "download";
    document.body.append(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(objectUrl);
  } catch (error) {
    setMessage(`Download failed: ${error.message}`, true);
  }
}

async function uploadFile(event) {
  event.preventDefault();

  const file = $("file-input").files[0];
  if (!file) {
    setMessage("Choose a file before uploading.", true);
    return;
  }

  const destination = $("upload-path").value.trim();
  const formData = new FormData();
  formData.append("file", file);

  const query = new URLSearchParams({ path: destination });

  try {
    await apiRequest(`/files/upload?${query.toString()}`, {
      method: "POST",
      body: formData,
    });

    $("file-input").value = "";
    setMessage("File uploaded successfully.");
    await loadFiles();
  } catch (error) {
    setMessage(`Upload failed: ${error.message}`, true);
  }
}

async function loadDashboard() {
  setMessage("");

  try {
    const me = await getJson("/auth/me");
    $("admin-label").textContent =
      me.email || me.username || me.full_name || "Administrator";
  } catch (error) {
    setMessage(`Could not verify your session: ${error.message}`, true);
    return;
  }

  try {
    await loadOverview();
  } catch (error) {
    setMessage(`Could not load dashboard: ${error.message}`, true);
  }
}

$("login-form").addEventListener("submit", login);
$("logout-button").addEventListener("click", logout);
$("refresh-button").addEventListener("click", loadDashboard);
$("browse-button").addEventListener("click", loadFiles);
$("file-upload-form").addEventListener("submit", uploadFile);

document.querySelectorAll(".nav-link").forEach((button) => {
  button.addEventListener("click", async () => {
    const section = button.dataset.section;
    showSection(section);
    setMessage("");

    try {
      if (section === "devices") await loadDevices();
      if (section === "monitoring") await loadMonitoring();
      if (section === "events") await loadEvents();
    } catch (error) {
      setMessage(`Could not load ${section}: ${error.message}`, true);
    }
  });
});

if (authToken) {
  showApp();
  loadDashboard();
} else {
  showLogin();
}
