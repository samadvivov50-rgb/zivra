const permissionItems = [
  ["Safe read", "Runs immediately for information-only requests like system status."],
  ["Low risk", "Requires confirmation for app launches, websites, and other small side effects."],
  ["Sensitive", "Requires confirmation for file changes, sends, and other meaningful mutations."],
  ["High risk", "Needs strong confirmation and should be blocked outright in safe mode."],
];

const phases = [
  ["Phase 1", "Ship the local MVP with chat, approvals, logging, notes, and system visibility."],
  ["Phase 2", "Add file search, clipboard tools, browser reading, and daily-use shortcuts."],
  ["Phase 3", "Expand into communication drafts, creator workflows, and structured exports."],
  ["Phase 4", "Harden trust with encrypted secrets, audit UX, and injection-resistant tooling."],
  ["Phase 5", "Layer in voice, screenshots, vision, and cross-device support."],
  ["Phase 6", "Introduce controlled agent mode with schedules, queues, supervisors, and rollback."],
];

const activityFilterItems = [
  ["all", "All"],
  ["attention", "Attention"],
  ["approval", "Approval"],
  ["executed", "Executed"],
];

const workflowWeekdayItems = [
  [0, "Monday"],
  [1, "Tuesday"],
  [2, "Wednesday"],
  [3, "Thursday"],
  [4, "Friday"],
  [5, "Saturday"],
  [6, "Sunday"],
];

const quickPrompts = [
  "Show my system status",
  "Search for AI desktop assistant examples",
  "Open notepad",
  "Open calculator",
  "Launch research workspace",
  "Remind me to review the roadmap every weekday at 9am",
  "Search notes for demo",
  "Read note demo",
  "Search files for roadmap",
  "Browse folder docs",
  "Search documents for roadmap",
  "Open document architecture",
  "Summarize document architecture",
  "Analyze document metrics",
  "Inspect document roadmap",
  "Inspect document metrics for Tue",
  "Inspect document config depth 3",
  "Inspect document config path assistant.voice depth 3",
  "Inspect document pipelines path jobs[].steps[] depth 2",
  "Show me my system status and open calculator",
  "Open calculator and open example.com",
  "Read my clipboard",
  "Copy deployment checklist to clipboard",
  "Read website example.com",
  "Summarize website example.com",
  "Research summary for AI desktop assistant patterns",
  "YouTube ideas for local-first AI assistant demos",
  "Draft WhatsApp to +15551234567 message Demo is ready for review",
  "Send WhatsApp to +15551234567 message Demo is ready for review",
  "Append to note demo with ship checklist and timing",
  "Open example.com",
  "Write down note ship the demo on Friday",
  "Draft an email to team@example.com subject Weekly sync update",
  "Send email to team@example.com subject Weekly sync body Status attached",
];

const commandPaletteItems = [
  {
    id: "screen-dashboard",
    title: "Open dashboard overview",
    subtitle: "Jump to the command center hero and system overview.",
    kind: "navigate",
    target: "#dashboard-overview",
    icon: "DB",
    meta: "Screen",
    keywords: ["home", "overview", "hero", "dashboard"],
  },
  {
    id: "screen-assistant",
    title: "Open assistant console",
    subtitle: "Go straight to chat, voice input, and quick prompts.",
    kind: "navigate",
    target: "#assistant-console",
    icon: "AI",
    meta: "Screen",
    keywords: ["chat", "assistant", "composer", "prompt"],
  },
  {
    id: "screen-execution",
    title: "Open task execution panel",
    subtitle: "Review pending approvals and live execution context.",
    kind: "navigate",
    target: "#tasks-section",
    icon: "TS",
    meta: "Screen",
    keywords: ["task", "execution", "queue", "approval"],
  },
  {
    id: "screen-logs",
    title: "Open audit log",
    subtitle: "Inspect recent actions, grouped flows, and replayable history.",
    kind: "navigate",
    target: "#logs-section",
    icon: "LG",
    meta: "Screen",
    keywords: ["logs", "audit", "history", "trace"],
  },
  {
    id: "screen-memory",
    title: "Open memory panel",
    subtitle: "Review conversation memory, stored sessions, and recall controls.",
    kind: "navigate",
    target: "#memory-section",
    icon: "MM",
    meta: "Screen",
    keywords: ["memory", "sessions", "context", "recall"],
  },
  {
    id: "screen-workflows",
    title: "Open workflow builder",
    subtitle: "Jump into scheduled tasks, supervisor controls, and queue state.",
    kind: "navigate",
    target: "#workflow-section",
    icon: "WF",
    meta: "Screen",
    keywords: ["workflow", "automation", "schedule", "builder"],
  },
  {
    id: "screen-research",
    title: "Open research mode",
    subtitle: "Go to the research brief builder and safe web reading tools.",
    kind: "navigate",
    target: "#research-panel",
    icon: "RS",
    meta: "Screen",
    keywords: ["research", "web", "brief", "browser"],
  },
  {
    id: "screen-messaging",
    title: "Open messaging",
    subtitle: "Jump to the WhatsApp panel and communication workflow.",
    kind: "navigate",
    target: "#messaging-panel",
    icon: "WA",
    meta: "Screen",
    keywords: ["whatsapp", "message", "messaging", "chat"],
  },
  {
    id: "run-system-status",
    title: "Run system status check",
    subtitle: "Ask Zivra for a live local system snapshot.",
    kind: "run",
    prompt: "Show my system status",
    icon: "ST",
    meta: "Run now",
    keywords: ["system", "status", "cpu", "memory", "snapshot"],
  },
  {
    id: "run-open-calculator",
    title: "Open calculator",
    subtitle: "Stage the approved desktop app launch through the assistant flow.",
    kind: "run",
    prompt: "Open calculator",
    icon: "AP",
    meta: "Run now",
    keywords: ["calculator", "app", "desktop", "launch"],
  },
  {
    id: "run-launch-research",
    title: "Launch research workspace",
    subtitle: "Kick off the saved research workspace shortcut.",
    kind: "run",
    prompt: "Launch research workspace",
    icon: "WK",
    meta: "Run now",
    keywords: ["workspace", "research", "launch", "mode"],
  },
  {
    id: "run-reminder",
    title: "Create a roadmap reminder",
    subtitle: "Queue a weekday reminder using the existing approval-safe reminder flow.",
    kind: "run",
    prompt: "Remind me to review the roadmap every weekday at 9am",
    icon: "RM",
    meta: "Run now",
    keywords: ["reminder", "schedule", "weekday", "roadmap"],
  },
  {
    id: "fill-web-research",
    title: "Draft a research brief request",
    subtitle: "Load a research command into the assistant composer.",
    kind: "fill",
    prompt: "Research summary for AI desktop assistant patterns",
    icon: "RB",
    meta: "Load draft",
    keywords: ["research", "brief", "draft", "summary"],
  },
  {
    id: "fill-document-analysis",
    title: "Draft document analysis",
    subtitle: "Prepare a structured analysis command for the current assistant flow.",
    kind: "fill",
    prompt: "Analyze document metrics",
    icon: "DA",
    meta: "Load draft",
    keywords: ["document", "analyze", "metrics", "data"],
  },
  {
    id: "fill-email",
    title: "Draft a status email",
    subtitle: "Load an email draft request into the composer for review before sending.",
    kind: "fill",
    prompt: "Draft an email to team@example.com subject Weekly sync update",
    icon: "EM",
    meta: "Load draft",
    keywords: ["email", "draft", "outbox", "status"],
  },
  {
    id: "fill-whatsapp",
    title: "Draft a WhatsApp message",
    subtitle: "Load a WhatsApp draft request into the assistant composer.",
    kind: "fill",
    prompt: "Draft WhatsApp to +15551234567 message Demo is ready for review",
    icon: "MS",
    meta: "Load draft",
    keywords: ["whatsapp", "message", "draft", "handoff"],
  },
];

const SpeechRecognitionConstructor = window.SpeechRecognition || window.webkitSpeechRecognition || null;
const speechRecognitionSupported = typeof SpeechRecognitionConstructor === "function";
const speechSynthesisSupported =
  typeof window.speechSynthesis !== "undefined" && typeof window.SpeechSynthesisUtterance !== "undefined";

const state = {
  assistantName: "Zivra",
  safeMode: false,
  memoryEnabled: true,
  voiceAutoSpeak: false,
  voiceAutoSend: false,
  voiceWakePhraseEnabled: false,
  voiceWakePhrase: "hey zivra",
  voiceListening: false,
  voiceSpeaking: false,
  voiceStatusMessage: "",
  voiceDraftBase: "",
  voiceInterimTranscript: "",
  voiceFinalTranscript: "",
  voiceRecognition: null,
  voiceRecognitionSupported: speechRecognitionSupported,
  voiceSynthesisSupported: speechSynthesisSupported,
  liveSearchResultLimit: 6,
  dashboardRefreshSeconds: 60,
  plannerInfo: { label: "Rule planner", mode: "rule" },
  sending: false,
  sessionId: getSessionId(),
  lastHistory: [],
  transientHistory: [],
  memorySessions: [],
  memoryStatusMessage: "",
  clipboardText: "",
  clipboardMetadata: null,
  clipboardStatusMessage: "",
  companionAccess: null,
  companionAccessStatus: "",
  companionAccessSessionId: "",
  visionStatus: { ready: false, provider: "local_only", mode: "metadata_only", model: null, max_upload_bytes: 0 },
  visionPrompt: "",
  visionInputDataUrl: "",
  visionInputName: "",
  selectedVisionAnalysis: null,
  visionStatusMessage: "",
  isAnalyzingVision: false,
  isCapturingVision: false,
  visionCameraSupported: Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
  visionCameraActive: false,
  visionCameraStream: null,
  visionCaptureSupported: Boolean(navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia),
  webReaderUrl: "",
  selectedWebPage: null,
  selectedWebSummary: null,
  webSearchQuery: "",
  webSearchResults: [],
  researchQuery: "",
  selectedResearchBrief: null,
  isResearching: false,
  researchStatusMessage: "",
  contentTopic: "",
  contentAudience: "",
  contentContext: "",
  selectedContentPackage: null,
  isGeneratingContent: false,
  contentStatusMessage: "",
  isReadingWebPage: false,
  isSummarizingWebPage: false,
  isSearchingWeb: false,
  webReaderStatusMessage: "",
  webSearchStatusMessage: "",
  emailComposeTo: "recipient@example.com",
  emailComposeSubject: "Draft from Zivra",
  emailComposeBody: "",
  emails: [],
  emailSummary: {},
  emailDelivery: { ready: false, status_label: "Not configured" },
  emailStatusMessage: "",
  whatsappComposeTo: "+15551234567",
  whatsappComposeBody: "",
  messages: [],
  messageSummary: {},
  messageDelivery: { ready: true, status_label: "Browser handoff", cloud_configured: false, delivery_mode: "browser_handoff" },
  messageStatusMessage: "",
  notesQuery: "",
  filesQuery: "",
  fileRoots: [],
  selectedFileFolderId: "",
  selectedFileFolder: null,
  fileSearchResults: [],
  filesStatusMessage: "",
  documentsQuery: "",
  selectedNoteName: "",
  selectedNote: null,
  selectedDocumentId: "",
  selectedDocument: null,
  selectedDocumentSummary: null,
  selectedDocumentAnalysis: null,
  selectedDocumentInspection: null,
  documentInspectionFilter: "",
  documentInspectionDepth: 2,
  documentInspectionPath: "",
  isSummarizingDocument: false,
  isAnalyzingDocument: false,
  isInspectingDocument: false,
  noteEditorContent: "",
  isEditingNote: false,
  includeArchived: false,
  reminderSummary: {},
  workflowSummary: {},
  workflows: [],
  workflowTasks: [],
  workflowStatusMessage: "",
  workflowName: "",
  workflowPrompt: "",
  workflowScheduleType: "manual",
  workflowIntervalHours: 4,
  workflowRunHour: 9,
  workflowRunMinute: 0,
  workflowRunWeekday: 0,
  workflowStartActive: true,
  workflowSupervisorEnabled: false,
  workflowSupervisorMaxTasksPerCycle: 1,
  workflowSupervisorMaxPendingApprovals: 1,
  workflowSupervisorPauseOnFailure: true,
  workflowSupervisorCycle: null,
  whatsappApiVersion: "v23.0",
  whatsappPhoneNumberId: "",
  whatsappVerifyToken: "",
  activityGroups: [],
  recentActions: [],
  activityFilter: "all",
  activityQuery: "",
  activityDateFrom: "",
  activityDateTo: "",
  activitySavedViews: loadActivitySavedViews(),
  activityGroupTotal: 0,
  activityTotal: 0,
  activityHasMore: false,
  activityLoading: false,
  expandedActivityEvents: {},
  commandPaletteOpen: false,
  commandPaletteQuery: "",
  commandPaletteSelection: 0,
  settingsStatusMessage: "",
  secretsStatusMessage: "",
  secretsInfo: {
    provider: { available: false, label: "Encrypted vault unavailable", provider: "unavailable" },
    fields: {},
    runtime: {},
  },
  notificationSupported: "Notification" in window,
  notificationPermission: "Notification" in window ? Notification.permission : "unsupported",
  notifiedReminders: loadNotifiedReminders(),
};

let backgroundRefreshTimerId = null;
let backgroundRefreshIntervalMs = 0;

function getSessionId() {
  const params = new URLSearchParams(window.location.search);
  const querySessionId = (params.get("session_id") || params.get("session") || "").trim();
  if (querySessionId) {
    window.localStorage.setItem("zivra_session_id", querySessionId);
    return querySessionId;
  }

  const existing = window.localStorage.getItem("zivra_session_id");
  if (existing) {
    return existing;
  }

  const created = `session-${Date.now()}`;
  window.localStorage.setItem("zivra_session_id", created);
  return created;
}

function loadNotifiedReminders() {
  try {
    const raw = window.localStorage.getItem("zivra_notified_reminders");
    if (!raw) {
      return {};
    }

    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function saveNotifiedReminders() {
  window.localStorage.setItem("zivra_notified_reminders", JSON.stringify(state.notifiedReminders));
}

function slugifyValue(value, fallback = "item") {
  return (
    String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 32) || fallback
  );
}

function getActivityFilterLabel(value) {
  const match = activityFilterItems.find(([itemValue]) => itemValue === value);
  return match ? match[1] : "All";
}

function buildSavedActivityViewLabel(view) {
  const segments = [];
  if (view.query) {
    segments.push(view.query);
  }
  if (view.status && view.status !== "all") {
    segments.push(getActivityFilterLabel(view.status));
  }
  if (view.dateFrom || view.dateTo) {
    segments.push(
      [view.dateFrom ? `from ${view.dateFrom}` : "", view.dateTo ? `to ${view.dateTo}` : ""]
        .filter(Boolean)
        .join(" "),
    );
  }
  return segments.join(" / ") || "Recent activity";
}

function normalizeSavedActivityView(view) {
  const status = activityFilterItems.some(([value]) => value === view?.status) ? view.status : "all";
  const dateFrom = String(view?.dateFrom || view?.date_from || "").trim();
  const dateTo = String(view?.dateTo || view?.date_to || "").trim();
  const query = String(view?.query || "").trim();
  return {
    id: String(view?.id || `activity-view-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`),
    label: String(view?.label || "").trim() || buildSavedActivityViewLabel({ query, status, dateFrom, dateTo }),
    query,
    status,
    dateFrom,
    dateTo,
  };
}

function loadActivitySavedViews() {
  try {
    const raw = window.localStorage.getItem("zivra_activity_saved_views");
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .map((view) => normalizeSavedActivityView(view))
      .filter((view, index, views) => views.findIndex((candidate) => candidate.id === view.id) === index)
      .slice(0, 8);
  } catch {
    return [];
  }
}

function saveActivitySavedViews() {
  window.localStorage.setItem("zivra_activity_saved_views", JSON.stringify(state.activitySavedViews));
}

function padNumber(value) {
  return String(value).padStart(2, "0");
}

function clampNumber(value, minimum, maximum, fallback) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return Math.min(Math.max(Math.trunc(parsed), minimum), maximum);
}

function buildAssistantInputLabel(name) {
  return `Message ${name}`;
}

function buildAssistantPlaceholder(name) {
  return (
    `Ask ${name} for system info, clipboard reads or writes, webpage reading or summaries, document reading, ` +
    "research briefs, YouTube or SEO ideas, document summaries, structure inspection, filtered document views, path-focused schema drills, or nested schema depth " +
    "checks, a web search, an approved app or workspace, a note, a one-off or recurring reminder, a local email draft or send request, or a WhatsApp draft or handoff."
  );
}

function getCompanionAccessSessionId() {
  const selected = String(state.companionAccessSessionId || "").trim();
  return selected || state.sessionId;
}

function getRecentCompanionSessions() {
  return (state.memorySessions || [])
    .filter((session) => session && session.session_id)
    .filter((session, index, sessions) => sessions.findIndex((candidate) => candidate.session_id === session.session_id) === index);
}

function getSelectedCompanionSessionSummary() {
  const activeSessionId = getCompanionAccessSessionId();
  const recentSessionOptions = getRecentCompanionSessions();
  return (
    recentSessionOptions.find((session) => session.session_id === activeSessionId) ||
    (activeSessionId === state.sessionId
      ? {
          session_id: state.sessionId,
          last_content_preview: "The current browser thread is selected for mobile handoff.",
          turn_count: (state.lastHistory || []).length || (state.transientHistory || []).length || 0,
          last_seen_at: "",
        }
      : null)
  );
}

function syncCompanionAccessSessionSelection() {
  const knownSessionIds = new Set([
    state.sessionId,
    ...(state.memorySessions || []).map((session) => String(session.session_id || "").trim()).filter(Boolean),
  ]);
  const selected = getCompanionAccessSessionId();
  state.companionAccessSessionId = knownSessionIds.has(selected) ? selected : state.sessionId;
}

function buildCompanionHandoffSummary(candidate, session) {
  const preview = session?.last_content_preview ? `Preview: ${session.last_content_preview}` : "Preview: No saved preview available.";
  const turns = Number(session?.turn_count || 0);
  const parts = [
    "Zivra mobile handoff",
    `Session: ${session?.session_id || getCompanionAccessSessionId()}`,
    `Turns: ${turns}`,
    preview,
    `Mobile: ${candidate?.mobile_session_url || candidate?.mobile_url || ""}`,
    `Control room: ${candidate?.control_room_session_url || candidate?.control_room_url || ""}`,
  ];
  return parts.join("\n");
}

async function shareCompanionAccess(candidate, session) {
  if (typeof navigator.share !== "function") {
    throw new Error("Native sharing is unavailable in this browser.");
  }

  await navigator.share({
    title: "Zivra mobile handoff",
    text: session?.last_content_preview || "Open this Zivra session on another device.",
    url: candidate?.mobile_session_url || candidate?.mobile_url || window.location.href,
  });
}

function buildCompanionEmailDraft(candidate, session) {
  const sessionId = session?.session_id || getCompanionAccessSessionId();
  const shortSessionId = sessionId.length > 24 ? `${sessionId.slice(0, 24)}...` : sessionId;
  return {
    subject: `Zivra handoff: ${shortSessionId}`,
    body: buildCompanionHandoffSummary(candidate, session),
  };
}

function buildCompanionWhatsAppDraft(candidate, session) {
  const preview = session?.last_content_preview ? `\nPreview: ${session.last_content_preview}` : "";
  return [
    "Zivra mobile handoff",
    `Session: ${session?.session_id || getCompanionAccessSessionId()}`,
    preview,
    `Open on phone: ${candidate?.mobile_session_url || candidate?.mobile_url || ""}`,
  ]
    .filter(Boolean)
    .join("\n");
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "0 bytes";
  }

  if (bytes < 1024) {
    return `${bytes} bytes`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function buildDateRangeIso(value, options = {}) {
  if (!value) {
    return "";
  }

  const suffix = options.endOfDay ? "T23:59:59" : "T00:00:00";
  return toOffsetIsoString(`${value}${suffix}`);
}

function toDateTimeLocalValue(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return `${date.getFullYear()}-${padNumber(date.getMonth() + 1)}-${padNumber(date.getDate())}T${padNumber(date.getHours())}:${padNumber(date.getMinutes())}`;
}

function toOffsetIsoString(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const offsetMinutes = -date.getTimezoneOffset();
  const sign = offsetMinutes >= 0 ? "+" : "-";
  const absoluteOffset = Math.abs(offsetMinutes);
  const offsetHours = padNumber(Math.floor(absoluteOffset / 60));
  const offsetRemainder = padNumber(absoluteOffset % 60);

  return (
    `${date.getFullYear()}-${padNumber(date.getMonth() + 1)}-${padNumber(date.getDate())}` +
    `T${padNumber(date.getHours())}:${padNumber(date.getMinutes())}:00${sign}${offsetHours}:${offsetRemainder}`
  );
}

function resolveInspectionSchemaPath(basePath, relativePath) {
  const normalizedBase = (basePath || "").trim();
  const normalizedRelative = (relativePath || "").trim();
  if (!normalizedRelative) {
    return normalizedBase;
  }
  if (!normalizedBase) {
    return normalizedRelative;
  }
  if (normalizedRelative.startsWith("[].") || normalizedRelative === "[]") {
    return `${normalizedBase}${normalizedRelative}`;
  }
  return `${normalizedBase}.${normalizedRelative}`;
}

function getInspectionParentPath(path) {
  const normalized = (path || "").trim();
  if (!normalized) {
    return "";
  }
  if (normalized.endsWith("[]")) {
    return normalized.slice(0, -2);
  }
  const lastDot = normalized.lastIndexOf(".");
  if (lastDot === -1) {
    return "";
  }
  return normalized.slice(0, lastDot);
}

function getFileParentFolderId(fileId) {
  const normalized = String(fileId || "").trim().replaceAll("\\", "/");
  const lastSlash = normalized.lastIndexOf("/");
  if (lastSlash === -1) {
    return "";
  }
  return normalized.slice(0, lastSlash);
}

function splitInspectionPath(path) {
  return String(path || "")
    .split(".")
    .map((segment) => segment.trim())
    .filter(Boolean);
}

function renderInspectionBreadcrumbs(path) {
  const segments = splitInspectionPath(path);
  const crumbs = [
    `
      <button
        class="inspection-breadcrumb ${!segments.length ? "is-active" : ""}"
        type="button"
        data-document-reader-action="clear-inspection-path"
      >
        Root
      </button>
    `,
  ];

  let currentPath = "";
  segments.forEach((segment, index) => {
    currentPath = resolveInspectionSchemaPath(currentPath, segment);
    crumbs.push('<span class="inspection-breadcrumb-sep">/</span>');
    crumbs.push(
      `
        <button
          class="inspection-breadcrumb ${index === segments.length - 1 ? "is-active" : ""}"
          type="button"
          data-document-reader-action="focus-inspection-path"
          data-schema-path="${escapeHtml(currentPath)}"
        >
          ${escapeHtml(segment)}
        </button>
      `,
    );
  });

  return `<div class="inspection-breadcrumbs">${crumbs.join("")}</div>`;
}

function renderInspectionPreviewCards(fields, options = {}) {
  const interactivePathBase = String(options.interactivePathBase || "").trim();
  const interactive = options.interactive !== false;
  return `
    <div class="inspection-grid">
      ${fields
        .map((field) => {
          const resolvedPath = interactive
            ? resolveInspectionSchemaPath(interactivePathBase, field.key)
            : "";
          const typeMarkup = field.type
            ? `<span class="inspection-depth-chip">${escapeHtml(field.type)}</span>`
            : "";
          const copyValue = encodeURIComponent(field.preview || "");
          const focusMarkup =
            interactive && resolvedPath
              ? `
                  <button
                    class="inspection-preview-button"
                    type="button"
                    data-document-reader-action="focus-inspection-path"
                    data-schema-path="${escapeHtml(resolvedPath)}"
                  >
                    <strong>${escapeHtml(field.key)}</strong>
                    ${typeMarkup}
                    <code>${escapeHtml(field.preview)}</code>
                  </button>
                `
              : `
                  <div class="inspection-preview-button is-static">
                    <strong>${escapeHtml(field.key)}</strong>
                    ${typeMarkup}
                    <code>${escapeHtml(field.preview)}</code>
                  </div>
                `;
          if (!interactive || !resolvedPath) {
            return `
              <article class="inspection-card inspection-preview-card">
                ${focusMarkup}
                <div class="inspection-preview-actions">
                  <button
                    class="ghost-button inspection-copy-button"
                    type="button"
                    data-document-reader-action="copy-preview-value"
                    data-copy-value="${copyValue}"
                  >
                    Copy
                  </button>
                </div>
              </article>
            `;
          }

          return `
            <article class="inspection-card inspection-preview-card">
              ${focusMarkup}
              <div class="inspection-preview-actions">
                <button
                  class="ghost-button inspection-copy-button"
                  type="button"
                  data-document-reader-action="copy-preview-value"
                  data-copy-value="${copyValue}"
                >
                  Copy
                </button>
              </div>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderInspectionPreviewItems(items, options = {}) {
  const drillPath = String(options.drillPath || "").trim();
  const interactive = Boolean(drillPath);
  return `
    <ul class="document-points">
      ${items
        .map((item) => {
          const previewItem = normalizeInspectionPreviewItem(item);
          const typeMarkup = previewItem.type
            ? `<span class="inspection-depth-chip">${escapeHtml(previewItem.type)}</span>`
            : "";
          const copyValue = encodeURIComponent(previewItem.preview);
          if (!interactive) {
            return `
              <li>
                <div class="inspection-item-row">
                  <div class="inspection-item-content">
                    ${typeMarkup}
                    <code>${escapeHtml(previewItem.preview)}</code>
                  </div>
                  <button
                    class="ghost-button inspection-copy-button"
                    type="button"
                    data-document-reader-action="copy-preview-value"
                    data-copy-value="${copyValue}"
                  >
                    Copy
                  </button>
                </div>
              </li>
            `;
          }

          return `
            <li>
              <div class="inspection-item-row">
                <button
                  class="inspection-item-button"
                  type="button"
                  data-document-reader-action="focus-inspection-path"
                  data-schema-path="${escapeHtml(drillPath)}"
                >
                  ${typeMarkup}
                  <code>${escapeHtml(previewItem.preview)}</code>
                </button>
                <button
                  class="ghost-button inspection-copy-button"
                  type="button"
                  data-document-reader-action="copy-preview-value"
                  data-copy-value="${copyValue}"
                >
                  Copy
                </button>
              </div>
            </li>
          `;
        })
        .join("")}
    </ul>
  `;
}

function normalizeInspectionPreviewItem(item) {
  if (item && typeof item === "object" && !Array.isArray(item)) {
    return {
      type: String(item.type || "").trim(),
      preview: String(item.preview ?? ""),
    };
  }

  return {
    type: "",
    preview: String(item ?? ""),
  };
}

function renderInspectionActionBar(scope) {
  const label = scope === "focus" ? "focus" : "inspection";
  const tableData = buildInspectionTableExport(scope);
  const csvActions = tableData
    ? `
        <button
          class="ghost-button inspection-export-button"
          type="button"
          data-document-reader-action="copy-inspection-csv"
          data-export-scope="${scope}"
        >
          Copy ${label} CSV
        </button>
        <button
          class="ghost-button inspection-export-button"
          type="button"
          data-document-reader-action="download-inspection-csv"
          data-export-scope="${scope}"
        >
          Download ${label} CSV
        </button>
      `
    : "";
  return `
    <div class="inspection-export-row">
      <button
        class="ghost-button inspection-export-button"
        type="button"
        data-document-reader-action="copy-inspection-json"
        data-export-scope="${scope}"
      >
        Copy ${label} JSON
      </button>
      <button
        class="ghost-button inspection-export-button"
        type="button"
        data-document-reader-action="download-inspection-json"
        data-export-scope="${scope}"
      >
        Download ${label} JSON
      </button>
      ${csvActions}
    </div>
  `;
}

function escapeHtml(value) {
  return String(value)
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

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json();
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

async function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("File read failed."));
    reader.readAsDataURL(file);
  });
}

async function captureScreenImageDataUrl() {
  if (!navigator.mediaDevices || typeof navigator.mediaDevices.getDisplayMedia !== "function") {
    throw new Error("Screen capture is not supported in this browser.");
  }

  const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
  try {
    const video = document.createElement("video");
    video.srcObject = stream;
    video.muted = true;
    video.playsInline = true;
    await new Promise((resolve, reject) => {
      video.onloadedmetadata = resolve;
      video.onerror = () => reject(new Error("Screen capture metadata failed to load."));
    });
    await video.play();
    await new Promise((resolve) => window.setTimeout(resolve, 120));
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const context = canvas.getContext("2d");
    if (!context) {
      throw new Error("Screen capture canvas could not be created.");
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/png");
  } finally {
    stream.getTracks().forEach((track) => track.stop());
  }
}

async function startVisionCameraStream() {
  if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== "function") {
    throw new Error("Camera capture is not supported in this browser.");
  }

  try {
    return await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    });
  } catch (error) {
    try {
      return await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    } catch (fallbackError) {
      throw fallbackError || error;
    }
  }
}

function stopVisionCamera() {
  if (state.visionCameraStream) {
    state.visionCameraStream.getTracks().forEach((track) => track.stop());
  }
  state.visionCameraStream = null;
  state.visionCameraActive = false;
}

function syncVisionCameraPreview() {
  const preview = document.getElementById("vision-camera-preview");
  if (!preview || !state.visionCameraStream) {
    return;
  }
  if (preview.srcObject !== state.visionCameraStream) {
    preview.srcObject = state.visionCameraStream;
  }
  preview
    .play()
    .then(() => undefined)
    .catch(() => undefined);
}

async function captureVisionCameraImageDataUrl() {
  const preview = document.getElementById("vision-camera-preview");
  if (!preview || !state.visionCameraStream) {
    throw new Error("Start the camera before capturing a frame.");
  }

  const width = preview.videoWidth || 1280;
  const height = preview.videoHeight || 720;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("Camera capture canvas could not be created.");
  }
  context.drawImage(preview, 0, 0, width, height);
  return canvas.toDataURL("image/png");
}

function normalizeVoiceText(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim();
}

function getActiveHistory() {
  return state.memoryEnabled ? state.lastHistory || [] : state.transientHistory;
}

function getLatestAssistantReply() {
  const history = getActiveHistory();
  for (let index = history.length - 1; index >= 0; index -= 1) {
    if (history[index].role === "assistant" && normalizeVoiceText(history[index].content)) {
      return normalizeVoiceText(history[index].content);
    }
  }
  return "";
}

function buildVoiceStatusCopy() {
  if (state.voiceListening) {
    if (state.voiceWakePhraseEnabled) {
      return state.voiceInterimTranscript
        ? `Heard: ${normalizeVoiceText(state.voiceInterimTranscript)}`
        : `Listening for "${state.voiceWakePhrase}"...`;
    }
    return state.voiceInterimTranscript
      ? `Listening: ${normalizeVoiceText(state.voiceInterimTranscript)}`
      : "Listening...";
  }
  if (state.voiceSpeaking) {
    return `Speaking the latest reply aloud.`;
  }
  if (state.voiceStatusMessage) {
    return state.voiceStatusMessage;
  }
  if (!state.voiceRecognitionSupported && !state.voiceSynthesisSupported) {
    return "Browser voice features are unavailable here.";
  }
  if (!state.voiceRecognitionSupported) {
    return "Mic input is unavailable here, but reply read-aloud still works.";
  }
  if (!state.voiceSynthesisSupported) {
    return "Mic input is available. Read-aloud is unavailable in this browser.";
  }
  return "Mic input and reply read-aloud are ready locally in this browser.";
}

function renderVoiceControls() {
  const toggleButton = document.getElementById("voice-toggle");
  const speakButton = document.getElementById("speak-latest-reply");
  const status = document.getElementById("voice-status");
  if (!toggleButton || !speakButton || !status) {
    return;
  }

  toggleButton.textContent = state.voiceListening ? "Stop mic" : "Start mic";
  toggleButton.disabled = !state.voiceRecognitionSupported || state.sending;
  toggleButton.classList.toggle("is-active", state.voiceListening);

  const latestReply = getLatestAssistantReply();
  speakButton.textContent = state.voiceSpeaking ? "Stop reply" : "Speak reply";
  speakButton.disabled = !state.voiceSynthesisSupported || (!latestReply && !state.voiceSpeaking);
  speakButton.classList.toggle("is-active", state.voiceSpeaking);

  status.textContent = buildVoiceStatusCopy();
  status.className = `voice-status${state.voiceListening || state.voiceSpeaking ? " is-live" : ""}`;
}

function stopSpeaking() {
  if (!state.voiceSynthesisSupported) {
    return;
  }
  window.speechSynthesis.cancel();
  state.voiceSpeaking = false;
  renderVoiceControls();
}

function speakText(text) {
  const normalized = normalizeVoiceText(text);
  if (!normalized || !state.voiceSynthesisSupported) {
    return;
  }

  stopSpeaking();
  const utterance = new window.SpeechSynthesisUtterance(normalized);
  const preferredLanguage = document.documentElement.lang || navigator.language || "en-US";
  utterance.lang = preferredLanguage;
  utterance.onend = () => {
    state.voiceSpeaking = false;
    renderVoiceControls();
  };
  utterance.onerror = () => {
    state.voiceSpeaking = false;
    state.voiceStatusMessage = "Read-aloud failed in this browser.";
    renderVoiceControls();
  };
  state.voiceSpeaking = true;
  state.voiceStatusMessage = "Speaking the latest reply aloud.";
  renderVoiceControls();
  window.speechSynthesis.speak(utterance);
}

function extractWakePhraseCommand(transcript) {
  const normalizedTranscript = normalizeVoiceText(transcript);
  if (!state.voiceWakePhraseEnabled) {
    return { matched: true, command: normalizedTranscript };
  }

  const wakePhrase = normalizeVoiceText(state.voiceWakePhrase).toLowerCase();
  if (!wakePhrase) {
    return { matched: true, command: normalizedTranscript };
  }

  const lowered = normalizedTranscript.toLowerCase();
  const matchIndex = lowered.indexOf(wakePhrase);
  if (matchIndex === -1) {
    return { matched: false, command: "" };
  }

  const remainder = normalizedTranscript
    .slice(matchIndex + wakePhrase.length)
    .replace(/^[,:;.!?\-\s]+/, "")
    .trim();
  return { matched: true, command: remainder };
}

function updateVoiceDraftPreview(transcript) {
  if (state.voiceWakePhraseEnabled) {
    state.voiceStatusMessage = transcript
      ? `Heard: ${normalizeVoiceText(transcript)}`
      : `Listening for "${state.voiceWakePhrase}"...`;
    renderVoiceControls();
    return;
  }

  const input = document.getElementById("assistant-input");
  if (!input) {
    return;
  }
  const combined = [normalizeVoiceText(state.voiceDraftBase), normalizeVoiceText(transcript)].filter(Boolean).join(" ");
  input.value = combined;
  renderVoiceControls();
}

async function finalizeVoiceTranscript(transcript) {
  const input = document.getElementById("assistant-input");
  if (!input) {
    return;
  }

  const normalized = normalizeVoiceText(transcript);
  state.voiceFinalTranscript = "";
  state.voiceInterimTranscript = "";
  if (!normalized) {
    state.voiceStatusMessage = "No speech was captured.";
    renderVoiceControls();
    return;
  }

  const wakeMatch = extractWakePhraseCommand(normalized);
  if (!wakeMatch.matched) {
    state.voiceStatusMessage = `No wake phrase heard. Say "${state.voiceWakePhrase}" followed by the command.`;
    input.value = state.voiceDraftBase;
    renderVoiceControls();
    return;
  }

  if (!wakeMatch.command) {
    state.voiceStatusMessage = state.voiceWakePhraseEnabled
      ? `Wake phrase heard. Include the command after "${state.voiceWakePhrase}".`
      : "No voice command was captured.";
    input.value = state.voiceDraftBase;
    renderVoiceControls();
    return;
  }

  const combined = [normalizeVoiceText(state.voiceDraftBase), wakeMatch.command].filter(Boolean).join(" ");
  input.value = combined;
  if (state.voiceAutoSend) {
    state.voiceStatusMessage = "Sending the captured voice command.";
    renderVoiceControls();
    await sendMessage(combined);
    return;
  }

  state.voiceStatusMessage = "Voice transcript added to the composer.";
  input.focus();
  renderVoiceControls();
}

function stopVoiceListening() {
  if (state.voiceRecognition) {
    state.voiceRecognition.stop();
  }
}

function ensureVoiceRecognition() {
  if (!state.voiceRecognitionSupported) {
    return null;
  }
  if (state.voiceRecognition) {
    return state.voiceRecognition;
  }

  const recognition = new SpeechRecognitionConstructor();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = document.documentElement.lang || navigator.language || "en-US";
  recognition.onstart = () => {
    state.voiceListening = true;
    state.voiceStatusMessage = state.voiceWakePhraseEnabled
      ? `Listening for "${state.voiceWakePhrase}"...`
      : "Listening...";
    renderVoiceControls();
  };
  recognition.onresult = (event) => {
    let transcript = "";
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      transcript += `${event.results[index][0]?.transcript || ""} `;
    }
    const normalized = normalizeVoiceText(transcript);
    if (normalized) {
      state.voiceInterimTranscript = normalized;
      updateVoiceDraftPreview(normalized);
    }
  };
  recognition.onerror = (event) => {
    const code = event?.error || "unknown";
    if (code === "not-allowed" || code === "service-not-allowed") {
      state.voiceStatusMessage = "Microphone permission was denied.";
    } else if (code === "no-speech") {
      state.voiceStatusMessage = "No speech was heard.";
    } else if (code === "audio-capture") {
      state.voiceStatusMessage = "No microphone was available.";
    } else {
      state.voiceStatusMessage = `Voice capture failed: ${code}.`;
    }
    state.voiceListening = false;
    renderVoiceControls();
  };
  recognition.onend = () => {
    const transcript = state.voiceInterimTranscript || state.voiceFinalTranscript;
    state.voiceListening = false;
    renderVoiceControls();
    void finalizeVoiceTranscript(transcript);
  };
  state.voiceRecognition = recognition;
  return recognition;
}

function startVoiceListening() {
  if (!state.voiceRecognitionSupported || state.voiceListening || state.sending) {
    renderVoiceControls();
    return;
  }
  stopSpeaking();
  const input = document.getElementById("assistant-input");
  state.voiceDraftBase = input ? input.value.trim() : "";
  state.voiceInterimTranscript = "";
  state.voiceFinalTranscript = "";
  const recognition = ensureVoiceRecognition();
  if (!recognition) {
    state.voiceStatusMessage = "Browser voice input is unavailable here.";
    renderVoiceControls();
    return;
  }
  try {
    recognition.start();
  } catch (error) {
    state.voiceStatusMessage = error instanceof Error ? error.message : "Voice capture could not start.";
    renderVoiceControls();
  }
}

function flashButtonLabel(button, label) {
  const original = button.dataset.originalLabel || button.textContent;
  button.dataset.originalLabel = original;
  button.textContent = label;
  window.setTimeout(() => {
    button.textContent = button.dataset.originalLabel || original;
  }, 1200);
}

function normalizeCommandPaletteText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

function getCommandPaletteEntries(query = state.commandPaletteQuery) {
  const normalizedQuery = normalizeCommandPaletteText(query);
  const entries = [...commandPaletteItems];
  if (!normalizedQuery) {
    return entries.slice(0, 10);
  }

  return entries
    .map((entry) => {
      const haystack = normalizeCommandPaletteText(
        [entry.title, entry.subtitle, entry.meta, ...(entry.keywords || []), entry.prompt || "", entry.target || ""].join(" "),
      );
      const score = haystack.includes(normalizedQuery) ? 1 : 0;
      return { ...entry, score };
    })
    .filter((entry) => entry.score > 0)
    .slice(0, 12);
}

function focusAssistantComposer(prompt = "") {
  const input = document.getElementById("assistant-input");
  if (!input) {
    return;
  }

  if (prompt) {
    input.value = prompt;
  }
  document.getElementById("assistant-console")?.scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => {
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  }, 80);
}

function openCommandPalette(query = "") {
  state.commandPaletteOpen = true;
  state.commandPaletteQuery = query;
  state.commandPaletteSelection = 0;
  renderCommandPalette();
  const input = document.getElementById("command-palette-input");
  if (input) {
    input.value = query;
    window.setTimeout(() => {
      input.focus();
      input.select();
    }, 0);
  }
}

function closeCommandPalette() {
  if (!state.commandPaletteOpen) {
    return;
  }

  state.commandPaletteOpen = false;
  renderCommandPalette();
}

function renderCommandPalette() {
  const root = document.getElementById("command-palette");
  const summary = document.getElementById("command-palette-summary");
  const results = document.getElementById("command-palette-results");
  const input = document.getElementById("command-palette-input");
  if (!root || !summary || !results || !input) {
    return;
  }

  root.classList.toggle("is-hidden", !state.commandPaletteOpen);
  root.setAttribute("aria-hidden", state.commandPaletteOpen ? "false" : "true");
  if (!state.commandPaletteOpen) {
    results.innerHTML = "";
    summary.innerHTML = "";
    return;
  }

  input.value = state.commandPaletteQuery;
  const entries = getCommandPaletteEntries();
  if (state.commandPaletteSelection >= entries.length) {
    state.commandPaletteSelection = Math.max(0, entries.length - 1);
  }

  summary.innerHTML = entries.length
    ? `
        <span class="meta-chip">${entries.length} command${entries.length === 1 ? "" : "s"} ready</span>
        <span class="meta-chip">Arrow keys to move</span>
        <span class="meta-chip">Enter to act</span>
        <span class="meta-chip">Esc to close</span>
      `
    : `
        <span class="meta-chip">No matches yet</span>
        <span class="meta-chip">Try “memory”, “research”, “calculator”, or “workflow”</span>
      `;

  results.innerHTML = entries.length
    ? entries
        .map((entry, index) => {
          const activeClass = index === state.commandPaletteSelection ? " is-active" : "";
          return `
            <button
              class="command-palette-item${activeClass}"
              type="button"
              data-command-palette-item="true"
              data-command-id="${escapeHtml(entry.id)}"
            >
              <span class="command-palette-icon" aria-hidden="true">${escapeHtml(entry.icon)}</span>
              <span class="command-palette-copy">
                <strong>${escapeHtml(entry.title)}</strong>
                <span>${escapeHtml(entry.subtitle)}</span>
              </span>
              <span class="command-palette-meta">${escapeHtml(entry.meta)}</span>
            </button>
          `;
        })
        .join("")
    : `
        <article class="empty-card">
          <strong>No matching commands</strong>
          <span>Search by screen, workflow, memory, research, email, WhatsApp, or system action.</span>
        </article>
      `;
}

async function runCommandPaletteEntry(entry) {
  if (!entry) {
    return;
  }

  closeCommandPalette();

  if (entry.kind === "navigate" && entry.target) {
    document.querySelector(entry.target)?.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }

  if (entry.kind === "fill" && entry.prompt) {
    focusAssistantComposer(entry.prompt);
    return;
  }

  if (entry.kind === "run" && entry.prompt) {
    focusAssistantComposer(entry.prompt);
    await sendMessage(entry.prompt);
  }
}

function moveCommandPaletteSelection(delta) {
  const entries = getCommandPaletteEntries();
  if (!entries.length) {
    state.commandPaletteSelection = 0;
    renderCommandPalette();
    return;
  }

  const total = entries.length;
  state.commandPaletteSelection = (state.commandPaletteSelection + delta + total) % total;
  renderCommandPalette();
}

function buildInspectionExportPayload(scope) {
  if (!state.selectedDocumentInspection || !state.selectedDocument) {
    return null;
  }

  const exportedAt = new Date().toISOString();
  if (scope === "focus") {
    if (!state.selectedDocumentInspection.focus) {
      return null;
    }

    return {
      exported_at: exportedAt,
      document_id: state.selectedDocument.id,
      document_title: state.selectedDocument.title,
      document_path: state.selectedDocument.path,
      focus: state.selectedDocumentInspection.focus,
    };
  }

  return {
    exported_at: exportedAt,
    document_id: state.selectedDocument.id,
    document_title: state.selectedDocument.title,
    document_path: state.selectedDocument.path,
    inspection: state.selectedDocumentInspection,
  };
}

function buildInspectionTableExport(scope) {
  if (!state.selectedDocumentInspection || !state.selectedDocument) {
    return null;
  }

  const source = scope === "focus" ? state.selectedDocumentInspection.focus : state.selectedDocumentInspection;
  if (!source || !(source.sample_rows || []).length) {
    return null;
  }

  const headers =
    (source.headers || []).length
      ? source.headers
      : Object.keys(source.sample_rows[0] || {});
  if (!headers.length) {
    return null;
  }

  return {
    headers,
    rows: source.sample_rows,
    label: scope === "focus" ? "focus" : "inspection",
  };
}

async function fetchInspectionTableExport(scope) {
  if (!state.selectedDocument || !state.selectedDocumentInspection) {
    return null;
  }

  const params = new URLSearchParams({
    document_id: state.selectedDocument.id,
  });
  if (state.documentInspectionFilter) {
    params.set("filter", state.documentInspectionFilter);
  }
  if (scope === "focus") {
    const focusPath = state.selectedDocumentInspection.focus?.path || state.documentInspectionPath;
    if (!focusPath) {
      return null;
    }
    params.set("schema_path", focusPath);
  }

  const payload = await api(`/documents/export-table?${params.toString()}`);
  return payload.table || null;
}

function toCsvValue(value) {
  const normalized = String(value ?? "");
  if (/[",\n]/.test(normalized)) {
    return `"${normalized.replaceAll('"', '""')}"`;
  }
  return normalized;
}

function buildCsvText(headers, rows) {
  const csvLines = [headers.map((header) => toCsvValue(header)).join(",")];
  rows.forEach((row) => {
    csvLines.push(headers.map((header) => toCsvValue(row[header] ?? "")).join(","));
  });
  return csvLines.join("\n");
}

async function copyInspectionExport(scope, button) {
  const payload = buildInspectionExportPayload(scope);
  if (!payload) {
    flashButtonLabel(button, "Unavailable");
    return;
  }

  try {
    await copyTextToClipboard(JSON.stringify(payload, null, 2));
    flashButtonLabel(button, "Copied");
  } catch {
    flashButtonLabel(button, "Failed");
  }
}

function downloadInspectionExport(scope, button) {
  const payload = buildInspectionExportPayload(scope);
  if (!payload) {
    flashButtonLabel(button, "Unavailable");
    return;
  }

  const label = scope === "focus" ? "focus" : "inspection";
  const safeTitle = (state.selectedDocument?.title || "document")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = `${safeTitle || "document"}-${label}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(href);
  flashButtonLabel(button, "Downloaded");
}

function buildActivityQueryParams(options = {}) {
  const append = options.append === true;
  const params = new URLSearchParams({
    limit: String(options.limit || 12),
    offset: String(options.offset ?? (append ? state.recentActions.length : 0)),
  });
  if (state.activityQuery) {
    params.set("q", state.activityQuery);
  }
  if (state.activityFilter && state.activityFilter !== "all") {
    params.set("status", state.activityFilter);
  }
  if (state.activityDateFrom) {
    params.set("start", buildDateRangeIso(state.activityDateFrom));
  }
  if (state.activityDateTo) {
    params.set("end", buildDateRangeIso(state.activityDateTo, { endOfDay: true }));
  }
  return params;
}

function buildActivityExportFilename() {
  const fragments = ["audit"];
  if (state.activityFilter && state.activityFilter !== "all") {
    fragments.push(state.activityFilter);
  }
  if (state.activityQuery) {
    fragments.push(slugifyValue(state.activityQuery, "search"));
  }
  if (state.activityDateFrom) {
    fragments.push(`from-${state.activityDateFrom}`);
  }
  if (state.activityDateTo) {
    fragments.push(`to-${state.activityDateTo}`);
  }
  fragments.push(new Date().toISOString().slice(0, 10));
  return `${fragments.join("-")}.json`;
}

async function fetchActivityExport() {
  const params = buildActivityQueryParams({ limit: 1000 });
  const payload = await api(`/dashboard/activity/export?${params.toString()}`);
  return {
    exported_at: new Date().toISOString(),
    filters: {
      query: payload.query || "",
      status: payload.status_scope || "all",
      started_after: payload.started_after || "",
      ended_before: payload.ended_before || "",
    },
    total: payload.total || 0,
    exported_count: payload.exported_count || 0,
    truncated: Boolean(payload.truncated),
    items: payload.items || [],
  };
}

function getCurrentActivityViewDraft() {
  return {
    query: state.activityQuery,
    status: state.activityFilter,
    dateFrom: state.activityDateFrom,
    dateTo: state.activityDateTo,
  };
}

function hasActiveActivityFilters() {
  return Boolean(
    state.activityQuery ||
      state.activityFilter !== "all" ||
      state.activityDateFrom ||
      state.activityDateTo,
  );
}

function isSameActivityView(left, right) {
  return (
    String(left?.query || "") === String(right?.query || "") &&
    String(left?.status || "all") === String(right?.status || "all") &&
    String(left?.dateFrom || "") === String(right?.dateFrom || "") &&
    String(left?.dateTo || "") === String(right?.dateTo || "")
  );
}

function isSavedActivityViewActive(view) {
  return isSameActivityView(view, getCurrentActivityViewDraft());
}

function buildActivityGroupExportPayload(group) {
  const latestTimestamp = group.latest_timestamp || group.latestTimestamp || "";
  const stepCount = Number(group.step_count ?? group.stepCount ?? 0);
  const eventCount = Number(group.event_count ?? group.eventCount ?? (group.entries || []).length);
  const hasLinkedFlow = Boolean(group.has_linked_flow ?? group.hasLinkedFlow);
  return {
    exported_at: new Date().toISOString(),
    filters: getCurrentActivityViewDraft(),
    flow: {
      key: group.key,
      title: group.title,
      latest_timestamp: latestTimestamp,
      event_count: eventCount,
      step_count: stepCount,
      has_linked_flow: hasLinkedFlow,
    },
    items: group.entries || [],
  };
}

function buildActivityGroupExportFilename(group) {
  const title = slugifyValue(group.title || "flow", "flow");
  const latestTimestamp = String(group.latest_timestamp || group.latestTimestamp || "").slice(0, 10);
  return `${title}-${latestTimestamp || new Date().toISOString().slice(0, 10)}.json`;
}

function findActivityGroupByKey(groupKey) {
  const groups = state.activityGroups.length ? state.activityGroups : groupActivityEntries(state.recentActions);
  return groups.find((group) => String(group.key) === String(groupKey)) || null;
}

async function copyActivityExport(button) {
  try {
    const payload = await fetchActivityExport();
    await copyTextToClipboard(JSON.stringify(payload, null, 2));
    flashButtonLabel(button, payload.truncated ? "Copied 1000" : "Copied");
  } catch {
    flashButtonLabel(button, "Failed");
  }
}

async function downloadActivityExport(button) {
  try {
    const payload = await fetchActivityExport();
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = buildActivityExportFilename();
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(href);
    flashButtonLabel(button, payload.truncated ? "Downloaded 1000" : "Downloaded");
  } catch {
    flashButtonLabel(button, "Failed");
  }
}

async function copyActivityGroupExport(groupKey, button) {
  const group = findActivityGroupByKey(groupKey);
  if (!group) {
    flashButtonLabel(button, "Missing");
    return;
  }

  try {
    await copyTextToClipboard(JSON.stringify(buildActivityGroupExportPayload(group), null, 2));
    flashButtonLabel(button, "Copied");
  } catch {
    flashButtonLabel(button, "Failed");
  }
}

function downloadActivityGroupExport(groupKey, button) {
  const group = findActivityGroupByKey(groupKey);
  if (!group) {
    flashButtonLabel(button, "Missing");
    return;
  }

  try {
    const payload = buildActivityGroupExportPayload(group);
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = buildActivityGroupExportFilename(group);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(href);
    flashButtonLabel(button, "Downloaded");
  } catch {
    flashButtonLabel(button, "Failed");
  }
}

async function saveCurrentActivityView(button) {
  const draft = normalizeSavedActivityView(getCurrentActivityViewDraft());
  const existing = state.activitySavedViews.find((view) => isSameActivityView(view, draft));
  const suggestedLabel = existing?.label || buildSavedActivityViewLabel(draft);
  const label = window.prompt("Name this audit view", suggestedLabel);
  if (label === null) {
    flashButtonLabel(button, "Canceled");
    return;
  }

  const savedView = normalizeSavedActivityView({
    ...draft,
    id: existing?.id,
    label: label.trim() || suggestedLabel,
  });
  state.activitySavedViews = [
    savedView,
    ...state.activitySavedViews.filter((view) => view.id !== savedView.id),
  ].slice(0, 8);
  saveActivitySavedViews();
  renderActivity(state.recentActions);
  flashButtonLabel(button, existing ? "Updated" : "Saved");
}

async function applySavedActivityView(viewId) {
  const view = state.activitySavedViews.find((candidate) => candidate.id === viewId);
  if (!view) {
    return;
  }

  state.activityQuery = view.query;
  state.activityFilter = view.status;
  state.activityDateFrom = view.dateFrom;
  state.activityDateTo = view.dateTo;
  state.expandedActivityEvents = {};
  await refreshActivity();
}

function removeSavedActivityView(viewId) {
  state.activitySavedViews = state.activitySavedViews.filter((view) => view.id !== viewId);
  saveActivitySavedViews();
  renderActivity(state.recentActions);
}

async function copyPreviewValue(encodedValue, button) {
  const previewValue = decodeURIComponent(encodedValue || "");
  try {
    await copyTextToClipboard(previewValue);
    flashButtonLabel(button, "Copied");
  } catch {
    flashButtonLabel(button, "Failed");
  }
}

async function copyInspectionCsv(scope, button) {
  const availability = buildInspectionTableExport(scope);
  if (!availability) {
    flashButtonLabel(button, "Unavailable");
    return;
  }

  try {
    const table = await fetchInspectionTableExport(scope);
    if (!table) {
      flashButtonLabel(button, "Unavailable");
      return;
    }
    await copyTextToClipboard(buildCsvText(table.headers, table.rows));
    flashButtonLabel(button, "Copied");
  } catch {
    flashButtonLabel(button, "Failed");
  }
}

async function downloadInspectionCsv(scope, button) {
  const availability = buildInspectionTableExport(scope);
  if (!availability) {
    flashButtonLabel(button, "Unavailable");
    return;
  }

  try {
    const table = await fetchInspectionTableExport(scope);
    if (!table) {
      flashButtonLabel(button, "Unavailable");
      return;
    }

    const safeTitle = (state.selectedDocument?.title || "document")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    const label = scope === "focus" ? "focus" : "inspection";
    const csvText = buildCsvText(table.headers, table.rows);
    const blob = new Blob([csvText], { type: "text/csv;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = `${safeTitle || "document"}-${label}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(href);
    flashButtonLabel(button, "Downloaded");
  } catch {
    flashButtonLabel(button, "Failed");
  }
}

function setConnectionStatus(text, mode) {
  const target = document.getElementById("connection-status");
  target.textContent = text;
  target.classList.remove("online", "offline");
  if (mode) {
    target.classList.add(mode);
  }
}

function renderStaticLists() {
  renderList(
    "permission-list",
    permissionItems.map(
      ([title, description]) => `
        <article class="stack-card">
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(description)}</span>
        </article>
      `,
    ),
  );

  renderList(
    "phase-list",
    phases.map(
      ([title, description]) => `
        <article class="phase-card">
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(description)}</span>
        </article>
      `,
    ),
  );

  renderList(
    "quick-prompts",
    quickPrompts.map(
      (prompt) => `
        <button class="ghost-button quick-prompt" type="button" data-prompt="${escapeHtml(prompt)}">
          ${escapeHtml(prompt)}
        </button>
      `,
    ),
  );
}

function renderList(targetId, items) {
  const markup = Array.isArray(items) ? items.join("") : String(items ?? "");
  document.getElementById(targetId).innerHTML = sanitizeMarkup(markup);
}

function sanitizeMarkup(markup) {
  return markup.replaceAll("\u00c2\u00b7", "/");
}

function renderSecurityWarning(security, subjectLabel, options = {}) {
  if (!security || !security.prompt_injection_detected) {
    return "";
  }

  const removedLineCount = Number(security.removed_line_count || security.flag_count || 0);
  const flagLabels = Array.isArray(security.flag_labels) ? security.flag_labels.filter(Boolean).slice(0, 3) : [];
  const chips = [];
  if (removedLineCount > 0) {
    chips.push(
      `<span class="meta-chip">${escapeHtml(`${removedLineCount} line${removedLineCount === 1 ? "" : "s"} removed`)}</span>`,
    );
  }
  flagLabels.forEach((label) => {
    chips.push(`<span class="meta-chip">${escapeHtml(label)}</span>`);
  });

  const notice = String(security.notice || "").trim() || `${subjectLabel} contained suspicious instruction-like text.`;
  const detail = String(options.detail || "").trim();

  return `
    <section class="security-warning">
      <strong>${escapeHtml(options.title || "Sanitized warning")}</strong>
      <p>${escapeHtml(notice)}</p>
      ${detail ? `<p>${escapeHtml(detail)}</p>` : ""}
      ${chips.length ? `<div class="stack-meta">${chips.join("")}</div>` : ""}
    </section>
  `;
}

function renderAggregateSecurityWarning(count, subjectLabel = "source") {
  const normalizedCount = Number(count || 0);
  if (normalizedCount <= 0) {
    return "";
  }

  return `
    <section class="security-warning">
      <strong>Sanitized sources</strong>
      <p>${escapeHtml(`Suspicious instruction-like text was removed from ${normalizedCount} ${subjectLabel}${normalizedCount === 1 ? "" : "s"} before this research brief was composed.`)}</p>
      <div class="stack-meta">
        <span class="meta-chip">${escapeHtml(`${normalizedCount} ${subjectLabel}${normalizedCount === 1 ? "" : "s"} sanitized`)}</span>
      </div>
    </section>
  `;
}

function getSecretFieldMeta(key) {
  return state.secretsInfo?.fields?.[key] || {
    configured: false,
    source: "unset",
    masked_value: "",
    stored_in_vault: false,
  };
}

function formatSecretSource(meta) {
  if (!meta || !meta.configured) {
    return "Currently unset";
  }
  if (meta.source === "vault") {
    return `Stored in encrypted vault as ${meta.masked_value || "configured"}`;
  }
  if (meta.source === "environment") {
    return `Using environment value ${meta.masked_value || "configured"}`;
  }
  return "Currently unset";
}

function addTransientAssistantMessage(message) {
  if (!state.memoryEnabled && message) {
    state.transientHistory.push({ role: "assistant", content: message });
  }
}

function renderHistory(history) {
  state.lastHistory = Array.isArray(history) ? history : [];
  const activeHistory = state.memoryEnabled ? history : state.transientHistory;

  if (!activeHistory.length) {
    const emptyTitle = state.memoryEnabled ? "No conversation yet" : "Memory is off for this session";
    const emptyCopy = state.memoryEnabled
      ? "Start with a system check, a search request, or a note capture prompt."
      : "New turns stay only in this browser tab until you re-enable memory.";

    renderList(
      "chat-thread",
      [
        `
          <article class="empty-card">
            <strong>${escapeHtml(emptyTitle)}</strong>
            <span>${escapeHtml(emptyCopy)}</span>
          </article>
        `,
      ],
    );
    return;
  }

  const markup = activeHistory.map((turn) => {
    const role = turn.role === "user" ? "You" : state.assistantName;
    const bubbleClass = turn.role === "user" ? "chat-bubble user" : "chat-bubble assistant";
    return `
      <article class="${bubbleClass}">
        <span class="chat-role">${escapeHtml(role)}</span>
        <p>${escapeHtml(turn.content)}</p>
      </article>
    `;
  });

  renderList("chat-thread", markup);
  const thread = document.getElementById("chat-thread");
  thread.scrollTop = thread.scrollHeight;
  renderVoiceControls();
}

function legacyGroupPendingActions(actions) {
  const groups = [];
  const grouped = new Map();

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

function legacyRenderPendingActionControls(action) {
  return `
    <div class="approval-actions">
      <button class="secondary-button" type="button" data-action="confirm" data-id="${escapeHtml(action.action_id)}">
        Approve
      </button>
      <button class="ghost-button" type="button" data-action="reject" data-id="${escapeHtml(action.action_id)}">
        Reject
      </button>
    </div>
  `;
}

function legacyRenderPendingActionItem(action, options = {}) {
  const compact = options.compact === true;
  const wrapperClass = compact ? "stack-card pending-child-card" : "stack-card";
  const titleTag = compact ? "span" : "strong";
  return `
    <article class="${wrapperClass}">
      <${titleTag}>${escapeHtml(action.summary)}</${titleTag}>
      <span>${escapeHtml(action.tool_name)} · ${escapeHtml(action.permission_level)}</span>
      <div class="stack-meta">
        <span class="meta-chip">${escapeHtml(action.category)}</span>
        <span class="meta-chip">${escapeHtml(action.approval_mode)}</span>
      </div>
      ${legacyRenderPendingActionControls(action)}
    </article>
  `;
}

function legacyRenderPending(actions) {
  const badge = document.getElementById("pending-badge");
  badge.textContent = `${actions.length} waiting`;

  if (!actions.length) {
    renderList(
      "pending-list",
      [
        `
          <article class="empty-card">
            <strong>No approvals waiting</strong>
            <span>Requests that change state will appear here before they execute.</span>
          </article>
        `,
      ],
    );
    return;
  }

  renderList(
    "pending-list",
    actions.map(
      (action) => `
        <article class="stack-card">
          <strong>${escapeHtml(action.summary)}</strong>
          <span>${escapeHtml(action.tool_name)} · ${escapeHtml(action.permission_level)}</span>
          <div class="stack-meta">
            <span class="meta-chip">${escapeHtml(action.category)}</span>
            <span class="meta-chip">${escapeHtml(action.approval_mode)}</span>
          </div>
          <div class="approval-actions">
            <button class="secondary-button" type="button" data-action="confirm" data-id="${escapeHtml(action.action_id)}">
              Approve
            </button>
            <button class="ghost-button" type="button" data-action="reject" data-id="${escapeHtml(action.action_id)}">
              Reject
            </button>
          </div>
        </article>
      `,
    ),
  );
}

function groupPendingActions(actions) {
  const groups = [];
  const grouped = new Map();

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

function getPendingStepNumber(action) {
  return Number(action.sequence_index || 0) + 1;
}

function getDependencyStepNumber(action, siblingActions = []) {
  if (!action.depends_on_action_id) {
    return 0;
  }

  const dependency = siblingActions.find((candidate) => candidate.action_id === action.depends_on_action_id);
  return dependency ? getPendingStepNumber(dependency) : 0;
}

function renderPendingBranchSummary(actions) {
  const dependencyGroups = new Map();
  actions.forEach((action) => {
    if (!action.depends_on_action_id) {
      return;
    }
    const dependencyStep = getDependencyStepNumber(action, actions);
    const key = String(dependencyStep || action.depends_on_action_id);
    if (!dependencyGroups.has(key)) {
      dependencyGroups.set(key, { dependencyStep, steps: [] });
    }
    dependencyGroups.get(key).steps.push(getPendingStepNumber(action));
  });

  if (!dependencyGroups.size) {
    return "";
  }

  const fragments = Array.from(dependencyGroups.values())
    .map((group) => {
      const stepList = group.steps.map((step) => `step ${step}`);
      const dependentCopy =
        stepList.length === 1
          ? stepList[0]
          : `${stepList.slice(0, -1).join(", ")} and ${stepList[stepList.length - 1]}`;
      return `${dependentCopy} depend on step ${group.dependencyStep || "?"}`;
    })
    .join("; ");
  return `Dependency branches: ${fragments}.`;
}

function renderPendingActionControls(action) {
  if (action.status === "queued") {
    return `
      <div class="approval-actions">
        <button class="ghost-button" type="button" data-action="reject" data-id="${escapeHtml(action.action_id)}">
          Remove
        </button>
      </div>
    `;
  }

  return `
    <div class="approval-actions">
      <button class="secondary-button" type="button" data-action="confirm" data-id="${escapeHtml(action.action_id)}">
        Approve
      </button>
      <button class="ghost-button" type="button" data-action="reject" data-id="${escapeHtml(action.action_id)}">
        Reject
      </button>
    </div>
  `;
}

function renderPendingActionItem(action, options = {}) {
  const compact = options.compact === true;
  const siblingActions = options.siblingActions || [];
  const wrapperClass = compact ? "stack-card pending-child-card" : "stack-card";
  const titleTag = compact ? "span" : "strong";
  const stepNumber = getPendingStepNumber(action);
  const dependencyStep = getDependencyStepNumber(action, siblingActions);
  const dependencyCopy = action.status === "queued"
    ? `Waiting for step ${dependencyStep || "?"} to be approved first.`
    : dependencyStep
      ? `Depends on step ${dependencyStep}.`
      : "";
  return `
    <article class="${wrapperClass}">
      <${titleTag}>${escapeHtml(action.summary)}</${titleTag}>
      <span>${escapeHtml(action.tool_name)} · ${escapeHtml(action.permission_level)}</span>
      <div class="stack-meta">
        <span class="meta-chip">${escapeHtml(`step ${stepNumber}`)}</span>
        <span class="meta-chip">${escapeHtml(action.category)}</span>
        <span class="meta-chip">${escapeHtml(action.approval_mode)}</span>
        <span class="meta-chip">${escapeHtml(action.status)}</span>
      </div>
      ${dependencyCopy ? `<p>${escapeHtml(dependencyCopy)}</p>` : ""}
      ${renderPendingActionControls(action)}
    </article>
  `;
}

function renderPending(actions) {
  const badge = document.getElementById("pending-badge");
  badge.textContent = `${actions.length} waiting`;

  if (!actions.length) {
    renderList(
      "pending-list",
      [
        `
          <article class="empty-card">
            <strong>No approvals waiting</strong>
            <span>Requests that change state will appear here before they execute.</span>
          </article>
        `,
      ],
    );
    return;
  }

  const groups = groupPendingActions(actions);
  renderList(
    "pending-list",
    groups.map((group) => {
      if (!group.groupId || group.actions.length === 1) {
        return renderPendingActionItem(group.actions[0]);
      }

      const label = group.groupSummary || "Multi-step request";
      const rootSteps = group.actions.filter((action) => !action.depends_on_action_id).length;
      const dependentSteps = group.actions.length - rootSteps;
      const branchSummary = renderPendingBranchSummary(group.actions);
      return `
        <article class="stack-card">
          <strong>${escapeHtml(label)}</strong>
          <span>${escapeHtml(`${group.actions.length} linked approvals`)}</span>
          <div class="stack-meta">
            <span class="meta-chip">grouped approval</span>
            <span class="meta-chip">${escapeHtml(`${rootSteps} root`)}</span>
            <span class="meta-chip">${escapeHtml(`${dependentSteps} dependent`)}</span>
            <span class="meta-chip">${escapeHtml(group.groupId.slice(0, 8))}</span>
          </div>
          ${branchSummary ? `<p>${escapeHtml(branchSummary)}</p>` : ""}
          <div class="approval-actions">
            <button
              class="secondary-button"
              type="button"
              data-group-action="confirm"
              data-group-id="${escapeHtml(group.groupId)}"
            >
              Approve all
            </button>
            <button
              class="ghost-button"
              type="button"
              data-group-action="reject"
              data-group-id="${escapeHtml(group.groupId)}"
            >
              Reject all
            </button>
          </div>
          <div class="stack-list compact-list pending-group-list">
            ${group.actions.map((action) => renderPendingActionItem(action, { compact: true, siblingActions: group.actions })).join("")}
          </div>
        </article>
      `;
    }),
  );
}

function formatActivityPrerequisiteLabel(trace) {
  if (!trace || !trace.prerequisite_action_id) {
    return "";
  }

  const stepLabel = trace.prerequisite_step_number ? `step ${trace.prerequisite_step_number}` : "an earlier step";
  if (!trace.prerequisite_summary) {
    return stepLabel;
  }
  return `${stepLabel} (${trace.prerequisite_summary})`;
}

function describePrerequisiteOutcome(status) {
  switch (status) {
    case "executed":
      return "completed";
    case "failed":
      return "failed";
    case "blocked":
      return "was blocked";
    case "rejected":
      return "was rejected";
    case "proposed":
      return "is still waiting for approval";
    case "queued":
      return "is still queued";
    default:
      return "did not complete";
  }
}

function renderActivityDependencyCopy(entry) {
  const trace = entry.trace || {};
  const prerequisiteLabel = formatActivityPrerequisiteLabel(trace);
  if (!prerequisiteLabel) {
    return "";
  }

  const prerequisiteOutcome = describePrerequisiteOutcome(trace.prerequisite_status);
  switch (entry.status) {
    case "queued":
      return `Queued behind ${prerequisiteLabel}.`;
    case "proposed":
      return trace.prerequisite_status === "executed"
        ? `Unlocked after ${prerequisiteLabel} completed and is now waiting for approval.`
        : `Depends on ${prerequisiteLabel}.`;
    case "executed":
      return `Ran after ${prerequisiteLabel} completed.`;
    case "failed":
      return `Ran after ${prerequisiteLabel} completed, but this step failed.`;
    case "blocked":
      return `Blocked because ${prerequisiteLabel} ${prerequisiteOutcome}.`;
    case "rejected":
      return `Removed because ${prerequisiteLabel} ${prerequisiteOutcome}.`;
    default:
      return `Depends on ${prerequisiteLabel}.`;
  }
}

function renderActivityDetail(entry) {
  const trace = entry.trace || {};
  const detail = entry.error || entry.result?.message || "";
  if (!detail) {
    return "";
  }

  if (trace.dependency_reason && detail === trace.dependency_reason) {
    return "";
  }

  if (entry.status === "rejected" && trace.prerequisite_action_id && detail === "Action rejected. No changes were made.") {
    return "";
  }

  return detail;
}

function getActivityEventKey(entry) {
  return `${entry.action?.action_id || "activity"}:${entry.status || "unknown"}:${entry.timestamp || ""}`;
}

function hasStructuredPayload(value) {
  if (value === null || value === undefined) {
    return false;
  }
  if (Array.isArray(value)) {
    return value.length > 0;
  }
  if (typeof value === "object") {
    return Object.keys(value).length > 0;
  }
  return Boolean(String(value));
}

function getActivityDetailSections(entry) {
  const sections = [];
  const argumentsPayload = entry.action?.arguments || {};
  if (hasStructuredPayload(argumentsPayload)) {
    sections.push(["Arguments", argumentsPayload]);
  }

  if (hasStructuredPayload(entry.decision)) {
    sections.push(["Policy", entry.decision]);
  }

  if (hasStructuredPayload(entry.result)) {
    sections.push(["Result", entry.result]);
  }

  if (entry.error) {
    sections.push(["Error", { message: entry.error }]);
  }

  if (hasStructuredPayload(entry.trace)) {
    sections.push(["Trace", entry.trace]);
  }

  return sections;
}

function renderActivityDetailPanel(entry) {
  const eventKey = getActivityEventKey(entry);
  if (!state.expandedActivityEvents[eventKey]) {
    return "";
  }

  const sections = getActivityDetailSections(entry);
  if (!sections.length) {
    return "";
  }

  return `
    <section class="activity-detail-panel">
      ${sections
        .map(
          ([label, payload]) => `
            <article class="activity-detail-section">
              <strong>${escapeHtml(label)}</strong>
              <pre>${escapeHtml(JSON.stringify(payload, null, 2))}</pre>
            </article>
          `,
        )
        .join("")}
    </section>
  `;
}

function matchesActivityFilter(entry, filter) {
  const status = String(entry.status || "");
  switch (filter) {
    case "attention":
      return ["failed", "blocked", "rejected"].includes(status);
    case "approval":
      return ["proposed", "queued"].includes(status);
    case "executed":
      return status === "executed";
    default:
      return true;
  }
}

function getActivityGroupKey(entry) {
  return entry.trace?.group_id || entry.action?.group_id || entry.action?.action_id || `${entry.timestamp}:${entry.action?.summary || "activity"}`;
}

function groupActivityEntries(actions) {
  const grouped = new Map();

  actions.forEach((entry) => {
    const key = getActivityGroupKey(entry);
    if (!grouped.has(key)) {
      grouped.set(key, {
        key,
        title: entry.trace?.group_summary || entry.action?.group_summary || entry.action?.summary || "Activity",
        entries: [],
      });
    }
    grouped.get(key).entries.push(entry);
  });

  return Array.from(grouped.values())
    .map((group) => {
      const entries = [...group.entries].sort(
        (left, right) => new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime(),
      );
      const latestTimestamp = entries.reduce((latest, entry) => {
        const next = new Date(entry.timestamp).getTime();
        return Number.isNaN(next) ? latest : Math.max(latest, next);
      }, 0);
      const uniqueSteps = new Set(
        entries
          .map((entry) => entry.trace?.step_number)
          .filter((stepNumber) => typeof stepNumber === "number"),
      );
      return {
        ...group,
        entries,
        latestTimestamp,
        stepCount: uniqueSteps.size,
        hasLinkedFlow: entries.some((entry) => Boolean(entry.trace?.group_id)),
      };
    })
    .sort((left, right) => right.latestTimestamp - left.latestTimestamp);
}

function renderActivityToolbar(actions, groups) {
  const items = activityFilterItems.map(([value, label]) => `
    <button
      class="ghost-button activity-filter-button ${state.activityFilter === value ? "is-active" : ""}"
      type="button"
      data-activity-filter="${escapeHtml(value)}"
    >
      ${escapeHtml(label)}
    </button>
  `);
  const savedViewsMarkup = state.activitySavedViews.length
    ? `
      <div class="activity-saved-views">
        <span class="activity-saved-label">Saved views</span>
        <div class="activity-saved-list">
          ${state.activitySavedViews
            .map((view) => {
              const isActive = isSavedActivityViewActive(view);
              return `
                <div class="activity-saved-chip ${isActive ? "is-active" : ""}">
                  <button
                    class="activity-saved-view-button"
                    type="button"
                    data-activity-view-action="apply"
                    data-activity-view-id="${escapeHtml(view.id)}"
                  >
                    ${escapeHtml(view.label)}
                  </button>
                  <button
                    class="activity-saved-remove-button"
                    type="button"
                    title="Remove saved view"
                    aria-label="${escapeHtml(`Remove ${view.label}`)}"
                    data-activity-view-action="remove"
                    data-activity-view-id="${escapeHtml(view.id)}"
                  >
                    x
                  </button>
                </div>
              `;
            })
            .join("")}
        </div>
      </div>
    `
    : "";

  document.getElementById("activity-toolbar").innerHTML = sanitizeMarkup(`
    <div class="activity-toolbar-row">
      ${items.join("")}
    </div>
    <div class="stack-meta activity-toolbar-meta">
      <span class="meta-chip">${escapeHtml(`${groups.length} loaded flow${groups.length === 1 ? "" : "s"}`)}</span>
      <span class="meta-chip">${escapeHtml(`${state.activityGroupTotal} matched flow${state.activityGroupTotal === 1 ? "" : "s"}`)}</span>
      <span class="meta-chip">${escapeHtml(`${actions.length} loaded`)}</span>
      <span class="meta-chip">${escapeHtml(`${state.activityTotal} matched`)}</span>
      ${state.activityQuery ? `<span class="meta-chip">${escapeHtml(`search: ${state.activityQuery}`)}</span>` : ""}
      ${state.activityDateFrom ? `<span class="meta-chip">${escapeHtml(`from: ${state.activityDateFrom}`)}</span>` : ""}
      ${state.activityDateTo ? `<span class="meta-chip">${escapeHtml(`to: ${state.activityDateTo}`)}</span>` : ""}
      <span class="meta-chip">grouped by request flow</span>
    </div>
    ${savedViewsMarkup}
  `);
}

function renderActivityControls() {
  const searchInput = document.getElementById("activity-search-input");
  if (searchInput && searchInput.value !== state.activityQuery) {
    searchInput.value = state.activityQuery;
  }

  const dateFromInput = document.getElementById("activity-date-from");
  if (dateFromInput && dateFromInput.value !== state.activityDateFrom) {
    dateFromInput.value = state.activityDateFrom;
  }

  const dateToInput = document.getElementById("activity-date-to");
  if (dateToInput && dateToInput.value !== state.activityDateTo) {
    dateToInput.value = state.activityDateTo;
  }

  const clearButton = document.getElementById("clear-activity-search");
  if (clearButton) {
    clearButton.disabled =
      !state.activityQuery &&
      state.activityFilter === "all" &&
      !state.activityDateFrom &&
      !state.activityDateTo;
  }

  const copyButton = document.getElementById("copy-activity-export");
  if (copyButton) {
    copyButton.disabled = state.activityLoading || state.activityTotal === 0;
  }

  const downloadButton = document.getElementById("download-activity-export");
  if (downloadButton) {
    downloadButton.disabled = state.activityLoading || state.activityTotal === 0;
  }

  const saveViewButton = document.getElementById("save-activity-view");
  if (saveViewButton) {
    saveViewButton.disabled = state.activityLoading;
  }

  const loadMoreButton = document.getElementById("load-more-activity");
  if (!loadMoreButton) {
    return;
  }

  if (state.activityLoading) {
    loadMoreButton.textContent = "Loading";
    loadMoreButton.disabled = true;
    loadMoreButton.hidden = false;
    return;
  }

  loadMoreButton.textContent = "Load more";
  loadMoreButton.disabled = !state.activityHasMore;
  loadMoreButton.hidden = !state.activityHasMore;
}

function renderActivityGroup(group) {
  const latestDate = group.latestTimestamp ? new Date(group.latestTimestamp).toLocaleString() : "Unknown time";
  const headerCopy =
    group.entries.length === 1
      ? `1 update · latest ${latestDate}`
      : `${group.entries.length} updates · latest ${latestDate}`;

  const groupMeta = [
    group.hasLinkedFlow ? "grouped flow" : "single action",
    group.stepCount ? `${group.stepCount} step${group.stepCount === 1 ? "" : "s"}` : "",
  ].filter(Boolean);

  const eventsMarkup = group.entries
    .map((entry) => {
      const status = entry.status || "unknown";
      const chipClass =
        status === "failed" || status === "rejected" || status === "blocked" ? "meta-chip danger" : "meta-chip";
      const trace = entry.trace || {};
      const eventKey = getActivityEventKey(entry);
      const hasDetails = getActivityDetailSections(entry).length > 0;
      const isExpanded = Boolean(state.expandedActivityEvents[eventKey]);
      const dependencyCopy = renderActivityDependencyCopy(entry);
      const detailCopy = renderActivityDetail(entry);
      const detailClass =
        status === "failed" || status === "blocked" || status === "rejected"
          ? "activity-note is-danger"
          : "activity-note";
      const stepLabel = trace.step_number ? `Step ${trace.step_number} · ` : "";

      return `
        <article class="activity-event-card">
          <div class="activity-event-head">
            <strong>${escapeHtml(`${stepLabel}${entry.action.summary}`.replaceAll("Â·", "-"))}</strong>
            <span>${escapeHtml(new Date(entry.timestamp).toLocaleString())}</span>
          </div>
          <div class="stack-meta">
            <span class="${chipClass}">${escapeHtml(status)}</span>
            <span class="meta-chip">${escapeHtml(entry.action.tool_name)}</span>
            ${trace.prerequisite_step_number ? `<span class="meta-chip">${escapeHtml(`after step ${trace.prerequisite_step_number}`)}</span>` : ""}
          </div>
          ${dependencyCopy ? `<p class="activity-note is-quiet">${escapeHtml(dependencyCopy)}</p>` : ""}
          ${detailCopy ? `<p class="${detailClass}">${escapeHtml(detailCopy)}</p>` : ""}
          ${
            hasDetails
              ? `
                <div class="activity-event-actions">
                  <button
                    class="ghost-button activity-detail-toggle"
                    type="button"
                    data-activity-event-toggle="${escapeHtml(eventKey)}"
                  >
                    ${isExpanded ? "Hide details" : "Show details"}
                  </button>
                </div>
              `
              : ""
          }
          ${renderActivityDetailPanel(entry)}
        </article>
      `;
    })
    .join("");

  return `
    <article class="stack-card activity-group-card">
      <strong>${escapeHtml(group.title)}</strong>
      <p>${escapeHtml(headerCopy.replaceAll("Â·", "-"))}</p>
      <div class="stack-meta">
        ${groupMeta.map((item) => `<span class="meta-chip">${escapeHtml(item)}</span>`).join("")}
      </div>
      <div class="activity-group-events">
        ${eventsMarkup}
      </div>
    </article>
  `;
}

function renderActivityFlowGroup(group) {
  const latestTimestamp = group.latest_timestamp || group.latestTimestamp || "";
  const latestDate = latestTimestamp ? new Date(latestTimestamp).toLocaleString() : "Unknown time";
  const eventCount = Number(group.event_count ?? group.eventCount ?? (group.entries || []).length);
  const stepCount = Number(group.step_count ?? group.stepCount ?? 0);
  const hasLinkedFlow = Boolean(group.has_linked_flow ?? group.hasLinkedFlow);
  const headerCopy = eventCount === 1 ? `1 update - latest ${latestDate}` : `${eventCount} updates - latest ${latestDate}`;

  const groupMeta = [
    hasLinkedFlow ? "grouped flow" : "single action",
    stepCount ? `${stepCount} step${stepCount === 1 ? "" : "s"}` : "",
  ].filter(Boolean);

  const eventsMarkup = (group.entries || [])
    .map((entry) => {
      const status = entry.status || "unknown";
      const chipClass =
        status === "failed" || status === "rejected" || status === "blocked" ? "meta-chip danger" : "meta-chip";
      const trace = entry.trace || {};
      const eventKey = getActivityEventKey(entry);
      const hasDetails = getActivityDetailSections(entry).length > 0;
      const isExpanded = Boolean(state.expandedActivityEvents[eventKey]);
      const dependencyCopy = renderActivityDependencyCopy(entry);
      const detailCopy = renderActivityDetail(entry);
      const detailClass =
        status === "failed" || status === "blocked" || status === "rejected"
          ? "activity-note is-danger"
          : "activity-note";
      const stepLabel = trace.step_number ? `Step ${trace.step_number} - ` : "";

      return `
        <article class="activity-event-card">
          <div class="activity-event-head">
            <strong>${escapeHtml(`${stepLabel}${entry.action.summary}`)}</strong>
            <span>${escapeHtml(new Date(entry.timestamp).toLocaleString())}</span>
          </div>
          <div class="stack-meta">
            <span class="${chipClass}">${escapeHtml(status)}</span>
            <span class="meta-chip">${escapeHtml(entry.action.tool_name)}</span>
            ${trace.prerequisite_step_number ? `<span class="meta-chip">${escapeHtml(`after step ${trace.prerequisite_step_number}`)}</span>` : ""}
          </div>
          ${dependencyCopy ? `<p class="activity-note is-quiet">${escapeHtml(dependencyCopy)}</p>` : ""}
          ${detailCopy ? `<p class="${detailClass}">${escapeHtml(detailCopy)}</p>` : ""}
          ${
            hasDetails
              ? `
                <div class="activity-event-actions">
                  <button
                    class="ghost-button activity-detail-toggle"
                    type="button"
                    data-activity-event-toggle="${escapeHtml(eventKey)}"
                  >
                    ${isExpanded ? "Hide details" : "Show details"}
                  </button>
                </div>
              `
              : ""
          }
          ${renderActivityDetailPanel(entry)}
        </article>
      `;
    })
    .join("");

  return `
    <article class="stack-card activity-group-card">
      <div class="activity-group-head">
        <div class="activity-group-copy">
          <strong>${escapeHtml(group.title)}</strong>
          <p>${escapeHtml(headerCopy)}</p>
        </div>
        <div class="activity-group-actions">
          <button
            class="ghost-button activity-group-button"
            type="button"
            data-activity-group-action="copy"
            data-activity-group-key="${escapeHtml(group.key)}"
          >
            Copy flow JSON
          </button>
          <button
            class="ghost-button activity-group-button"
            type="button"
            data-activity-group-action="download"
            data-activity-group-key="${escapeHtml(group.key)}"
          >
            Download flow JSON
          </button>
        </div>
      </div>
      <div class="stack-meta">
        ${groupMeta.map((item) => `<span class="meta-chip">${escapeHtml(item)}</span>`).join("")}
      </div>
      <div class="activity-group-events">
        ${eventsMarkup}
      </div>
    </article>
  `;
}

function renderActivity(actions) {
  const groups = state.activityGroups.length ? state.activityGroups : groupActivityEntries(actions);
  renderActivityToolbar(actions, groups);
  renderActivityControls();

  if (!actions.length) {
    const emptyTitle = hasActiveActivityFilters() ? "No matching activity" : "No activity yet";
    const emptyCopy = hasActiveActivityFilters()
      ? "The current audit view does not match any request flows."
      : "Executed, blocked, and rejected actions will be logged here.";
    renderList(
      "activity-list",
      [
        `
          <article class="empty-card">
            <strong>${escapeHtml(emptyTitle)}</strong>
            <span>${escapeHtml(emptyCopy)}</span>
          </article>
        `,
      ],
    );
    return;
  }

  renderList(
    "activity-list",
    groups.map((group) => renderActivityFlowGroup(group)),
  );
  return;

  renderList(
    "activity-list",
    actions.map((entry) => {
      const status = entry.status || "unknown";
      const chipClass =
        status === "failed" || status === "rejected" || status === "blocked" ? "meta-chip danger" : "meta-chip";
      const trace = entry.trace || {};
      const flowCopy = trace.group_summary ? `Flow: ${trace.group_summary}` : "";
      const dependencyCopy = renderActivityDependencyCopy(entry);
      const detailCopy = renderActivityDetail(entry);
      const detailClass =
        status === "failed" || status === "blocked" || status === "rejected"
          ? "activity-note is-danger"
          : "activity-note";
      return `
        <article class="stack-card">
          <strong>${escapeHtml(entry.action.summary)}</strong>
          <p>${escapeHtml(status)} · ${escapeHtml(new Date(entry.timestamp).toLocaleString())}</p>
          <div class="stack-meta">
            <span class="${chipClass}">${escapeHtml(status)}</span>
            <span class="meta-chip">${escapeHtml(entry.action.tool_name)}</span>
            ${trace.step_number ? `<span class="meta-chip">${escapeHtml(`step ${trace.step_number}`)}</span>` : ""}
            ${trace.group_id ? `<span class="meta-chip">grouped</span>` : ""}
            ${trace.prerequisite_step_number ? `<span class="meta-chip">${escapeHtml(`after step ${trace.prerequisite_step_number}`)}</span>` : ""}
          </div>
          ${flowCopy ? `<p class="activity-note is-quiet">${escapeHtml(flowCopy)}</p>` : ""}
          ${dependencyCopy ? `<p class="activity-note is-quiet">${escapeHtml(dependencyCopy)}</p>` : ""}
          ${detailCopy ? `<p class="${detailClass}">${escapeHtml(detailCopy)}</p>` : ""}
        </article>
      `;
    }),
  );
}

function renderTools(tools) {
  renderList(
    "tool-list",
    tools.map(
      (tool) => `
        <article class="stack-card">
          <strong>${escapeHtml(tool.name)}</strong>
          <p>${escapeHtml(tool.description)}</p>
          <div class="stack-meta">
            <span class="meta-chip">${escapeHtml(tool.category)}</span>
            <span class="meta-chip">${escapeHtml(tool.permission_level)}</span>
          </div>
        </article>
      `,
    ),
  );
}

function renderMemoryPanel() {
  const buttonLabel = state.memoryEnabled ? "Disable memory" : "Enable memory";
  const statusTitle = state.memoryEnabled ? "Memory is enabled" : "Memory is disabled";
  const statusCopy =
    state.memoryStatusMessage ||
    (state.memoryEnabled
      ? "Conversation turns are being saved in local SQLite storage for this session."
      : "New turns will not be written to disk until memory is enabled again, but stored sessions can still be reviewed or deleted.");
  const plannerLabel = state.plannerInfo?.label || "Rule planner";
  const plannerModel = state.plannerInfo?.model ? `<span class="meta-chip">${escapeHtml(state.plannerInfo.model)}</span>` : "";
  const sessions = state.memorySessions || [];
  const sessionMarkup = sessions.length
    ? `
        <div class="memory-session-grid">
          ${sessions
            .map(
              (session) => `
                <article class="stack-card ${session.session_id === state.sessionId ? "is-selected" : ""}">
                  <strong>${escapeHtml(session.session_id === state.sessionId ? "Current browser session" : session.session_id)}</strong>
                  <span>${escapeHtml(session.last_content_preview || "No saved preview yet.")}</span>
                  <div class="stack-meta">
                    <span class="meta-chip">${escapeHtml(`${session.turn_count || 0} turns`)}</span>
                    <span class="meta-chip">${escapeHtml(session.last_role || "unknown")}</span>
                    <span class="meta-chip">${escapeHtml(new Date(session.last_seen_at).toLocaleString())}</span>
                    ${session.session_id === state.sessionId ? '<span class="meta-chip">current</span>' : ""}
                  </div>
                  <div class="approval-actions">
                    <button
                      class="ghost-button"
                      type="button"
                      data-memory-action="prepare-phone-link"
                      data-session-id="${escapeHtml(session.session_id)}"
                    >
                      Prepare phone link
                    </button>
                    <button
                      class="ghost-button danger-button"
                      type="button"
                      data-memory-action="delete-session"
                      data-session-id="${escapeHtml(session.session_id)}"
                    >
                      Delete session
                    </button>
                  </div>
                </article>
              `,
            )
            .join("")}
        </div>
      `
    : `
        <article class="empty-card">
          <strong>No stored sessions yet</strong>
          <span>Once memory is used, recent local sessions will appear here for review and deletion.</span>
        </article>
      `;

  renderList(
    "memory-panel",
    [
      `
        <article class="stack-card">
          <strong>${escapeHtml(statusTitle)}</strong>
          <p>${escapeHtml(statusCopy)}</p>
          <div class="stack-meta">
            <span class="meta-chip">${state.memoryEnabled ? "persistent session" : "transient session"}</span>
            <span class="meta-chip">${escapeHtml(plannerLabel)}</span>
            ${plannerModel}
            <span class="meta-chip">${escapeHtml(state.sessionId)}</span>
            <span class="meta-chip">${escapeHtml(`${sessions.length} stored session${sessions.length === 1 ? "" : "s"}`)}</span>
          </div>
          <div class="approval-actions control-row">
            <button id="toggle-memory" class="secondary-button" type="button">${escapeHtml(buttonLabel)}</button>
            <button id="clear-session" class="ghost-button" type="button">Clear session history</button>
            <button id="refresh-memory-sessions" class="ghost-button" type="button">Refresh sessions</button>
            <button id="clear-all-memory" class="ghost-button danger-button" type="button" ${sessions.length ? "" : "disabled"}>Delete all memory</button>
          </div>
        </article>
        ${sessionMarkup}
      `,
    ],
  );
}

function renderSettingsPanel() {
  const statusCopy =
    state.settingsStatusMessage ||
    "These preferences stay local to this device and survive restarts. Safe mode and memory keep their own quick toggles above.";
  const provider = state.secretsInfo?.provider || {};
  const runtime = state.secretsInfo?.runtime || {};
  const llmApiKey = getSecretFieldMeta("llm_api_key");
  const smtpUsername = getSecretFieldMeta("smtp_username");
  const smtpPassword = getSecretFieldMeta("smtp_password");
  const whatsappAccessToken = getSecretFieldMeta("whatsapp_access_token");
  const whatsappAppSecret = getSecretFieldMeta("whatsapp_app_secret");
  const secretStatusCopy =
    state.secretsStatusMessage ||
    (provider.available
      ? "Sensitive credentials are stored in an encrypted local vault. Leave a field blank to keep its current value."
      : "Encrypted vault storage is unavailable here. Environment variables still work, but secrets cannot be saved from this panel.");
  const secretsDisabled = provider.available ? "" : "disabled";

  renderList(
    "settings-panel",
    [
      `
        <form id="settings-form" class="stack-card settings-form">
          <strong>Local preferences</strong>
          <p>${escapeHtml(statusCopy)}</p>
          <div class="settings-grid">
            <label class="settings-field" for="settings-assistant-name">
              <span>Assistant name</span>
              <input
                id="settings-assistant-name"
                class="settings-input"
                type="text"
                maxlength="32"
                value="${escapeHtml(state.assistantName)}"
              >
            </label>
            <label class="settings-field" for="settings-search-limit">
              <span>Live search results</span>
              <input
                id="settings-search-limit"
                class="settings-input"
                type="number"
                min="1"
                max="10"
                value="${escapeHtml(String(state.liveSearchResultLimit))}"
              >
            </label>
            <label class="settings-field" for="settings-refresh-seconds">
              <span>Auto refresh seconds</span>
              <input
                id="settings-refresh-seconds"
                class="settings-input"
                type="number"
                min="15"
                max="300"
                step="15"
                value="${escapeHtml(String(state.dashboardRefreshSeconds))}"
              >
            </label>
            <label class="settings-field" for="settings-whatsapp-api-version">
              <span>WhatsApp API version</span>
              <input
                id="settings-whatsapp-api-version"
                class="settings-input"
                type="text"
                maxlength="16"
                value="${escapeHtml(state.whatsappApiVersion)}"
                placeholder="v23.0"
              >
            </label>
            <label class="settings-field" for="settings-whatsapp-phone-number-id">
              <span>WhatsApp phone number ID</span>
              <input
                id="settings-whatsapp-phone-number-id"
                class="settings-input"
                type="text"
                maxlength="64"
                value="${escapeHtml(state.whatsappPhoneNumberId)}"
                placeholder="Meta Cloud API phone number ID"
              >
            </label>
            <label class="settings-field" for="settings-whatsapp-verify-token">
              <span>WhatsApp webhook verify token</span>
              <input
                id="settings-whatsapp-verify-token"
                class="settings-input"
                type="text"
                maxlength="128"
                value="${escapeHtml(state.whatsappVerifyToken)}"
                placeholder="Used when Meta verifies your webhook"
              >
            </label>
          </div>
          <section class="settings-section">
            <strong>Browser voice</strong>
            <p>Use browser speech recognition and the system voice locally. Audio stays in the browser unless you explicitly send the resulting text.</p>
            <div class="settings-grid">
              <label class="settings-toggle-card" for="settings-voice-auto-speak">
                <input
                  id="settings-voice-auto-speak"
                  class="settings-checkbox"
                  type="checkbox"
                  ${state.voiceAutoSpeak ? "checked" : ""}
                >
                <span>Read assistant replies aloud</span>
                <span class="field-note">Uses browser speech synthesis after chat replies.</span>
              </label>
              <label class="settings-toggle-card" for="settings-voice-auto-send">
                <input
                  id="settings-voice-auto-send"
                  class="settings-checkbox"
                  type="checkbox"
                  ${state.voiceAutoSend ? "checked" : ""}
                >
                <span>Send captured voice immediately</span>
                <span class="field-note">Otherwise the transcript lands in the composer for review first.</span>
              </label>
              <label class="settings-toggle-card" for="settings-voice-wake-enabled">
                <input
                  id="settings-voice-wake-enabled"
                  class="settings-checkbox"
                  type="checkbox"
                  ${state.voiceWakePhraseEnabled ? "checked" : ""}
                >
                <span>Require wake phrase</span>
                <span class="field-note">Groundwork for hands-free use without accepting every spoken phrase as a command.</span>
              </label>
              <label class="settings-field" for="settings-voice-wake-phrase">
                <span>Wake phrase</span>
                <input
                  id="settings-voice-wake-phrase"
                  class="settings-input"
                  type="text"
                  maxlength="48"
                  value="${escapeHtml(state.voiceWakePhrase)}"
                  placeholder="hey zivra"
                >
                <span class="field-note">Say the wake phrase and the command in one utterance when voice capture is active.</span>
              </label>
            </div>
            <div class="stack-meta">
              <span class="meta-chip">${state.voiceRecognitionSupported ? "mic ready" : "mic unavailable"}</span>
              <span class="meta-chip">${state.voiceSynthesisSupported ? "speech ready" : "speech unavailable"}</span>
              <span class="meta-chip">${state.voiceWakePhraseEnabled ? `wake: ${state.voiceWakePhrase}` : "wake off"}</span>
            </div>
          </section>
          <div class="stack-meta">
            <span class="meta-chip">local profile</span>
            <span class="meta-chip">search x${escapeHtml(String(state.liveSearchResultLimit))}</span>
            <span class="meta-chip">refresh ${escapeHtml(String(state.dashboardRefreshSeconds))}s</span>
            <span class="meta-chip">${escapeHtml(state.whatsappApiVersion || "v23.0")}</span>
            <span class="meta-chip">${state.whatsappPhoneNumberId ? "whatsapp id set" : "whatsapp id missing"}</span>
            <span class="meta-chip">${state.whatsappVerifyToken ? "verify token set" : "verify token missing"}</span>
          </div>
          <div class="approval-actions control-row">
            <button class="secondary-button" type="submit">Save settings</button>
            <button id="reset-settings" class="ghost-button" type="button">Reset defaults</button>
          </div>
        </form>
      `,
      `
        <form id="secrets-form" class="stack-card settings-form">
          <strong>Encrypted secrets</strong>
          <p>${escapeHtml(secretStatusCopy)}</p>
          <div class="stack-meta">
            <span class="meta-chip">${escapeHtml(provider.label || "Encrypted vault unavailable")}</span>
            <span class="meta-chip">${provider.available ? "vault ready" : "env only"}</span>
            <span class="meta-chip">${runtime.planner_ready ? "planner ready" : "planner waiting for key/model"}</span>
            <span class="meta-chip">${runtime.smtp_ready ? "smtp ready" : "smtp waiting for auth/host"}</span>
            <span class="meta-chip">${runtime.whatsapp_ready ? "whatsapp ready" : "whatsapp waiting for token/id"}</span>
            <span class="meta-chip">${runtime.whatsapp_signature_ready ? "signature ready" : "signature optional"}</span>
          </div>
          <div class="settings-grid">
            <label class="settings-field" for="secret-llm-api-key">
              <span>OpenAI-compatible API key</span>
              <input
                id="secret-llm-api-key"
                class="settings-input"
                type="password"
                placeholder="${escapeHtml(llmApiKey.masked_value || "Leave blank to keep current value")}"
                ${secretsDisabled}
              >
              <span class="field-note">${escapeHtml(formatSecretSource(llmApiKey))}</span>
            </label>
            <label class="settings-field" for="secret-smtp-username">
              <span>SMTP username</span>
              <input
                id="secret-smtp-username"
                class="settings-input"
                type="text"
                placeholder="${escapeHtml(smtpUsername.masked_value || "Leave blank to keep current value")}"
                ${secretsDisabled}
              >
              <span class="field-note">${escapeHtml(formatSecretSource(smtpUsername))}</span>
            </label>
            <label class="settings-field" for="secret-smtp-password">
              <span>SMTP password</span>
              <input
                id="secret-smtp-password"
                class="settings-input"
                type="password"
                placeholder="${escapeHtml(smtpPassword.masked_value || "Leave blank to keep current value")}"
                ${secretsDisabled}
              >
              <span class="field-note">${escapeHtml(formatSecretSource(smtpPassword))}</span>
            </label>
            <label class="settings-field" for="secret-whatsapp-access-token">
              <span>WhatsApp access token</span>
              <input
                id="secret-whatsapp-access-token"
                class="settings-input"
                type="password"
                placeholder="${escapeHtml(whatsappAccessToken.masked_value || "Leave blank to keep current value")}"
                ${secretsDisabled}
              >
              <span class="field-note">${escapeHtml(formatSecretSource(whatsappAccessToken))}</span>
            </label>
            <label class="settings-field" for="secret-whatsapp-app-secret">
              <span>WhatsApp app secret</span>
              <input
                id="secret-whatsapp-app-secret"
                class="settings-input"
                type="password"
                placeholder="${escapeHtml(whatsappAppSecret.masked_value || "Leave blank to keep current value")}"
                ${secretsDisabled}
              >
              <span class="field-note">${escapeHtml(formatSecretSource(whatsappAppSecret))}</span>
            </label>
          </div>
          <div class="stack-meta">
            <span class="meta-chip">${escapeHtml(runtime.planner_mode || "auto")}</span>
            <span class="meta-chip">${escapeHtml(runtime.planner_model || "no planner model")}</span>
            <span class="meta-chip">${escapeHtml(runtime.smtp_host || "no SMTP host")}</span>
            <span class="meta-chip">${escapeHtml(runtime.smtp_port ? `port ${runtime.smtp_port}` : "no SMTP port")}</span>
            <span class="meta-chip">${escapeHtml(runtime.whatsapp_api_version || "v23.0")}</span>
            <span class="meta-chip">${escapeHtml(runtime.whatsapp_phone_number_id || "no WhatsApp phone ID")}</span>
            <span class="meta-chip">${runtime.whatsapp_verify_token_configured ? "verify token ready" : "verify token missing"}</span>
          </div>
          <div class="approval-actions control-row">
            <button class="secondary-button" type="submit" ${secretsDisabled}>Save encrypted secrets</button>
            <button id="clear-secrets" class="ghost-button" type="button" ${secretsDisabled}>Clear stored secrets</button>
          </div>
        </form>
      `,
    ],
  );
}

function renderClipboardPanel() {
  const metadata = state.clipboardMetadata;
  const metaChips = metadata
    ? `
      <div class="stack-meta">
        <span class="meta-chip">${escapeHtml(`${metadata.length || 0} chars`)}</span>
        <span class="meta-chip">${escapeHtml(`${metadata.line_count || 0} lines`)}</span>
        <span class="meta-chip">${metadata.empty ? "empty" : "loaded"}</span>
      </div>
    `
    : "";
  const statusCopy =
    state.clipboardStatusMessage ||
    "Read or update the local clipboard explicitly from here. Audit logs keep only clipboard metadata.";

  renderList(
    "clipboard-panel",
    [
      `
        <article class="stack-card">
          <strong>Local clipboard</strong>
          <p>${escapeHtml(statusCopy)}</p>
          ${metaChips}
          <textarea
            id="clipboard-editor"
            class="clipboard-editor"
            rows="8"
            placeholder="Read the current clipboard or type text here to copy it into the local clipboard."
          >${escapeHtml(state.clipboardText)}</textarea>
          <div class="approval-actions control-row">
            <button id="read-clipboard" class="secondary-button" type="button">Read clipboard</button>
            <button id="write-clipboard" class="ghost-button" type="button">Copy from editor</button>
            <button id="clear-clipboard-editor" class="ghost-button" type="button">Clear editor</button>
          </div>
        </article>
      `,
    ],
  );
}

function renderCompanionAccessPanel() {
  const access = state.companionAccess;
  const statusCopy =
    state.companionAccessStatus ||
    "Use one of these local URLs on a phone connected to the same network as this machine.";
  const hasSessionHandoff = Boolean(access?.session_id);
  const activeSessionId = getCompanionAccessSessionId();
  const recentSessionOptions = getRecentCompanionSessions();
  const selectedSession = getSelectedCompanionSessionSummary();
  const preferredCandidate = access?.preferred_candidate && access.preferred_candidate.host
    ? access.preferred_candidate
    : (access?.candidates || []).find((candidate) => candidate.preferred) || null;
  const shareSupported = typeof navigator.share === "function";

  if (!access || !(access.candidates || []).length) {
    renderList(
      "companion-access-panel",
      [
      `
        <article class="stack-card">
          <strong>Mobile companion access</strong>
            <p>${escapeHtml(statusCopy)}</p>
            <p class="inline-note">Select a session first if you want to hand off something other than the current browser thread.</p>
            <div class="approval-actions control-row">
              <button id="refresh-companion-access" class="ghost-button" type="button">Refresh access links</button>
            </div>
          </article>
          <article class="empty-card">
            <strong>No access URLs yet</strong>
            <span>Refresh this card to detect local addresses that can open the mobile companion.</span>
          </article>
        `,
      ].join(""),
    );
    return;
  }

  renderList(
    "companion-access-panel",
    [
      `
          <article class="stack-card">
            <strong>Mobile companion access</strong>
            <p>${escapeHtml(statusCopy)}</p>
            ${
              hasSessionHandoff
                ? `<p class="inline-note">These links carry the selected session into the companion.</p>`
                : ""
            }
            <div class="stack-meta">
              <span class="meta-chip">${escapeHtml(access.request_host || access.hostname || "local host")}</span>
              <span class="meta-chip">${escapeHtml(`${(access.candidates || []).length} link${(access.candidates || []).length === 1 ? "" : "s"}`)}</span>
              ${
                hasSessionHandoff
                  ? `<span class="meta-chip">${escapeHtml(`session ${access.session_id}`)}</span>`
                  : ""
              }
            </div>
            <div class="approval-actions control-row">
              <button id="refresh-companion-access" class="ghost-button" type="button">Refresh access links</button>
          </div>
        </article>
      `,
      preferredCandidate
        ? `
            <article class="stack-card companion-access-card companion-access-primary">
              <strong>Best link for phone</strong>
              <p>${escapeHtml(preferredCandidate.label || "Preferred same-network link")}</p>
              <code>${escapeHtml(preferredCandidate.mobile_session_url || preferredCandidate.mobile_url || "")}</code>
              <div class="stack-meta">
                <span class="meta-chip">${escapeHtml(preferredCandidate.origin || "")}</span>
                <span class="meta-chip">preferred</span>
              </div>
              <div class="approval-actions">
                <a class="secondary-button" href="${escapeHtml(preferredCandidate.mobile_session_url || preferredCandidate.mobile_url || "#")}" target="_blank" rel="noreferrer">Open mobile</a>
                <button
                  class="ghost-button"
                  type="button"
                  data-companion-access-action="copy-mobile"
                  data-url="${escapeHtml(preferredCandidate.mobile_session_url || preferredCandidate.mobile_url || "")}"
                >
                  Copy mobile link
                </button>
                <button
                  class="ghost-button"
                  type="button"
                  data-companion-access-action="copy-control-room"
                  data-url="${escapeHtml(preferredCandidate.control_room_session_url || preferredCandidate.control_room_url || "")}"
                >
                  Copy room link
                </button>
                ${
                  shareSupported
                    ? `
                        <button
                          class="ghost-button"
                          type="button"
                          data-companion-access-action="share-mobile"
                        >
                          Share link
                        </button>
                      `
                    : ""
                }
                <button
                  class="ghost-button"
                  type="button"
                  data-companion-access-action="copy-handoff-summary"
                >
                  Copy handoff summary
                </button>
                <button
                  class="ghost-button"
                  type="button"
                  data-companion-access-action="draft-email"
                >
                  Use in email
                </button>
                <button
                  class="ghost-button"
                  type="button"
                  data-companion-access-action="draft-whatsapp"
                >
                  Use in WhatsApp
                </button>
              </div>
            </article>
          `
        : "",
      `
        <article class="stack-card companion-access-card">
          <strong>Choose session</strong>
          <p>Build companion links for the current browser thread or another recent saved session.</p>
          <div class="companion-session-grid">
            <button
              class="ghost-button companion-session-button ${activeSessionId === state.sessionId ? "is-active" : ""}"
              type="button"
              data-companion-session-id="${escapeHtml(state.sessionId)}"
            >
              <strong>${escapeHtml("Current browser session")}</strong>
              <span class="field-note">${escapeHtml(state.sessionId)}</span>
            </button>
            ${recentSessionOptions
              .filter((session) => session.session_id !== state.sessionId)
              .map(
                (session) => `
                  <button
                    class="ghost-button companion-session-button ${activeSessionId === session.session_id ? "is-active" : ""}"
                    type="button"
                    data-companion-session-id="${escapeHtml(session.session_id)}"
                  >
                    <strong>${escapeHtml(session.last_content_preview || session.session_id)}</strong>
                    <span class="field-note">${escapeHtml(session.session_id)}</span>
                    <span class="field-note">${escapeHtml(`${session.turn_count || 0} turns`)}${session.last_seen_at ? ` · ${escapeHtml(new Date(session.last_seen_at).toLocaleString())}` : ""}</span>
                  </button>
                `,
              )
              .join("")}
          </div>
        </article>
      `,
      selectedSession
        ? `
            <article class="stack-card companion-access-card">
              <strong>Selected handoff target</strong>
              <p>${escapeHtml(selectedSession.last_content_preview || "No saved preview yet.")}</p>
              <div class="stack-meta">
                <span class="meta-chip">${escapeHtml(selectedSession.session_id)}</span>
                <span class="meta-chip">${escapeHtml(`${selectedSession.turn_count || 0} turns`)}</span>
                ${
                  selectedSession.last_seen_at
                    ? `<span class="meta-chip">${escapeHtml(new Date(selectedSession.last_seen_at).toLocaleString())}</span>`
                    : ""
                }
              </div>
            </article>
          `
        : "",
      ...(access.candidates || []).map(
        (candidate) => `
          <article class="stack-card companion-access-card">
            <strong>${escapeHtml(candidate.label || "Local URL")}</strong>
            <code>${escapeHtml(candidate.mobile_session_url || candidate.mobile_url)}</code>
            <div class="stack-meta">
              <span class="meta-chip">${escapeHtml(candidate.origin)}</span>
              ${
                hasSessionHandoff
                  ? '<span class="meta-chip">selected session handoff</span>'
                  : ""
              }
              ${candidate.preferred ? '<span class="meta-chip">preferred</span>' : ""}
            </div>
            <div class="approval-actions">
              <a class="secondary-button" href="${escapeHtml(candidate.mobile_session_url || candidate.mobile_url)}" target="_blank" rel="noreferrer">Open mobile</a>
              <button
                class="ghost-button"
                type="button"
                data-companion-access-action="copy-mobile"
                data-url="${escapeHtml(candidate.mobile_session_url || candidate.mobile_url)}"
              >
                ${hasSessionHandoff ? "Copy mobile link" : "Copy mobile URL"}
              </button>
              <button
                class="ghost-button"
                type="button"
                data-companion-access-action="copy-control-room"
                data-url="${escapeHtml(candidate.control_room_session_url || candidate.control_room_url)}"
              >
                ${hasSessionHandoff ? "Copy room link" : "Copy control room URL"}
              </button>
            </div>
          </article>
        `,
      ),
      `
        <article class="stack-card companion-access-card">
          <strong>How to use it</strong>
          <ul class="document-points">
            ${(access.notes || [])
              .map((item) => `<li>${escapeHtml(item)}</li>`)
              .join("")}
          </ul>
        </article>
      `,
    ].join(""),
  );
}

function formatWorkflowStatusLabel(status) {
  return String(status || "unknown").replaceAll("_", " ");
}

function workflowStatusChipClass(status) {
  return status === "failed" || status === "paused" ? "meta-chip danger" : "meta-chip";
}

function findWorkflowById(workflowId) {
  return state.workflows.find((workflow) => String(workflow.id) === String(workflowId)) || null;
}

function findWorkflowTaskById(taskId) {
  return state.workflowTasks.find((task) => String(task.id) === String(taskId)) || null;
}

function formatWorkflowSupervisorReason(reason) {
  const normalized = String(reason || "").trim();
  if (!normalized || normalized === "completed" || normalized === "idle") {
    return "";
  }
  if (normalized === "approval_limit_reached") {
    return "The supervisor stopped after hitting the approval backlog limit.";
  }
  if (normalized === "cycle_limit_reached") {
    return "The supervisor stopped after reaching this cycle's run limit.";
  }
  if (normalized === "workflow_failed") {
    return "The supervisor stopped after a workflow task failed.";
  }
  if (normalized === "disabled") {
    return "The supervisor is paused. Scheduled tasks can still queue for manual review.";
  }
  return normalized.replaceAll("_", " ");
}

function resetWorkflowComposer() {
  state.workflowName = "";
  state.workflowPrompt = "";
  state.workflowScheduleType = "manual";
  state.workflowIntervalHours = 4;
  state.workflowRunHour = 9;
  state.workflowRunMinute = 0;
  state.workflowRunWeekday = 0;
  state.workflowStartActive = true;
}

function renderWorkflowPanel() {
  const summary = state.workflowSummary || {};
  const workflows = state.workflows || [];
  const tasks = state.workflowTasks || [];
  const scheduleType = state.workflowScheduleType || "manual";
  const supervisorCycle = state.workflowSupervisorCycle || null;
  const supervisorReason = formatWorkflowSupervisorReason(supervisorCycle?.stopped_reason);
  const scheduleDetails =
    scheduleType === "hourly"
      ? `
        <div class="workflow-schedule-grid">
          <label class="settings-field" for="workflow-interval-hours">
            <span>Every how many hours</span>
            <input
              id="workflow-interval-hours"
              class="settings-input"
              type="number"
              min="1"
              max="24"
              value="${escapeHtml(String(state.workflowIntervalHours))}"
              required
            >
            <span class="field-note">Queued on an hourly cadence inside the local task queue.</span>
          </label>
        </div>
      `
      : scheduleType === "daily"
        ? `
          <div class="workflow-schedule-grid">
            <label class="settings-field" for="workflow-run-hour">
              <span>Run hour</span>
              <input
                id="workflow-run-hour"
                class="settings-input"
                type="number"
                min="0"
                max="23"
                value="${escapeHtml(String(state.workflowRunHour))}"
                required
              >
            </label>
            <label class="settings-field" for="workflow-run-minute">
              <span>Run minute</span>
              <input
                id="workflow-run-minute"
                class="settings-input"
                type="number"
                min="0"
                max="59"
                value="${escapeHtml(String(state.workflowRunMinute))}"
                required
              >
            </label>
          </div>
        `
        : scheduleType === "weekly"
          ? `
            <div class="workflow-schedule-grid">
              <label class="settings-field" for="workflow-run-weekday">
                <span>Run weekday</span>
                <select id="workflow-run-weekday" class="settings-input">
                  ${workflowWeekdayItems
                    .map(
                      ([value, label]) => `
                        <option value="${escapeHtml(String(value))}" ${Number(state.workflowRunWeekday) === value ? "selected" : ""}>
                          ${escapeHtml(label)}
                        </option>
                      `,
                    )
                    .join("")}
                </select>
              </label>
              <label class="settings-field" for="workflow-run-hour">
                <span>Run hour</span>
                <input
                  id="workflow-run-hour"
                  class="settings-input"
                  type="number"
                  min="0"
                  max="23"
                  value="${escapeHtml(String(state.workflowRunHour))}"
                  required
                >
              </label>
              <label class="settings-field" for="workflow-run-minute">
                <span>Run minute</span>
                <input
                  id="workflow-run-minute"
                  class="settings-input"
                  type="number"
                  min="0"
                  max="59"
                  value="${escapeHtml(String(state.workflowRunMinute))}"
                  required
                >
              </label>
            </div>
          `
          : `
            <div class="workflow-note">
              <strong>Manual queue</strong>
              <p>Manual workflows never auto-dispatch. They stay local until you click Queue now.</p>
            </div>
          `;
  const statusCopy =
    state.workflowStatusMessage ||
    "Create supervised recurring workflows that queue tasks locally, then let the guarded supervisor run them within your current approval limits.";
  const supervisorSummaryMarkup = `
    <div class="workflow-summary-row">
      <span class="${state.workflowSupervisorEnabled ? "meta-chip" : "meta-chip danger"}">
        ${state.workflowSupervisorEnabled ? "supervisor on" : "supervisor paused"}
      </span>
      <span class="meta-chip">${escapeHtml(`max ${state.workflowSupervisorMaxTasksPerCycle} run${state.workflowSupervisorMaxTasksPerCycle === 1 ? "" : "s"} per cycle`)}</span>
      <span class="meta-chip">${escapeHtml(`approval cap ${state.workflowSupervisorMaxPendingApprovals}`)}</span>
      <span class="meta-chip">${state.workflowSupervisorPauseOnFailure ? "pause on failure" : "keep workflows active on failure"}</span>
      ${
        supervisorCycle
          ? `
            <span class="meta-chip">${escapeHtml(`last cycle ran ${supervisorCycle.run_count || 0}`)}</span>
            <span class="meta-chip">${escapeHtml(`dispatched ${supervisorCycle.dispatched_count || 0}`)}</span>
          `
          : ""
      }
    </div>
  `;
  const supervisorNoteMarkup =
    supervisorCycle && (supervisorReason || (supervisorCycle.run_count || 0) || (supervisorCycle.dispatched_count || 0))
      ? `
        <p class="workflow-task-preview ${supervisorCycle.paused_workflows?.length ? "is-danger" : ""}">
          ${escapeHtml(
            supervisorReason ||
              `The last supervisor cycle dispatched ${supervisorCycle.dispatched_count || 0} task${supervisorCycle.dispatched_count === 1 ? "" : "s"} and ran ${supervisorCycle.run_count || 0}.`,
          )}
        </p>
      `
      : "";
  const workflowsMarkup = workflows.length
    ? `
        <div class="workflow-grid">
          ${workflows
            .map((workflow) => {
              const lastTaskStatus = workflow.last_task_status || "";
              const lastTaskClass = workflowStatusChipClass(lastTaskStatus);
              const promptPreview =
                workflow.prompt.length > 180 ? `${workflow.prompt.slice(0, 180).trim()}...` : workflow.prompt;
              return `
                <article class="stack-card workflow-card ${workflow.active ? "" : "is-paused"}">
                  <div class="workflow-card-head">
                    <div>
                      <strong>${escapeHtml(workflow.name)}</strong>
                      <p>${escapeHtml(promptPreview)}</p>
                    </div>
                    <div class="stack-meta">
                      <span class="${workflowStatusChipClass(workflow.active ? "active" : "paused")}">${workflow.active ? "active" : "paused"}</span>
                    </div>
                  </div>
                  <div class="stack-meta">
                    <span class="meta-chip">${escapeHtml(workflow.schedule_label || "manual")}</span>
                    ${workflow.next_run_display ? `<span class="meta-chip">${escapeHtml(`Next: ${workflow.next_run_display}`)}</span>` : '<span class="meta-chip">manual queue</span>'}
                    ${workflow.last_run_display ? `<span class="meta-chip">${escapeHtml(`Last run: ${workflow.last_run_display}`)}</span>` : ""}
                    ${workflow.last_queued_display ? `<span class="meta-chip">${escapeHtml(`Queued: ${workflow.last_queued_display}`)}</span>` : ""}
                    ${
                      lastTaskStatus
                        ? `<span class="${lastTaskClass}">${escapeHtml(`Last task: ${formatWorkflowStatusLabel(lastTaskStatus)}`)}</span>`
                        : ""
                    }
                  </div>
                  <div class="approval-actions">
                    <button
                      class="ghost-button"
                      type="button"
                      data-workflow-action="queue"
                      data-workflow-id="${escapeHtml(String(workflow.id))}"
                    >
                      Queue now
                    </button>
                    <button
                      class="${workflow.active ? "ghost-button" : "secondary-button"}"
                      type="button"
                      data-workflow-action="toggle"
                      data-workflow-id="${escapeHtml(String(workflow.id))}"
                      data-active="${workflow.active ? "true" : "false"}"
                    >
                      ${workflow.active ? "Pause" : "Resume"}
                    </button>
                  </div>
                </article>
              `;
            })
            .join("")}
        </div>
      `
    : `
        <article class="empty-card">
          <strong>No workflows yet</strong>
          <span>Save a manual or recurring workflow here and queued tasks will appear below.</span>
        </article>
      `;
  const tasksMarkup = tasks.length
    ? `
        <div class="workflow-task-grid">
          ${tasks
            .map((task) => {
              const previewSource = task.error || task.assistant_text || "";
              const preview = previewSource.length > 220 ? `${previewSource.slice(0, 220).trim()}...` : previewSource;
              const previewClass =
                task.status === "failed" ? "workflow-task-preview is-danger" : "workflow-task-preview";
              return `
                <article class="stack-card workflow-task-card">
                  <div class="workflow-card-head">
                    <div>
                      <strong>${escapeHtml(task.workflow_name)}</strong>
                      <p>${escapeHtml(task.prompt)}</p>
                    </div>
                    <span class="${workflowStatusChipClass(task.status)}">${escapeHtml(formatWorkflowStatusLabel(task.status))}</span>
                  </div>
                  <div class="stack-meta">
                    <span class="meta-chip">${escapeHtml(task.source || "schedule")}</span>
                    ${task.queued_for_display ? `<span class="meta-chip">${escapeHtml(`Queued for ${task.queued_for_display}`)}</span>` : ""}
                    ${task.finished_display ? `<span class="meta-chip">${escapeHtml(`Finished ${task.finished_display}`)}</span>` : ""}
                    ${task.pending_action_count ? `<span class="meta-chip">${escapeHtml(`${task.pending_action_count} approval${task.pending_action_count === 1 ? "" : "s"}`)}</span>` : ""}
                    ${task.outcome_count ? `<span class="meta-chip">${escapeHtml(`${task.outcome_count} outcome${task.outcome_count === 1 ? "" : "s"}`)}</span>` : ""}
                  </div>
                  ${
                    preview
                      ? `<p class="${previewClass}">${escapeHtml(preview)}</p>`
                      : '<p class="workflow-task-preview">This queued task has not run yet.</p>'
                  }
                  <div class="approval-actions">
                    ${
                      task.status === "queued"
                        ? `
                          <button
                            class="secondary-button"
                            type="button"
                            data-workflow-task-action="run"
                            data-task-id="${escapeHtml(String(task.id))}"
                          >
                            Run task
                          </button>
                          <button
                            class="ghost-button danger-button"
                            type="button"
                            data-workflow-task-action="cancel"
                            data-task-id="${escapeHtml(String(task.id))}"
                          >
                            Cancel
                          </button>
                        `
                        : ""
                    }
                    ${
                      task.status === "failed" || task.status === "canceled"
                        ? `
                          <button
                            class="ghost-button"
                            type="button"
                            data-workflow-task-action="retry"
                            data-task-id="${escapeHtml(String(task.id))}"
                          >
                            Retry
                          </button>
                        `
                        : ""
                    }
                    ${
                      task.status === "approval_pending"
                        ? '<span class="field-note">Review any staged approvals in the queue panel above.</span>'
                        : ""
                    }
                  </div>
                </article>
              `;
            })
            .join("")}
        </div>
      `
    : `
        <article class="empty-card">
          <strong>No queued workflow tasks</strong>
          <span>Scheduled dispatches and manual queue runs will accumulate here for supervised execution.</span>
        </article>
      `;

  renderList(
    "workflow-panel",
    [
      `
        <article class="stack-card workflow-form-card">
          <strong>Scheduled workflows</strong>
          <p>${escapeHtml(statusCopy)}</p>
          <div class="workflow-summary-row">
            <span class="meta-chip">${escapeHtml(`Active: ${summary.active_workflows ?? 0}`)}</span>
            <span class="meta-chip">${escapeHtml(`Paused: ${summary.paused_workflows ?? 0}`)}</span>
            <span class="meta-chip">${escapeHtml(`Manual: ${summary.manual_workflows ?? 0}`)}</span>
            <span class="meta-chip">${escapeHtml(`Queued: ${summary.queued_tasks ?? 0}`)}</span>
            <span class="meta-chip">${escapeHtml(`Running: ${summary.running_tasks ?? 0}`)}</span>
            <span class="meta-chip">${escapeHtml(`Approval pending: ${summary.approval_pending_tasks ?? 0}`)}</span>
            <span class="${summary.failed_tasks ? "meta-chip danger" : "meta-chip"}">${escapeHtml(`Failed: ${summary.failed_tasks ?? 0}`)}</span>
            <span class="meta-chip">${escapeHtml(`Canceled: ${summary.canceled_tasks ?? 0}`)}</span>
          </div>
          <form id="workflow-supervisor-form" class="settings-form">
            <strong>Background supervisor</strong>
            <p>Supervisor cycles run from the local control room refresh loop, queue due tasks, and auto-run a limited number of queued jobs while respecting approval backlog limits.</p>
            ${supervisorSummaryMarkup}
            ${supervisorNoteMarkup}
            <div class="settings-grid">
              <label class="settings-toggle-card" for="workflow-supervisor-enabled">
                <input
                  id="workflow-supervisor-enabled"
                  class="settings-checkbox"
                  type="checkbox"
                  ${state.workflowSupervisorEnabled ? "checked" : ""}
                >
                <span>Enable supervisor</span>
                <span class="field-note">When on, each dashboard refresh can queue due workflows and auto-run a bounded number of tasks.</span>
              </label>
              <label class="settings-field" for="workflow-supervisor-max-tasks">
                <span>Max runs per cycle</span>
                <input
                  id="workflow-supervisor-max-tasks"
                  class="settings-input"
                  type="number"
                  min="1"
                  max="5"
                  value="${escapeHtml(String(state.workflowSupervisorMaxTasksPerCycle))}"
                >
                <span class="field-note">Keeps background execution bounded even if many tasks are queued.</span>
              </label>
              <label class="settings-field" for="workflow-supervisor-max-approvals">
                <span>Approval backlog cap</span>
                <input
                  id="workflow-supervisor-max-approvals"
                  class="settings-input"
                  type="number"
                  min="1"
                  max="10"
                  value="${escapeHtml(String(state.workflowSupervisorMaxPendingApprovals))}"
                >
                <span class="field-note">Stops new supervisor runs once this many approval-pending tasks exist.</span>
              </label>
              <label class="settings-toggle-card" for="workflow-supervisor-pause-on-failure">
                <input
                  id="workflow-supervisor-pause-on-failure"
                  class="settings-checkbox"
                  type="checkbox"
                  ${state.workflowSupervisorPauseOnFailure ? "checked" : ""}
                >
                <span>Pause failed workflows</span>
                <span class="field-note">Recovery can retry the failed task later without letting the workflow keep running blindly.</span>
              </label>
            </div>
            <div class="approval-actions">
              <button class="secondary-button" type="submit">Save supervisor</button>
              <button id="run-workflow-supervisor" class="ghost-button" type="button">Run cycle now</button>
            </div>
          </form>
          <form id="workflow-form" class="settings-form">
            <div class="settings-grid">
              <label class="settings-field" for="workflow-name">
                <span>Workflow name</span>
                <input
                  id="workflow-name"
                  class="settings-input"
                  type="text"
                  maxlength="80"
                  value="${escapeHtml(state.workflowName)}"
                  placeholder="Morning review"
                  required
                >
              </label>
              <label class="settings-field" for="workflow-schedule-type">
                <span>Schedule</span>
                <select id="workflow-schedule-type" class="settings-input">
                  <option value="manual" ${scheduleType === "manual" ? "selected" : ""}>Manual</option>
                  <option value="hourly" ${scheduleType === "hourly" ? "selected" : ""}>Hourly</option>
                  <option value="daily" ${scheduleType === "daily" ? "selected" : ""}>Daily</option>
                  <option value="weekly" ${scheduleType === "weekly" ? "selected" : ""}>Weekly</option>
                </select>
              </label>
              <label class="settings-toggle-card" for="workflow-start-active">
                <input
                  id="workflow-start-active"
                  class="settings-checkbox"
                  type="checkbox"
                  ${state.workflowStartActive ? "checked" : ""}
                >
                <span>Start active</span>
                <span class="field-note">Pause it first if you want to save the workflow without scheduled dispatch.</span>
              </label>
            </div>
            <label class="settings-field" for="workflow-prompt">
              <span>Workflow prompt</span>
              <textarea
                id="workflow-prompt"
                class="settings-input workflow-prompt"
                placeholder="Show my system status and summarize pending reminders."
                required
              >${escapeHtml(state.workflowPrompt)}</textarea>
              <span class="field-note">Each queued task runs through the same planner, policy checks, approvals, and audit log as a normal chat request.</span>
            </label>
            ${scheduleDetails}
            <div class="approval-actions">
              <button class="primary-button" type="submit">Save workflow</button>
              <button id="clear-workflow-compose" class="ghost-button" type="button">Clear</button>
            </div>
          </form>
        </article>
      `,
      `
        <article class="stack-card">
          <strong>Saved workflows</strong>
          <p>Recurring workflows queue locally on schedule. Manual workflows only queue when you ask for them.</p>
          ${workflowsMarkup}
        </article>
      `,
      `
        <article class="stack-card">
          <strong>Task queue</strong>
          <p>Queued tasks stay supervised. Running one can still produce safe reads immediately and stage side effects behind approvals.</p>
          ${tasksMarkup}
        </article>
      `,
    ],
  );
}

function renderVisionList(title, items, emptyCopy) {
  if (!items.length) {
    return `
      <section class="vision-section">
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(emptyCopy)}</p>
      </section>
    `;
  }

  return `
    <section class="vision-section">
      <strong>${escapeHtml(title)}</strong>
      <ul class="document-points">
        ${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
      </ul>
    </section>
  `;
}

function renderVisionPanel() {
  const status = state.visionStatus || {};
  const analysis = state.selectedVisionAnalysis;
  const image = analysis?.image || null;
  const summary = analysis?.summary || null;
  const warnings = analysis?.warnings || [];
  const hasInput = Boolean(state.visionInputDataUrl);
  const cameraMarkup = state.visionCameraActive
    ? `
      <article class="stack-card vision-preview-card">
        <div class="vision-preview-head">
          <div>
            <strong>Live camera preview</strong>
            <p>Camera frames stay local in this browser until you capture one explicitly for analysis.</p>
          </div>
          <div class="stack-meta">
            <span class="meta-chip">camera live</span>
            <span class="meta-chip">${state.visionCameraSupported ? "browser media" : "unavailable"}</span>
          </div>
        </div>
        <video id="vision-camera-preview" class="vision-preview-image" autoplay muted playsinline></video>
      </article>
    `
    : "";
  const statusCopy = state.isCapturingVision
    ? "Capturing a screen snapshot locally..."
    : state.isAnalyzingVision
      ? "Analyzing the selected image..."
      : state.visionStatusMessage ||
        (state.visionCameraActive
          ? "The camera is live locally. Capture a frame when you want to analyze it."
          : null) ||
        (status.ready
          ? "Upload an image, capture your screen, or grab a camera frame. Zivra will combine local image metadata with a multimodal summary."
          : "Upload an image, capture your screen, or grab a camera frame. Without a configured vision model, Zivra will still inspect image metadata locally.");
  const previewMarkup = hasInput
    ? `
      <article class="stack-card vision-preview-card">
        <div class="vision-preview-head">
          <div>
            <strong>${escapeHtml(state.visionInputName || image?.filename || "Current image")}</strong>
            <p>Image bytes stay in the browser session and are sent only for this explicit analysis request.</p>
          </div>
          <div class="stack-meta">
            ${image?.format ? `<span class="meta-chip">${escapeHtml(image.format)}</span>` : '<span class="meta-chip">ready</span>'}
            ${image?.width && image?.height ? `<span class="meta-chip">${escapeHtml(`${image.width} x ${image.height}`)}</span>` : ""}
            ${image?.size_label ? `<span class="meta-chip">${escapeHtml(image.size_label)}</span>` : ""}
          </div>
        </div>
        <img class="vision-preview-image" src="${escapeHtml(state.visionInputDataUrl)}" alt="Selected screenshot preview">
      </article>
    `
    : `
      <article class="empty-card">
        <strong>No image selected</strong>
        <span>Choose an image file or capture your screen to inspect a screenshot locally.</span>
      </article>
    `;
  const analysisMarkup = analysis
    ? `
      <article class="stack-card">
        <strong>Image analysis</strong>
        <p>${escapeHtml(summary?.overview || "No overview returned.")}</p>
        <div class="stack-meta">
          <span class="meta-chip">${status.ready ? "model ready" : "local only"}</span>
          <span class="meta-chip">${escapeHtml(summary?.provider || "local")}</span>
          <span class="meta-chip">${escapeHtml(summary?.mode || status.mode || "metadata_only")}</span>
          ${status.model ? `<span class="meta-chip">${escapeHtml(status.model)}</span>` : ""}
          ${image?.orientation && image.orientation !== "unknown" ? `<span class="meta-chip">${escapeHtml(image.orientation)}</span>` : ""}
          ${image?.aspect_ratio ? `<span class="meta-chip">${escapeHtml(image.aspect_ratio)}</span>` : ""}
        </div>
        ${
          summary?.contains_sensitive_content === true
            ? '<p class="activity-note is-danger">This screenshot may contain sensitive information. Share or store it carefully.</p>'
            : ""
        }
        ${
          warnings.length
            ? `
              <div class="security-warning-card">
                <strong>Vision fallback</strong>
                <ul class="document-points">
                  ${warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}
                </ul>
              </div>
            `
            : ""
        }
        <div class="vision-analysis-grid">
          ${renderVisionList("Key points", summary?.key_points || [], "No key points were returned for this image.")}
          ${renderVisionList("Visible text", summary?.visible_text || [], "No visible text was extracted from the image.")}
          ${renderVisionList("Suggested follow-ups", summary?.suggested_actions || [], "No follow-up suggestions were returned.")}
        </div>
      </article>
      `
    : `
      <article class="empty-card">
        <strong>No analysis yet</strong>
        <span>Once you run analysis, the screenshot, screen capture, or camera-frame summary will appear here with visible text hints and suggested next steps.</span>
      </article>
    `;

  renderList(
    "vision-panel",
    [
      `
        <article class="stack-card">
          <strong>Screenshot understanding</strong>
          <p>${escapeHtml(statusCopy)}</p>
          <div class="stack-meta">
            <span class="meta-chip">${status.ready ? "multimodal ready" : "local metadata mode"}</span>
            <span class="meta-chip">${escapeHtml(status.provider || "local_only")}</span>
            ${status.model ? `<span class="meta-chip">${escapeHtml(status.model)}</span>` : ""}
            ${state.visionCameraSupported ? '<span class="meta-chip">camera ready</span>' : '<span class="meta-chip">camera unavailable</span>'}
            ${
              status.max_upload_bytes
                ? `<span class="meta-chip">limit ${escapeHtml(formatBytes(status.max_upload_bytes))}</span>`
                : ""
            }
          </div>
          <div class="approval-actions control-row">
            <label class="ghost-button vision-picker-button" for="vision-file-input">Choose image</label>
            <input id="vision-file-input" class="sr-only" type="file" accept="image/png,image/jpeg,image/webp,image/gif,image/bmp">
            <button
              id="toggle-vision-camera"
              class="ghost-button"
              type="button"
              ${state.visionCameraSupported && !state.isCapturingVision ? "" : "disabled"}
            >
              ${state.visionCameraActive ? "Stop camera" : "Start camera"}
            </button>
            <button
              id="capture-vision-camera"
              class="ghost-button"
              type="button"
              ${state.visionCameraActive && !state.isCapturingVision ? "" : "disabled"}
            >
              Capture camera
            </button>
            <button
              id="capture-vision-screen"
              class="ghost-button"
              type="button"
              ${state.visionCaptureSupported && !state.isCapturingVision ? "" : "disabled"}
            >
              ${state.isCapturingVision ? "Capturing" : "Capture screen"}
            </button>
            <button
              id="analyze-vision"
              class="secondary-button"
              type="button"
              ${hasInput && !state.isAnalyzingVision ? "" : "disabled"}
            >
              ${state.isAnalyzingVision ? "Analyzing" : "Analyze image"}
            </button>
            <button id="clear-vision" class="ghost-button" type="button">Clear</button>
          </div>
          <label class="settings-field" for="vision-prompt">
            <span>Focus prompt</span>
            <textarea
              id="vision-prompt"
              class="vision-prompt"
              rows="4"
              placeholder="Optional: ask about an error dialog, chart, layout issue, or visible text."
            >${escapeHtml(state.visionPrompt)}</textarea>
            <span class="field-note">
              ${
                state.visionCaptureSupported && state.visionCameraSupported
                  ? "Camera and screen capture both use your browser permission flow. Images are not written to disk by this panel."
                  : state.visionCaptureSupported
                    ? "Screen capture uses your browser permission flow. Images are not written to disk by this panel."
                    : state.visionCameraSupported
                      ? "Camera capture uses your browser permission flow. Images are not written to disk by this panel."
                      : "This browser cannot capture camera or screen input directly, but you can still upload screenshots."
              }
            </span>
          </label>
        </article>
      `,
      cameraMarkup,
      previewMarkup,
      analysisMarkup,
    ],
  );
  if (state.visionCameraActive) {
    window.requestAnimationFrame(syncVisionCameraPreview);
  }
}

function renderWebReaderPanel() {
  const page = state.selectedWebPage;
  const summary = state.selectedWebSummary;
  const results = state.webSearchResults || [];
  const statusCopy =
    state.isReadingWebPage
      ? "Reading the webpage in a sanitized text-only form..."
      : state.isSummarizingWebPage
        ? "Summarizing the sanitized webpage content..."
        : state.isSearchingWeb
          ? "Searching the web for live results..."
          : state.webReaderStatusMessage || "Fetch a webpage safely, strip noisy markup, and review the readable text locally.";
  const searchStatusCopy =
    state.webSearchStatusMessage ||
    "Run a live web search here, then open any result in the safe reader instead of a full browser tab.";
  const metaMarkup = page
    ? `
      <div class="stack-meta">
        <span class="meta-chip">${escapeHtml(page.source_kind || "web")}</span>
        <span class="meta-chip">${escapeHtml(`${page.word_count || 0} words`)}</span>
        <span class="meta-chip">${escapeHtml(page.title || page.url || "webpage")}</span>
      </div>
    `
    : "";
  const securityMarkup = page
    ? renderSecurityWarning(page.security, "This webpage", {
        title: "Sanitized webpage warning",
        detail: "The readable text shown below has already had suspicious instruction-like lines removed.",
      })
    : "";
  const summaryMarkup = summary
    ? `
      <section class="document-summary">
        <strong>Web summary</strong>
        <p>${escapeHtml(summary.overview || "No summary available.")}</p>
        ${
          (summary.key_points || []).length
            ? `
              <ul class="document-points">
                ${summary.key_points.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
              </ul>
            `
            : ""
        }
      </section>
    `
    : "";
  const resultsMarkup = results.length
    ? `
      <div class="stack-list web-search-results">
        ${results
          .map(
            (result) => `
              <article class="stack-card web-search-result">
                <strong>${escapeHtml(result.title || result.url || "Result")}</strong>
                <p>${escapeHtml(result.url || "")}</p>
                ${result.snippet ? `<p>${escapeHtml(result.snippet)}</p>` : ""}
                <div class="approval-actions">
                  <button
                    class="ghost-button"
                    type="button"
                    data-web-result-action="read"
                    data-web-result-url="${escapeHtml(result.url || "")}"
                  >
                    Read result
                  </button>
                  <button
                    class="ghost-button"
                    type="button"
                    data-web-result-action="summarize"
                    data-web-result-url="${escapeHtml(result.url || "")}"
                  >
                    Summarize result
                  </button>
                </div>
              </article>
            `,
          )
          .join("")}
      </div>
    `
    : `
      <article class="empty-card">
        <strong>No search results yet</strong>
        <span>Search for a topic like <code>AI desktop assistant examples</code> to pull live web results into the panel.</span>
      </article>
    `;
  const contentMarkup = page
    ? `
      <article class="stack-card">
        <strong>${escapeHtml(page.title || page.url)}</strong>
        <p>${escapeHtml(page.url || "")}</p>
        ${metaMarkup}
        ${securityMarkup}
        ${summaryMarkup}
        <pre>${escapeHtml(page.content || "")}</pre>
      </article>
      `
    : `
      <article class="empty-card">
        <strong>No webpage loaded</strong>
        <span>Enter a URL like <code>example.com</code> and read it here without opening a browser tab.</span>
      </article>
    `;

  renderList(
    "web-reader-panel",
    [
      `
        <article class="stack-card">
          <strong>Live search</strong>
          <p>${escapeHtml(searchStatusCopy)}</p>
          <form id="web-search-form" class="search-form web-search-form">
            <label class="sr-only" for="web-search-query">Search the web</label>
            <input
              id="web-search-query"
              class="search-input"
              type="search"
              value="${escapeHtml(state.webSearchQuery)}"
              placeholder="Search the live web for a topic or question"
            >
            <button class="ghost-button" type="submit">Search web</button>
            <button id="clear-web-search" class="ghost-button" type="button">Clear results</button>
          </form>
        </article>
      `,
      resultsMarkup,
      `
        <article class="stack-card">
          <strong>Safe webpage reader</strong>
          <p>${escapeHtml(statusCopy)}</p>
          <form id="web-reader-form" class="search-form web-reader-form">
            <label class="sr-only" for="web-reader-url">Webpage URL</label>
            <input
              id="web-reader-url"
              class="search-input"
              type="url"
              value="${escapeHtml(state.webReaderUrl)}"
              placeholder="Enter a webpage URL like example.com or https://example.com"
            >
            <button class="ghost-button" type="submit">Read page</button>
            <button id="summarize-webpage" class="ghost-button" type="button">Summarize page</button>
            <button id="clear-web-reader" class="ghost-button" type="button">Clear</button>
          </form>
        </article>
      `,
      contentMarkup,
    ],
  );
}

function renderResearchPanel() {
  const payload = state.selectedResearchBrief;
  const brief = payload?.brief || null;
  const sources = payload?.sources || [];
  const errors = payload?.fetch_errors || [];
  const statusCopy = state.isResearching
    ? "Building a research brief from live search results and sanitized page summaries..."
    : state.researchStatusMessage ||
      "Build a compact local research brief from live results, then open any source in the safe reader.";

  const briefMarkup = brief
    ? `
      <article class="stack-card">
        <strong>${escapeHtml(payload.query || state.researchQuery || "Research brief")}</strong>
        <p>${escapeHtml(brief.overview || "No overview available.")}</p>
        <div class="stack-meta">
          <span class="meta-chip">${escapeHtml(`${brief.source_count || 0} sources`)}</span>
          <span class="meta-chip">${brief.partial ? "partial" : "complete"}</span>
        </div>
        ${renderAggregateSecurityWarning(brief.suspicious_source_count || 0)}
        ${
          (brief.key_findings || []).length
            ? `
              <ul class="document-points">
                ${brief.key_findings.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
              </ul>
            `
            : ""
        }
      </article>
    `
    : `
      <article class="empty-card">
        <strong>No brief yet</strong>
        <span>Try a topic like <code>AI desktop assistant patterns</code> to generate a compact research summary.</span>
      </article>
    `;

  const sourceMarkup = sources.length
    ? `
      <div class="research-source-grid">
        ${sources
          .map(
            (source) => `
              <article class="stack-card">
                <strong>${escapeHtml(source.title || source.url || "Source")}</strong>
                <p>${escapeHtml(source.url || "")}</p>
                <div class="stack-meta">
                  <span class="meta-chip">${escapeHtml(source.domain || "web")}</span>
                  <span class="meta-chip">${escapeHtml(`rank ${source.rank || "?"}`)}</span>
                </div>
                <span>${escapeHtml(source.overview || source.search_snippet || "No source summary available.")}</span>
                ${renderSecurityWarning(source.security, "This source", {
                  title: "Sanitized source",
                  detail: "This source summary excluded suspicious instruction-like lines before it was added to the research brief.",
                })}
                ${
                  (source.key_points || []).length
                    ? `
                      <ul class="document-points">
                        ${source.key_points.slice(0, 3).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
                      </ul>
                    `
                    : ""
                }
                <div class="approval-actions">
                  <button
                    class="ghost-button"
                    type="button"
                    data-research-action="read-source"
                    data-source-url="${escapeHtml(source.url || "")}"
                  >
                    Read source
                  </button>
                  <button
                    class="ghost-button"
                    type="button"
                    data-research-action="summarize-source"
                    data-source-url="${escapeHtml(source.url || "")}"
                  >
                    Summarize source
                  </button>
                </div>
              </article>
            `,
          )
          .join("")}
      </div>
    `
    : "";

  const errorMarkup = errors.length
    ? `
      <article class="stack-card">
        <strong>Unavailable sources</strong>
        <ul class="document-points">
          ${errors.map((item) => `<li>${escapeHtml(item.url || "source")}: ${escapeHtml(item.error || "Unavailable")}</li>`).join("")}
        </ul>
      </article>
    `
    : "";

  renderList(
    "research-panel",
    [
      `
        <article class="stack-card">
          <strong>Research brief builder</strong>
          <p>${escapeHtml(statusCopy)}</p>
          <form id="research-form" class="search-form web-search-form">
            <label class="sr-only" for="research-query">Research query</label>
            <input
              id="research-query"
              class="search-input"
              type="search"
              value="${escapeHtml(state.researchQuery)}"
              placeholder="Research a topic and summarize the top safe-readable sources"
            >
            <button class="ghost-button" type="submit">Build brief</button>
            <button id="clear-research" class="ghost-button" type="button">Clear</button>
          </form>
        </article>
      `,
      briefMarkup,
      sourceMarkup,
      errorMarkup,
    ],
  );
}

function buildSelectedContentContext(source) {
  if (source === "note" && state.selectedNote) {
    return state.selectedNote.content || "";
  }
  if (source === "document" && state.selectedDocument) {
    return state.selectedDocument.content || "";
  }
  if (source === "research" && state.selectedResearchBrief?.brief) {
    const brief = state.selectedResearchBrief.brief;
    return [brief.overview || "", ...(brief.key_findings || [])].filter(Boolean).join("\n");
  }
  return "";
}

function renderContentPanel() {
  const payload = state.selectedContentPackage;
  const packageData = payload?.package || null;
  const statusCopy = state.isGeneratingContent
    ? "Generating YouTube titles, SEO copy, and creator structure suggestions..."
    : state.contentStatusMessage ||
      "Turn a topic and optional local context into YouTube title ideas, SEO copy, tags, and chapters.";
  const canUseNote = Boolean(state.selectedNote?.content);
  const canUseDocument = Boolean(state.selectedDocument?.content);
  const canUseResearch = Boolean(state.selectedResearchBrief?.brief);

  const resultsMarkup = packageData
    ? `
        <article class="stack-card">
          <strong>${escapeHtml(payload.topic || state.contentTopic || "Creator package")}</strong>
          <p>${escapeHtml(packageData.angle || "No angle available.")}</p>
          <div class="stack-meta">
            <span class="meta-chip">${escapeHtml(`${(packageData.youtube_titles || []).length} titles`)}</span>
            <span class="meta-chip">${escapeHtml(`${(packageData.tags || []).length} tags`)}</span>
            <span class="meta-chip">${escapeHtml(`${(packageData.chapters || []).length} chapters`)}</span>
          </div>
          ${
            (packageData.highlights || []).length
              ? `
                <ul class="document-points">
                  ${(packageData.highlights || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
                </ul>
              `
              : ""
          }
        </article>
      <div class="content-strategy-grid">
        <article class="stack-card">
          <strong>YouTube titles</strong>
          <ul class="document-points">
            ${(packageData.youtube_titles || [])
              .map(
                (title, index) => `
                  <li>
                    ${escapeHtml(title)}
                    <button
                      class="ghost-button"
                      type="button"
                      data-content-action="copy-title"
                      data-title-index="${escapeHtml(index)}"
                    >
                      Copy
                    </button>
                  </li>
                `,
              )
              .join("")}
          </ul>
        </article>
        <article class="stack-card">
          <strong>SEO title</strong>
          <p>${escapeHtml(packageData.seo_title || "")}</p>
          <strong>Meta description</strong>
          <p>${escapeHtml(packageData.meta_description || "")}</p>
          <div class="approval-actions">
            <button class="ghost-button" type="button" data-content-action="copy-seo-title">Copy SEO title</button>
            <button class="ghost-button" type="button" data-content-action="copy-meta-description">Copy meta description</button>
          </div>
        </article>
        <article class="stack-card">
          <strong>YouTube description</strong>
          <pre>${escapeHtml(packageData.youtube_description || "")}</pre>
          <div class="approval-actions">
            <button class="ghost-button" type="button" data-content-action="copy-youtube-description">Copy description</button>
          </div>
        </article>
        <article class="stack-card">
          <strong>Tags</strong>
          <ul class="document-points">
            ${(packageData.tags || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
          </ul>
          <strong>Chapters</strong>
          <ul class="document-points">
            ${(packageData.chapters || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
          </ul>
        </article>
      </div>
    `
    : `
      <article class="empty-card">
        <strong>No creator package yet</strong>
        <span>Try a topic like <code>local-first AI assistant demos</code> and optionally pull in a selected note, document, or research brief for context.</span>
      </article>
    `;

  renderList(
    "content-panel",
    [
      `
        <article class="stack-card">
          <strong>Creator brief builder</strong>
          <p>${escapeHtml(statusCopy)}</p>
          <form id="content-form" class="email-compose">
            <input
              id="content-topic"
              class="settings-input"
              type="text"
              value="${escapeHtml(state.contentTopic)}"
              placeholder="Topic or video idea"
              required
            >
            <input
              id="content-audience"
              class="settings-input"
              type="text"
              value="${escapeHtml(state.contentAudience)}"
              placeholder="Optional audience, like indie builders or ops teams"
            >
            <textarea
              id="content-context"
              class="settings-input"
              placeholder="Optional local context, notes, or source summary"
            >${escapeHtml(state.contentContext)}</textarea>
            <div class="approval-actions">
              <button class="primary-button" type="submit" ${state.isGeneratingContent ? "disabled" : ""}>Generate package</button>
              <button id="clear-content" class="ghost-button" type="button">Clear</button>
              <button id="use-note-context" class="ghost-button" type="button" ${canUseNote ? "" : "disabled"}>Use note</button>
              <button id="use-document-context" class="ghost-button" type="button" ${canUseDocument ? "" : "disabled"}>Use document</button>
              <button id="use-research-context" class="ghost-button" type="button" ${canUseResearch ? "" : "disabled"}>Use research</button>
            </div>
          </form>
        </article>
      `,
      resultsMarkup,
    ],
  );
}

function findEmailById(emailId) {
  return state.emails.find((email) => String(email.id) === String(emailId)) || null;
}

function findMessageById(messageId) {
  return state.messages.find((message) => String(message.id) === String(messageId)) || null;
}

function renderMessagingPanel() {
  const delivery = state.messageDelivery || { ready: true, status_label: "Browser handoff", delivery_mode: "browser_handoff" };
  const summary = state.messageSummary || {};
  const messages = state.messages || [];
  const usingCloud = delivery.delivery_mode === "cloud_api";
  const statusCopy = state.messageStatusMessage || (
    usingCloud
      ? "Meta WhatsApp Cloud API is configured. New sends can go out directly, and inbound replies can land here once your Meta webhook points at the local webhook path."
      : delivery.isolated_available
        ? "Save drafts locally, then open a prefilled WhatsApp compose window in an isolated private browser window when available. Final send still happens in WhatsApp."
        : "Save drafts locally, then open a prefilled WhatsApp compose window after confirmation. Final send still happens in WhatsApp."
  );

  const summaryMarkup = `
    <div class="email-summary-row">
      <span class="meta-chip">${escapeHtml(delivery.status_label || "Browser handoff")}</span>
      ${delivery.api_version ? `<span class="meta-chip">${escapeHtml(delivery.api_version)}</span>` : ""}
      ${delivery.phone_number_id_masked ? `<span class="meta-chip">${escapeHtml(delivery.phone_number_id_masked)}</span>` : ""}
      ${delivery.browser ? `<span class="meta-chip">${escapeHtml(delivery.browser)}</span>` : ""}
      <span class="meta-chip">${escapeHtml(`Drafts: ${summary.draft ?? 0}`)}</span>
      <span class="meta-chip">${escapeHtml(`Received: ${summary.received ?? 0}`)}</span>
      <span class="meta-chip">${escapeHtml(`Sent: ${summary.sent ?? 0}`)}</span>
      <span class="meta-chip">${escapeHtml(`Delivered: ${summary.delivered ?? 0}`)}</span>
      <span class="meta-chip">${escapeHtml(`Read: ${summary.read ?? 0}`)}</span>
      <span class="meta-chip">${escapeHtml(`Opened: ${summary.opened ?? 0}`)}</span>
      <span class="meta-chip">${escapeHtml(`Failed: ${summary.failed ?? 0}`)}</span>
      <span class="meta-chip">${delivery.verify_token_configured ? "webhook verify ready" : "webhook verify missing"}</span>
      <span class="meta-chip">${delivery.signature_validation ? "signature checked" : "signature optional"}</span>
    </div>
  `;

  const messageCards = messages.length
    ? messages
        .map(
          (message) => {
            const isInbound = message.direction === "inbound";
            const actionLabel = isInbound
              ? "Reply here"
              : usingCloud
                ? message.status === "sent" || message.status === "delivered" || message.status === "read"
                  ? "Send again"
                  : "Send now"
                : message.status === "opened"
                  ? "Open again"
                  : message.status === "failed"
                    ? "Retry handoff"
                    : "Open in WhatsApp";
            return `
            <article class="stack-card">
              <strong>${escapeHtml(message.contact_name || message.to || "WhatsApp message")}</strong>
              <span>${escapeHtml(message.body_preview || "No message body saved yet.")}</span>
              <div class="email-meta-grid">
                <span class="meta-chip">${escapeHtml(message.status)}</span>
                <span class="meta-chip">${escapeHtml(isInbound ? "inbound" : "outbound")}</span>
                <span class="meta-chip">${escapeHtml(message.provider || message.channel || "whatsapp")}</span>
                <span class="meta-chip">${escapeHtml(message.message_type || "text")}</span>
                <span class="meta-chip">${escapeHtml(message.to || "unknown")}</span>
                <span class="meta-chip">${escapeHtml(`${message.body_length || 0} chars`)}</span>
                <span class="meta-chip">${escapeHtml(new Date(message.remote_timestamp || message.updated_at || message.created_at).toLocaleString())}</span>
              </div>
              ${message.error ? `<p>${escapeHtml(message.error)}</p>` : ""}
              <div class="approval-actions">
                <button
                  class="ghost-button"
                  type="button"
                  data-message-action="copy-body"
                  data-message-id="${escapeHtml(message.id)}"
                >
                  Copy body
                </button>
                <button
                  class="secondary-button"
                  type="button"
                  data-message-action="${isInbound ? "reply" : "dispatch"}"
                  data-message-id="${escapeHtml(message.id)}"
                >
                  ${escapeHtml(actionLabel)}
                </button>
              </div>
            </article>
          `;
          },
        )
        .join("")
    : `
      <article class="empty-card">
        <strong>No WhatsApp activity yet</strong>
        <span>Cloud API replies or browser-handoff drafts will appear here once the integration starts receiving traffic.</span>
      </article>
    `;

  renderList(
    "messaging-panel",
    [
      `
        <article class="stack-card">
          <strong>${usingCloud ? "WhatsApp Cloud console" : "WhatsApp outbox"}</strong>
          <p>${escapeHtml(statusCopy)}</p>
          ${summaryMarkup}
          <div class="stack-meta">
            <span class="meta-chip">${usingCloud ? "direct send enabled" : "browser handoff mode"}</span>
            <span class="meta-chip">${delivery.conversation_ready ? "inbox ready when webhook reaches this app" : "inbox waiting for webhook verification"}</span>
            ${delivery.webhook_path ? `<span class="meta-chip">${escapeHtml(delivery.webhook_path)}</span>` : ""}
          </div>
          <form id="whatsapp-compose-form" class="email-compose">
            <input
              id="whatsapp-to"
              class="settings-input"
              type="text"
              value="${escapeHtml(state.whatsappComposeTo)}"
              placeholder="WhatsApp number with country code"
              required
            >
            <textarea
              id="whatsapp-body"
              class="settings-input"
              placeholder="Write the WhatsApp message here"
              required
            >${escapeHtml(state.whatsappComposeBody)}</textarea>
            <div class="approval-actions">
              <button class="primary-button" type="submit">Save draft</button>
              <button id="clear-whatsapp-compose" class="ghost-button" type="button">Clear</button>
            </div>
          </form>
          <p class="field-note">
            ${usingCloud
              ? "This uses your Meta business number configuration. Replies show up here after Meta posts webhook events to this local endpoint."
              : "This is still using browser handoff. Add Cloud API credentials in Settings to move from handoff mode into a real inbox-and-send integration."}
          </p>
        </article>
      `,
      messageCards,
    ],
  );
}

function renderEmailPanel() {
  const delivery = state.emailDelivery || { ready: false, status_label: "Not configured" };
  const summary = state.emailSummary || {};
  const emails = state.emails || [];
  const statusCopy =
    state.emailStatusMessage ||
    (delivery.ready
      ? `SMTP is configured for ${delivery.from_email || "the current sender"} via ${delivery.host}.`
      : "SMTP is not configured yet. You can save drafts locally now, and sending will unlock once SMTP settings are provided.");

  const summaryMarkup = `
    <div class="email-summary-row">
      <span class="meta-chip">${escapeHtml(delivery.status_label || "Not configured")}</span>
      <span class="meta-chip">${escapeHtml(`Drafts: ${summary.draft ?? 0}`)}</span>
      <span class="meta-chip">${escapeHtml(`Sent: ${summary.sent ?? 0}`)}</span>
      <span class="meta-chip">${escapeHtml(`Failed: ${summary.failed ?? 0}`)}</span>
    </div>
  `;

  const emailCards = emails.length
    ? emails
        .map(
          (email) => `
            <article class="stack-card">
              <strong>${escapeHtml(email.subject || "Untitled draft")}</strong>
              <span>${escapeHtml(email.body_preview || "No body saved yet.")}</span>
              <div class="email-meta-grid">
                <span class="meta-chip">${escapeHtml(email.status)}</span>
                <span class="meta-chip">${escapeHtml(email.to)}</span>
                <span class="meta-chip">${escapeHtml(`${email.body_length || 0} chars`)}</span>
                <span class="meta-chip">${escapeHtml(new Date(email.updated_at || email.created_at).toLocaleString())}</span>
              </div>
              ${email.error ? `<p>${escapeHtml(email.error)}</p>` : ""}
              <div class="approval-actions">
                <button
                  class="ghost-button"
                  type="button"
                  data-email-action="copy-body"
                  data-email-id="${escapeHtml(email.id)}"
                >
                  Copy body
                </button>
                ${
                  email.status !== "sent"
                    ? `
                      <button
                        class="secondary-button"
                        type="button"
                        data-email-action="send"
                        data-email-id="${escapeHtml(email.id)}"
                        ${delivery.ready ? "" : "disabled"}
                      >
                        ${email.status === "failed" ? "Retry send" : "Send email"}
                      </button>
                    `
                    : ""
                }
              </div>
            </article>
          `,
        )
        .join("")
    : `
      <article class="empty-card">
        <strong>No outbox activity yet</strong>
        <span>Assistant-created drafts and dashboard drafts will appear here for review and sending.</span>
      </article>
    `;

  renderList(
    "email-panel",
    [
      `
        <article class="stack-card">
          <strong>Local outbox</strong>
          <p>${escapeHtml(statusCopy)}</p>
          ${summaryMarkup}
          <form id="email-compose-form" class="email-compose">
            <input
              id="email-to"
              class="settings-input"
              type="email"
              value="${escapeHtml(state.emailComposeTo)}"
              placeholder="Recipient email"
              required
            >
            <input
              id="email-subject"
              class="settings-input"
              type="text"
              value="${escapeHtml(state.emailComposeSubject)}"
              placeholder="Subject"
              required
            >
            <textarea
              id="email-body"
              class="settings-input"
              placeholder="Write the email body here"
            >${escapeHtml(state.emailComposeBody)}</textarea>
            <div class="approval-actions">
              <button class="primary-button" type="submit">Save draft</button>
              <button id="clear-email-compose" class="ghost-button" type="button">Clear</button>
            </div>
          </form>
        </article>
      `,
      emailCards,
    ],
  );
}

function renderNotes(notes) {
  if (!notes.length) {
    const emptyTitle = state.notesQuery ? "No matching notes" : "No notes yet";
    const emptyCopy = state.notesQuery
      ? `No notes matched "${state.notesQuery}" in the approved workspace.`
      : "Create a note from the assistant and it will appear here inside the approved workspace.";
    renderList(
      "notes-list",
      [
        `
          <article class="empty-card">
            <strong>${escapeHtml(emptyTitle)}</strong>
            <span>${escapeHtml(emptyCopy)}</span>
          </article>
        `,
      ],
    );
    return;
  }

  renderList(
    "notes-list",
    notes.map(
      (note) => `
        <article class="stack-card ${state.selectedNoteName === note.name ? "is-selected" : ""}">
          <strong>${escapeHtml(note.title)}</strong>
          <span>${escapeHtml(note.match_preview || note.preview)}</span>
          <div class="stack-meta">
            <span class="meta-chip">${escapeHtml(new Date(note.updated_at).toLocaleString())}</span>
            <span class="meta-chip">${escapeHtml(`${note.size_bytes} bytes`)}</span>
            ${note.match_score ? `<span class="meta-chip">match ${escapeHtml(note.match_score)}</span>` : ""}
          </div>
          <code>${escapeHtml(note.name)}</code>
          <p>${escapeHtml(note.path)}</p>
          <div class="approval-actions">
            <button
              class="ghost-button ${state.selectedNoteName === note.name ? "is-active" : ""}"
              type="button"
              data-note-action="open"
              data-name="${escapeHtml(note.name)}"
            >
              Read note
            </button>
          </div>
        </article>
      `,
    ),
  );
}

function renderNotesStatus(count) {
  const label = state.notesQuery ? `Search: ${state.notesQuery}` : "Recent notes";
  document.getElementById("notes-status").innerHTML = sanitizeMarkup(
    `
      <span class="meta-chip">${escapeHtml(label)}</span>
      <span class="meta-chip">${escapeHtml(`${count} result${count === 1 ? "" : "s"}`)}</span>
    `,
  );

  const clearButton = document.getElementById("clear-notes-search");
  if (clearButton) {
    clearButton.disabled = !state.notesQuery;
  }
}

function renderNoteReader(note) {
  state.selectedNote = note;

  if (!note) {
    state.noteEditorContent = "";
    state.isEditingNote = false;
    renderList(
      "note-reader",
      [
        `
          <article class="empty-card">
            <strong>No note selected</strong>
            <span>Choose a note from the workspace list to read the full content here.</span>
          </article>
        `,
      ],
    );
    renderContentPanel();
    return;
  }

  renderList(
    "note-reader",
    [
      `
        <article class="stack-card">
          <strong>${escapeHtml(note.title)}</strong>
          <span>${escapeHtml(note.path)}</span>
          <div class="stack-meta">
            <span class="meta-chip">${escapeHtml(new Date(note.updated_at).toLocaleString())}</span>
            <span class="meta-chip">${escapeHtml(`${note.size_bytes} bytes`)}</span>
          </div>
          <div class="approval-actions">
            ${
              state.isEditingNote
                ? `
                  <button class="secondary-button" type="button" data-note-reader-action="save">Save changes</button>
                  <button class="ghost-button" type="button" data-note-reader-action="discard">Discard changes</button>
                `
                : `
                  <button class="secondary-button" type="button" data-note-reader-action="edit">Edit note</button>
                `
            }
          </div>
          ${
            state.isEditingNote
              ? `<textarea id="note-editor" class="note-editor">${escapeHtml(state.noteEditorContent)}</textarea>`
              : `<pre>${escapeHtml(note.content || "This note is empty.")}</pre>`
          }
        </article>
      `,
    ],
  );
  renderContentPanel();
}

function hasUnsavedNoteChanges() {
  if (!state.isEditingNote || !state.selectedNote) {
    return false;
  }
  return state.noteEditorContent !== (state.selectedNote.content || "");
}

function renderDocuments(documents) {
  if (!documents.length) {
    const emptyTitle = state.documentsQuery ? "No matching documents" : "No approved documents yet";
    const emptyCopy = state.documentsQuery
      ? `No documents matched "${state.documentsQuery}" in the approved read-only roots.`
      : "Approved notes and docs will appear here for safe local reading.";
    renderList(
      "documents-list",
      [
        `
          <article class="empty-card">
            <strong>${escapeHtml(emptyTitle)}</strong>
            <span>${escapeHtml(emptyCopy)}</span>
          </article>
        `,
      ],
    );
    return;
  }

  renderList(
    "documents-list",
    documents.map(
      (document) => `
        <article class="stack-card ${state.selectedDocumentId === document.id ? "is-selected" : ""}">
          <strong>${escapeHtml(document.title)}</strong>
          <span>${escapeHtml(document.match_preview || document.preview)}</span>
          <div class="stack-meta">
            <span class="meta-chip">${escapeHtml(document.root)}</span>
            <span class="meta-chip">${escapeHtml(new Date(document.updated_at).toLocaleString())}</span>
            <span class="meta-chip">${escapeHtml(`${document.size_bytes} bytes`)}</span>
            ${document.match_score ? `<span class="meta-chip">match ${escapeHtml(document.match_score)}</span>` : ""}
          </div>
          <code>${escapeHtml(document.relative_path)}</code>
          <p>${escapeHtml(document.path)}</p>
          <div class="approval-actions">
            <button
              class="ghost-button ${state.selectedDocumentId === document.id ? "is-active" : ""}"
              type="button"
              data-document-action="open"
              data-id="${escapeHtml(document.id)}"
            >
              Read document
            </button>
          </div>
        </article>
      `,
    ),
  );
}

function renderFilesStatus() {
  const folder = state.selectedFileFolder;
  const scopeLabel = state.filesQuery
    ? `Search: ${state.filesQuery}`
    : folder && folder.kind !== "workspace"
      ? `Folder: ${folder.root}/${folder.relative_path || folder.name}`
      : "Approved roots";
  const resultCount = state.filesQuery ? state.fileSearchResults.length : folder?.direct_file_count || 0;

  document.getElementById("files-status").innerHTML = sanitizeMarkup(
    `
      <span class="meta-chip">${escapeHtml(scopeLabel)}</span>
      <span class="meta-chip">${escapeHtml(`${resultCount} file${resultCount === 1 ? "" : "s"}`)}</span>
      ${folder ? `<span class="meta-chip">${escapeHtml(`${folder.folder_count || 0} folders`)}</span>` : ""}
    `,
  );

  const clearButton = document.getElementById("clear-files-search");
  if (clearButton) {
    clearButton.disabled = !state.filesQuery;
  }
}

function renderFilesPanel() {
  const folder = state.selectedFileFolder;
  const roots = state.fileRoots || [];
  const rootButtons = roots
    .map(
      (root) => `
        <button
          class="file-breadcrumb ${folder?.id === root.id ? "is-active" : ""}"
          type="button"
          data-file-browser-action="open-folder"
          data-folder-id="${escapeHtml(root.id)}"
        >
          ${escapeHtml(root.name)}
        </button>
      `,
    )
    .join("");

  if (state.filesQuery) {
    const results = state.fileSearchResults || [];
    const resultMarkup = results.length
      ? results
          .map(
            (file) => `
              <article class="stack-card">
                <strong>${escapeHtml(file.name)}</strong>
                <span>${escapeHtml(file.match_preview || file.preview || file.relative_path)}</span>
                <div class="stack-meta">
                  <span class="meta-chip">${escapeHtml(file.root)}</span>
                  <span class="meta-chip">${escapeHtml(file.extension || "file")}</span>
                  <span class="meta-chip">${escapeHtml(formatBytes(file.size_bytes))}</span>
                  ${file.writable ? '<span class="meta-chip">writable</span>' : '<span class="meta-chip">read-only</span>'}
                </div>
                <code>${escapeHtml(file.relative_path)}</code>
                <p class="file-path">${escapeHtml(file.path)}</p>
                <div class="file-entry-actions">
                  <button
                    class="ghost-button"
                    type="button"
                    data-file-browser-action="open-folder"
                    data-folder-id="${escapeHtml(getFileParentFolderId(file.id))}"
                  >
                    Open folder
                  </button>
                  ${
                    file.readable_document_id
                      ? `
                        <button
                          class="secondary-button"
                          type="button"
                          data-file-browser-action="open-reader"
                          data-document-id="${escapeHtml(file.readable_document_id)}"
                        >
                          Open in reader
                        </button>
                      `
                      : ""
                  }
                  <button
                    class="ghost-button"
                    type="button"
                    data-file-browser-action="copy-path"
                    data-path="${escapeHtml(file.path)}"
                  >
                    Copy path
                  </button>
                </div>
              </article>
            `,
          )
          .join("")
      : `
        <article class="empty-card">
          <strong>No matching files</strong>
          <span>${escapeHtml(`No approved files matched "${state.filesQuery}".`)}</span>
        </article>
      `;

    renderList(
      "files-panel",
      [
        `
          <article class="stack-card">
            <strong>Approved file search</strong>
            <p>Search spans file names, relative paths, and supported local text content inside approved roots.</p>
            <div class="file-breadcrumbs">${rootButtons}</div>
          </article>
          <div class="file-browser-grid">${resultMarkup}</div>
        `,
      ],
    );
    return;
  }

  if (!folder) {
    renderList(
      "files-panel",
      [
        `
          <article class="empty-card">
            <strong>No folder selected</strong>
            <span>Browse the approved roots to explore local files and folders.</span>
          </article>
        `,
      ],
    );
    return;
  }

  const breadcrumbMarkup = (folder.breadcrumbs || [])
    .map(
      (crumb, index, crumbs) => `
        <button
          class="file-breadcrumb ${index === crumbs.length - 1 ? "is-active" : ""}"
          type="button"
          data-file-browser-action="open-folder"
          data-folder-id="${escapeHtml(crumb.id)}"
        >
          ${escapeHtml(crumb.label)}
        </button>
      `,
    )
    .join("");

  const foldersMarkup = (folder.folders || []).length
    ? `
      <section class="file-browser-section">
        <strong>Folders</strong>
        <div class="file-browser-grid">
          ${(folder.folders || [])
            .map(
              (entry) => `
                <article class="stack-card">
                  <strong>${escapeHtml(entry.name)}</strong>
                  <span>${escapeHtml(entry.relative_path || entry.root)}</span>
                  <div class="stack-meta">
                    <span class="meta-chip">${escapeHtml(`${entry.file_count} files`)}</span>
                    <span class="meta-chip">${escapeHtml(`${entry.folder_count} folders`)}</span>
                    <span class="meta-chip">${escapeHtml(formatBytes(entry.total_size_bytes))}</span>
                  </div>
                  <p class="file-path">${escapeHtml(entry.path)}</p>
                  <div class="file-entry-actions">
                    <button
                      class="ghost-button"
                      type="button"
                      data-file-browser-action="open-folder"
                      data-folder-id="${escapeHtml(entry.id)}"
                    >
                      Browse folder
                    </button>
                  </div>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const filesMarkup = (folder.files || []).length
    ? `
      <section class="file-browser-section">
        <strong>Files</strong>
        <div class="file-browser-grid">
          ${(folder.files || [])
            .map(
              (file) => `
                <article class="stack-card">
                  <strong>${escapeHtml(file.name)}</strong>
                  <span>${escapeHtml(file.preview || file.relative_path)}</span>
                  <div class="stack-meta">
                    <span class="meta-chip">${escapeHtml(file.extension || "file")}</span>
                    <span class="meta-chip">${escapeHtml(formatBytes(file.size_bytes))}</span>
                    ${file.writable ? '<span class="meta-chip">writable</span>' : '<span class="meta-chip">read-only</span>'}
                  </div>
                  <code>${escapeHtml(file.relative_path)}</code>
                  <p class="file-path">${escapeHtml(file.path)}</p>
                  <div class="file-entry-actions">
                    ${
                      file.readable_document_id
                        ? `
                          <button
                            class="secondary-button"
                            type="button"
                            data-file-browser-action="open-reader"
                            data-document-id="${escapeHtml(file.readable_document_id)}"
                          >
                            Open in reader
                          </button>
                        `
                        : ""
                    }
                    <button
                      class="ghost-button"
                      type="button"
                      data-file-browser-action="copy-path"
                      data-path="${escapeHtml(file.path)}"
                    >
                      Copy path
                    </button>
                  </div>
                </article>
              `,
            )
            .join("")}
        </div>
        ${folder.remaining_file_count ? `<p>${escapeHtml(`${folder.remaining_file_count} more file(s) in this folder are hidden from the preview list.`)}</p>` : ""}
      </section>
    `
    : `
      <article class="empty-card">
        <strong>No direct files here</strong>
        <span>Use the folders above or search to explore more of the approved roots.</span>
      </article>
    `;

  renderList(
    "files-panel",
    [
      `
        <article class="stack-card">
          <div class="file-breadcrumbs">${breadcrumbMarkup || rootButtons}</div>
          <strong>${escapeHtml(folder.name)}</strong>
          <p>${escapeHtml(folder.kind === "workspace" ? "Browse local approved roots and recent files." : folder.path)}</p>
          <div class="stack-meta">
            <span class="meta-chip">${escapeHtml(`${folder.direct_folder_count || 0} direct folders`)}</span>
            <span class="meta-chip">${escapeHtml(`${folder.direct_file_count || 0} direct files`)}</span>
            <span class="meta-chip">${escapeHtml(`${folder.file_count || 0} total files`)}</span>
            <span class="meta-chip">${escapeHtml(formatBytes(folder.total_size_bytes || 0))}</span>
          </div>
          ${rootButtons ? `<div class="file-breadcrumbs">${rootButtons}</div>` : ""}
        </article>
        ${foldersMarkup}
        ${filesMarkup}
      `,
    ],
  );
}

function renderDocumentsStatus(count) {
  const label = state.documentsQuery ? `Search: ${state.documentsQuery}` : "Recent approved documents";
  document.getElementById("documents-status").innerHTML = sanitizeMarkup(
    `
      <span class="meta-chip">${escapeHtml(label)}</span>
      <span class="meta-chip">${escapeHtml(`${count} result${count === 1 ? "" : "s"}`)}</span>
    `,
  );

  const clearButton = document.getElementById("clear-documents-search");
  if (clearButton) {
    clearButton.disabled = !state.documentsQuery;
  }
}

function renderDocumentReader(document) {
  state.selectedDocument = document;

  if (!document) {
    state.selectedDocumentSummary = null;
    state.selectedDocumentAnalysis = null;
    state.selectedDocumentInspection = null;
    state.documentInspectionFilter = "";
    state.documentInspectionDepth = 2;
    state.documentInspectionPath = "";
    state.isSummarizingDocument = false;
    state.isAnalyzingDocument = false;
    state.isInspectingDocument = false;
    renderList(
      "document-reader",
      [
        `
          <article class="empty-card">
            <strong>No document selected</strong>
            <span>Choose a document from the approved roots to read it here.</span>
          </article>
        `,
      ],
    );
    renderContentPanel();
    return;
  }

  renderList(
    "document-reader",
    [
      `
        <article class="stack-card">
          <strong>${escapeHtml(document.title)}</strong>
          <span>${escapeHtml(document.path)}</span>
          <div class="stack-meta">
            <span class="meta-chip">${escapeHtml(document.root)}</span>
            <span class="meta-chip">${escapeHtml(document.relative_path)}</span>
            <span class="meta-chip">${escapeHtml(new Date(document.updated_at).toLocaleString())}</span>
            <span class="meta-chip">${escapeHtml(`${document.size_bytes} bytes`)}</span>
          </div>
          <div class="approval-actions">
            <button
              class="secondary-button"
              type="button"
              data-document-reader-action="summarize"
              ${state.isSummarizingDocument ? "disabled" : ""}
            >
              ${state.selectedDocumentSummary ? "Refresh summary" : "Summarize document"}
            </button>
            <button
              class="ghost-button"
              type="button"
              data-document-reader-action="analyze"
              ${state.isAnalyzingDocument ? "disabled" : ""}
            >
              ${state.selectedDocumentAnalysis ? "Refresh analysis" : "Analyze data"}
            </button>
            <button
              class="ghost-button"
              type="button"
              data-document-reader-action="inspect"
              ${state.isInspectingDocument ? "disabled" : ""}
            >
              ${state.selectedDocumentInspection ? "Refresh structure" : "Inspect structure"}
            </button>
          </div>
          ${renderSecurityWarning(document.security, "This document", {
            title: "Untrusted document warning",
            detail: "Preview and summary text were sanitized before use. The raw document view below is shown as-is for local review.",
          })}
          ${
            state.selectedDocumentSummary
              ? `
                <section class="document-summary">
                  <strong>Summary</strong>
                  <p>${escapeHtml(state.selectedDocumentSummary.overview || "No summary available.")}</p>
                  <div class="stack-meta">
                    <span class="meta-chip">${escapeHtml(`${state.selectedDocumentSummary.word_count || 0} words`)}</span>
                    <span class="meta-chip">${escapeHtml(`${state.selectedDocumentSummary.estimated_read_time_minutes || 1} min read`)}</span>
                  </div>
                  ${
                    state.selectedDocumentSummary.format_hint
                      ? `<p>${escapeHtml(state.selectedDocumentSummary.format_hint)}</p>`
                      : ""
                  }
                  ${
                    (state.selectedDocumentSummary.headings || []).length
                      ? `
                        <div class="stack-meta">
                          ${state.selectedDocumentSummary.headings
                            .map((heading) => `<span class="meta-chip">${escapeHtml(heading)}</span>`)
                            .join("")}
                        </div>
                      `
                      : ""
                  }
                  ${
                    (state.selectedDocumentSummary.key_points || []).length
                      ? `
                        <ul class="document-points">
                          ${state.selectedDocumentSummary.key_points
                            .map((point) => `<li>${escapeHtml(point)}</li>`)
                            .join("")}
                        </ul>
                      `
                      : ""
                  }
                </section>
              `
              : ""
          }
          ${renderDocumentAnalysis(state.selectedDocumentAnalysis)}
          ${renderDocumentInspection(state.selectedDocumentInspection)}
          <pre>${escapeHtml(document.content || "This document is empty.")}</pre>
        </article>
      `,
    ],
  );
  renderContentPanel();
}

function renderDocumentInspection(inspection) {
  if (!inspection) {
    return "";
  }

  const chips = [];
  if (inspection.field_count !== undefined) {
    chips.push(`<span class="meta-chip">${escapeHtml(`${inspection.field_count} fields`)}</span>`);
  }
  if (inspection.item_count !== undefined) {
    chips.push(`<span class="meta-chip">${escapeHtml(`${inspection.item_count} items`)}</span>`);
  }
  if (inspection.row_count !== undefined) {
    chips.push(`<span class="meta-chip">${escapeHtml(`${inspection.row_count} rows`)}</span>`);
  }
  if (inspection.filtered_row_count !== undefined) {
    chips.push(`<span class="meta-chip">${escapeHtml(`${inspection.filtered_row_count} shown`)}</span>`);
  }
  if (inspection.filtered_item_count !== undefined) {
    chips.push(`<span class="meta-chip">${escapeHtml(`${inspection.filtered_item_count} matched`)}</span>`);
  }
  if (inspection.schema_depth !== undefined) {
    chips.push(`<span class="meta-chip">${escapeHtml(`depth ${inspection.schema_depth}`)}</span>`);
  }
  if (inspection.focus && inspection.focus.found) {
    chips.push(`<span class="meta-chip">${escapeHtml(`path ${inspection.focus.path}`)}</span>`);
  }

  let body = "";
  if ((inspection.sample_rows || []).length) {
    const headers = inspection.headers || inspection.top_level_keys || Object.keys(inspection.sample_rows[0] || {});
    body = renderInspectionTable(headers, inspection.sample_rows);
  } else if ((inspection.sample_fields || []).length) {
    body = renderInspectionPreviewCards(inspection.sample_fields, {
      interactive: inspection.kind === "json_object",
    });
  } else if ((inspection.sample_items || []).length) {
    const rootArrayDrillPath =
      inspection.kind === "json_array" && ["array", "object", "mixed"].includes(inspection.item_type || "")
        ? "[]"
        : "";
    body = renderInspectionPreviewItems(inspection.sample_items, {
      drillPath: rootArrayDrillPath,
    });
  } else if ((inspection.sample_lines || []).length) {
    body = `
      <ul class="document-points">
        ${inspection.sample_lines.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}
      </ul>
    `;
  }
  if (!body && inspection.filterable && state.documentInspectionFilter) {
    body = "<p>No rows matched the current filter.</p>";
  } else if (!body) {
    body = "<p>No structural preview is available for this document yet.</p>";
  }

  const schemaMarkup = (inspection.schema_fields || []).length
    ? `
        <div class="inspection-grid">
          ${inspection.schema_fields
            .map(
              (field) => `
                <button
                  class="inspection-card inspection-card-button ${state.documentInspectionPath === field.name ? "is-active" : ""}"
                  type="button"
                  data-document-reader-action="focus-inspection-path"
                  data-schema-path="${escapeHtml(field.name)}"
                >
                  <strong>${escapeHtml(field.name)}</strong>
                  <span class="inspection-depth-chip">${escapeHtml(`level ${field.depth || 1}`)}</span>
                  <span>${escapeHtml(field.type || "unknown")}</span>
                </button>
              `,
            )
            .join("")}
        </div>
      `
    : "";

  const depthMarkup = (inspection.schema_depth !== undefined)
    ? `
        <div class="inspection-depth-row">
          ${[1, 2, 3, 4]
            .map(
              (depth) => `
                <button
                  class="ghost-button ${state.documentInspectionDepth === depth ? "is-active" : ""}"
                  type="button"
                  data-document-reader-action="set-inspection-depth"
                  data-depth="${depth}"
                >
                  Depth ${depth}
                </button>
              `,
            )
            .join("")}
        </div>
      `
    : "";

  const filterMarkup = inspection.filterable
    ? `
        <form class="inspection-filter-form" data-document-inspection-form="true">
          <label class="sr-only" for="document-inspection-filter">Filter structure rows</label>
          <input
            id="document-inspection-filter"
            class="search-input"
            type="search"
            name="filter"
            placeholder="Filter rows by value or column"
            value="${escapeHtml(state.documentInspectionFilter)}"
          >
          <button class="ghost-button" type="submit">
            ${state.isInspectingDocument ? "Filtering" : "Apply filter"}
          </button>
          <button class="ghost-button" type="button" data-document-reader-action="clear-inspection-filter">
            Clear
          </button>
        </form>
      `
    : "";

  const focusMarkup = renderInspectionFocus(inspection.focus);
  const actionMarkup = renderInspectionActionBar("inspection");

  return `
    <section class="document-summary document-structure">
      <strong>${escapeHtml(inspection.label || "Structure")}</strong>
      ${depthMarkup}
      ${filterMarkup}
      ${actionMarkup}
      ${focusMarkup}
      <div class="stack-meta">
        ${chips.join("")}
        ${
          (inspection.top_level_keys || []).length
            ? inspection.top_level_keys
                .slice(0, 8)
                .map((key) => `<span class="meta-chip">${escapeHtml(key)}</span>`)
                .join("")
            : ""
        }
      </div>
      ${inspection.error ? `<p>${escapeHtml(inspection.error)}</p>` : ""}
      ${schemaMarkup}
      ${body}
    </section>
  `;
}

function renderDocumentAnalysis(analysis) {
  if (!analysis) {
    return "";
  }

  const chips = [
    `<span class="meta-chip">${escapeHtml(`${analysis.row_count || 0} rows`)}</span>`,
    `<span class="meta-chip">${escapeHtml(`${analysis.column_count || 0} columns`)}</span>`,
    `<span class="meta-chip">${escapeHtml(`${analysis.numeric_column_count || 0} numeric`)}</span>`,
    `<span class="meta-chip">${escapeHtml(`${analysis.categorical_column_count || 0} categorical`)}</span>`,
  ];
  if (analysis.schema_path) {
    chips.push(`<span class="meta-chip">${escapeHtml(`path ${analysis.schema_path}`)}</span>`);
  }
  if (analysis.filter_applied) {
    chips.push(`<span class="meta-chip">${escapeHtml(`filter ${analysis.filter_applied}`)}</span>`);
  }

  const numericMarkup = (analysis.numeric_columns || []).length
    ? `
        <div class="analysis-grid">
          ${analysis.numeric_columns
            .map(
              (column) => `
                <article class="inspection-card">
                  <strong>${escapeHtml(column.name)}</strong>
                  <div class="stack-meta">
                    <span class="meta-chip">${escapeHtml(`${column.count} values`)}</span>
                    <span class="meta-chip">${escapeHtml(`${column.missing_count} missing`)}</span>
                  </div>
                  <p>${escapeHtml(`Mean ${column.mean} | Min ${column.min} | Max ${column.max}`)}</p>
                  <p>${escapeHtml(`Sum ${column.sum}`)}</p>
                </article>
              `,
            )
            .join("")}
        </div>
      `
    : "<p>No fully numeric columns were detected in this table view.</p>";

  const categoricalMarkup = (analysis.categorical_columns || []).length
    ? `
        <div class="analysis-grid">
          ${analysis.categorical_columns
            .map(
              (column) => `
                <article class="inspection-card">
                  <strong>${escapeHtml(column.name)}</strong>
                  <div class="stack-meta">
                    <span class="meta-chip">${escapeHtml(`${column.unique_count} unique`)}</span>
                    <span class="meta-chip">${escapeHtml(`${column.missing_count} missing`)}</span>
                  </div>
                  ${
                    (column.top_values || []).length
                      ? `
                        <ul class="document-points">
                          ${column.top_values
                            .map(
                              (item) => `
                                <li>${escapeHtml(`${item.value}: ${item.count}`)}</li>
                              `,
                            )
                            .join("")}
                        </ul>
                      `
                      : "<p>No categorical samples available.</p>"
                  }
                </article>
              `,
            )
            .join("")}
        </div>
      `
    : "";

  const emptyColumnsMarkup = (analysis.empty_columns || []).length
    ? `
        <p>${escapeHtml(`Empty columns: ${analysis.empty_columns.join(", ")}`)}</p>
      `
    : "";

  return `
    <section class="document-summary document-analysis">
      <strong>${escapeHtml(analysis.label || "Table analysis")}</strong>
      <p>${escapeHtml(analysis.overview || "No analysis overview available.")}</p>
      <div class="stack-meta">
        ${chips.join("")}
      </div>
      <div class="analysis-section">
        <strong>Numeric columns</strong>
        ${numericMarkup}
      </div>
      ${
        categoricalMarkup
          ? `
            <div class="analysis-section">
              <strong>Categorical columns</strong>
              ${categoricalMarkup}
            </div>
          `
          : ""
      }
      ${emptyColumnsMarkup}
    </section>
  `;
}

function renderInspectionFocus(focus) {
  if (!focus) {
    return "";
  }

  const parentPath = getInspectionParentPath(focus.path);
  const breadcrumbs = renderInspectionBreadcrumbs(focus.path);
  const actionBar = renderInspectionActionBar("focus");
  const actions = state.documentInspectionPath
    ? `
        ${
          parentPath
            ? `
                <button
                  class="ghost-button"
                  type="button"
                  data-document-reader-action="focus-parent-inspection-path"
                  data-schema-path="${escapeHtml(parentPath)}"
                >
                  Up one level
                </button>
              `
            : ""
        }
        <button class="ghost-button" type="button" data-document-reader-action="clear-inspection-path">
          Clear path
        </button>
      `
    : "";

  if (!focus.found) {
    return `
      <div class="inspection-focus">
        <div class="inspection-path-row">
          <strong>${escapeHtml(`Focused path: ${focus.path || "Unknown"}`)}</strong>
          ${actions}
        </div>
        ${actionBar}
        ${breadcrumbs}
        <p>No matching structure path was found.</p>
      </div>
    `;
  }

  const chips = [];
  if (focus.type) {
    chips.push(`<span class="meta-chip">${escapeHtml(focus.type)}</span>`);
  }
  if (focus.match_count !== undefined) {
    chips.push(`<span class="meta-chip">${escapeHtml(`${focus.match_count} match${focus.match_count === 1 ? "" : "es"}`)}</span>`);
  }
  if (focus.item_count !== undefined) {
    chips.push(`<span class="meta-chip">${escapeHtml(`${focus.item_count} items`)}</span>`);
  }
  if (focus.field_count !== undefined) {
    chips.push(`<span class="meta-chip">${escapeHtml(`${focus.field_count} fields`)}</span>`);
  }

  let body = "";
  if ((focus.sample_rows || []).length) {
    body = renderInspectionTable(
      focus.headers || Object.keys(focus.sample_rows[0] || {}),
      focus.sample_rows,
      {
        interactivePathBase: focus.path,
      },
    );
  } else if ((focus.sample_fields || []).length) {
    body = renderInspectionPreviewCards(focus.sample_fields, {
      interactivePathBase: focus.path,
    });
  } else if ((focus.sample_items || []).length) {
    const focusArrayDrillPath =
      focus.type === "array" && !focus.path.endsWith("[]") ? resolveInspectionSchemaPath(focus.path, "[]") : "";
    body = renderInspectionPreviewItems(focus.sample_items, {
      drillPath: focusArrayDrillPath,
    });
  } else if ((focus.sample_lines || []).length) {
    body = `
      <ul class="document-points">
        ${focus.sample_lines.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}
      </ul>
    `;
  } else {
    body = "<p>No focused preview is available for this path yet.</p>";
  }

  const lineActionMarkup = (focus.line_actions || []).length
    ? `
        <div class="inspection-line-actions">
          ${focus.line_actions
            .map(
              (action) => `
                <button
                  class="inspection-line-button"
                  type="button"
                  data-document-reader-action="focus-inspection-path"
                  data-schema-path="${escapeHtml(action.path)}"
                >
                  <strong>${escapeHtml(action.name)}</strong>
                  <span>${escapeHtml(action.preview || action.path)}</span>
                </button>
              `,
            )
            .join("")}
        </div>
      `
    : "";

  const schemaMarkup = (focus.schema_fields || []).length
    ? `
        <div class="inspection-grid">
          ${focus.schema_fields
            .map(
              (field) => {
                const resolvedPath = resolveInspectionSchemaPath(focus.path, field.name);
                return `
                  <button
                    class="inspection-card inspection-card-button ${state.documentInspectionPath === resolvedPath ? "is-active" : ""}"
                    type="button"
                    data-document-reader-action="focus-inspection-path"
                    data-schema-path="${escapeHtml(resolvedPath)}"
                  >
                    <strong>${escapeHtml(field.name)}</strong>
                    <span class="inspection-depth-chip">${escapeHtml(`level ${field.depth || 1}`)}</span>
                    <span>${escapeHtml(field.type || "unknown")}</span>
                  </button>
                `;
              },
            )
            .join("")}
        </div>
      `
    : "";

  return `
    <div class="inspection-focus">
      <div class="inspection-path-row">
        <strong>${escapeHtml(`Focused path: ${focus.path}`)}</strong>
        ${actions}
      </div>
      ${actionBar}
      ${breadcrumbs}
      <div class="stack-meta">
        ${chips.join("")}
      </div>
      ${schemaMarkup}
      ${lineActionMarkup}
      ${body}
    </div>
  `;
}

function renderInspectionTable(headers, rows, options = {}) {
  const visibleHeaders = (headers || []).slice(0, 8);
  if (!visibleHeaders.length) {
    return "";
  }

  const interactivePathBase = String(options.interactivePathBase || "").trim();
  const renderHeader = (header) => {
    if (!interactivePathBase) {
      return `<th>${escapeHtml(header)}</th>`;
    }

    const headerPath = resolveInspectionSchemaPath(interactivePathBase, header);
    return `
      <th>
        <button
          class="inspection-table-button inspection-table-head-button"
          type="button"
          data-document-reader-action="focus-inspection-path"
          data-schema-path="${escapeHtml(headerPath)}"
        >
          ${escapeHtml(header)}
        </button>
      </th>
    `;
  };

  const renderCell = (header, row) => {
    if (!interactivePathBase) {
      return `<td>${escapeHtml(row[header] ?? "")}</td>`;
    }

    const headerPath = resolveInspectionSchemaPath(interactivePathBase, header);
    return `
      <td>
        <button
          class="inspection-table-button"
          type="button"
          data-document-reader-action="focus-inspection-path"
          data-schema-path="${escapeHtml(headerPath)}"
        >
          ${escapeHtml(row[header] ?? "")}
        </button>
      </td>
    `;
  };

  return `
    <div class="inspection-table-wrap">
      <table class="inspection-table">
        <thead>
          <tr>
            ${visibleHeaders.map((header) => renderHeader(header)).join("")}
          </tr>
        </thead>
        <tbody>
          ${rows
            .slice(0, 5)
            .map(
              (row) => `
                <tr>
                  ${visibleHeaders
                    .map((header) => renderCell(header, row))
                    .join("")}
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderReminders(reminders) {
  if (!reminders.length) {
    const emptyCopy = state.includeArchived
      ? "No reminders match this view right now. Archive history stays available when you need it."
      : "Create a reminder from the assistant and upcoming follow-ups will appear here.";
    renderList(
      "reminders-list",
      [
        `
          <article class="empty-card">
            <strong>No reminders yet</strong>
            <span>${escapeHtml(emptyCopy)}</span>
          </article>
        `,
      ],
    );
    return;
  }

  renderList(
    "reminders-list",
    reminders.map((reminder) => {
      const scheduleChipClass = reminder.is_overdue ? "meta-chip danger" : "meta-chip";
      const completedCopy = reminder.completed_display
        ? `Completed ${reminder.completed_display}`
        : "Completed";
      const archivedCopy = reminder.archived_display
        ? `Archived ${reminder.archived_display}`
        : "Archived";
      const recurrenceMarkup = reminder.recurrence_label
        ? `<span class="meta-chip">${escapeHtml(reminder.recurrence_label)}</span>`
        : "";
      let actionMarkup = "";

      if (reminder.status === "completed") {
        actionMarkup = `
            <div class="approval-actions">
              <button class="ghost-button" type="button" data-reminder-action="reopen" data-id="${escapeHtml(reminder.id)}">
                Reopen
              </button>
              <button class="ghost-button" type="button" data-reminder-action="archive" data-id="${escapeHtml(reminder.id)}">
                Archive
              </button>
            </div>
          `;
      } else if (reminder.status === "archived") {
        actionMarkup = `
            <div class="approval-actions">
              <button class="secondary-button" type="button" data-reminder-action="restore" data-id="${escapeHtml(reminder.id)}">
                Restore
              </button>
              <button class="ghost-button danger-button" type="button" data-reminder-action="delete" data-id="${escapeHtml(reminder.id)}">
                Delete
              </button>
            </div>
          `;
      } else {
        const recurrenceControls = reminder.due_at
          ? `
            <div class="approval-actions">
              <button
                class="ghost-button ${reminder.recurrence_rule === "daily" ? "is-active" : ""}"
                type="button"
                data-reminder-action="recurrence"
                data-preset="daily"
                data-id="${escapeHtml(reminder.id)}"
              >
                Every day
              </button>
              <button
                class="ghost-button ${reminder.recurrence_rule === "weekdays" ? "is-active" : ""}"
                type="button"
                data-reminder-action="recurrence"
                data-preset="weekdays"
                data-id="${escapeHtml(reminder.id)}"
              >
                Weekdays
              </button>
              <button
                class="ghost-button ${reminder.recurrence_rule === "weekly" ? "is-active" : ""}"
                type="button"
                data-reminder-action="recurrence"
                data-preset="weekly"
                data-id="${escapeHtml(reminder.id)}"
              >
                Every week
              </button>
              ${
                reminder.recurrence_rule
                  ? `
                    <button class="ghost-button" type="button" data-reminder-action="clear-recurrence" data-id="${escapeHtml(reminder.id)}">
                      Stop repeating
                    </button>
                  `
                  : ""
              }
            </div>
          `
          : `
            <p>Schedule this reminder before turning on repeat.</p>
          `;
        actionMarkup = `
            <div class="approval-actions">
              <button class="secondary-button" type="button" data-reminder-action="complete" data-id="${escapeHtml(reminder.id)}">
                Mark done
              </button>
              <button class="ghost-button" type="button" data-reminder-action="snooze" data-preset="hour" data-id="${escapeHtml(reminder.id)}">
                Snooze 1h
              </button>
              <button class="ghost-button" type="button" data-reminder-action="snooze" data-preset="tomorrow" data-id="${escapeHtml(reminder.id)}">
                Tomorrow 9am
              </button>
              <button class="ghost-button" type="button" data-reminder-action="archive" data-id="${escapeHtml(reminder.id)}">
                Archive
              </button>
            </div>
            <div class="reminder-scheduler">
              <input
                class="reminder-input"
                type="datetime-local"
                required
                data-schedule-input="true"
                data-id="${escapeHtml(reminder.id)}"
                value="${escapeHtml(toDateTimeLocalValue(reminder.due_at))}"
              >
              <button class="ghost-button" type="button" data-reminder-action="schedule" data-id="${escapeHtml(reminder.id)}">
                Schedule
              </button>
            </div>
            ${recurrenceControls}
          `;
      }
      return `
        <article class="stack-card">
          <strong>${escapeHtml(reminder.title)}</strong>
          <span>${escapeHtml(reminder.details || "Reminder captured from the assistant workflow.")}</span>
          <div class="stack-meta">
            <span class="${scheduleChipClass}">${escapeHtml(reminder.due_display)}</span>
            <span class="meta-chip">${escapeHtml(reminder.status)}</span>
            ${recurrenceMarkup}
            ${reminder.status === "completed" ? `<span class="meta-chip">${escapeHtml(completedCopy)}</span>` : ""}
            ${reminder.status === "archived" ? `<span class="meta-chip">${escapeHtml(archivedCopy)}</span>` : ""}
          </div>
          ${actionMarkup}
        </article>
      `;
    }),
  );
}

function renderReminderSummary(summary = {}) {
  const chips = [
    ["Pending", summary.pending ?? 0],
    ["Due today", summary.due_today ?? 0],
    ["Overdue", summary.overdue ?? 0],
    ["Unscheduled", summary.unscheduled ?? 0],
    ["Completed", summary.completed ?? 0],
    ["Archived", summary.archived ?? 0],
  ];

  document.getElementById("reminder-summary").innerHTML = chips
    .map(
      ([label, value]) => `
        <span class="meta-chip">${escapeHtml(`${label}: ${value}`)}</span>
      `,
    )
    .join("");
}

function renderReminderToolbar() {
  const toggleButton = document.getElementById("toggle-archived-reminders");
  const archiveCompletedButton = document.getElementById("archive-completed-reminders");
  const restoreArchivedButton = document.getElementById("restore-archived-reminders");
  const purgeArchivedButton = document.getElementById("purge-archived-reminders");

  if (toggleButton) {
    toggleButton.textContent = state.includeArchived ? "Hide archived" : "Show archived";
    toggleButton.classList.toggle("is-active", state.includeArchived);
  }

  if (archiveCompletedButton) {
    const completedCount = state.reminderSummary.completed ?? 0;
    archiveCompletedButton.disabled = completedCount === 0;
    archiveCompletedButton.title =
      completedCount === 0 ? "No completed reminders to archive yet." : "Move completed reminders out of the main queue.";
  }

  if (restoreArchivedButton) {
    const archivedCount = state.reminderSummary.archived ?? 0;
    restoreArchivedButton.disabled = archivedCount === 0;
    restoreArchivedButton.title =
      archivedCount === 0 ? "No archived reminders to restore yet." : "Return archived reminders to the pending queue.";
  }

  if (purgeArchivedButton) {
    const archivedCount = state.reminderSummary.archived ?? 0;
    purgeArchivedButton.disabled = archivedCount === 0;
    purgeArchivedButton.title =
      archivedCount === 0 ? "No archived reminders to delete yet." : "Permanently delete archived reminders.";
  }
}

function renderNotificationButton() {
  const button = document.getElementById("notification-toggle");
  if (!button) {
    return;
  }

  if (!state.notificationSupported) {
    button.textContent = "Alerts unavailable";
    button.disabled = true;
    return;
  }

  if (state.notificationPermission === "granted") {
    button.textContent = "Alerts enabled";
    button.disabled = true;
    return;
  }

  if (state.notificationPermission === "denied") {
    button.textContent = "Alerts blocked";
    button.disabled = true;
    return;
  }

  button.textContent = "Enable alerts";
  button.disabled = false;
}

function emitReminderNotifications(reminders) {
  if (!state.notificationSupported || state.notificationPermission !== "granted") {
    return;
  }

  const now = Date.now();
  const dueSoonWindowMs = 10 * 60 * 1000;
  const nextNotified = { ...state.notifiedReminders };
  let didChange = false;

  reminders.forEach((reminder) => {
    const reminderId = String(reminder.id);
    if (reminder.status !== "pending") {
      if (reminderId in nextNotified) {
        delete nextNotified[reminderId];
        didChange = true;
      }
      return;
    }

    if (!reminder.due_at) {
      return;
    }

    const dueTime = new Date(reminder.due_at).getTime();
    if (Number.isNaN(dueTime) || dueTime > now + dueSoonWindowMs) {
      return;
    }

    const notificationKey = `${reminder.status}:${reminder.due_at}`;
    if (nextNotified[reminderId] === notificationKey) {
      return;
    }

    const body = dueTime <= now ? `Overdue: ${reminder.due_display}` : `Due soon: ${reminder.due_display}`;
    new Notification(`${state.assistantName} reminder: ${reminder.title}`, { body });
    nextNotified[reminderId] = notificationKey;
    didChange = true;
  });

  if (didChange) {
    state.notifiedReminders = nextNotified;
    saveNotifiedReminders();
  }
}

function applyOverview(overview) {
  state.assistantName = overview.assistant_name || state.assistantName;
  state.safeMode = overview.safe_mode;
  state.memoryEnabled = overview.memory_enabled;
  state.voiceAutoSpeak = Boolean(overview.voice_auto_speak);
  state.voiceAutoSend = Boolean(overview.voice_auto_send);
  state.voiceWakePhraseEnabled = Boolean(overview.voice_wake_phrase_enabled);
  state.voiceWakePhrase = normalizeVoiceText(overview.voice_wake_phrase || state.voiceWakePhrase || "hey zivra");
  state.workflowSupervisorEnabled = Boolean(overview.workflow_supervisor_enabled);
  state.workflowSupervisorMaxTasksPerCycle = clampNumber(
    overview.workflow_supervisor_max_tasks_per_cycle,
    1,
    5,
    state.workflowSupervisorMaxTasksPerCycle,
  );
  state.workflowSupervisorMaxPendingApprovals = clampNumber(
    overview.workflow_supervisor_max_pending_approvals,
    1,
    10,
    state.workflowSupervisorMaxPendingApprovals,
  );
  state.workflowSupervisorPauseOnFailure =
    overview.workflow_supervisor_pause_on_failure === undefined
      ? state.workflowSupervisorPauseOnFailure
      : Boolean(overview.workflow_supervisor_pause_on_failure);
  state.liveSearchResultLimit = clampNumber(
    overview.live_search_result_limit,
    1,
    10,
    state.liveSearchResultLimit,
  );
  state.dashboardRefreshSeconds = clampNumber(
    overview.dashboard_refresh_seconds,
    15,
    300,
    state.dashboardRefreshSeconds,
  );
  state.whatsappApiVersion = String(overview.whatsapp_api_version || state.whatsappApiVersion || "v23.0").trim() || "v23.0";
  state.whatsappPhoneNumberId = String(overview.whatsapp_phone_number_id || state.whatsappPhoneNumberId || "").trim();
  state.whatsappVerifyToken = String(overview.whatsapp_verify_token || state.whatsappVerifyToken || "").trim();
  state.plannerInfo = overview.planner || state.plannerInfo;
  state.reminderSummary = overview.reminder_summary || {};
  state.workflowSummary = overview.workflow_summary || state.workflowSummary;
  state.workflowSupervisorCycle = overview.workflow_supervisor_cycle || state.workflowSupervisorCycle;
  if (
    !state.recentActions.length &&
    !state.activityQuery &&
    state.activityFilter === "all" &&
    !state.activityDateFrom &&
    !state.activityDateTo
  ) {
    state.activityGroups = [];
    state.recentActions = overview.recent_actions || [];
    state.activityGroupTotal = groupActivityEntries(state.recentActions).length;
    state.activityTotal = state.recentActions.length;
    state.activityHasMore = false;
  }
  const plannerLabel = state.plannerInfo?.label || "Rule planner";
  document.title = `${state.assistantName} Control Room`;
  document.getElementById("assistant-name-heading").textContent = state.assistantName;
  document.getElementById("assistant-input-label").textContent = buildAssistantInputLabel(state.assistantName);
  document.getElementById("assistant-input").placeholder = buildAssistantPlaceholder(state.assistantName);
  document.getElementById("metric-pending").textContent = String(overview.pending_actions);
  document.getElementById("metric-reminders").textContent = String(overview.pending_reminders || 0);
  document.getElementById("metric-mode").textContent = `${overview.safe_mode ? "Safe on" : "Safe off"} | ${plannerLabel}`;
  document.getElementById("metric-roots").textContent = overview.approved_roots.join(", ") || "None";
  document.getElementById("metric-memory").textContent = overview.memory_enabled ? "Enabled" : "Disabled";

  const toggle = document.getElementById("safe-mode-toggle");
  toggle.textContent = overview.safe_mode ? "Disable safe mode" : "Enable safe mode";

  renderPending(overview.pending_queue || []);
  renderActivity(state.recentActions);
  renderTools(overview.tools || []);
  renderVoiceControls();
  renderSettingsPanel();
  renderMemoryPanel();
  renderClipboardPanel();
  renderCompanionAccessPanel();
  renderWorkflowPanel();
  renderResearchPanel();
  renderContentPanel();
  renderMessagingPanel();
  renderWebReaderPanel();
  renderReminderSummary(state.reminderSummary);
  renderReminderToolbar();
  renderNotificationButton();
  renderActivityControls();
  startBackgroundRefresh();
}

async function refreshOverview(runSupervisor = true) {
  const overview = await api(`/dashboard/overview?run_supervisor=${runSupervisor ? "1" : "0"}`);
  applyOverview(overview);
}

async function refreshActivity(options = {}) {
  const append = options.append === true;
  const params = buildActivityQueryParams({
    offset: append ? state.activityGroups.length : 0,
    limit: 6,
  });

  state.activityLoading = true;
  renderActivityControls();

  try {
    const payload = await api(`/dashboard/activity/groups?${params.toString()}`);
    const groups = payload.groups || [];
    state.activityGroups = append ? [...state.activityGroups, ...groups] : groups;
    state.recentActions = state.activityGroups.flatMap((group) => group.entries || []);
    state.activityGroupTotal = payload.total_groups || 0;
    state.activityTotal = payload.total_events || 0;
    state.activityHasMore = Boolean(payload.has_more);
    renderActivity(state.recentActions);
  } finally {
    state.activityLoading = false;
    renderActivityControls();
  }
}

async function refreshHistory() {
  const payload = await api(`/assistant/sessions/${state.sessionId}/history`);
  renderHistory(payload.history || []);
}

async function refreshMemorySessions() {
  const payload = await api("/assistant/sessions?limit=10");
  state.memorySessions = payload.sessions || [];
  syncCompanionAccessSessionSelection();
  renderMemoryPanel();
  renderCompanionAccessPanel();
}

async function refreshCompanionAccess() {
  const sessionId = getCompanionAccessSessionId();
  const payload = await api(`/sync/access?session_id=${encodeURIComponent(sessionId)}`);
  state.companionAccess = payload;
  state.companionAccessSessionId = payload.session_id || sessionId;
  state.companionAccessStatus = payload.candidates?.length
    ? payload.preferred_candidate?.host
      ? "Local companion URLs detected. A same-network phone-ready link has been highlighted."
      : "Local companion URLs detected. These links can carry the active session to another device."
    : "No local companion URLs were detected yet.";
  renderCompanionAccessPanel();
}

async function loadFileFolder(folderId = "", options = {}) {
  const query = folderId ? `?folder_id=${encodeURIComponent(folderId)}&limit=16` : "?limit=16";
  const payload = await api(`/files/folder${query}`);
  state.fileRoots = payload.roots || [];
  state.selectedFileFolder = payload.folder || null;
  state.selectedFileFolderId = payload.folder?.id || "";
  if (!options.preserveQuery) {
    state.filesQuery = "";
    state.fileSearchResults = [];
    const input = document.getElementById("files-search-input");
    if (input) {
      input.value = "";
    }
  }
  renderFilesStatus();
  renderFilesPanel();
}

async function refreshFiles() {
  if (state.filesQuery) {
    const payload = await api(`/files/search?q=${encodeURIComponent(state.filesQuery)}&limit=12`);
    state.fileRoots = payload.roots || [];
    state.fileSearchResults = payload.files || [];
    renderFilesStatus();
    renderFilesPanel();
    return;
  }

  await loadFileFolder(state.selectedFileFolderId || "", { preserveQuery: true });
}

async function refreshDocuments() {
  const path = state.documentsQuery
    ? `/documents/search?q=${encodeURIComponent(state.documentsQuery)}&limit=8`
    : "/documents?limit=8";
  const payload = await api(path);
  renderDocuments(payload.documents || []);
  renderDocumentsStatus((payload.documents || []).length);
  if (state.selectedDocumentId) {
    await loadSelectedDocument(state.selectedDocumentId, { silentNotFound: true });
  } else {
    renderDocumentReader(null);
  }
}

async function loadSelectedDocument(documentId, options = {}) {
  try {
    const document = await api(`/documents/read?document_id=${encodeURIComponent(documentId)}`);
    state.selectedDocumentId = document.id;
    state.selectedDocumentSummary = null;
    state.selectedDocumentAnalysis = null;
    state.selectedDocumentInspection = null;
    state.documentInspectionFilter = "";
    state.documentInspectionDepth = 2;
    state.documentInspectionPath = "";
    state.isSummarizingDocument = false;
    state.isAnalyzingDocument = false;
    state.isInspectingDocument = false;
    renderDocumentReader(document);
    return document;
  } catch (error) {
    if (!options.silentNotFound) {
      throw error;
    }
    state.selectedDocumentId = "";
    state.selectedDocumentSummary = null;
    state.selectedDocumentAnalysis = null;
    state.selectedDocumentInspection = null;
    state.documentInspectionFilter = "";
    state.documentInspectionDepth = 2;
    state.documentInspectionPath = "";
    state.isSummarizingDocument = false;
    state.isAnalyzingDocument = false;
    state.isInspectingDocument = false;
    renderDocumentReader(null);
    return null;
  }
}

async function summarizeSelectedDocument() {
  if (!state.selectedDocumentId || !state.selectedDocument) {
    return;
  }

  state.isSummarizingDocument = true;
  renderDocumentReader(state.selectedDocument);

  try {
    const payload = await api(`/documents/summary?document_id=${encodeURIComponent(state.selectedDocumentId)}`);
    state.selectedDocumentSummary = payload.summary || null;
    renderDocumentReader(payload.document || state.selectedDocument);
  } finally {
    state.isSummarizingDocument = false;
    renderDocumentReader(state.selectedDocument);
  }
}

async function analyzeSelectedDocument() {
  if (!state.selectedDocumentId || !state.selectedDocument) {
    return;
  }

  state.isAnalyzingDocument = true;
  renderDocumentReader(state.selectedDocument);

  try {
    const filterQuery = state.documentInspectionFilter
      ? `&filter=${encodeURIComponent(state.documentInspectionFilter)}`
      : "";
    const pathQuery = state.documentInspectionPath
      ? `&schema_path=${encodeURIComponent(state.documentInspectionPath)}`
      : "";
    const payload = await api(
      `/documents/analyze?document_id=${encodeURIComponent(state.selectedDocumentId)}${filterQuery}${pathQuery}`,
    );
    state.selectedDocumentAnalysis = payload.analysis || null;
    renderDocumentReader(payload.document || state.selectedDocument);
  } finally {
    state.isAnalyzingDocument = false;
    renderDocumentReader(state.selectedDocument);
  }
}

async function inspectSelectedDocument() {
  if (!state.selectedDocumentId || !state.selectedDocument) {
    return;
  }

  state.isInspectingDocument = true;
  renderDocumentReader(state.selectedDocument);

  try {
    const filterQuery = state.documentInspectionFilter
      ? `&filter=${encodeURIComponent(state.documentInspectionFilter)}`
      : "";
    const pathQuery = state.documentInspectionPath
      ? `&schema_path=${encodeURIComponent(state.documentInspectionPath)}`
      : "";
    const payload = await api(
      `/documents/inspect?document_id=${encodeURIComponent(state.selectedDocumentId)}${filterQuery}${pathQuery}&limit=8&schema_depth=${state.documentInspectionDepth}`,
    );
    state.selectedDocumentInspection = payload.inspection || null;
    renderDocumentReader(payload.document || state.selectedDocument);
  } finally {
    state.isInspectingDocument = false;
    renderDocumentReader(state.selectedDocument);
  }
}

async function refreshNotes() {
  const path = state.notesQuery
    ? `/notes/search?q=${encodeURIComponent(state.notesQuery)}&limit=8`
    : "/notes?limit=8";
  const payload = await api(path);
  renderNotes(payload.notes || []);
  renderNotesStatus((payload.notes || []).length);
  if (state.selectedNoteName && !state.isEditingNote) {
    await loadSelectedNote(state.selectedNoteName, { silentNotFound: true });
  } else if (state.isEditingNote) {
    renderNoteReader(state.selectedNote);
  } else {
    renderNoteReader(null);
  }
}

async function refreshEmails() {
  const payload = await api("/emails?limit=10");
  state.emails = payload.emails || [];
  state.emailSummary = payload.summary || {};
  state.emailDelivery = payload.delivery || { ready: false, status_label: "Not configured" };
  renderEmailPanel();
}

async function refreshMessages() {
  const payload = await api("/messages?limit=10");
  state.messages = payload.messages || [];
  state.messageSummary = payload.summary || {};
  state.messageDelivery = payload.delivery || { ready: true, status_label: "Browser handoff" };
  renderMessagingPanel();
}

async function refreshWorkflows() {
  const [workflowPayload, taskPayload] = await Promise.all([api("/workflows?limit=8"), api("/workflows/tasks?limit=10")]);
  state.workflows = workflowPayload.workflows || [];
  state.workflowTasks = taskPayload.tasks || [];
  state.workflowSummary = taskPayload.summary || workflowPayload.summary || state.workflowSummary;
  state.workflowSupervisorCycle = taskPayload.supervisor_cycle || workflowPayload.supervisor_cycle || state.workflowSupervisorCycle;
  renderWorkflowPanel();
}

async function saveWorkflow() {
  const payload = {
    name: state.workflowName.trim(),
    prompt: state.workflowPrompt.trim(),
    schedule_type: state.workflowScheduleType,
    active: Boolean(state.workflowStartActive),
  };

  if (payload.schedule_type === "hourly") {
    payload.interval_hours = clampNumber(state.workflowIntervalHours, 1, 24, 4);
  }

  if (payload.schedule_type === "daily" || payload.schedule_type === "weekly") {
    payload.run_hour = clampNumber(state.workflowRunHour, 0, 23, 9);
    payload.run_minute = clampNumber(state.workflowRunMinute, 0, 59, 0);
  }

  if (payload.schedule_type === "weekly") {
    payload.run_weekday = clampNumber(state.workflowRunWeekday, 0, 6, 0);
  }

  const response = await api("/workflows", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.workflowStatusMessage = response.message || "Workflow saved.";
  addTransientAssistantMessage(response.message);
  resetWorkflowComposer();
  await refreshAll();
}

async function toggleWorkflowActive(workflowId, active) {
  const response = await api(`/workflows/${encodeURIComponent(String(workflowId))}/toggle`, {
    method: "POST",
    body: JSON.stringify({ active }),
  });
  state.workflowStatusMessage = response.message || "Workflow updated.";
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function queueWorkflow(workflowId) {
  const response = await api(`/workflows/${encodeURIComponent(String(workflowId))}/queue`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.workflowStatusMessage = response.message || "Workflow queued.";
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function runWorkflowTask(taskId) {
  const response = await api(`/workflows/tasks/${encodeURIComponent(String(taskId))}/run`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.workflowStatusMessage = response.message || "Workflow task executed.";
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function cancelWorkflowTask(taskId) {
  const response = await api(`/workflows/tasks/${encodeURIComponent(String(taskId))}/cancel`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.workflowStatusMessage = response.message || "Workflow task canceled.";
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function retryWorkflowTask(taskId) {
  const response = await api(`/workflows/tasks/${encodeURIComponent(String(taskId))}/retry`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.workflowStatusMessage = response.message || "Workflow task re-queued.";
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function saveWorkflowSupervisorSettings() {
  const payload = {
    workflow_supervisor_enabled: Boolean(state.workflowSupervisorEnabled),
    workflow_supervisor_max_tasks_per_cycle: clampNumber(
      state.workflowSupervisorMaxTasksPerCycle,
      1,
      5,
      1,
    ),
    workflow_supervisor_max_pending_approvals: clampNumber(
      state.workflowSupervisorMaxPendingApprovals,
      1,
      10,
      1,
    ),
    workflow_supervisor_pause_on_failure: Boolean(state.workflowSupervisorPauseOnFailure),
  };

  const response = await api("/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  state.workflowStatusMessage = response.message || "Workflow supervisor settings updated.";
  await refreshAll();
}

async function runWorkflowSupervisorNow() {
  const response = await api("/workflows/supervisor/run", {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.workflowStatusMessage = response.message || "Supervisor cycle finished.";
  const cycle = response.cycle || state.workflowSupervisorCycle;
  state.workflowSupervisorCycle = cycle;
  addTransientAssistantMessage(response.message);
  await refreshOverview(false);
  await Promise.all([refreshWorkflows(), refreshActivity()]);
  state.workflowSupervisorCycle = cycle;
  renderWorkflowPanel();
}

async function refreshVisionStatus() {
  const payload = await api("/vision/status");
  state.visionStatus = payload.status || state.visionStatus;
  renderVisionPanel();
}

async function analyzeVisionInput() {
  if (!state.visionInputDataUrl || state.isAnalyzingVision) {
    return;
  }

  state.isAnalyzingVision = true;
  renderVisionPanel();
  try {
    const payload = await api("/vision/analyze", {
      method: "POST",
      body: JSON.stringify({
        data_url: state.visionInputDataUrl,
        filename: state.visionInputName || undefined,
        prompt: state.visionPrompt.trim() || undefined,
      }),
    });
    state.selectedVisionAnalysis = payload.analysis || null;
    if (payload.analysis?.model) {
      state.visionStatus = payload.analysis.model;
    }
    state.visionStatusMessage = payload.message || "Image analysis complete.";
    renderVisionPanel();
  } catch (error) {
    state.visionStatusMessage = error instanceof Error ? error.message : "Image analysis failed.";
    renderVisionPanel();
    throw error;
  } finally {
    state.isAnalyzingVision = false;
    renderVisionPanel();
  }
}

async function buildResearchBrief() {
  const query = state.researchQuery.trim();
  if (!query) {
    return;
  }

  state.isResearching = true;
  renderResearchPanel();

  try {
    const payload = await api(`/research/summary?q=${encodeURIComponent(query)}&search_limit=5&source_limit=3`);
    state.selectedResearchBrief = payload;
    state.researchStatusMessage = `Built a research brief for "${payload.query}".`;
    renderResearchPanel();
    renderContentPanel();
    await refreshActivity();
  } catch (error) {
    state.researchStatusMessage = error instanceof Error ? error.message : "Research brief failed.";
    renderResearchPanel();
    throw error;
  } finally {
    state.isResearching = false;
    renderResearchPanel();
  }
}

async function buildContentPackage() {
  const topic = state.contentTopic.trim();
  if (!topic || state.isGeneratingContent) {
    return;
  }

  state.isGeneratingContent = true;
  renderContentPanel();

  try {
    const payload = await api("/content/youtube-seo", {
      method: "POST",
      body: JSON.stringify({
        topic,
        audience: state.contentAudience.trim(),
        context: state.contentContext,
      }),
    });
    state.selectedContentPackage = payload;
    state.contentTopic = payload.topic || topic;
    state.contentAudience = payload.audience || state.contentAudience.trim();
    state.contentStatusMessage = `Generated a creator package for "${payload.topic || topic}".`;
    renderContentPanel();
    await refreshActivity();
  } catch (error) {
    state.contentStatusMessage = error instanceof Error ? error.message : "Creator package generation failed.";
    renderContentPanel();
    throw error;
  } finally {
    state.isGeneratingContent = false;
    renderContentPanel();
  }
}

async function loadSelectedNote(name, options = {}) {
  try {
    const note = await api(`/notes/${encodeURIComponent(name)}`);
    state.selectedNoteName = note.name;
    state.noteEditorContent = note.content || "";
    state.isEditingNote = false;
    renderNoteReader(note);
    return note;
  } catch (error) {
    if (!options.silentNotFound) {
      throw error;
    }
    state.selectedNoteName = "";
    state.noteEditorContent = "";
    state.isEditingNote = false;
    renderNoteReader(null);
    return null;
  }
}

async function saveSelectedNote() {
  if (!state.selectedNoteName) {
    return;
  }

  const response = await api(`/notes/${encodeURIComponent(state.selectedNoteName)}`, {
    method: "PUT",
    body: JSON.stringify({ content: state.noteEditorContent }),
  });
  addTransientAssistantMessage(response.message);
  state.selectedNoteName = response.note.name;
  state.noteEditorContent = response.note.content || "";
  state.isEditingNote = false;
  renderNoteReader(response.note);
  await refreshNotes();
}

async function loadClipboard() {
  const payload = await api("/clipboard");
  state.clipboardText = payload.text || "";
  state.clipboardMetadata = payload.metadata || null;
  state.clipboardStatusMessage = payload.message || "Clipboard loaded from the local desktop.";
  renderClipboardPanel();
  await refreshActivity();
}

async function writeClipboard() {
  const payload = await api("/clipboard", {
    method: "POST",
    body: JSON.stringify({ text: state.clipboardText }),
  });
  state.clipboardMetadata = payload.metadata || null;
  state.clipboardStatusMessage = payload.message || "Clipboard updated from the dashboard.";
  renderClipboardPanel();
  await refreshActivity();
}

async function saveEmailDraft() {
  const response = await api("/emails/drafts", {
    method: "POST",
    body: JSON.stringify({
      to: state.emailComposeTo.trim() || "recipient@example.com",
      subject: state.emailComposeSubject.trim() || "Draft from Zivra",
      body: state.emailComposeBody,
      source: "dashboard",
    }),
  });
  state.emailStatusMessage = response.message || "Email draft saved.";
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function saveWhatsAppDraft() {
  const response = await api("/messages/whatsapp/drafts", {
    method: "POST",
    body: JSON.stringify({
      to: state.whatsappComposeTo.trim(),
      body: state.whatsappComposeBody.trim(),
      source: "dashboard",
    }),
  });
  state.messageStatusMessage = response.message || "WhatsApp draft saved.";
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function sendSavedEmail(emailId) {
  try {
    const response = await api(`/emails/${encodeURIComponent(String(emailId))}/send`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    state.emailStatusMessage = response.message || "Email sent.";
    addTransientAssistantMessage(response.message);
    await refreshAll();
  } catch (error) {
    state.emailStatusMessage = error instanceof Error ? error.message : "Email send failed.";
    await refreshAll();
    throw error;
  }
}

async function sendSavedWhatsAppMessage(messageId) {
  try {
    const response = await api(`/messages/${encodeURIComponent(String(messageId))}/send`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    state.messageStatusMessage = response.message || "WhatsApp message dispatched.";
    addTransientAssistantMessage(response.message);
    await refreshAll();
  } catch (error) {
    state.messageStatusMessage = error instanceof Error ? error.message : "WhatsApp dispatch failed.";
    await refreshAll();
    throw error;
  }
}

async function searchWeb() {
  const query = state.webSearchQuery.trim();
  if (!query) {
    return;
  }

  state.isSearchingWeb = true;
  renderWebReaderPanel();
  try {
    const payload = await api(
      `/web/search?q=${encodeURIComponent(query)}&limit=${encodeURIComponent(String(state.liveSearchResultLimit))}`,
    );
    state.webSearchResults = payload.results || [];
    state.webSearchStatusMessage = state.webSearchResults.length
      ? `Loaded ${state.webSearchResults.length} live result${state.webSearchResults.length === 1 ? "" : "s"} for "${payload.query}".`
      : `No live results were found for "${payload.query}".`;
    renderWebReaderPanel();
    await refreshActivity();
  } catch (error) {
    state.webSearchStatusMessage = error instanceof Error ? error.message : "Web search failed.";
    throw error;
  } finally {
    state.isSearchingWeb = false;
    renderWebReaderPanel();
  }
}

async function readWebPage() {
  const url = state.webReaderUrl.trim();
  if (!url) {
    return;
  }

  state.isReadingWebPage = true;
  renderWebReaderPanel();
  try {
    const payload = await api(`/web/read?url=${encodeURIComponent(url)}`);
    state.selectedWebPage = payload.page || null;
    state.selectedWebSummary = null;
    state.webReaderStatusMessage = state.selectedWebPage
      ? `Loaded ${state.selectedWebPage.title || state.selectedWebPage.url} from the safe web reader.`
      : "Loaded the webpage.";
    if (state.selectedWebPage?.url) {
      state.webReaderUrl = state.selectedWebPage.url;
    }
    renderWebReaderPanel();
    await refreshActivity();
  } catch (error) {
    state.webReaderStatusMessage = error instanceof Error ? error.message : "Webpage read failed.";
    throw error;
  } finally {
    state.isReadingWebPage = false;
    renderWebReaderPanel();
  }
}

async function summarizeWebPage() {
  const url = state.webReaderUrl.trim();
  if (!url) {
    return;
  }

  state.isSummarizingWebPage = true;
  renderWebReaderPanel();
  try {
    const payload = await api(`/web/summary?url=${encodeURIComponent(url)}`);
    state.selectedWebPage = payload.page || state.selectedWebPage;
    state.selectedWebSummary = payload.summary || null;
    state.webReaderStatusMessage = state.selectedWebPage
      ? `Summarized ${state.selectedWebPage.title || state.selectedWebPage.url} from the safe web reader.`
      : "Summarized the webpage.";
    if (state.selectedWebPage?.url) {
      state.webReaderUrl = state.selectedWebPage.url;
    }
    renderWebReaderPanel();
    await refreshActivity();
  } catch (error) {
    state.webReaderStatusMessage = error instanceof Error ? error.message : "Webpage summary failed.";
    throw error;
  } finally {
    state.isSummarizingWebPage = false;
    renderWebReaderPanel();
  }
}

async function refreshReminders() {
  const payload = await api(`/reminders?limit=8&include_completed=true&include_archived=${state.includeArchived}`);
  renderReminders(payload.reminders || []);
  emitReminderNotifications(payload.reminders || []);
}

async function refreshAll() {
  await refreshOverview();
  await Promise.all([
    refreshHistory(),
    refreshMemorySessions(),
    refreshSecretsStatus(),
    refreshCompanionAccess(),
    refreshVisionStatus(),
    refreshFiles(),
    refreshDocuments(),
    refreshNotes(),
    refreshEmails(),
    refreshMessages(),
    refreshWorkflows(),
    refreshReminders(),
    refreshActivity(),
  ]);
}

async function sendMessage(message) {
  if (!message.trim() || state.sending) {
    return;
  }

  state.sending = true;
  renderVoiceControls();
  const submitButton = document.querySelector("#assistant-form button[type='submit']");
  submitButton.disabled = true;
  submitButton.textContent = "Sending";

  try {
    const response = await api("/assistant/message", {
      method: "POST",
      body: JSON.stringify({
        message,
        session_id: state.sessionId,
      }),
    });

    if (!state.memoryEnabled) {
      state.transientHistory.push({ role: "user", content: message });
      state.transientHistory.push({ role: "assistant", content: response.assistant_text });
    }

    document.getElementById("assistant-input").value = "";
    await refreshAll();
    if (state.voiceAutoSpeak && response.assistant_text) {
      speakText(response.assistant_text);
    }
  } finally {
    state.sending = false;
    submitButton.disabled = false;
    submitButton.textContent = "Send";
    renderVoiceControls();
  }
}

async function toggleSafeMode() {
  const toggle = document.getElementById("safe-mode-toggle");
  toggle.disabled = true;
  try {
    await api("/runtime/safe-mode", {
      method: "POST",
      body: JSON.stringify({ enabled: !state.safeMode }),
    });
    await refreshOverview();
  } finally {
    toggle.disabled = false;
  }
}

async function toggleMemory() {
  const nextValue = !state.memoryEnabled;
  await api("/runtime/memory", {
    method: "POST",
    body: JSON.stringify({ enabled: nextValue }),
  });
  state.memoryStatusMessage = nextValue
    ? "Memory enabled. New conversation turns will be saved locally."
    : "Memory disabled. Existing stored sessions remain reviewable until you delete them.";
  await refreshAll();
}

async function saveSettings() {
  const assistantNameInput = document.getElementById("settings-assistant-name");
  const voiceAutoSpeakInput = document.getElementById("settings-voice-auto-speak");
  const voiceAutoSendInput = document.getElementById("settings-voice-auto-send");
  const voiceWakeEnabledInput = document.getElementById("settings-voice-wake-enabled");
  const voiceWakePhraseInput = document.getElementById("settings-voice-wake-phrase");
  const searchLimitInput = document.getElementById("settings-search-limit");
  const refreshSecondsInput = document.getElementById("settings-refresh-seconds");
  const whatsappApiVersionInput = document.getElementById("settings-whatsapp-api-version");
  const whatsappPhoneNumberIdInput = document.getElementById("settings-whatsapp-phone-number-id");
  const whatsappVerifyTokenInput = document.getElementById("settings-whatsapp-verify-token");
  const payload = {
    assistant_name: assistantNameInput.value.trim() || state.assistantName,
    voice_auto_speak: Boolean(voiceAutoSpeakInput?.checked),
    voice_auto_send: Boolean(voiceAutoSendInput?.checked),
    voice_wake_phrase_enabled: Boolean(voiceWakeEnabledInput?.checked),
    voice_wake_phrase: normalizeVoiceText(voiceWakePhraseInput?.value || state.voiceWakePhrase || "hey zivra"),
    live_search_result_limit: clampNumber(searchLimitInput.value, 1, 10, state.liveSearchResultLimit),
    dashboard_refresh_seconds: clampNumber(
      refreshSecondsInput.value,
      15,
      300,
      state.dashboardRefreshSeconds,
    ),
    whatsapp_api_version: (whatsappApiVersionInput?.value || state.whatsappApiVersion || "v23.0").trim() || "v23.0",
    whatsapp_phone_number_id: (whatsappPhoneNumberIdInput?.value || "").trim(),
    whatsapp_verify_token: (whatsappVerifyTokenInput?.value || "").trim(),
  };

  const response = await api("/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  state.settingsStatusMessage = response.message || "Settings updated.";
  if (!payload.voice_auto_speak) {
    stopSpeaking();
  }
  await refreshAll();
}

async function refreshSecretsStatus() {
  state.secretsInfo = await api("/settings/secrets");
  renderSettingsPanel();
}

async function resetSettings() {
  const response = await api("/settings/reset", {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.settingsStatusMessage = response.message || "Settings reset to defaults.";
  await refreshAll();
}

async function saveSecrets() {
  const llmApiKeyInput = document.getElementById("secret-llm-api-key");
  const smtpUsernameInput = document.getElementById("secret-smtp-username");
  const smtpPasswordInput = document.getElementById("secret-smtp-password");
  const whatsappAccessTokenInput = document.getElementById("secret-whatsapp-access-token");
  const whatsappAppSecretInput = document.getElementById("secret-whatsapp-app-secret");
  const payload = {};

  if (llmApiKeyInput.value.trim()) {
    payload.llm_api_key = llmApiKeyInput.value.trim();
  }
  if (smtpUsernameInput.value.trim()) {
    payload.smtp_username = smtpUsernameInput.value.trim();
  }
  if (smtpPasswordInput.value.trim()) {
    payload.smtp_password = smtpPasswordInput.value.trim();
  }
  if (whatsappAccessTokenInput.value.trim()) {
    payload.whatsapp_access_token = whatsappAccessTokenInput.value.trim();
  }
  if (whatsappAppSecretInput.value.trim()) {
    payload.whatsapp_app_secret = whatsappAppSecretInput.value.trim();
  }

  if (!Object.keys(payload).length) {
    state.secretsStatusMessage = "Enter at least one new secret value to save.";
    renderSettingsPanel();
    return;
  }

  const response = await api("/settings/secrets", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  state.secretsStatusMessage = response.message || "Encrypted secrets updated.";
  llmApiKeyInput.value = "";
  smtpUsernameInput.value = "";
  smtpPasswordInput.value = "";
  whatsappAccessTokenInput.value = "";
  whatsappAppSecretInput.value = "";
  await refreshAll();
}

async function clearStoredSecrets() {
  const response = await api("/settings/secrets/clear", {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.secretsStatusMessage = response.message || "Stored encrypted secrets cleared.";
  await refreshAll();
}

async function clearSession(sessionId = state.sessionId) {
  await api(`/assistant/sessions/${encodeURIComponent(sessionId)}/clear`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  if (sessionId === state.sessionId) {
    state.transientHistory = [];
    state.memoryStatusMessage = "Current session history cleared.";
  } else {
    state.memoryStatusMessage = `Deleted stored session ${sessionId}.`;
  }
  await Promise.all([refreshHistory(), refreshMemorySessions()]);
}

async function clearAllMemory() {
  await api("/assistant/sessions/clear-all", {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.transientHistory = [];
  state.memoryStatusMessage = "All stored session history cleared.";
  await Promise.all([refreshHistory(), refreshMemorySessions()]);
}

async function resolvePendingAction(actionId, decision) {
  const path = decision === "confirm" ? "confirm" : "reject";
  const payload = decision === "confirm" ? {} : { reason: "Action rejected from the dashboard." };
  const response = await api(`/assistant/actions/${actionId}/${path}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  addTransientAssistantMessage(response.assistant_text);
  await refreshAll();
}

async function resolvePendingGroup(groupId, decision) {
  const path = decision === "confirm" ? "confirm" : "reject";
  const payload = decision === "confirm" ? {} : { reason: "Action group rejected from the dashboard." };
  const response = await api(`/assistant/action-groups/${groupId}/${path}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  addTransientAssistantMessage(response.assistant_text);
  await refreshAll();
}

async function updateReminder(reminderId, action, payload = {}) {
  const response = await api(`/reminders/${reminderId}/${action}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function archiveCompletedReminders() {
  const response = await api("/reminders/archive-completed", {
    method: "POST",
    body: JSON.stringify({}),
  });
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function restoreArchivedReminders() {
  const response = await api("/reminders/restore-archived", {
    method: "POST",
    body: JSON.stringify({}),
  });
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function purgeArchivedReminders() {
  const response = await api("/reminders/purge-archived", {
    method: "POST",
    body: JSON.stringify({}),
  });
  addTransientAssistantMessage(response.message);
  await refreshAll();
}

async function toggleArchivedReminders() {
  state.includeArchived = !state.includeArchived;
  renderReminderToolbar();
  await refreshReminders();
}

async function enableReminderAlerts() {
  if (!state.notificationSupported || state.notificationPermission === "granted") {
    renderNotificationButton();
    return;
  }

  const permission = await Notification.requestPermission();
  state.notificationPermission = permission;
  renderNotificationButton();
  if (permission === "granted") {
    await refreshReminders();
  }
}

function startBackgroundRefresh() {
  const intervalMs = clampNumber(state.dashboardRefreshSeconds, 15, 300, 60) * 1000;
  if (backgroundRefreshTimerId && backgroundRefreshIntervalMs === intervalMs) {
    return;
  }

  if (backgroundRefreshTimerId) {
    window.clearInterval(backgroundRefreshTimerId);
  }

  backgroundRefreshIntervalMs = intervalMs;
  backgroundRefreshTimerId = window.setInterval(async () => {
    try {
      await Promise.all([refreshOverview(), refreshReminders(), refreshActivity()]);
    } catch (error) {
      console.error(error);
    }
  }, intervalMs);
}

function bindEvents() {
  document.getElementById("assistant-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.getElementById("assistant-input");
    if (state.voiceListening) {
      stopVoiceListening();
    }
    await sendMessage(input.value);
  });

  document.getElementById("open-command-palette").addEventListener("click", () => {
    openCommandPalette();
  });

  document.getElementById("close-command-palette").addEventListener("click", () => {
    closeCommandPalette();
  });

  document.getElementById("command-palette-backdrop").addEventListener("click", () => {
    closeCommandPalette();
  });

  document.getElementById("command-palette-input").addEventListener("input", (event) => {
    state.commandPaletteQuery = event.target.value;
    state.commandPaletteSelection = 0;
    renderCommandPalette();
  });

  document.getElementById("command-palette-input").addEventListener("keydown", async (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveCommandPaletteSelection(1);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveCommandPaletteSelection(-1);
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      closeCommandPalette();
      return;
    }

    if (event.key === "Enter") {
      event.preventDefault();
      const entry = getCommandPaletteEntries()[state.commandPaletteSelection];
      await runCommandPaletteEntry(entry);
    }
  });

  document.getElementById("command-palette-results").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-command-palette-item]");
    if (!button) {
      return;
    }

    const entry = getCommandPaletteEntries().find((item) => item.id === button.dataset.commandId);
    await runCommandPaletteEntry(entry);
  });

  document.getElementById("voice-toggle").addEventListener("click", () => {
    if (state.voiceListening) {
      stopVoiceListening();
      return;
    }
    startVoiceListening();
  });

  document.getElementById("speak-latest-reply").addEventListener("click", () => {
    if (state.voiceSpeaking) {
      stopSpeaking();
      return;
    }
    const latestReply = getLatestAssistantReply();
    if (!latestReply) {
      state.voiceStatusMessage = "There is no assistant reply to read aloud yet.";
      renderVoiceControls();
      return;
    }
    speakText(latestReply);
  });

  document.getElementById("safe-mode-toggle").addEventListener("click", toggleSafeMode);
  document.getElementById("settings-panel").addEventListener("submit", async (event) => {
    if (event.target.id !== "settings-form" && event.target.id !== "secrets-form") {
      return;
    }

    event.preventDefault();
    const submitButton = event.target.querySelector("button[type='submit']");
    submitButton.disabled = true;
    try {
      if (event.target.id === "settings-form") {
        await saveSettings();
      } else {
        await saveSecrets();
      }
    } finally {
      submitButton.disabled = false;
    }
  });
  document.getElementById("settings-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button || (button.id !== "reset-settings" && button.id !== "clear-secrets")) {
      return;
    }

    button.disabled = true;
    try {
      if (button.id === "reset-settings") {
        await resetSettings();
      } else {
        await clearStoredSecrets();
      }
    } finally {
      button.disabled = false;
    }
  });
  document.getElementById("companion-access-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }

    if (button.id === "refresh-companion-access") {
      button.disabled = true;
      try {
        await refreshCompanionAccess();
      } catch {
        flashButtonLabel(button, "Failed");
      } finally {
        button.disabled = false;
      }
      return;
    }

    const selectedSessionId = button.dataset.companionSessionId || "";
    if (selectedSessionId) {
      button.disabled = true;
      state.companionAccessSessionId = selectedSessionId;
      try {
        await refreshCompanionAccess();
      } catch {
        flashButtonLabel(button, "Failed");
      } finally {
        button.disabled = false;
      }
      return;
    }

    const action = button.dataset.companionAccessAction;
    if (!action) {
      return;
    }

    button.disabled = true;
    try {
      const preferredCandidate = state.companionAccess?.preferred_candidate && state.companionAccess.preferred_candidate.host
        ? state.companionAccess.preferred_candidate
        : (state.companionAccess?.candidates || []).find((candidate) => candidate.preferred) || null;
      const selectedSession = getSelectedCompanionSessionSummary();

      if (action === "share-mobile") {
        await shareCompanionAccess(preferredCandidate, selectedSession);
        flashButtonLabel(button, "Shared");
        return;
      }

      if (action === "copy-handoff-summary") {
        await copyTextToClipboard(buildCompanionHandoffSummary(preferredCandidate, selectedSession));
        flashButtonLabel(button, "Copied summary");
        return;
      }

      if (action === "draft-email") {
        const draft = buildCompanionEmailDraft(preferredCandidate, selectedSession);
        state.emailComposeSubject = draft.subject;
        state.emailComposeBody = draft.body;
        state.emailStatusMessage = "Loaded the selected handoff into the email draft composer.";
        renderEmailPanel();
        document.getElementById("email-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
        flashButtonLabel(button, "Email ready");
        return;
      }

      if (action === "draft-whatsapp") {
        state.whatsappComposeBody = buildCompanionWhatsAppDraft(preferredCandidate, selectedSession);
        state.messageStatusMessage = "Loaded the selected handoff into the WhatsApp draft composer.";
        renderMessagingPanel();
        document.getElementById("messaging-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
        flashButtonLabel(button, "WhatsApp ready");
        return;
      }

      await copyTextToClipboard(button.dataset.url || "");
      flashButtonLabel(button, action === "copy-control-room" ? "Copied room" : "Copied mobile");
    } catch {
      flashButtonLabel(button, "Failed");
    } finally {
      button.disabled = false;
    }
  });
  document.getElementById("refresh-files").addEventListener("click", refreshFiles);
  document.getElementById("refresh-documents").addEventListener("click", refreshDocuments);
  document.getElementById("refresh-emails").addEventListener("click", refreshEmails);
  document.getElementById("refresh-messages").addEventListener("click", refreshMessages);
  document.getElementById("refresh-workflows").addEventListener("click", refreshWorkflows);
  document.getElementById("refresh-notes").addEventListener("click", refreshNotes);
  document.getElementById("refresh-reminders").addEventListener("click", refreshReminders);
  document.getElementById("notification-toggle").addEventListener("click", enableReminderAlerts);
  document.getElementById("toggle-archived-reminders").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await toggleArchivedReminders();
    } finally {
      button.disabled = false;
    }
  });
  document.getElementById("archive-completed-reminders").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await archiveCompletedReminders();
    } finally {
      button.disabled = false;
    }
  });
  document.getElementById("restore-archived-reminders").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await restoreArchivedReminders();
    } finally {
      button.disabled = false;
    }
  });
  document.getElementById("purge-archived-reminders").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      if (!window.confirm("Permanently delete all archived reminders? This cannot be undone.")) {
        return;
      }
      await purgeArchivedReminders();
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("pending-list").addEventListener("click", async (event) => {
    const groupButton = event.target.closest("button[data-group-action]");
    if (groupButton) {
      groupButton.disabled = true;
      try {
        await resolvePendingGroup(groupButton.dataset.groupId, groupButton.dataset.groupAction);
      } finally {
        groupButton.disabled = false;
      }
      return;
    }

    const button = event.target.closest("button[data-action]");
    if (!button) {
      return;
    }

    button.disabled = true;
    try {
      await resolvePendingAction(button.dataset.id, button.dataset.action);
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("activity-toolbar").addEventListener("click", async (event) => {
    const viewButton = event.target.closest("button[data-activity-view-action]");
    if (viewButton) {
      const viewId = viewButton.dataset.activityViewId;
      if (!viewId) {
        return;
      }

      if (viewButton.dataset.activityViewAction === "remove") {
        removeSavedActivityView(viewId);
        return;
      }

      viewButton.disabled = true;
      try {
        await applySavedActivityView(viewId);
      } finally {
        viewButton.disabled = false;
      }
      return;
    }

    const button = event.target.closest("button[data-activity-filter]");
    if (!button) {
      return;
    }

    state.activityFilter = button.dataset.activityFilter || "all";
    state.expandedActivityEvents = {};
    await refreshActivity();
  });

  document.getElementById("activity-list").addEventListener("click", async (event) => {
    const groupButton = event.target.closest("button[data-activity-group-action]");
    if (groupButton) {
      const groupKey = groupButton.dataset.activityGroupKey;
      if (!groupKey) {
        return;
      }

      groupButton.disabled = true;
      try {
        if (groupButton.dataset.activityGroupAction === "copy") {
          await copyActivityGroupExport(groupKey, groupButton);
          return;
        }

        if (groupButton.dataset.activityGroupAction === "download") {
          downloadActivityGroupExport(groupKey, groupButton);
        }
      } finally {
        groupButton.disabled = false;
      }
      return;
    }

    const button = event.target.closest("button[data-activity-event-toggle]");
    if (!button) {
      return;
    }

    const eventKey = button.dataset.activityEventToggle;
    if (!eventKey) {
      return;
    }

    state.expandedActivityEvents[eventKey] = !state.expandedActivityEvents[eventKey];
    renderActivity(state.recentActions);
  });

  document.getElementById("activity-search-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.getElementById("activity-search-input");
    const dateFromInput = document.getElementById("activity-date-from");
    const dateToInput = document.getElementById("activity-date-to");
    state.activityQuery = input.value.trim();
    state.activityDateFrom = dateFromInput ? dateFromInput.value : "";
    state.activityDateTo = dateToInput ? dateToInput.value : "";
    state.expandedActivityEvents = {};
    await refreshActivity();
  });

  document.getElementById("save-activity-view").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await saveCurrentActivityView(button);
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("copy-activity-export").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await copyActivityExport(button);
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("download-activity-export").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await downloadActivityExport(button);
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("clear-activity-search").addEventListener("click", async () => {
    state.activityQuery = "";
    state.activityFilter = "all";
    state.activityDateFrom = "";
    state.activityDateTo = "";
    state.expandedActivityEvents = {};
    document.getElementById("activity-search-input").value = "";
    document.getElementById("activity-date-from").value = "";
    document.getElementById("activity-date-to").value = "";
    await refreshActivity();
  });

  document.getElementById("load-more-activity").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await refreshActivity({ append: true });
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("clipboard-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }

    if (button.id === "clear-clipboard-editor") {
      state.clipboardText = "";
      state.clipboardStatusMessage = "Clipboard editor cleared locally.";
      state.clipboardMetadata = null;
      renderClipboardPanel();
      return;
    }

    if (button.id === "read-clipboard") {
      button.disabled = true;
      try {
        await loadClipboard();
      } catch {
        flashButtonLabel(button, "Failed");
      } finally {
        button.disabled = false;
      }
      return;
    }

    if (button.id === "write-clipboard") {
      button.disabled = true;
      try {
        await writeClipboard();
      } catch {
        flashButtonLabel(button, "Failed");
      } finally {
        button.disabled = false;
      }
    }
  });

  document.getElementById("clipboard-panel").addEventListener("input", (event) => {
    if (event.target.id === "clipboard-editor") {
      state.clipboardText = event.target.value;
    }
  });

  document.getElementById("email-panel").addEventListener("submit", async (event) => {
    const form = event.target.closest("form#email-compose-form");
    if (!form) {
      return;
    }

    event.preventDefault();
    try {
      await saveEmailDraft();
    } catch (error) {
      state.emailStatusMessage = error instanceof Error ? error.message : "Email draft save failed.";
      renderEmailPanel();
    }
  });

  document.getElementById("email-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }

    if (button.id === "clear-email-compose") {
      state.emailComposeTo = "recipient@example.com";
      state.emailComposeSubject = "Draft from Zivra";
      state.emailComposeBody = "";
      state.emailStatusMessage = "Email composer cleared locally.";
      renderEmailPanel();
      return;
    }

    const action = button.dataset.emailAction;
    if (!action) {
      return;
    }

    button.disabled = true;
    try {
      if (action === "copy-body") {
        const email = findEmailById(button.dataset.emailId || "");
        if (!email) {
          flashButtonLabel(button, "Missing");
          return;
        }
        await copyTextToClipboard(email.body || "");
        flashButtonLabel(button, "Copied");
        return;
      }

      if (action === "send") {
        const email = findEmailById(button.dataset.emailId || "");
        if (!email) {
          flashButtonLabel(button, "Missing");
          return;
        }
        const confirmed = window.confirm(`Send "${email.subject}" to ${email.to}?`);
        if (!confirmed) {
          return;
        }
        await sendSavedEmail(email.id);
      }
    } catch {
      flashButtonLabel(button, "Failed");
      renderEmailPanel();
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("email-panel").addEventListener("input", (event) => {
    if (event.target.id === "email-to") {
      state.emailComposeTo = event.target.value;
    }
    if (event.target.id === "email-subject") {
      state.emailComposeSubject = event.target.value;
    }
    if (event.target.id === "email-body") {
      state.emailComposeBody = event.target.value;
    }
  });

  document.getElementById("messaging-panel").addEventListener("submit", async (event) => {
    const form = event.target.closest("form#whatsapp-compose-form");
    if (!form) {
      return;
    }

    event.preventDefault();
    try {
      await saveWhatsAppDraft();
    } catch (error) {
      state.messageStatusMessage = error instanceof Error ? error.message : "WhatsApp draft save failed.";
      renderMessagingPanel();
    }
  });

  document.getElementById("messaging-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }

    if (button.id === "clear-whatsapp-compose") {
      state.whatsappComposeTo = "+15551234567";
      state.whatsappComposeBody = "";
      state.messageStatusMessage = "WhatsApp composer cleared locally.";
      renderMessagingPanel();
      return;
    }

    const action = button.dataset.messageAction;
    if (!action) {
      return;
    }

    button.disabled = true;
    try {
      if (action === "copy-body") {
        const outboxMessage = findMessageById(button.dataset.messageId || "");
        if (!outboxMessage) {
          flashButtonLabel(button, "Missing");
          return;
        }
        await copyTextToClipboard(outboxMessage.body || "");
        flashButtonLabel(button, "Copied");
        return;
      }

      if (action === "reply") {
        const inboxMessage = findMessageById(button.dataset.messageId || "");
        if (!inboxMessage) {
          flashButtonLabel(button, "Missing");
          return;
        }
        state.whatsappComposeTo = inboxMessage.to || state.whatsappComposeTo;
        state.messageStatusMessage = `Loaded ${inboxMessage.to || "the sender"} into the WhatsApp composer.`;
        renderMessagingPanel();
        flashButtonLabel(button, "Ready");
        return;
      }

      if (action === "dispatch") {
        const outboxMessage = findMessageById(button.dataset.messageId || "");
        if (!outboxMessage) {
          flashButtonLabel(button, "Missing");
          return;
        }
        const confirmed = window.confirm(state.messageDelivery?.delivery_mode === "cloud_api"
          ? `Send a WhatsApp message to ${outboxMessage.to} through the configured Meta Cloud API business number?`
          : `Open a WhatsApp compose window for ${outboxMessage.to}? Final send still happens inside WhatsApp.`);
        if (!confirmed) {
          return;
        }
        await sendSavedWhatsAppMessage(outboxMessage.id);
      }
    } catch {
      flashButtonLabel(button, "Failed");
      renderMessagingPanel();
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("messaging-panel").addEventListener("input", (event) => {
    if (event.target.id === "whatsapp-to") {
      state.whatsappComposeTo = event.target.value;
    }
    if (event.target.id === "whatsapp-body") {
      state.whatsappComposeBody = event.target.value;
    }
  });

  document.getElementById("workflow-panel").addEventListener("submit", async (event) => {
    const form = event.target.closest("form");
    if (!form || (form.id !== "workflow-form" && form.id !== "workflow-supervisor-form")) {
      return;
    }

    event.preventDefault();
    const submitButton = form.querySelector("button[type='submit']");
    submitButton.disabled = true;
    try {
      if (form.id === "workflow-form") {
        await saveWorkflow();
      } else {
        await saveWorkflowSupervisorSettings();
      }
    } catch (error) {
      state.workflowStatusMessage = error instanceof Error ? error.message : "Workflow update failed.";
      renderWorkflowPanel();
    } finally {
      submitButton.disabled = false;
    }
  });

  document.getElementById("workflow-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }

    if (button.id === "clear-workflow-compose") {
      resetWorkflowComposer();
      state.workflowStatusMessage = "Workflow composer reset.";
      renderWorkflowPanel();
      return;
    }

    if (button.id === "run-workflow-supervisor") {
      button.disabled = true;
      try {
        await runWorkflowSupervisorNow();
      } catch {
        flashButtonLabel(button, "Failed");
        renderWorkflowPanel();
      } finally {
        button.disabled = false;
      }
      return;
    }

    const workflowAction = button.dataset.workflowAction;
    if (workflowAction) {
      button.disabled = true;
      try {
        const workflow = findWorkflowById(button.dataset.workflowId || "");
        if (!workflow) {
          flashButtonLabel(button, "Missing");
          return;
        }

        if (workflowAction === "toggle") {
          await toggleWorkflowActive(workflow.id, !workflow.active);
          return;
        }

        if (workflowAction === "queue") {
          await queueWorkflow(workflow.id);
        }
      } catch {
        flashButtonLabel(button, "Failed");
        renderWorkflowPanel();
      } finally {
        button.disabled = false;
      }
      return;
    }

    const taskAction = button.dataset.workflowTaskAction;
    if (!taskAction) {
      return;
    }

    button.disabled = true;
    try {
      const task = findWorkflowTaskById(button.dataset.taskId || "");
      if (!task) {
        flashButtonLabel(button, "Missing");
        return;
      }

      if (taskAction === "run") {
        await runWorkflowTask(task.id);
        return;
      }

      if (taskAction === "cancel") {
        const confirmed = window.confirm(`Cancel queued task ${task.id} for ${task.workflow_name}?`);
        if (!confirmed) {
          return;
        }
        await cancelWorkflowTask(task.id);
        return;
      }

      if (taskAction === "retry") {
        await retryWorkflowTask(task.id);
      }
    } catch {
      flashButtonLabel(button, "Failed");
      renderWorkflowPanel();
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("workflow-panel").addEventListener("input", (event) => {
    if (event.target.id === "workflow-name") {
      state.workflowName = event.target.value;
    }
    if (event.target.id === "workflow-prompt") {
      state.workflowPrompt = event.target.value;
    }
    if (event.target.id === "workflow-interval-hours") {
      state.workflowIntervalHours = clampNumber(event.target.value, 1, 24, state.workflowIntervalHours);
    }
    if (event.target.id === "workflow-run-hour") {
      state.workflowRunHour = clampNumber(event.target.value, 0, 23, state.workflowRunHour);
    }
    if (event.target.id === "workflow-run-minute") {
      state.workflowRunMinute = clampNumber(event.target.value, 0, 59, state.workflowRunMinute);
    }
    if (event.target.id === "workflow-supervisor-max-tasks") {
      state.workflowSupervisorMaxTasksPerCycle = clampNumber(
        event.target.value,
        1,
        5,
        state.workflowSupervisorMaxTasksPerCycle,
      );
    }
    if (event.target.id === "workflow-supervisor-max-approvals") {
      state.workflowSupervisorMaxPendingApprovals = clampNumber(
        event.target.value,
        1,
        10,
        state.workflowSupervisorMaxPendingApprovals,
      );
    }
  });

  document.getElementById("workflow-panel").addEventListener("change", (event) => {
    if (event.target.id === "workflow-schedule-type") {
      state.workflowScheduleType = event.target.value || "manual";
      renderWorkflowPanel();
    }
    if (event.target.id === "workflow-run-weekday") {
      state.workflowRunWeekday = clampNumber(event.target.value, 0, 6, state.workflowRunWeekday);
    }
    if (event.target.id === "workflow-start-active") {
      state.workflowStartActive = Boolean(event.target.checked);
    }
    if (event.target.id === "workflow-supervisor-enabled") {
      state.workflowSupervisorEnabled = Boolean(event.target.checked);
    }
    if (event.target.id === "workflow-supervisor-pause-on-failure") {
      state.workflowSupervisorPauseOnFailure = Boolean(event.target.checked);
    }
  });

  document.getElementById("vision-panel").addEventListener("change", async (event) => {
    if (event.target.id !== "vision-file-input") {
      return;
    }

    const [file] = Array.from(event.target.files || []);
    if (!file) {
      return;
    }

    const maxBytes = Number(state.visionStatus?.max_upload_bytes || 0);
    if (maxBytes && file.size > maxBytes) {
      state.visionStatusMessage = `That image is larger than the ${formatBytes(maxBytes)} local limit.`;
      renderVisionPanel();
      return;
    }

    try {
      state.visionInputDataUrl = await readFileAsDataUrl(file);
      state.visionInputName = file.name || "upload";
      state.selectedVisionAnalysis = null;
      state.visionStatusMessage = `Loaded ${state.visionInputName} locally and ready for analysis.`;
      renderVisionPanel();
    } catch (error) {
      state.visionStatusMessage = error instanceof Error ? error.message : "Image load failed.";
      renderVisionPanel();
    }
  });

  document.getElementById("vision-panel").addEventListener("input", (event) => {
    if (event.target.id === "vision-prompt") {
      state.visionPrompt = event.target.value;
    }
  });

  document.getElementById("vision-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }

    if (button.id === "clear-vision") {
      state.visionInputDataUrl = "";
      state.visionInputName = "";
      state.visionPrompt = "";
      state.selectedVisionAnalysis = null;
      state.visionStatusMessage = state.visionCameraActive
        ? "Cleared the captured image. The live camera preview is still running."
        : "";
      renderVisionPanel();
      return;
    }

    if (button.id === "toggle-vision-camera") {
      button.disabled = true;
      try {
        if (state.visionCameraActive) {
          stopVisionCamera();
          state.visionStatusMessage = "Stopped the local camera preview.";
          renderVisionPanel();
          return;
        }
        state.isCapturingVision = true;
        renderVisionPanel();
        state.visionCameraStream = await startVisionCameraStream();
        state.visionCameraActive = true;
        state.visionCameraStream.getTracks().forEach((track) => {
          track.onended = () => {
            if (!state.visionCameraStream) {
              return;
            }
            stopVisionCamera();
            state.visionStatusMessage = "The camera preview ended.";
            renderVisionPanel();
          };
        });
        state.visionStatusMessage = "Started the local camera preview. Capture a frame when you're ready.";
      } catch (error) {
        state.visionStatusMessage = error instanceof Error ? error.message : "Camera start failed.";
      } finally {
        state.isCapturingVision = false;
        button.disabled = false;
        renderVisionPanel();
      }
      return;
    }

    if (button.id === "capture-vision-camera") {
      button.disabled = true;
      state.isCapturingVision = true;
      renderVisionPanel();
      try {
        state.visionInputDataUrl = await captureVisionCameraImageDataUrl();
        state.visionInputName = `camera-capture-${new Date().toISOString().replaceAll(/[:.-]/g, "").slice(0, 15)}.png`;
        state.selectedVisionAnalysis = null;
        state.visionStatusMessage = "Captured a camera frame locally and queued it for analysis.";
      } catch (error) {
        state.visionStatusMessage = error instanceof Error ? error.message : "Camera capture failed.";
      } finally {
        state.isCapturingVision = false;
        button.disabled = false;
        renderVisionPanel();
      }
      return;
    }

    if (button.id === "capture-vision-screen") {
      button.disabled = true;
      state.isCapturingVision = true;
      renderVisionPanel();
      try {
        state.visionInputDataUrl = await captureScreenImageDataUrl();
        state.visionInputName = `screen-capture-${new Date().toISOString().replaceAll(/[:.-]/g, "").slice(0, 15)}.png`;
        state.selectedVisionAnalysis = null;
        state.visionStatusMessage = "Captured a screen snapshot locally and queued it for analysis.";
      } catch (error) {
        state.visionStatusMessage = error instanceof Error ? error.message : "Screen capture failed.";
      } finally {
        state.isCapturingVision = false;
        button.disabled = false;
        renderVisionPanel();
      }
      return;
    }

    if (button.id === "analyze-vision") {
      button.disabled = true;
      try {
        await analyzeVisionInput();
      } catch {
        flashButtonLabel(button, "Failed");
      } finally {
        button.disabled = false;
      }
    }
  });

  window.addEventListener("beforeunload", () => {
    stopVisionCamera();
  });

  document.getElementById("research-panel").addEventListener("submit", async (event) => {
    const form = event.target.closest("form#research-form");
    if (!form) {
      return;
    }

    event.preventDefault();
    const input = document.getElementById("research-query");
    state.researchQuery = input ? input.value.trim() : state.researchQuery;
    try {
      await buildResearchBrief();
    } catch {
      renderResearchPanel();
    }
  });

  document.getElementById("research-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }

    if (button.id === "clear-research") {
      state.researchQuery = "";
      state.selectedResearchBrief = null;
      state.researchStatusMessage = "";
      renderResearchPanel();
      renderContentPanel();
      return;
    }

    const action = button.dataset.researchAction;
    if (!action) {
      return;
    }

    const sourceUrl = button.dataset.sourceUrl || "";
    if (!sourceUrl) {
      return;
    }

    button.disabled = true;
    try {
      state.webReaderUrl = sourceUrl;
      if (action === "read-source") {
        await readWebPage();
        return;
      }
      if (action === "summarize-source") {
        await summarizeWebPage();
      }
    } catch {
      flashButtonLabel(button, "Failed");
    } finally {
      button.disabled = false;
      renderResearchPanel();
    }
  });

  document.getElementById("research-panel").addEventListener("input", (event) => {
    if (event.target.id === "research-query") {
      state.researchQuery = event.target.value;
    }
  });

  document.getElementById("content-panel").addEventListener("submit", async (event) => {
    const form = event.target.closest("form#content-form");
    if (!form) {
      return;
    }

    event.preventDefault();
    const topicInput = document.getElementById("content-topic");
    const audienceInput = document.getElementById("content-audience");
    const contextInput = document.getElementById("content-context");
    state.contentTopic = topicInput ? topicInput.value.trim() : state.contentTopic;
    state.contentAudience = audienceInput ? audienceInput.value.trim() : state.contentAudience;
    state.contentContext = contextInput ? contextInput.value : state.contentContext;
    try {
      await buildContentPackage();
    } catch {
      renderContentPanel();
    }
  });

  document.getElementById("content-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }

    if (button.id === "clear-content") {
      state.contentTopic = "";
      state.contentAudience = "";
      state.contentContext = "";
      state.selectedContentPackage = null;
      state.contentStatusMessage = "";
      renderContentPanel();
      return;
    }

    if (button.id === "use-note-context") {
      state.contentContext = buildSelectedContentContext("note");
      state.contentStatusMessage = "Loaded context from the selected note.";
      renderContentPanel();
      return;
    }

    if (button.id === "use-document-context") {
      state.contentContext = buildSelectedContentContext("document");
      state.contentStatusMessage = "Loaded context from the selected document.";
      renderContentPanel();
      return;
    }

    if (button.id === "use-research-context") {
      state.contentContext = buildSelectedContentContext("research");
      state.contentStatusMessage = "Loaded context from the current research brief.";
      renderContentPanel();
      return;
    }

    const action = button.dataset.contentAction;
    if (!action) {
      return;
    }

    const packageData = state.selectedContentPackage?.package;
    if (!packageData) {
      flashButtonLabel(button, "Missing");
      return;
    }

    button.disabled = true;
    try {
      if (action === "copy-title") {
        const titleIndex = Number(button.dataset.titleIndex || -1);
        const title = (packageData.youtube_titles || [])[titleIndex];
        if (!title) {
          flashButtonLabel(button, "Missing");
          return;
        }
        await copyTextToClipboard(title);
        flashButtonLabel(button, "Copied");
        return;
      }

      if (action === "copy-seo-title") {
        await copyTextToClipboard(packageData.seo_title || "");
        flashButtonLabel(button, "Copied");
        return;
      }

      if (action === "copy-meta-description") {
        await copyTextToClipboard(packageData.meta_description || "");
        flashButtonLabel(button, "Copied");
        return;
      }

      if (action === "copy-youtube-description") {
        await copyTextToClipboard(packageData.youtube_description || "");
        flashButtonLabel(button, "Copied");
      }
    } catch {
      flashButtonLabel(button, "Failed");
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("content-panel").addEventListener("input", (event) => {
    if (event.target.id === "content-topic") {
      state.contentTopic = event.target.value;
    }
    if (event.target.id === "content-audience") {
      state.contentAudience = event.target.value;
    }
    if (event.target.id === "content-context") {
      state.contentContext = event.target.value;
    }
  });

  document.getElementById("web-reader-panel").addEventListener("submit", async (event) => {
    const searchForm = event.target.closest("form#web-search-form");
    if (searchForm) {
      event.preventDefault();
      const input = document.getElementById("web-search-query");
      state.webSearchQuery = input ? input.value.trim() : state.webSearchQuery;
      try {
        await searchWeb();
      } catch {
        renderWebReaderPanel();
      }
      return;
    }

    const form = event.target.closest("form#web-reader-form");
    if (!form) {
      return;
    }

    event.preventDefault();
    const input = document.getElementById("web-reader-url");
    state.webReaderUrl = input ? input.value.trim() : state.webReaderUrl;
    try {
      await readWebPage();
    } catch {
      renderWebReaderPanel();
    }
  });

  document.getElementById("web-reader-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }

    if (button.id === "clear-web-search") {
      state.webSearchQuery = "";
      state.webSearchResults = [];
      state.webSearchStatusMessage = "";
      renderWebReaderPanel();
      return;
    }

    if (button.id === "clear-web-reader") {
      state.webReaderUrl = "";
      state.selectedWebPage = null;
      state.selectedWebSummary = null;
      state.isReadingWebPage = false;
      state.isSummarizingWebPage = false;
      state.webReaderStatusMessage = "";
      renderWebReaderPanel();
      return;
    }

    const resultUrl = button.dataset.webResultUrl || "";
    if (button.dataset.webResultAction === "read" && resultUrl) {
      state.webReaderUrl = resultUrl;
      button.disabled = true;
      try {
        await readWebPage();
      } catch {
        flashButtonLabel(button, "Failed");
      } finally {
        button.disabled = false;
      }
      return;
    }

    if (button.dataset.webResultAction === "summarize" && resultUrl) {
      state.webReaderUrl = resultUrl;
      button.disabled = true;
      try {
        await summarizeWebPage();
      } catch {
        flashButtonLabel(button, "Failed");
      } finally {
        button.disabled = false;
      }
      return;
    }

    if (button.id === "summarize-webpage") {
      const input = document.getElementById("web-reader-url");
      state.webReaderUrl = input ? input.value.trim() : state.webReaderUrl;
      button.disabled = true;
      try {
        await summarizeWebPage();
      } catch {
        flashButtonLabel(button, "Failed");
      } finally {
        button.disabled = false;
      }
    }
  });

  document.getElementById("web-reader-panel").addEventListener("input", (event) => {
    if (event.target.id === "web-search-query") {
      state.webSearchQuery = event.target.value;
    }

    if (event.target.id === "web-reader-url") {
      state.webReaderUrl = event.target.value;
    }
  });

  document.getElementById("quick-prompts").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-prompt]");
    if (!button) {
      return;
    }

    focusAssistantComposer(button.dataset.prompt);
  });

  document.addEventListener("keydown", async (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      openCommandPalette();
      return;
    }

    if (event.key === "Escape" && state.commandPaletteOpen) {
      event.preventDefault();
      closeCommandPalette();
      return;
    }

    if (!state.commandPaletteOpen) {
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveCommandPaletteSelection(1);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveCommandPaletteSelection(-1);
      return;
    }

    if (event.key === "Enter" && document.activeElement?.id !== "command-palette-input") {
      event.preventDefault();
      const entry = getCommandPaletteEntries()[state.commandPaletteSelection];
      await runCommandPaletteEntry(entry);
    }
  });

  document.getElementById("files-search-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.getElementById("files-search-input");
    state.filesQuery = input.value.trim();
    await refreshFiles();
  });

  document.getElementById("clear-files-search").addEventListener("click", async () => {
    state.filesQuery = "";
    document.getElementById("files-search-input").value = "";
    await loadFileFolder(state.selectedFileFolderId || "");
  });

  document.getElementById("files-panel").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-file-browser-action]");
    if (!button) {
      return;
    }

    button.disabled = true;
    try {
      if (button.dataset.fileBrowserAction === "open-folder") {
        await loadFileFolder(button.dataset.folderId || "");
        return;
      }

      if (button.dataset.fileBrowserAction === "open-reader") {
        await loadSelectedDocument(button.dataset.documentId || "");
        return;
      }

      if (button.dataset.fileBrowserAction === "copy-path") {
        await copyTextToClipboard(button.dataset.path || "");
        flashButtonLabel(button, "Copied");
      }
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("documents-search-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.getElementById("documents-search-input");
    state.documentsQuery = input.value.trim();
    await refreshDocuments();
  });

  document.getElementById("clear-documents-search").addEventListener("click", async () => {
    state.documentsQuery = "";
    document.getElementById("documents-search-input").value = "";
    await refreshDocuments();
  });

  document.getElementById("documents-list").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-document-action]");
    if (!button) {
      return;
    }

    button.disabled = true;
    try {
      await loadSelectedDocument(button.dataset.id);
      await refreshDocuments();
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("document-reader").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-document-reader-action]");
    if (!button) {
      return;
    }

    button.disabled = true;
    try {
      if (button.dataset.documentReaderAction === "summarize") {
        await summarizeSelectedDocument();
        return;
      }

      if (button.dataset.documentReaderAction === "analyze") {
        await analyzeSelectedDocument();
        return;
      }

      if (button.dataset.documentReaderAction === "inspect") {
        await inspectSelectedDocument();
        return;
      }

      if (button.dataset.documentReaderAction === "set-inspection-depth") {
        state.documentInspectionDepth = Number(button.dataset.depth || "2");
        await inspectSelectedDocument();
        return;
      }

      if (button.dataset.documentReaderAction === "copy-preview-value") {
        await copyPreviewValue(button.dataset.copyValue || "", button);
        return;
      }

      if (button.dataset.documentReaderAction === "copy-inspection-json") {
        await copyInspectionExport(button.dataset.exportScope || "inspection", button);
        return;
      }

      if (button.dataset.documentReaderAction === "copy-inspection-csv") {
        await copyInspectionCsv(button.dataset.exportScope || "inspection", button);
        return;
      }

      if (button.dataset.documentReaderAction === "download-inspection-json") {
        downloadInspectionExport(button.dataset.exportScope || "inspection", button);
        return;
      }

      if (button.dataset.documentReaderAction === "download-inspection-csv") {
        await downloadInspectionCsv(button.dataset.exportScope || "inspection", button);
        return;
      }

      if (button.dataset.documentReaderAction === "focus-inspection-path") {
        state.documentInspectionPath = button.dataset.schemaPath || "";
        await inspectSelectedDocument();
        return;
      }

      if (button.dataset.documentReaderAction === "focus-parent-inspection-path") {
        state.documentInspectionPath = button.dataset.schemaPath || "";
        await inspectSelectedDocument();
        return;
      }

      if (button.dataset.documentReaderAction === "clear-inspection-filter") {
        state.documentInspectionFilter = "";
        if (state.selectedDocumentInspection) {
          await inspectSelectedDocument();
        } else {
          renderDocumentReader(state.selectedDocument);
        }
        return;
      }

      if (button.dataset.documentReaderAction === "clear-inspection-path") {
        state.documentInspectionPath = "";
        if (state.selectedDocumentInspection) {
          await inspectSelectedDocument();
        } else {
          renderDocumentReader(state.selectedDocument);
        }
      }
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("document-reader").addEventListener("submit", async (event) => {
    const form = event.target.closest("form[data-document-inspection-form]");
    if (!form) {
      return;
    }

    event.preventDefault();
    const input = form.querySelector("input[name='filter']");
    state.documentInspectionFilter = input ? input.value.trim() : "";
    await inspectSelectedDocument();
  });

  document.getElementById("notes-search-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (hasUnsavedNoteChanges()) {
      const confirmed = window.confirm("Discard unsaved note changes and run a new search?");
      if (!confirmed) {
        return;
      }
      state.isEditingNote = false;
    }
    const input = document.getElementById("notes-search-input");
    state.notesQuery = input.value.trim();
    await refreshNotes();
  });

  document.getElementById("clear-notes-search").addEventListener("click", async () => {
    if (hasUnsavedNoteChanges()) {
      const confirmed = window.confirm("Discard unsaved note changes and show recent notes?");
      if (!confirmed) {
        return;
      }
      state.isEditingNote = false;
    }
    state.notesQuery = "";
    document.getElementById("notes-search-input").value = "";
    await refreshNotes();
  });

  document.getElementById("notes-list").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-note-action]");
    if (!button) {
      return;
    }

    button.disabled = true;
    try {
      if (hasUnsavedNoteChanges() && state.selectedNoteName !== button.dataset.name) {
        const confirmed = window.confirm("Discard unsaved note changes and open another note?");
        if (!confirmed) {
          return;
        }
      }
      await loadSelectedNote(button.dataset.name);
      await refreshNotes();
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("note-reader").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-note-reader-action]");
    if (!button) {
      return;
    }

    button.disabled = true;
    try {
      if (button.dataset.noteReaderAction === "edit") {
        if (!state.selectedNote) {
          return;
        }
        state.noteEditorContent = state.selectedNote.content || "";
        state.isEditingNote = true;
        renderNoteReader(state.selectedNote);
        return;
      }

      if (button.dataset.noteReaderAction === "discard") {
        if (!state.selectedNote) {
          return;
        }
        state.noteEditorContent = state.selectedNote.content || "";
        state.isEditingNote = false;
        renderNoteReader(state.selectedNote);
        return;
      }

      if (button.dataset.noteReaderAction === "save") {
        const editor = document.getElementById("note-editor");
        if (editor) {
          state.noteEditorContent = editor.value;
        }
        await saveSelectedNote();
      }
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("note-reader").addEventListener("input", (event) => {
    if (event.target.id === "note-editor") {
      state.noteEditorContent = event.target.value;
    }
  });

  document.getElementById("memory-panel").addEventListener("click", async (event) => {
    const target = event.target.closest("button");
    if (!target) {
      return;
    }

    if (target.id === "toggle-memory") {
      target.disabled = true;
      try {
        await toggleMemory();
      } finally {
        target.disabled = false;
      }
    }

    if (target.id === "clear-session") {
      target.disabled = true;
      try {
        await clearSession();
      } finally {
        target.disabled = false;
      }
    }

    if (target.id === "refresh-memory-sessions") {
      target.disabled = true;
      try {
        await refreshMemorySessions();
      } finally {
        target.disabled = false;
      }
    }

    if (target.id === "clear-all-memory") {
      const confirmed = window.confirm("Delete all stored conversation memory from local SQLite storage?");
      if (!confirmed) {
        return;
      }
      target.disabled = true;
      try {
        await clearAllMemory();
      } finally {
        target.disabled = false;
      }
    }

    if (target.dataset.memoryAction === "delete-session") {
      const sessionId = target.dataset.sessionId || "";
      if (!sessionId) {
        return;
      }
      const confirmed = window.confirm(`Delete stored session ${sessionId}?`);
      if (!confirmed) {
        return;
      }
      target.disabled = true;
      try {
        await clearSession(sessionId);
      } finally {
        target.disabled = false;
      }
    }

    if (target.dataset.memoryAction === "prepare-phone-link") {
      const sessionId = target.dataset.sessionId || "";
      if (!sessionId) {
        return;
      }
      target.disabled = true;
      state.companionAccessSessionId = sessionId;
      state.companionAccessStatus = "Preparing same-network handoff links for the selected saved session.";
      renderCompanionAccessPanel();
      try {
        await refreshCompanionAccess();
        document.getElementById("companion-access-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
      } finally {
        target.disabled = false;
      }
    }
  });

  document.getElementById("reminders-list").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-reminder-action]");
    if (!button) {
      return;
    }

    button.disabled = true;
    try {
      let payload = {};
      let actionPath = button.dataset.reminderAction;
      if (button.dataset.reminderAction === "delete") {
        const confirmed = window.confirm("Permanently delete this archived reminder? This cannot be undone.");
        if (!confirmed) {
          return;
        }
      }

      if (button.dataset.reminderAction === "snooze") {
        payload = { preset: button.dataset.preset || "hour" };
      }

      if (button.dataset.reminderAction === "recurrence") {
        payload = { preset: button.dataset.preset || "daily" };
        actionPath = "recurrence";
      }

      if (button.dataset.reminderAction === "clear-recurrence") {
        actionPath = "recurrence/clear";
      }

      if (button.dataset.reminderAction === "schedule") {
        const input = document.querySelector(`input[data-schedule-input="true"][data-id="${button.dataset.id}"]`);
        if (!input || !input.value) {
          if (input) {
            input.reportValidity();
            input.focus();
          }
          return;
        }

        payload = { due_at: toOffsetIsoString(input.value) };
      }

      await updateReminder(button.dataset.id, actionPath, payload);
    } finally {
      button.disabled = false;
    }
  });
}

async function init() {
  renderStaticLists();
  bindEvents();
  renderCommandPalette();
  renderNotificationButton();
  renderVoiceControls();
  renderCompanionAccessPanel();
  renderWorkflowPanel();

  try {
    await api("/health");
    setConnectionStatus("Backend connected", "online");
    await refreshAll();
    startBackgroundRefresh();
  } catch (error) {
    console.error(error);
    setConnectionStatus("Backend unavailable", "offline");
    renderHistory([]);
    renderPending([]);
    renderActivity([]);
    renderTools([]);
    renderVoiceControls();
    renderSettingsPanel();
    renderFilesStatus();
    renderFilesPanel();
    renderMemoryPanel();
    renderClipboardPanel();
    renderCompanionAccessPanel();
    renderWorkflowPanel();
    renderVisionPanel();
    renderResearchPanel();
    renderContentPanel();
    renderEmailPanel();
    renderMessagingPanel();
    renderWebReaderPanel();
    renderReminderSummary({});
    renderReminderToolbar();
    renderNotificationButton();
    renderDocuments([]);
    renderDocumentsStatus(0);
    renderDocumentReader(null);
    renderNotes([]);
    renderNotesStatus(0);
    renderNoteReader(null);
    renderReminders([]);
  }
}

init();
