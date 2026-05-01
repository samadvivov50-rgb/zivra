const state = {
  snapshot: loadCachedSnapshot(),
  assistantReply: "",
  sessionId: getMobileSessionId(),
  sessionHistory: [],
  deferredInstallPrompt: null,
  refreshTimerId: null,
  refreshSeconds: 30,
  snapshotStatus: "Connecting to the local sync feed...",
  lastSupervisorCycle: null,
};

function buildMobileSessionId() {
  return `mobile-session-${Date.now()}`;
}

function getMobileSessionId() {
  const params = new URLSearchParams(window.location.search);
  const querySessionId = (params.get("session_id") || params.get("session") || "").trim();
  if (querySessionId) {
    window.localStorage.setItem("zivra_mobile_session_id", querySessionId);
    return querySessionId;
  }

  const existing = window.localStorage.getItem("zivra_mobile_session_id");
  if (existing) {
    return existing;
  }

  const created = buildMobileSessionId();
  window.localStorage.setItem("zivra_mobile_session_id", created);
  return created;
}

function persistMobileSessionId(sessionId) {
  const normalized = String(sessionId || "").trim() || buildMobileSessionId();
  state.sessionId = normalized;
  window.localStorage.setItem("zivra_mobile_session_id", normalized);
  const nextUrl = new URL(window.location.href);
  nextUrl.searchParams.set("session_id", normalized);
  window.history.replaceState({}, "", nextUrl.toString());
}

function buildCurrentSessionLinks() {
  const mobileUrl = new URL("/mobile", window.location.origin);
  mobileUrl.searchParams.set("session_id", state.sessionId);
  const controlRoomUrl = new URL("/ui/", window.location.origin);
  controlRoomUrl.searchParams.set("session_id", state.sessionId);
  return {
    mobileUrl: mobileUrl.toString(),
    controlRoomUrl: controlRoomUrl.toString(),
  };
}

function loadCachedSnapshot() {
  try {
    const raw = window.localStorage.getItem("zivra_mobile_companion_snapshot");
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function saveCachedSnapshot(snapshot) {
  window.localStorage.setItem("zivra_mobile_companion_snapshot", JSON.stringify(snapshot));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let payload = {};
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }

  if (!response.ok) {
    const detail = payload.detail || payload.message || `Request failed with ${response.status}`;
    throw new Error(detail);
  }
  return payload;
}

async function copyTextToClipboard(text) {
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
    await navigator.clipboard.writeText(text);
    return;
  }

  const input = document.createElement("textarea");
  input.value = text;
  input.setAttribute("readonly", "true");
  input.style.position = "absolute";
  input.style.left = "-9999px";
  document.body.appendChild(input);
  input.select();
  document.execCommand("copy");
  document.body.removeChild(input);
}

function renderList(targetId, markup) {
  document.getElementById(targetId).innerHTML = markup;
}

function formatTimestamp(value) {
  if (!value) {
    return "";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return String(value);
  }
  return parsed.toLocaleString();
}

function setConnectionStatus(text, mode) {
  const target = document.getElementById("connection-status");
  target.textContent = text;
  target.classList.remove("is-online", "is-offline");
  if (mode) {
    target.classList.add(mode);
  }
}

function renderMetrics(snapshot) {
  const reminderSummary = (snapshot.summary || {}).reminders || {};
  const workflowSummary = (snapshot.summary || {}).workflows || {};
  const cards = [
    ["Pending approvals", snapshot.summary?.pending_actions || 0],
    ["Due today", reminderSummary.due_today || 0],
    ["Overdue", reminderSummary.overdue || 0],
    ["Queued tasks", workflowSummary.queued_tasks || 0],
    ["Approval backlog", workflowSummary.approval_pending_tasks || 0],
    ["Active workflows", workflowSummary.active_workflows || 0],
  ];

  renderList(
    "metric-grid",
    cards
      .map(
        ([label, value]) => `
          <article class="metric-card">
            <strong>${escapeHtml(String(value))}</strong>
            <span>${escapeHtml(label)}</span>
          </article>
        `,
      )
      .join(""),
  );
}

function renderApprovals(snapshot) {
  const approvals = snapshot.approvals || [];
  if (!approvals.length) {
    renderList(
      "approvals-list",
      `
        <article class="empty-card">
          <strong>No pending approvals</strong>
          <span>Low-risk and sensitive actions waiting for review will appear here.</span>
        </article>
      `,
    );
    return;
  }

  const approvalGroups = groupPendingApprovals(approvals);
  renderList(
    "approvals-list",
    approvalGroups
      .map((group) => {
        if (!group.groupId) {
          return renderApprovalItem(group.actions[0] || {});
        }

        const readyActions = group.actions.filter((action) => action.status !== "queued");
        const branchSummary = renderApprovalBranchSummary(group.actions);
        return `
          <article class="stack-card">
            <strong>${escapeHtml(group.groupSummary || "Linked approval flow")}</strong>
            <div class="stack-meta">
              <span class="meta-chip">${escapeHtml(`${group.actions.length} step${group.actions.length === 1 ? "" : "s"}`)}</span>
              <span class="meta-chip">${escapeHtml(`${readyActions.length} ready`)}</span>
            </div>
            ${branchSummary ? `<p class="inline-note">${escapeHtml(branchSummary)}</p>` : ""}
            <div class="card-actions">
              <button class="primary-button" type="button" data-approval-group-action="confirm" data-group-id="${escapeHtml(group.groupId)}">Approve all</button>
              <button class="ghost-button" type="button" data-approval-group-action="reject" data-group-id="${escapeHtml(group.groupId)}">Reject all</button>
            </div>
            <div class="stack-list">
              ${group.actions.map((action) => renderApprovalItem(action, { compact: true, siblingActions: group.actions })).join("")}
            </div>
          </article>
        `;
      })
      .join(""),
  );
}

function groupPendingApprovals(actions) {
  const grouped = new Map();
  const groups = [];

  actions.forEach((action) => {
    const key = action.group_id || action.action_id;
    if (!grouped.has(key)) {
      const bucket = {
        key,
        groupId: action.group_id || "",
        groupSummary: action.group_summary || "",
        actions: [],
      };
      grouped.set(key, bucket);
      groups.push(bucket);
    }
    grouped.get(key).actions.push(action);
  });

  return groups;
}

function getApprovalStepNumber(action) {
  return Number(action.sequence_index || 0) + 1;
}

function getApprovalDependencyStepNumber(action, siblingActions = []) {
  if (!action.depends_on_action_id) {
    return 0;
  }

  const dependency = siblingActions.find((candidate) => candidate.action_id === action.depends_on_action_id);
  return dependency ? getApprovalStepNumber(dependency) : 0;
}

function renderApprovalBranchSummary(actions) {
  const dependencies = new Map();
  actions.forEach((action) => {
    if (!action.depends_on_action_id) {
      return;
    }
    const dependencyStep = getApprovalDependencyStepNumber(action, actions);
    if (!dependencyStep) {
      return;
    }
    if (!dependencies.has(dependencyStep)) {
      dependencies.set(dependencyStep, []);
    }
    dependencies.get(dependencyStep).push(getApprovalStepNumber(action));
  });

  if (!dependencies.size) {
    return "";
  }

  return Array.from(dependencies.entries())
    .map(([dependencyStep, dependentSteps]) => {
      if (dependentSteps.length === 1) {
        return `Step ${dependentSteps[0]} depends on step ${dependencyStep}.`;
      }
      const labels = dependentSteps.slice(0, -1).join(", ");
      const lastStep = dependentSteps[dependentSteps.length - 1];
      return `Steps ${labels}, and ${lastStep} depend on step ${dependencyStep}.`;
    })
    .join(" ");
}

function renderApprovalItem(action, options = {}) {
  const compact = options.compact === true;
  const siblingActions = options.siblingActions || [];
  const stepNumber = getApprovalStepNumber(action);
  const dependencyStep = getApprovalDependencyStepNumber(action, siblingActions);
  const dependencyCopy = action.status === "queued"
    ? `Waiting for step ${dependencyStep || "?"} to be approved first.`
    : dependencyStep
      ? `Depends on step ${dependencyStep}.`
      : "";
  const titleTag = compact ? "h3" : "strong";
  return `
    <article class="stack-card">
      <${titleTag}>${escapeHtml(action.summary || "Pending action")}</${titleTag}>
      <div class="stack-meta">
        <span class="meta-chip">${escapeHtml(`step ${stepNumber}`)}</span>
        <span class="meta-chip">${escapeHtml(action.permission_level || "approval")}</span>
        <span class="meta-chip">${escapeHtml(action.tool_name || "tool")}</span>
        <span class="${action.status === "queued" ? "meta-chip is-danger" : "meta-chip"}">${escapeHtml(action.status || "proposed")}</span>
      </div>
      ${dependencyCopy ? `<p class="inline-note">${escapeHtml(dependencyCopy)}</p>` : ""}
      <div class="card-actions">
        ${
          action.status === "queued"
            ? `<button class="ghost-button" type="button" data-approval-action="reject" data-action-id="${escapeHtml(action.action_id)}">Remove</button>`
            : `<button class="primary-button" type="button" data-approval-action="confirm" data-action-id="${escapeHtml(action.action_id)}">Approve</button>
               <button class="ghost-button" type="button" data-approval-action="reject" data-action-id="${escapeHtml(action.action_id)}">Reject</button>`
        }
      </div>
    </article>
  `;
}

function renderReminders(snapshot) {
  const reminders = snapshot.reminders || [];
  if (!reminders.length) {
    renderList(
      "reminders-list",
      `
        <article class="empty-card">
          <strong>No pending reminders</strong>
          <span>Due-soon reminders will sync here from the local control room.</span>
        </article>
      `,
    );
    return;
  }

  renderList(
    "reminders-list",
    reminders
      .map((reminder) => {
        const detailClass = reminder.status === "pending" && reminder.is_overdue ? "inline-note is-danger" : "inline-note";
        const dueLabel = reminder.due_display || reminder.schedule_hint || "Unscheduled";
        return `
          <article class="stack-card">
            <strong>${escapeHtml(reminder.title)}</strong>
            <div class="stack-meta">
              <span class="${reminder.is_overdue ? "meta-chip is-danger" : "meta-chip"}">${escapeHtml(reminder.status)}</span>
              <span class="meta-chip">${escapeHtml(dueLabel)}</span>
            </div>
            <p class="${detailClass}">${escapeHtml(reminder.details || reminder.schedule_hint || "No extra details.")}</p>
            <div class="card-actions">
              <button class="ghost-button" type="button" data-reminder-action="complete" data-reminder-id="${escapeHtml(String(reminder.id))}">Mark done</button>
            </div>
          </article>
        `;
      })
      .join(""),
  );
}

function renderWorkflows(snapshot) {
  const workflows = snapshot.workflows || [];
  const tasks = snapshot.workflow_tasks || [];
  const supervisor = snapshot.supervisor || {};
  const reason = formatSupervisorReason(state.lastSupervisorCycle);
  const summaryMarkup = `
    <article class="stack-card">
      <strong>Supervisor guardrails</strong>
      <div class="stack-meta">
        <span class="${supervisor.enabled ? "meta-chip" : "meta-chip is-danger"}">${supervisor.enabled ? "enabled" : "paused"}</span>
        <span class="meta-chip">${escapeHtml(`${supervisor.max_tasks_per_cycle || 1} task${supervisor.max_tasks_per_cycle === 1 ? "" : "s"} per cycle`)}</span>
        <span class="meta-chip">${escapeHtml(`approval cap ${supervisor.max_pending_approvals || 1}`)}</span>
      </div>
      ${reason ? `<p class="inline-note">${escapeHtml(reason)}</p>` : ""}
    </article>
  `;

  const workflowCards = workflows.length
    ? workflows
        .map(
          (workflow) => `
            <article class="stack-card">
              <strong>${escapeHtml(workflow.name)}</strong>
              <span>${escapeHtml(workflow.schedule_label || "Manual")}</span>
              <div class="stack-meta">
                <span class="${workflow.active ? "meta-chip" : "meta-chip is-danger"}">${workflow.active ? "active" : "paused"}</span>
                ${workflow.next_run_display ? `<span class="meta-chip">${escapeHtml(workflow.next_run_display)}</span>` : ""}
                ${workflow.last_task_status ? `<span class="${workflow.last_task_status === "failed" ? "meta-chip is-danger" : "meta-chip"}">${escapeHtml(workflow.last_task_status)}</span>` : ""}
              </div>
              <div class="card-actions">
                <button class="ghost-button" type="button" data-workflow-action="queue" data-workflow-id="${escapeHtml(String(workflow.id))}">Queue now</button>
                <button class="ghost-button" type="button" data-workflow-action="toggle" data-workflow-id="${escapeHtml(String(workflow.id))}" data-active="${workflow.active ? "true" : "false"}">
                  ${workflow.active ? "Pause" : "Resume"}
                </button>
              </div>
            </article>
          `,
        )
        .join("")
    : `
      <article class="empty-card">
        <strong>No workflows saved</strong>
        <span>Create workflows in the main control room and they will sync here.</span>
      </article>
    `;

  const taskCards = tasks.length
    ? tasks
        .map(
          (task) => `
            <article class="stack-card">
              <strong>${escapeHtml(task.workflow_name)}</strong>
              <span>${escapeHtml(task.prompt)}</span>
              <div class="stack-meta">
                <span class="${task.status === "failed" ? "meta-chip is-danger" : "meta-chip"}">${escapeHtml(task.status)}</span>
                <span class="meta-chip">${escapeHtml(task.source || "schedule")}</span>
                ${task.queued_for_display ? `<span class="meta-chip">${escapeHtml(task.queued_for_display)}</span>` : ""}
              </div>
              ${task.error ? `<p class="inline-note is-danger">${escapeHtml(task.error)}</p>` : ""}
              <div class="card-actions">
                ${task.status === "queued" ? `<button class="primary-button" type="button" data-task-action="run" data-task-id="${escapeHtml(String(task.id))}">Run</button>` : ""}
                ${task.status === "queued" ? `<button class="ghost-button" type="button" data-task-action="cancel" data-task-id="${escapeHtml(String(task.id))}">Cancel</button>` : ""}
                ${task.status === "failed" || task.status === "canceled" ? `<button class="ghost-button" type="button" data-task-action="retry" data-task-id="${escapeHtml(String(task.id))}">Retry</button>` : ""}
              </div>
            </article>
          `,
        )
        .join("")
    : `
      <article class="empty-card">
        <strong>No queued workflow tasks</strong>
        <span>Queued, failed, and recovery tasks will appear here.</span>
      </article>
    `;

  renderList("workflows-panel", `${summaryMarkup}${workflowCards}${taskCards}`);
}

function formatSupervisorReason(cycle) {
  if (!cycle || !cycle.stopped_reason) {
    return "";
  }
  if (cycle.stopped_reason === "manual_refresh") {
    return "The companion is showing the last known supervisor settings without triggering a new cycle.";
  }
  if (cycle.stopped_reason === "approval_limit_reached") {
    return "The supervisor stopped at the configured approval backlog limit.";
  }
  if (cycle.stopped_reason === "cycle_limit_reached") {
    return "The supervisor reached the max task count for one cycle.";
  }
  if (cycle.stopped_reason === "workflow_failed") {
    return "The supervisor stopped after a workflow failure.";
  }
  if (cycle.stopped_reason === "disabled") {
    return "The supervisor is paused.";
  }
  if (cycle.stopped_reason === "idle") {
    return "No queued workflow tasks were ready during the last cycle.";
  }
  return String(cycle.stopped_reason).replaceAll("_", " ");
}

function renderNotes(snapshot) {
  const notes = snapshot.notes || [];
  if (!notes.length) {
    renderList(
      "notes-list",
      `
        <article class="empty-card">
          <strong>No recent notes</strong>
          <span>Recent workspace notes will sync here for quick reading.</span>
        </article>
      `,
    );
    return;
  }

  renderList(
    "notes-list",
    notes
      .map(
        (note) => `
          <article class="stack-card">
            <strong>${escapeHtml(note.title)}</strong>
            <span>${escapeHtml(note.preview || "No preview available.")}</span>
            <div class="stack-meta">
              <span class="meta-chip">${escapeHtml(note.name)}</span>
              <span class="meta-chip">${escapeHtml(formatTimestamp(note.updated_at))}</span>
            </div>
          </article>
        `,
      )
      .join(""),
  );
}

function renderActivity(snapshot) {
  const flows = snapshot.recent_flows || [];
  if (!flows.length) {
    renderList(
      "activity-list",
      `
        <article class="empty-card">
          <strong>No recent flows</strong>
          <span>Recent request timelines will appear here after activity is logged.</span>
        </article>
      `,
    );
    return;
  }

  renderList(
    "activity-list",
    flows
      .map(
        (flow) => `
          <article class="stack-card">
            <strong>${escapeHtml(flow.title || "Recent flow")}</strong>
            <ul class="flow-list">
              <li>${escapeHtml(`${flow.event_count || 0} events • ${flow.step_count || 0} steps`)}</li>
              <li>${escapeHtml(formatTimestamp(flow.latest_timestamp))}</li>
            </ul>
          </article>
        `,
      )
      .join(""),
  );
}

function renderSessionHistory() {
  const history = state.sessionHistory || [];
  const recentSessions = Array.isArray(state.snapshot?.sessions) ? state.snapshot.sessions : [];
  const currentSessionLinks = buildCurrentSessionLinks();
  const controlRoomLink = document.getElementById("control-room-link");
  if (controlRoomLink) {
    controlRoomLink.href = currentSessionLinks.controlRoomUrl;
  }

  const sessionSwitcherMarkup = `
    <article class="stack-card">
      <strong>Shared session</strong>
      <p class="session-id">${escapeHtml(state.sessionId)}</p>
      <p class="inline-note">This companion can stay on the handed-off thread, copy the current session link, or jump to another recent saved session.</p>
      <div class="card-actions">
        <button class="ghost-button" type="button" data-session-action="fresh">Start fresh session</button>
        <button class="ghost-button" type="button" data-session-action="copy-mobile-link">Copy mobile link</button>
        <button class="ghost-button" type="button" data-session-action="copy-room-link">Copy room link</button>
        ${
          typeof navigator.share === "function"
            ? '<button class="ghost-button" type="button" data-session-action="share-link">Share link</button>'
            : ""
        }
      </div>
      <p class="session-id">${escapeHtml(currentSessionLinks.mobileUrl)}</p>
    </article>
    ${
      recentSessions.length
        ? `
          <article class="stack-card">
            <strong>Recent saved sessions</strong>
            <div class="stack-list">
              ${recentSessions
                .map((session) => {
                  const sessionId = String(session.session_id || "");
                  const active = sessionId === state.sessionId;
                  return `
                    <article class="stack-card session-switch-card">
                      <div class="stack-meta">
                        <span class="meta-chip">${escapeHtml(`${session.turn_count || 0} turn${session.turn_count === 1 ? "" : "s"}`)}</span>
                        ${
                          active
                            ? '<span class="meta-chip">active</span>'
                            : ""
                        }
                        ${
                          session.last_seen_at
                            ? `<span class="meta-chip">${escapeHtml(formatTimestamp(session.last_seen_at))}</span>`
                            : ""
                        }
                      </div>
                      <p class="session-id">${escapeHtml(sessionId)}</p>
                      <p>${escapeHtml(session.last_content_preview || "No preview available.")}</p>
                      <div class="card-actions">
                        ${
                          active
                            ? '<button class="ghost-button" type="button" disabled>Current session</button>'
                            : `<button class="primary-button" type="button" data-session-action="switch" data-session-id="${escapeHtml(sessionId)}">Use this session</button>`
                        }
                      </div>
                    </article>
                  `;
                })
                .join("")}
            </div>
          </article>
        `
        : `
          <article class="empty-card">
            <strong>No saved sessions yet</strong>
            <span>Once this companion or the desktop control room stores more conversations, they will appear here for quick switching.</span>
          </article>
        `
    }
  `;

  if (!history.length) {
    renderList(
      "session-history",
      `
        ${sessionSwitcherMarkup}
        <article class="empty-card">
          <strong>No recent turns yet</strong>
          <span>This session has not saved any conversation history yet, or memory is currently off.</span>
        </article>
      `,
    );
    return;
  }

  renderList(
    "session-history",
    [
      sessionSwitcherMarkup,
      ...history.map(
        (turn) => `
          <article class="stack-card">
            <div class="stack-meta">
              <span class="meta-chip">${escapeHtml(turn.role || "message")}</span>
              ${
                turn.sensitivity && turn.sensitivity !== "normal"
                  ? `<span class="meta-chip">${escapeHtml(turn.sensitivity)}</span>`
                  : ""
              }
              ${
                turn.created_at
                  ? `<span class="meta-chip">${escapeHtml(formatTimestamp(turn.created_at))}</span>`
                  : ""
              }
            </div>
            <p class="history-turn">${escapeHtml(turn.content || "")}</p>
          </article>
        `,
      ),
    ].join(""),
  );
}

function renderSnapshot(snapshot) {
  const assistant = snapshot.assistant || {};
  document.title = `${assistant.name || "Zivra"} Companion`;
  document.getElementById("assistant-name").textContent = assistant.name || "Zivra";
  document.getElementById("sync-status").textContent = state.snapshotStatus;
  document.getElementById("supervisor-status").textContent = (snapshot.supervisor || {}).enabled
    ? "Supervisor enabled"
    : "Supervisor paused";
  renderMetrics(snapshot);
  renderApprovals(snapshot);
  renderReminders(snapshot);
  renderWorkflows(snapshot);
  renderNotes(snapshot);
  renderActivity(snapshot);
  renderSessionHistory();

  const replyTarget = document.getElementById("assistant-reply");
  if (state.assistantReply) {
    replyTarget.innerHTML = `
      <strong>Latest reply</strong>
      <p>${escapeHtml(state.assistantReply)}</p>
    `;
  } else {
    replyTarget.innerHTML = "";
  }
}

async function switchMobileSession(sessionId) {
  persistMobileSessionId(sessionId);
  state.assistantReply = "";
  state.sessionHistory = [];
  renderSnapshot(state.snapshot || loadCachedSnapshot() || { assistant: { name: "Zivra" } });
  await refreshSessionHistory({ silent: true });
  renderSnapshot(state.snapshot || loadCachedSnapshot() || { assistant: { name: "Zivra" } });
}

async function shareCurrentSession(button) {
  const links = buildCurrentSessionLinks();
  if (typeof navigator.share !== "function") {
    throw new Error("This browser does not support native sharing.");
  }

  await navigator.share({
    title: "Zivra shared session",
    text: "Open the current Zivra companion session on this device.",
    url: links.mobileUrl,
  });
  flashButton(button, "Shared");
}

async function refreshSessionHistory(options = {}) {
  const silent = options.silent === true;
  try {
    const payload = await api(`/assistant/sessions/${encodeURIComponent(state.sessionId)}/history?limit=8`);
    state.sessionHistory = Array.isArray(payload.history) ? payload.history : [];
    renderSessionHistory();
  } catch (error) {
    if (!silent) {
      document.getElementById("assistant-reply").innerHTML = `
        <strong>Session sync notice</strong>
        <p>${escapeHtml(error instanceof Error ? error.message : "Session history refresh failed.")}</p>
      `;
    }
  }
}

async function refreshCompanionData(options = {}) {
  await refreshSnapshot(options);
  await refreshSessionHistory({ silent: options.silent === true });
}

async function refreshSnapshot(options = {}) {
  const silent = options.silent === true;
  try {
    const snapshot = await api("/sync/companion");
    state.snapshot = snapshot;
    state.snapshotStatus = `Synced ${formatTimestamp(snapshot.generated_at)} from the local control room.`;
    saveCachedSnapshot(snapshot);
    setConnectionStatus("Backend connected", "is-online");
    renderSnapshot(snapshot);
  } catch (error) {
    const fallback = loadCachedSnapshot();
    if (fallback) {
      state.snapshot = fallback;
      state.snapshotStatus = `Offline snapshot from ${formatTimestamp(fallback.generated_at)}.`;
      setConnectionStatus("Using cached snapshot", "is-offline");
      renderSnapshot(fallback);
      if (!silent) {
        document.getElementById("assistant-reply").innerHTML = `
          <strong>Offline notice</strong>
          <p>${escapeHtml(error instanceof Error ? error.message : "Refresh failed.")}</p>
        `;
      }
      return;
    }

    setConnectionStatus("Backend unavailable", "is-offline");
    if (!silent) {
      document.getElementById("assistant-reply").innerHTML = `
        <strong>Connection error</strong>
        <p>${escapeHtml(error instanceof Error ? error.message : "Refresh failed.")}</p>
      `;
    }
  }
}

async function sendMessage() {
  const textarea = document.getElementById("mobile-message");
  const message = textarea.value.trim();
  if (!message) {
    return;
  }

  const response = await api("/assistant/message", {
    method: "POST",
    body: JSON.stringify({
      message,
      session_id: state.sessionId,
    }),
  });
  state.assistantReply = response.assistant_text || "Message sent.";
  textarea.value = "";
  await refreshCompanionData({ silent: true });
  renderSnapshot(state.snapshot || loadCachedSnapshot() || { assistant: { name: "Zivra" } });
}

async function resolveApproval(actionId, action) {
  const path = action === "confirm" ? "confirm" : "reject";
  const payload = action === "confirm" ? {} : { reason: "Rejected from the mobile companion." };
  const response = await api(`/assistant/actions/${encodeURIComponent(actionId)}/${path}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.assistantReply = response.assistant_text || state.assistantReply;
  await refreshCompanionData({ silent: true });
  renderSnapshot(state.snapshot || {});
}

async function resolveApprovalGroup(groupId, action) {
  const path = action === "confirm" ? "confirm" : "reject";
  const payload = action === "confirm" ? {} : { reason: "Rejected from the mobile companion." };
  const response = await api(`/assistant/action-groups/${encodeURIComponent(groupId)}/${path}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.assistantReply = response.assistant_text || state.assistantReply;
  await refreshCompanionData({ silent: true });
  renderSnapshot(state.snapshot || {});
}

async function completeReminder(reminderId) {
  await api(`/reminders/${encodeURIComponent(String(reminderId))}/complete`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  await refreshCompanionData({ silent: true });
}

async function queueWorkflow(workflowId) {
  await api(`/workflows/${encodeURIComponent(String(workflowId))}/queue`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  await refreshCompanionData({ silent: true });
}

async function toggleWorkflow(workflowId, active) {
  await api(`/workflows/${encodeURIComponent(String(workflowId))}/toggle`, {
    method: "POST",
    body: JSON.stringify({ active }),
  });
  await refreshCompanionData({ silent: true });
}

async function runWorkflowTask(taskId) {
  const response = await api(`/workflows/tasks/${encodeURIComponent(String(taskId))}/run`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.assistantReply = response.message || state.assistantReply;
  await refreshCompanionData({ silent: true });
}

async function cancelWorkflowTask(taskId) {
  await api(`/workflows/tasks/${encodeURIComponent(String(taskId))}/cancel`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  await refreshCompanionData({ silent: true });
}

async function retryWorkflowTask(taskId) {
  await api(`/workflows/tasks/${encodeURIComponent(String(taskId))}/retry`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  await refreshCompanionData({ silent: true });
}

async function runSupervisor() {
  const response = await api("/workflows/supervisor/run", {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.assistantReply = response.message || state.assistantReply;
  state.lastSupervisorCycle = response.cycle || null;
  await refreshCompanionData({ silent: true });
}

async function downloadSnapshot(button) {
  const includeNoteContent = document.getElementById("include-note-content").checked;
  const payload = await api(`/sync/export?include_note_content=${includeNoteContent ? "1" : "0"}`);
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = includeNoteContent ? "zivra-sync-with-notes.json" : "zivra-sync-snapshot.json";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(href);
  const status = document.getElementById("snapshot-status");
  status.textContent = includeNoteContent
    ? "Downloaded a snapshot with note text."
    : "Downloaded a lightweight metadata snapshot.";
  flashButton(button, "Downloaded");
}

function flashButton(button, label) {
  const original = button.textContent;
  button.textContent = label;
  window.setTimeout(() => {
    button.textContent = original;
  }, 1200);
}

function scheduleRefresh() {
  if (state.refreshTimerId) {
    window.clearInterval(state.refreshTimerId);
  }
  state.refreshTimerId = window.setInterval(() => {
    refreshCompanionData({ silent: true });
  }, state.refreshSeconds * 1000);
}

function bindEvents() {
  document.getElementById("mobile-message-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.target.querySelector("button[type='submit']");
    button.disabled = true;
    try {
      await sendMessage();
    } catch (error) {
      document.getElementById("assistant-reply").innerHTML = `
        <strong>Message failed</strong>
        <p>${escapeHtml(error instanceof Error ? error.message : "Message failed.")}</p>
      `;
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("clear-mobile-message").addEventListener("click", () => {
    document.getElementById("mobile-message").value = "";
  });

  document.getElementById("session-history").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-session-action]");
    if (!button) {
      return;
    }

    button.disabled = true;
    try {
      if (button.dataset.sessionAction === "fresh") {
        await switchMobileSession(buildMobileSessionId());
        return;
      }

      if (button.dataset.sessionAction === "switch") {
        await switchMobileSession(button.dataset.sessionId || "");
        return;
      }

      if (button.dataset.sessionAction === "copy-mobile-link") {
        await copyTextToClipboard(buildCurrentSessionLinks().mobileUrl);
        flashButton(button, "Copied");
        return;
      }

      if (button.dataset.sessionAction === "copy-room-link") {
        await copyTextToClipboard(buildCurrentSessionLinks().controlRoomUrl);
        flashButton(button, "Copied");
        return;
      }

      if (button.dataset.sessionAction === "share-link") {
        await shareCurrentSession(button);
      }
    } catch (error) {
      document.getElementById("assistant-reply").innerHTML = `
        <strong>Session action failed</strong>
        <p>${escapeHtml(error instanceof Error ? error.message : "Session action failed.")}</p>
      `;
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("refresh-companion").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await refreshCompanionData();
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("run-supervisor").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await runSupervisor();
    } catch (error) {
      document.getElementById("assistant-reply").innerHTML = `
        <strong>Supervisor cycle failed</strong>
        <p>${escapeHtml(error instanceof Error ? error.message : "Supervisor cycle failed.")}</p>
      `;
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("download-snapshot").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await downloadSnapshot(button);
    } catch (error) {
      document.getElementById("snapshot-status").textContent =
        error instanceof Error ? error.message : "Snapshot export failed.";
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("approvals-list").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-approval-action], button[data-approval-group-action]");
    if (!button) {
      return;
    }

    button.disabled = true;
    try {
      if (button.dataset.approvalGroupAction) {
        await resolveApprovalGroup(button.dataset.groupId || "", button.dataset.approvalGroupAction || "reject");
        return;
      }

      await resolveApproval(button.dataset.actionId || "", button.dataset.approvalAction || "reject");
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("reminders-list").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-reminder-action='complete']");
    if (!button) {
      return;
    }

    button.disabled = true;
    try {
      await completeReminder(button.dataset.reminderId || "");
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("workflows-panel").addEventListener("click", async (event) => {
    const workflowButton = event.target.closest("button[data-workflow-action]");
    const taskButton = event.target.closest("button[data-task-action]");

    if (workflowButton) {
      workflowButton.disabled = true;
      try {
        if (workflowButton.dataset.workflowAction === "queue") {
          await queueWorkflow(workflowButton.dataset.workflowId || "");
        } else if (workflowButton.dataset.workflowAction === "toggle") {
          const active = workflowButton.dataset.active !== "true";
          await toggleWorkflow(workflowButton.dataset.workflowId || "", active);
        }
      } finally {
        workflowButton.disabled = false;
      }
      return;
    }

    if (!taskButton) {
      return;
    }

    taskButton.disabled = true;
    try {
      if (taskButton.dataset.taskAction === "run") {
        await runWorkflowTask(taskButton.dataset.taskId || "");
      } else if (taskButton.dataset.taskAction === "cancel") {
        await cancelWorkflowTask(taskButton.dataset.taskId || "");
      } else if (taskButton.dataset.taskAction === "retry") {
        await retryWorkflowTask(taskButton.dataset.taskId || "");
      }
    } finally {
      taskButton.disabled = false;
    }
  });

  const installButton = document.getElementById("install-companion");
  installButton.addEventListener("click", async () => {
    if (!state.deferredInstallPrompt) {
      return;
    }
    state.deferredInstallPrompt.prompt();
    await state.deferredInstallPrompt.userChoice;
    state.deferredInstallPrompt = null;
    installButton.hidden = true;
  });

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    state.deferredInstallPrompt = event;
    installButton.hidden = false;
  });
}

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    return;
  }
  try {
    await navigator.serviceWorker.register("./sw.js");
  } catch {
    // Keep the companion usable even if service worker registration fails.
  }
}

async function init() {
  bindEvents();
  await registerServiceWorker();

  if (state.snapshot) {
    state.snapshotStatus = `Loaded cached snapshot from ${formatTimestamp(state.snapshot.generated_at)}.`;
    renderSnapshot(state.snapshot);
  }

  await refreshCompanionData();
  scheduleRefresh();
}

init();
