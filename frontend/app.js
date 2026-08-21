const state = {
  view: "dashboard",
  token: localStorage.getItem("auth_token") || "",
  currentUser: null,
  requirements: [],
  plans: [],
  cases: [],
  defects: [],
  users: [],
  roles: [],
  search: "",
  selectedRequirementId: "",
  requirementDetailTab: "basic",
};

const permissionOptions = [
  { value: "requirements", label: "需求管理" },
  { value: "plans", label: "测试计划" },
  { value: "cases", label: "测试用例" },
  { value: "defects", label: "缺陷管理" },
  { value: "users", label: "用户管理" },
  { value: "roles", label: "角色管理" },
];

const processTypeOptions = ["标准产品流程", "紧急需求流程", "技术改造流程", "运营配置流程"];
const businessLineOptions = ["系统平台需求", "API接口", "支付风控需求", "新手引导"];
const countryOptions = ["中国", "坦桑尼亚", "肯尼亚", "尼日利亚", "菲律宾", "印尼", "越南"];
const participantRoleOptions = ["产品经理", "业务方", "开发（web端）", "开发（移动端）", "开发（后端）", "测试"];
const requirementFlowSteps = ["需求提出", "需求确认", "需求评审", "后端开发", "冒烟测试", "测试", "测试环境验收", "待发布", "上线", "产品验收"];
const requirementStatusStepMap = {
  待评审: "需求评审",
  进行中: "后端开发",
  待验收: "测试环境验收",
  已完成: "产品验收",
  已关闭: "产品验收",
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
  defects: {
    title: "缺陷管理",
    subtitle: "记录缺陷、绑定需求并跟踪处理状态。",
    action: "新建缺陷",
    search: "搜索缺陷标题、状态、严重程度、处理人",
  },
  users: {
    title: "用户管理",
    subtitle: "维护团队成员、绑定角色和账号状态。",
    action: "新建用户",
    search: "搜索姓名、邮箱、角色、电话",
  },
  roles: {
    title: "角色管理",
    subtitle: "维护系统角色、权限范围和启停状态。",
    action: "新建角色",
    search: "搜索角色名称、描述、状态",
  },
  requirementDetail: {
    title: "需求流程",
    subtitle: "查看需求节点、关联测试和缺陷信息。",
    action: "编辑需求",
  },
};

const schemas = {
  requirement: [
    { label: "需求信息", type: "section" },
    { name: "title", label: "需求名称", type: "text", required: true, full: true },
    { name: "process_type", label: "流程类型", type: "select", options: processTypeOptions, required: true },
    { name: "description", label: "需求描述", type: "textarea", full: true },
    { name: "business_line", label: "业务线", type: "select", options: businessLineOptions, required: true, placeholder: "待填" },
    { name: "priority", label: "优先级", type: "select", options: ["P0", "P1", "P2", "P3"], required: true },
    { name: "requirement_doc", label: "需求文档", type: "text", full: true },
    { name: "need_tech_review", label: "是否需要技术评审", type: "radio", options: ["是", "否"], required: true, full: true },
    { name: "participants", label: "角色与人员", type: "participants", full: true },
    { name: "launch_country", label: "上线国家", type: "select", options: countryOptions, required: true, full: true },
    { label: "相关人员", type: "section" },
    { name: "followers", label: "关注人", type: "user", full: true, emptyText: "不设置关注人" },
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
  defect: [
    { name: "title", label: "缺陷标题", type: "text", required: true, full: true },
    { name: "requirement_id", label: "关联需求", type: "requirement" },
    { name: "severity", label: "严重程度", type: "select", options: ["S1", "S2", "S3", "S4"] },
    { name: "priority", label: "优先级", type: "select", options: ["P0", "P1", "P2", "P3"] },
    { name: "status", label: "状态", type: "select", options: ["新建", "处理中", "已修复", "已验证", "已拒绝", "已关闭", "重新打开"] },
    { name: "reporter", label: "报告人", type: "reporter" },
    { name: "assignee", label: "处理人", type: "user" },
    { name: "environment", label: "发现环境", type: "text" },
    { name: "steps", label: "复现步骤", type: "textarea", full: true },
    { name: "actual_result", label: "实际结果", type: "textarea", full: true },
    { name: "expected_result", label: "期望结果", type: "textarea", full: true },
  ],
  user: [
    { name: "name", label: "姓名", type: "text", required: true },
    { name: "email", label: "邮箱", type: "email" },
    { name: "role", label: "角色", type: "role" },
    { name: "phone", label: "电话", type: "tel" },
    { name: "status", label: "状态", type: "select", options: ["启用", "停用"] },
    { name: "last_login", label: "最近登录", type: "date" },
  ],
  role: [
    { name: "name", label: "角色名称", type: "text", required: true },
    { name: "status", label: "状态", type: "select", options: ["启用", "停用"] },
    { name: "permissions", label: "权限", type: "permissions", full: true },
    { name: "description", label: "职责描述", type: "textarea", full: true },
  ],
};

const endpoints = {
  requirement: "/api/requirements",
  plan: "/api/test-plans",
  case: "/api/test-cases",
  defect: "/api/defects",
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
    else if (state.view === "defects") openEditor("defect");
    else if (state.view === "requirementDetail") editSelectedRequirement();
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
    if (type === "requirement") {
      const formData = new FormData(form);
      const roles = formData.getAll("participant_role");
      const users = formData.getAll("participant_user");
      payload.participants = roles.map((role, index) => ({ role, user: users[index] || "" }))
        .filter((item) => item.role || item.user);
      delete payload.participant_role;
      delete payload.participant_user;
    }
    if (type === "role") {
      payload.permissions = new FormData(form).getAll("permissions");
    }
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
  const [summary, requirements, plans, cases, defects, users, roles] = await Promise.all([
    apiGet("/api/summary"),
    apiGet("/api/requirements"),
    apiGet("/api/test-plans"),
    apiGet("/api/test-cases"),
    apiGet("/api/defects"),
    apiGet("/api/users"),
    apiGet("/api/roles"),
  ]);
  state.summary = summary;
  state.requirements = requirements;
  state.plans = plans;
  state.cases = cases;
  state.defects = defects;
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
  document.getElementById("search-input").style.display = ["dashboard", "requirementDetail"].includes(view) ? "none" : "block";
  render();
}

function openRequirementDetail(id) {
  state.selectedRequirementId = id;
  state.requirementDetailTab = "basic";
  switchView("requirementDetail");
}

function backToRequirements() {
  state.selectedRequirementId = "";
  switchView("requirements");
}

function switchRequirementDetailTab(tab) {
  state.requirementDetailTab = tab;
  renderRequirementDetail();
}

function editSelectedRequirement() {
  const item = state.requirements.find((row) => row.id === state.selectedRequirementId);
  if (item) openEditor("requirement", item);
}

function openDefectForRequirement(requirementId) {
  openEditor("defect", { requirement_id: requirementId, status: "新建", priority: "P2", severity: "S2" });
}

function render() {
  renderDashboard();
  renderRequirements();
  renderPlans();
  renderCases();
  renderDefects();
  renderUsers();
  renderRoles();
  renderRequirementDetail();
}

function renderDashboard() {
  const summary = state.summary || {};
  document.getElementById("metric-requirements").textContent = summary.requirements || 0;
  document.getElementById("metric-plans").textContent = summary.test_plans || 0;
  document.getElementById("metric-cases").textContent = summary.test_cases || 0;
  document.getElementById("metric-defects").textContent = `${summary.open_defects || 0}/${summary.defects || 0}`;
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

  document.getElementById("recent-defects").innerHTML = state.defects
    .filter((item) => !["已验证", "已关闭", "已拒绝"].includes(item.status))
    .slice(0, 5)
    .map((item) => compactItem(item.title, `${item.status} · ${item.severity} · ${item.assignee || "未分配"}`))
    .join("") || emptyState("暂无开放缺陷");

  document.getElementById("recent-users").innerHTML = state.users
    .filter((item) => item.status === "启用")
    .slice(0, 5)
    .map((item) => compactItem(item.name, `${item.role || "未设置角色"} · ${permissionSummary(item.role_permissions)}`))
    .join("") || emptyState("暂无启用用户");

  document.getElementById("recent-roles").innerHTML = state.roles
    .filter((item) => item.status === "启用")
    .slice(0, 7)
    .map((item) => compactItem(item.name, `${item.user_count || 0} 个用户 · ${permissionSummary(item.permissions)}`))
    .join("") || emptyState("暂无启用角色");
}

function renderRequirements() {
  const rows = filterRows(state.requirements, ["title", "owner", "status", "priority", "business_line", "process_type", "launch_country"]);
  document.getElementById("requirements-table").innerHTML = rows.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td class="title-cell">
        <button class="title-link" onclick="openRequirementDetail('${item.id}')">${escapeHtml(item.title)}</button>
        <span class="description">${escapeHtml(item.description)}</span>
      </td>
      <td>${escapeHtml(item.business_line || "-")}</td>
      <td>${escapeHtml(item.process_type || "-")}</td>
      <td>${badge(item.priority)}</td>
      <td>${badge(item.status)}</td>
      <td>${escapeHtml(item.launch_country || "-")}</td>
      <td>${actions("requirement", item.id)}</td>
    </tr>
  `).join("") || tableEmpty(7);
}

function renderRequirementDetail() {
  const container = document.getElementById("requirement-detail");
  if (!container) return;
  const item = state.requirements.find((row) => row.id === state.selectedRequirementId);
  if (!item) {
    container.innerHTML = emptyState("请选择一个需求");
    return;
  }

  const currentStep = item.current_step || requirementStatusStepMap[item.status] || "需求提出";
  const currentIndex = requirementFlowSteps.indexOf(currentStep);
  const relatedPlans = state.plans.filter((plan) => plan.requirement_id === item.id);
  const relatedCases = state.cases.filter((testCase) => testCase.requirement_id === item.id);
  const relatedDefects = state.defects.filter((defect) => defect.requirement_id === item.id);
  const participants = parseParticipants(item.participants);

  container.innerHTML = `
    <div class="detail-shell">
      <header class="detail-header">
        <div class="detail-title-row">
          <button class="icon-button" onclick="backToRequirements()" aria-label="返回">‹</button>
          <h2>${escapeHtml(item.title)}</h2>
          ${badge(item.priority)}
          ${badge(item.status)}
          <span class="muted-text">${escapeHtml(item.launch_country || "未设置上线国家")}</span>
        </div>
        <div class="detail-actions">
          <button onclick="openEditor('requirement', state.requirements.find((row) => row.id === '${item.id}'))">编辑需求</button>
        </div>
      </header>

      <div class="flow-strip">
        ${requirementFlowSteps.map((step, index) => {
          const stateClass = index < currentIndex ? "done" : index === currentIndex ? "active" : "";
          return `<button class="flow-step ${stateClass}" onclick='updateRequirementNode("${item.id}", ${JSON.stringify(step)})'><span></span>${escapeHtml(step)}</button>`;
        }).join("")}
      </div>

      <section class="node-panel">
        <div class="node-panel-title">
          <strong>${escapeHtml(currentStep)}</strong>
          ${badge(item.status)}
        </div>
        <form class="node-edit-grid" onsubmit="saveRequirementNode(event, '${item.id}')">
          <label>
            <span>负责人</span>
            ${userSelect("node_owner", item.node_owner || item.owner || "", "选择负责人")}
          </label>
          <label>
            <span>总估分</span>
            <input name="node_score" type="text" value="${escapeHtml(item.node_score || "")}" placeholder="必填" />
          </label>
          <label>
            <span>总排期</span>
            <input name="node_schedule" type="text" value="${escapeHtml(item.node_schedule || "")}" placeholder="必填" />
          </label>
          <label>
            <span>是否技术评审</span>
            <input type="text" value="${escapeHtml(item.need_tech_review || "否")}" readonly />
          </label>
          <button class="primary" type="submit">保存节点信息</button>
        </form>
        <div class="node-subsection">
          <span>全部任务 (${relatedCases.length}/${relatedCases.length})</span>
          <button class="small-button" onclick="openEditor('case')">新增任务</button>
        </div>
      </section>

      <nav class="detail-tabs">
        ${detailTabButton("basic", "基本信息")}
        ${detailTabButton("plans", `测试计划关联 (${relatedPlans.length})`)}
        ${detailTabButton("cases", `测试用例 (${relatedCases.length})`)}
        ${detailTabButton("defects", `缺陷管理 (${relatedDefects.length})`)}
        ${detailTabButton("participants", "相关人员")}
        ${detailTabButton("activity", "操作记录")}
      </nav>

      <div class="detail-tab-actions">
        ${state.requirementDetailTab === "defects" ? `<button class="primary" onclick="openDefectForRequirement('${item.id}')">提缺陷</button>` : ""}
      </div>

      <section class="detail-content">
        ${requirementDetailTabContent(item, relatedPlans, relatedCases, relatedDefects, participants)}
      </section>
    </div>
  `;
}

async function updateRequirementNode(id, step) {
  const item = state.requirements.find((row) => row.id === id);
  if (!item) return;
  const payload = { ...item, current_step: step };
  const saved = await saveRecord("requirement", id, payload);
  if (saved) {
    await loadAll();
  }
}

async function saveRequirementNode(event, id) {
  event.preventDefault();
  const item = state.requirements.find((row) => row.id === id);
  if (!item) return;
  const payload = {
    ...item,
    ...Object.fromEntries(new FormData(event.currentTarget).entries()),
  };
  const saved = await saveRecord("requirement", id, payload);
  if (saved) {
    await loadAll();
  }
}

function detailTabButton(tab, label) {
  return `<button class="${state.requirementDetailTab === tab ? "active" : ""}" onclick="switchRequirementDetailTab('${tab}')">${escapeHtml(label)}</button>`;
}

function requirementDetailTabContent(item, plans, cases, defects, participants) {
  if (state.requirementDetailTab === "plans") {
    return relatedList(plans, (plan) => `${plan.name} · ${plan.status} · ${plan.owner || "未分配"}`, "暂无关联测试计划");
  }
  if (state.requirementDetailTab === "cases") {
    return relatedList(cases, (testCase) => `${testCase.title} · ${testCase.status} · ${testCase.assignee || "未分配"}`, "暂无关联测试用例");
  }
  if (state.requirementDetailTab === "defects") {
    return relatedList(defects, (defect) => `${defect.title} · ${defect.status} · ${defect.assignee || "未分配"}`, "暂无关联缺陷");
  }
  if (state.requirementDetailTab === "participants") {
    return participants.length
      ? `<div class="detail-info-grid">${participants.map((person) => detailInfo(person.role || "未设置角色", person.user || "待填")).join("")}</div>`
      : emptyState("暂无相关人员");
  }
  if (state.requirementDetailTab === "activity") {
    return `<div class="compact-list">${compactItem("需求创建/更新", `${item.updated_at || item.created_at || "-"}`)}</div>`;
  }
  return `<div class="detail-info-grid">
    ${detailInfo("需求名称", item.title)}
    ${detailInfo("流程类型", item.process_type)}
    ${detailInfo("需求描述", item.description || "-")}
    ${detailInfo("业务线", item.business_line)}
    ${detailInfo("优先级", item.priority)}
    ${detailInfo("需求文档", item.requirement_doc || "-")}
    ${detailInfo("是否需要技术评审", item.need_tech_review || "否")}
    ${detailInfo("上线国家", item.launch_country || "-")}
    ${detailInfo("关注人", item.followers || "-")}
  </div>`;
}

function detailInfo(label, value) {
  return `<div class="detail-info-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value || "-")}</strong></div>`;
}

function relatedList(rows, formatter, emptyText) {
  if (!rows.length) return emptyState(emptyText);
  return `<div class="compact-list">${rows.map((row) => compactItem(formatter(row), row.id)).join("")}</div>`;
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

function renderDefects() {
  const rows = filterRows(state.defects, ["title", "status", "severity", "priority", "reporter", "assignee", "requirement_title"]);
  document.getElementById("defects-table").innerHTML = rows.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td class="title-cell">${escapeHtml(item.title)}<span class="description">${escapeHtml(item.actual_result || item.steps || "")}</span></td>
      <td>${escapeHtml(item.requirement_title || "-")}</td>
      <td>${badge(item.severity)}</td>
      <td>${badge(item.priority)}</td>
      <td>${badge(item.status)}</td>
      <td>${escapeHtml(item.reporter || "-")}</td>
      <td>${escapeHtml(item.assignee || "-")}</td>
      <td>${actions("defect", item.id)}</td>
    </tr>
  `).join("") || tableEmpty(9);
}

function renderUsers() {
  const rows = filterRows(state.users, ["name", "email", "role", "phone", "status"]);
  document.getElementById("users-table").innerHTML = rows.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td class="title-cell">${escapeHtml(item.name)}</td>
      <td>${escapeHtml(item.email || "-")}</td>
      <td>${escapeHtml(item.role || "-")}</td>
      <td>${permissionBadges(item.role_permissions)}</td>
      <td>${escapeHtml(item.phone || "-")}</td>
      <td>${badge(item.status)}</td>
      <td>${escapeHtml(item.last_login || "-")}</td>
      <td>${actions("user", item.id)}</td>
    </tr>
  `).join("") || tableEmpty(9);
}

function renderRoles() {
  const rows = filterRows(state.roles, ["name", "description", "status", "permissions"]);
  document.getElementById("roles-table").innerHTML = rows.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td class="title-cell">${escapeHtml(item.name)}</td>
      <td>${escapeHtml(item.description || "-")}</td>
      <td>${permissionBadges(item.permissions)}</td>
      <td>${badge(item.status)}</td>
      <td>${escapeHtml(item.user_count ?? 0)}</td>
      <td>${actions("role", item.id)}</td>
    </tr>
  `).join("") || tableEmpty(7);
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
  if (field.type === "section") {
    return `<div class="form-section">${escapeHtml(field.label)}</div>`;
  }

  const value = item[field.name] || "";
  const required = field.required ? "required" : "";
  const full = field.full ? " full" : "";
  let control = "";

  if (field.type === "textarea") {
    control = `<textarea name="${field.name}" ${required}>${escapeHtml(value)}</textarea>`;
  } else if (field.type === "select") {
    const placeholder = field.placeholder
      ? `<option value="" ${value ? "" : "selected"} disabled>${escapeHtml(field.placeholder)}</option>`
      : "";
    control = `<select name="${field.name}" ${required}>${placeholder}${field.options.map((option) => (
      `<option value="${escapeHtml(option)}" ${value === option ? "selected" : ""}>${escapeHtml(option)}</option>`
    )).join("")}</select>`;
  } else if (field.type === "radio") {
    control = radioGroup(field.name, value || field.options[0], field.options);
  } else if (field.type === "requirement") {
    control = relationSelect(field.name, value, state.requirements, "title", "不关联需求");
  } else if (field.type === "plan") {
    control = relationSelect(field.name, value, state.plans, "name", "不关联计划");
  } else if (field.type === "role") {
    control = roleSelect(field.name, value);
  } else if (field.type === "user") {
    control = userSelect(field.name, value, field.emptyText);
  } else if (field.type === "reporter") {
    control = reporterField(value);
  } else if (field.type === "participants") {
    control = participantsEditor(value);
  } else if (field.type === "permissions") {
    control = permissionCheckboxes(value);
  } else {
    control = `<input name="${field.name}" type="${field.type}" value="${escapeHtml(value)}" ${required} />`;
  }

  return `<div class="form-field${full}"><label>${escapeHtml(field.label)}</label>${control}</div>`;
}

function radioGroup(name, value, options) {
  return `<div class="radio-group">
    ${options.map((option) => `
      <label class="radio-field">
        <input type="radio" name="${escapeHtml(name)}" value="${escapeHtml(option)}" ${value === option ? "checked" : ""} />
        <span>${escapeHtml(option)}</span>
      </label>
    `).join("")}
  </div>`;
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

function userSelect(name, value, emptyText = "不指定处理人") {
  const activeUsers = state.users.filter((item) => item.status === "启用");
  const options = activeUsers.some((item) => item.name === value)
    ? activeUsers
    : [{ name: value || "", status: "启用", email: "" }, ...activeUsers].filter((item) => item.name);
  return `<select name="${name}">
    <option value="">${escapeHtml(emptyText)}</option>
    ${options.map((item) => `
      <option value="${escapeHtml(item.name)}" ${value === item.name ? "selected" : ""}>
        ${escapeHtml(item.name)}${item.role ? ` · ${escapeHtml(item.role)}` : ""}
      </option>
    `).join("")}
  </select>`;
}

function reporterField(value) {
  const reporter = value || state.currentUser?.name || "";
  return `<input name="reporter_display" type="text" value="${escapeHtml(reporter)}" readonly />`;
}

function participantsEditor(value) {
  const participants = parseParticipants(value);
  const rows = participants.length
    ? participants
    : [{ role: "产品经理", user: state.currentUser?.name || "" }, { role: "业务方", user: "" }];
  return `<div class="participants-editor" id="participants-editor">
    ${rows.map((item) => participantRow(item)).join("")}
    <button type="button" class="small-button" onclick="addParticipantRow()">添加角色</button>
  </div>`;
}

function participantRow(item = {}) {
  return `<div class="participant-row">
    <select name="participant_role">
      <option value="">选择角色</option>
      ${participantRoleOptions.map((role) => `
        <option value="${escapeHtml(role)}" ${item.role === role ? "selected" : ""}>${escapeHtml(role)}</option>
      `).join("")}
    </select>
    ${userSelect("participant_user", item.user || "", "待填")}
    <button type="button" class="icon-button" onclick="removeParticipantRow(this)" aria-label="删除角色">×</button>
  </div>`;
}

function addParticipantRow() {
  const editor = document.getElementById("participants-editor");
  const button = editor.querySelector(".small-button");
  button.insertAdjacentHTML("beforebegin", participantRow());
}

function removeParticipantRow(button) {
  const row = button.closest(".participant-row");
  const editor = document.getElementById("participants-editor");
  if (editor.querySelectorAll(".participant-row").length > 1) {
    row.remove();
  }
}

function permissionCheckboxes(value) {
  const selected = new Set(parsePermissions(value));
  return `<div class="permission-grid">
    ${permissionOptions.map((item) => `
      <label class="checkbox-field">
        <input type="checkbox" name="permissions" value="${escapeHtml(item.value)}" ${selected.has(item.value) ? "checked" : ""} />
        <span>${escapeHtml(item.label)}</span>
      </label>
    `).join("")}
  </div>`;
}

function actions(type, id) {
  return `<div class="actions">
    <button class="link-button" onclick="editById('${type}', '${id}')">编辑</button>
    <button class="link-button danger-button" onclick="deleteRecord('${type}', '${id}')">删除</button>
  </div>`;
}

function editById(type, id) {
  const source = { requirement: state.requirements, plan: state.plans, case: state.cases, defect: state.defects, user: state.users, role: state.roles }[type];
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
  if (["待评审", "待验收", "待执行", "未开始", "草稿", "新建", "处理中", "已修复", "重新打开"].includes(value)) cls += " warn";
  if (["阻塞", "失败", "P0", "S1", "停用"].includes(value)) cls += " danger";
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

function parsePermissions(value) {
  if (Array.isArray(value)) return value;
  try {
    const parsed = JSON.parse(value || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function parseParticipants(value) {
  if (Array.isArray(value)) return value;
  try {
    const parsed = JSON.parse(value || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function permissionLabel(value) {
  return permissionOptions.find((item) => item.value === value)?.label || value;
}

function permissionSummary(value) {
  const permissions = parsePermissions(value);
  if (!permissions.length) return "暂无权限";
  return permissions.map(permissionLabel).join("、");
}

function permissionBadges(value) {
  const permissions = parsePermissions(value);
  if (!permissions.length) return `<span class="muted-text">暂无权限</span>`;
  return `<div class="permission-list">${permissions.map((item) => (
    `<span class="badge">${escapeHtml(permissionLabel(item))}</span>`
  )).join("")}</div>`;
}

function typeLabel(type) {
  return { requirement: "需求", plan: "测试计划", case: "测试用例", defect: "缺陷", user: "用户", role: "角色" }[type];
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
