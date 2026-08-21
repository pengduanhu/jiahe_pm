const state = {
  view: "dashboard",
  token: localStorage.getItem("auth_token") || "",
  currentUser: null,
  requirements: [],
  plans: [],
  cases: [],
  users: [],
  roles: [],
  search: "",
};

const viewMeta = {
  dashboard: {
    title: "工作台",
    subtitle: "查看需求、计划、用例的整体状态。",
    action: "新建需求",
  },
  requirements: {
    title: "需求管理",
    subtitle: "维护产品需求、负责人、优先级和交付状态。",
    action: "新建需求",
    search: "搜索需求标题、负责人、状态",
  },
  plans: {
    title: "测试计划管理",
    subtitle: "围绕需求规划测试周期、环境、目标和执行状态。",
    action: "新建计划",
    search: "搜索计划名称、负责人、环境",
  },
  cases: {
    title: "测试用例管理",
    subtitle: "编写、维护并跟踪测试用例的执行状态。",
    action: "新建用例",
    search: "搜索用例标题、模块、执行人",
  },
  users: {
    title: "用户管理",
    subtitle: "维护团队成员、角色、部门和账号状态。",
    action: "新建用户",
    search: "搜索姓名、邮箱、角色、部门",
  },
  roles: {
    title: "角色管理",
    subtitle: "维护系统角色、职责说明和启停状态。",
    action: "新建角色",
    search: "搜索角色名称、描述、状态",
  },
};

const schemas = {
  requirement: [
    { name: "title", label: "需求标题", type: "text", required: true, full: true },
    { name: "description", label: "需求描述", type: "textarea", full: true },
    { name: "owner", label: "负责人", type: "text" },
    { name: "priority", label: "优先级", type: "select", options: ["P0", "P1", "P2", "P3"] },
    { name: "status", label: "状态", type: "select", options: ["待评审", "进行中", "待验收", "已完成", "已关闭"] },
    { name: "due_date", label: "截止日期", type: "date" },
  ],
  plan: [
    { name: "name", label: "计划名称", type: "text", required: true, full: true },
    { name: "goal", label: "测试目标", type: "textarea", full: true },
    { name: "requirement_id", label: "关联需求", type: "requirement" },
    { name: "owner", label: "负责人", type: "text" },
    { name: "environment", label: "测试环境", type: "text" },
    { name: "status", label: "状态", type: "select", options: ["未开始", "执行中", "阻塞", "已完成", "已取消"] },
    { name: "start_date", label: "开始日期", type: "date" },
    { name: "end_date", label: "结束日期", type: "date" },
  ],
  case: [
    { name: "title", label: "用例标题", type: "text", required: true, full: true },
    { name: "requirement_id", label: "关联需求", type: "requirement" },
    { name: "plan_id", label: "测试计划", type: "plan" },
    { name: "module", label: "模块", type: "text" },
    { name: "priority", label: "优先级", type: "select", options: ["P0", "P1", "P2", "P3"] },
    { name: "type", label: "用例类型", type: "select", options: ["功能", "接口", "性能", "安全", "兼容性"] },
    { name: "status", label: "状态", type: "select", options: ["草稿", "待执行", "通过", "失败", "阻塞"] },
    { name: "assignee", label: "执行人", type: "text" },
    { name: "precondition", label: "前置条件", type: "textarea", full: true },
    { name: "steps", label: "测试步骤", type: "textarea", full: true },
    { name: "expected_result", label: "预期结果", type: "textarea", full: true },
  ],
  user: [
    { name: "name", label: "姓名", type: "text", required: true },
    { name: "email", label: "邮箱", type: "email" },
    { name: "role", label: "角色", type: "role" },
    { name: "department", label: "部门", type: "text" },
    { name: "phone", label: "电话", type: "tel" },
    { name: "status", label: "状态", type: "select", options: ["启用", "停用"] },
    { name: "last_login", label: "最近登录", type: "date" },
  ],
  role: [
    { name: "name", label: "角色名称", type: "text", required: true },
    { name: "status", label: "状态", type: "select", options: ["启用", "停用"] },
    { name: "description", label: "职责描述", type: "textarea", full: true },
  ],
};

const endpoints = {
  requirement: "/api/requirements",
  plan: "/api/test-plans",
  case: "/api/test-cases",
  user: "/api/users",
  role: "/api/roles",
};

document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  restoreSession();
});

function bindEvents() {
  document.getElementById("login-tab").addEventListener("click", () => switchAuthMode("login"));
  document.getElementById("register-tab").addEventListener("click", () => switchAuthMode("register"));
  document.getElementById("login-form").addEventListener("submit", handleLogin);
  document.getElementById("register-form").addEventListener("submit", handleRegister);
  document.getElementById("logout-button").addEventListener("click", logout);

  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => {
      switchView(button.dataset.view);
    });
  });

  document.getElementById("primary-action").addEventListener("click", () => {
    if (state.view === "plans") openEditor("plan");
    else if (state.view === "cases") openEditor("case");
    else if (state.view === "users") openEditor("user");
    else if (state.view === "roles") openEditor("role");
    else openEditor("requirement");
  });

  document.getElementById("search-input").addEventListener("input", (event) => {
    state.search = event.target.value.trim();
    render();
  });

  document.getElementById("close-dialog").addEventListener("click", closeDialog);
  document.getElementById("cancel-dialog").addEventListener("click", closeDialog);

  document.getElementById("editor-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const type = form.dataset.type;
    const id = form.dataset.id;
    const payload = Object.fromEntries(new FormData(form).entries());
    const saved = await saveRecord(type, id, payload);
    if (saved) {
      closeDialog();
      await loadAll();
    }
  });
}

async function restoreSession() {
  if (!state.token) {
    showAuth();
    return;
  }
  try {
    const result = await apiGet("/api/auth/me");
    state.currentUser = result.user;
    await enterApp();
  } catch (error) {
    clearSession();
    showAuth();
  }
}

function switchAuthMode(mode) {
  const isLogin = mode === "login";
  document.getElementById("login-tab").classList.toggle("active", isLogin);
  document.getElementById("register-tab").classList.toggle("active", !isLogin);
  document.getElementById("login-form").classList.toggle("hidden", !isLogin);
  document.getElementById("register-form").classList.toggle("hidden", isLogin);
  setAuthMessage("");
}

async function handleLogin(event) {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
  await authenticate("/api/auth/login", payload);
}

async function handleRegister(event) {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
  await authenticate("/api/auth/register", payload);
}

async function authenticate(path, payload) {
  setAuthMessage("");
  try {
    const result = await apiPost(path, payload, false);
    state.token = result.token;
    state.currentUser = result.user;
    localStorage.setItem("auth_token", state.token);
    await enterApp();
  } catch (error) {
    setAuthMessage(error.message || "操作失败，请稍后重试");
  }
}

async function enterApp() {
  showApp();
  document.getElementById("current-user").textContent = state.currentUser
    ? `${state.currentUser.name} · ${state.currentUser.role || "未设置角色"}`
    : "";
  await loadAll();
}

async function logout() {
  try {
    await fetch("/api/auth/logout", { method: "DELETE", headers: authHeaders() });
  } finally {
    clearSession();
    showAuth();
  }
}

function showAuth() {
  document.getElementById("auth-screen").hidden = false;
  document.getElementById("app-shell").hidden = true;
}

function showApp() {
  document.getElementById("auth-screen").hidden = true;
  document.getElementById("app-shell").hidden = false;
}

function clearSession() {
  state.token = "";
  state.currentUser = null;
  localStorage.removeItem("auth_token");
}

function setAuthMessage(message) {
  document.getElementById("auth-message").textContent = message;
}

async function loadAll() {
  const [summary, requirements, plans, cases, users, roles] = await Promise.all([
    apiGet("/api/summary"),
    apiGet("/api/requirements"),
    apiGet("/api/test-plans"),
    apiGet("/api/test-cases"),
    apiGet("/api/users"),
    apiGet("/api/roles"),
  ]);
  state.summary = summary;
  state.requirements = requirements;
  state.plans = plans;
  state.cases = cases;
  state.users = users;
  state.roles = roles;
  render();
}

async function apiGet(path) {
  const response = await fetch(path, { headers: authHeaders() });
  if (!response.ok) throw new Error(await errorMessage(response));
  return response.json();
}

async function apiPost(path, payload, withAuth = true) {
  const response = await fetch(path, {
    method: "POST",
    headers: withAuth ? authHeaders({ "Content-Type": "application/json" }) : { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await errorMessage(response));
  return response.json();
}

async function saveRecord(type, id, payload) {
  const response = await fetch(id ? `${endpoints[type]}/${id}` : endpoints[type], {
    method: id ? "PUT" : "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    alert(`保存失败：${await errorMessage(response)}`);
    return false;
  }
  return true;
}

async function deleteRecord(type, id) {
  if (!confirm("确定删除这条记录吗？")) return;
  const response = await fetch(`${endpoints[type]}/${id}`, { method: "DELETE", headers: authHeaders() });
  if (!response.ok) {
    alert(`删除失败：${await errorMessage(response)}`);
    return;
  }
  await loadAll();
}

function authHeaders(extra = {}) {
  return state.token ? { ...extra, Authorization: `Bearer ${state.token}` } : extra;
}

async function errorMessage(response) {
  const text = await response.text();
  try {
    const data = JSON.parse(text);
    return data.error || text;
  } catch {
    return text || response.statusText;
  }
}

function switchView(view) {
  state.view = view;
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("active", section.id === `${view}-view`);
  });
  const meta = viewMeta[view];
  document.getElementById("page-title").textContent = meta.title;
  document.getElementById("page-subtitle").textContent = meta.subtitle;
  document.getElementById("primary-action").textContent = meta.action;
  document.getElementById("search-input").placeholder = meta.search || "";
  document.getElementById("search-input").style.display = view === "dashboard" ? "none" : "block";
  render();
}

function render() {
  renderDashboard();
  renderRequirements();
  renderPlans();
  renderCases();
  renderUsers();
  renderRoles();
}

function renderDashboard() {
  const summary = state.summary || {};
  document.getElementById("metric-requirements").textContent = summary.requirements || 0;
  document.getElementById("metric-plans").textContent = summary.test_plans || 0;
  document.getElementById("metric-cases").textContent = summary.test_cases || 0;
  document.getElementById("metric-users").textContent = `${summary.active_users || 0}/${summary.users || 0}`;
  document.getElementById("metric-roles").textContent = `${summary.active_roles || 0}/${summary.roles || 0}`;

  document.getElementById("recent-requirements").innerHTML = state.requirements
    .slice(0, 5)
    .map((item) => compactItem(item.title, `${item.owner || "未分配"} · ${item.status} · ${item.priority}`))
    .join("") || emptyState("暂无需求");

  document.getElementById("recent-cases").innerHTML = state.cases
    .filter((item) => ["草稿", "待执行", "阻塞"].includes(item.status))
    .slice(0, 5)
    .map((item) => compactItem(item.title, `${item.module || "未归类"} · ${item.status} · ${item.assignee || "未分配"}`))
    .join("") || emptyState("暂无待执行用例");

  document.getElementById("recent-users").innerHTML = state.users
    .filter((item) => item.status === "启用")
    .slice(0, 5)
    .map((item) => compactItem(item.name, `${item.role || "未设置角色"} · ${item.department || "未设置部门"}`))
    .join("") || emptyState("暂无启用用户");

  document.getElementById("recent-roles").innerHTML = state.roles
    .filter((item) => item.status === "启用")
    .slice(0, 7)
    .map((item) => compactItem(item.name, `${item.user_count || 0} 个用户 · ${item.description || "未填写职责"}`))
    .join("") || emptyState("暂无启用角色");
}

function renderRequirements() {
  const rows = filterRows(state.requirements, ["title", "owner", "status", "priority"]);
  document.getElementById("requirements-table").innerHTML = rows.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td class="title-cell">${escapeHtml(item.title)}<span class="description">${escapeHtml(item.description)}</span></td>
      <td>${escapeHtml(item.owner || "-")}</td>
      <td>${badge(item.priority)}</td>
      <td>${badge(item.status)}</td>
      <td>${escapeHtml(item.due_date || "-")}</td>
      <td>${actions("requirement", item.id)}</td>
    </tr>
  `).join("") || tableEmpty(7);
}

function renderPlans() {
  const rows = filterRows(state.plans, ["name", "owner", "status", "environment", "requirement_title"]);
  document.getElementById("plans-table").innerHTML = rows.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td class="title-cell">${escapeHtml(item.name)}<span class="description">${escapeHtml(item.goal)}</span></td>
      <td>${escapeHtml(item.requirement_title || "-")}</td>
      <td>${escapeHtml(item.owner || "-")}</td>
      <td>${escapeHtml(item.environment || "-")}</td>
      <td>${escapeHtml(item.start_date || "-")} 至 ${escapeHtml(item.end_date || "-")}</td>
      <td>${badge(item.status)}</td>
      <td>${actions("plan", item.id)}</td>
    </tr>
  `).join("") || tableEmpty(8);
}

function renderCases() {
  const rows = filterRows(state.cases, ["title", "module", "status", "assignee", "requirement_title", "plan_name"]);
  document.getElementById("cases-table").innerHTML = rows.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td class="title-cell">${escapeHtml(item.title)}<span class="description">${escapeHtml(item.steps)}</span></td>
      <td>${escapeHtml(item.module || "-")}</td>
      <td>${escapeHtml(item.requirement_title || "-")}</td>
      <td>${escapeHtml(item.plan_name || "-")}</td>
      <td>${badge(item.priority)}</td>
      <td>${badge(item.status)}</td>
      <td>${escapeHtml(item.assignee || "-")}</td>
      <td>${actions("case", item.id)}</td>
    </tr>
  `).join("") || tableEmpty(9);
}

function renderUsers() {
  const rows = filterRows(state.users, ["name", "email", "role", "department", "phone", "status"]);
  document.getElementById("users-table").innerHTML = rows.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td class="title-cell">${escapeHtml(item.name)}</td>
      <td>${escapeHtml(item.email || "-")}</td>
      <td>${escapeHtml(item.role || "-")}</td>
      <td>${escapeHtml(item.department || "-")}</td>
      <td>${escapeHtml(item.phone || "-")}</td>
      <td>${badge(item.status)}</td>
      <td>${escapeHtml(item.last_login || "-")}</td>
      <td>${actions("user", item.id)}</td>
    </tr>
  `).join("") || tableEmpty(9);
}

function renderRoles() {
  const rows = filterRows(state.roles, ["name", "description", "status"]);
  document.getElementById("roles-table").innerHTML = rows.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td class="title-cell">${escapeHtml(item.name)}</td>
      <td>${escapeHtml(item.description || "-")}</td>
      <td>${badge(item.status)}</td>
      <td>${escapeHtml(item.user_count ?? 0)}</td>
      <td>${actions("role", item.id)}</td>
    </tr>
  `).join("") || tableEmpty(6);
}

function openEditor(type, item = null) {
  const dialog = document.getElementById("editor-dialog");
  const form = document.getElementById("editor-form");
  form.dataset.type = type;
  form.dataset.id = item?.id || "";
  document.getElementById("dialog-title").textContent = `${item ? "编辑" : "新建"}${typeLabel(type)}`;
  document.getElementById("form-fields").innerHTML = schemas[type].map((field) => fieldHtml(field, item || {})).join("");
  dialog.showModal();
}

function fieldHtml(field, item) {
  const value = item[field.name] || "";
  const required = field.required ? "required" : "";
  const full = field.full ? " full" : "";
  let control = "";

  if (field.type === "textarea") {
    control = `<textarea name="${field.name}" ${required}>${escapeHtml(value)}</textarea>`;
  } else if (field.type === "select") {
    control = `<select name="${field.name}" ${required}>${field.options.map((option) => (
      `<option value="${escapeHtml(option)}" ${value === option ? "selected" : ""}>${escapeHtml(option)}</option>`
    )).join("")}</select>`;
  } else if (field.type === "requirement") {
    control = relationSelect(field.name, value, state.requirements, "title", "不关联需求");
  } else if (field.type === "plan") {
    control = relationSelect(field.name, value, state.plans, "name", "不关联计划");
  } else if (field.type === "role") {
    control = roleSelect(field.name, value);
  } else {
    control = `<input name="${field.name}" type="${field.type}" value="${escapeHtml(value)}" ${required} />`;
  }

  return `<div class="form-field${full}"><label>${escapeHtml(field.label)}</label>${control}</div>`;
}

function relationSelect(name, value, options, labelKey, emptyText) {
  return `<select name="${name}">
    <option value="">${emptyText}</option>
    ${options.map((item) => `<option value="${escapeHtml(item.id)}" ${value === item.id ? "selected" : ""}>${escapeHtml(item[labelKey])}</option>`).join("")}
  </select>`;
}

function roleSelect(name, value) {
  const activeRoles = state.roles.filter((item) => item.status === "启用");
  const options = activeRoles.some((item) => item.name === value)
    ? activeRoles
    : [{ name: value || "", status: "启用" }, ...activeRoles].filter((item) => item.name);
  return `<select name="${name}">
    <option value="">不设置角色</option>
    ${options.map((item) => `<option value="${escapeHtml(item.name)}" ${value === item.name ? "selected" : ""}>${escapeHtml(item.name)}</option>`).join("")}
  </select>`;
}

function actions(type, id) {
  return `<div class="actions">
    <button class="link-button" onclick="editById('${type}', '${id}')">编辑</button>
    <button class="link-button danger-button" onclick="deleteRecord('${type}', '${id}')">删除</button>
  </div>`;
}

function editById(type, id) {
  const source = { requirement: state.requirements, plan: state.plans, case: state.cases, user: state.users, role: state.roles }[type];
  openEditor(type, source.find((item) => item.id === id));
}

function closeDialog() {
  document.getElementById("editor-dialog").close();
}

function filterRows(rows, fields) {
  if (!state.search) return rows;
  const keyword = state.search.toLowerCase();
  return rows.filter((row) => fields.some((field) => String(row[field] || "").toLowerCase().includes(keyword)));
}

function badge(value) {
  const text = escapeHtml(value || "-");
  let cls = "badge";
  if (["已完成", "已关闭", "通过", "启用"].includes(value)) cls += " done";
  if (["待评审", "待验收", "待执行", "未开始", "草稿"].includes(value)) cls += " warn";
  if (["阻塞", "失败", "P0", "停用"].includes(value)) cls += " danger";
  return `<span class="${cls}">${text}</span>`;
}

function compactItem(title, meta) {
  return `<div class="compact-item"><strong>${escapeHtml(title)}</strong><small>${escapeHtml(meta)}</small></div>`;
}

function emptyState(text) {
  return `<div class="empty-state">${escapeHtml(text)}</div>`;
}

function tableEmpty(columns) {
  return `<tr><td colspan="${columns}" class="empty-state">暂无数据</td></tr>`;
}

function typeLabel(type) {
  return { requirement: "需求", plan: "测试计划", case: "测试用例", user: "用户", role: "角色" }[type];
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
