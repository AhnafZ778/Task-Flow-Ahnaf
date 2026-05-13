// Task-Flow — Frontend Application
// This handles all the CRUD operations, filtering, inline editing,
// confirmation dialogs, toast notifications, and the calendar popup
// Basically everything the user interacts with on the frontend

// ============================================================
// Configuration
// ============================================================

const API_BASE = "http://localhost:8000";

// Inline SVG reference for calendar icon — used in deadline badges, chips, and filter labels
const CALENDAR_ICON = '<img src="icons/icon_calendar.svg" alt="" class="icon-inline icon-sm" />';

// Maps priority numbers to their display labels and CSS classes

const PRIORITY_LABELS = {
    1: "Low",
    2: "Medium",
    3: "Hard",
};

const PRIORITY_CLASSES = {
    1: "priority-low",
    2: "priority-med",
    3: "priority-hard",
};

// ============================================================
// State — these track the current app state across interactions
// ============================================================

let currentFilter = "all";
let tasks = [];
let deleteTargetId = null;
let detectedDeadline = null;   // ISO string from date parser
let detectedDateText = null;   // matched text to strip from title

// ============================================================
// DOM References — grabbing all the elements we need upfront
// ============================================================

const addForm = document.getElementById("add-task-form");
const titleInput = document.getElementById("task-title");
const descInput = document.getElementById("task-description");
const priorityInput = document.getElementById("task-priority");
const priorityDisplay = document.getElementById("priority-display");
const titleError = document.getElementById("title-error");
const taskListEl = document.getElementById("task-list");
const emptyStateEl = document.getElementById("empty-state");
const loadingEl = document.getElementById("loading");
const deleteModal = document.getElementById("delete-modal");
const deleteMessage = document.getElementById("delete-message");
const cancelDeleteBtn = document.getElementById("cancel-delete-btn");
const confirmDeleteBtn = document.getElementById("confirm-delete-btn");
const toastContainer = document.getElementById("toast-container");
const dateChip = document.getElementById("date-chip");
const dateChipText = document.getElementById("date-chip-text");
const dateChipDismiss = document.getElementById("date-chip-dismiss");
const titleHighlight = document.getElementById("title-highlight");
const calendarModal = document.getElementById("calendar-modal");
const calGrid = document.getElementById("cal-grid");
const calTitle = document.getElementById("cal-title");
const dateFilterActive = document.getElementById("date-filter-active");
const dfaLabel = document.getElementById("dfa-label");
const dfaClose = document.getElementById("dfa-close");

// ============================================================
// Initialization — runs when the page first loads
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    loadTasks();
    setupEventListeners();
    updatePriorityDisplay();
    startMascotBlink();
});

function setupEventListeners() {
    addForm.addEventListener("submit", handleAddTask);
    cancelDeleteBtn.addEventListener("click", closeDeleteModal);
    confirmDeleteBtn.addEventListener("click", confirmDelete);

    // Priority slider live update
    priorityInput.addEventListener("input", updatePriorityDisplay);

    // Title input — real-time date parsing
    titleInput.addEventListener("input", onTitleInput);

    // Date chip dismiss
    if (dateChipDismiss) dateChipDismiss.addEventListener("click", dismissDateChip);

    // Filter buttons (standard filters)
    document.querySelectorAll(".filter-btn[data-filter]").forEach((btn) => {
        btn.addEventListener("click", () => {
            setFilter(btn.dataset.filter);
        });
    });

    // Upcoming button — opens calendar popup
    const upcomingBtn = document.getElementById("upcoming-btn");
    if (upcomingBtn) upcomingBtn.addEventListener("click", openCalendarPopup);

    // Calendar navigation & close
    const calPrev = document.getElementById("cal-prev");
    const calNext = document.getElementById("cal-next");
    const calClose = document.getElementById("cal-close");
    if (calPrev) calPrev.addEventListener("click", () => navigateCalendar(-1));
    if (calNext) calNext.addEventListener("click", () => navigateCalendar(1));
    if (calClose) calClose.addEventListener("click", closeCalendarPopup);
    if (calendarModal) calendarModal.addEventListener("click", (e) => {
        if (e.target === calendarModal) closeCalendarPopup();
    });

    // Date filter dismiss
    if (dfaClose) dfaClose.addEventListener("click", clearDateFilter);

    // Close modal on overlay click
    deleteModal.addEventListener("click", (e) => {
        if (e.target === deleteModal) closeDeleteModal();
    });

    // Escape key closes modals
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeDeleteModal();
            closeCalendarPopup();
        }
    });
}

function updatePriorityDisplay() {
    const val = parseInt(priorityInput.value);
    priorityDisplay.textContent = PRIORITY_LABELS[val] || "Medium";
    priorityDisplay.className = `priority-value ${PRIORITY_CLASSES[val] || "priority-med"}`;
}

// ============================================================
// API Helper — all backend calls go through this
// ============================================================

async function apiRequest(path, method = "GET", data = null) {
    const options = {
        method,
        headers: { "Content-Type": "application/json" },
    };
    if (data !== null) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(`${API_BASE}${path}`, options);
    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || "Request failed");
    }
    return result;
}

// ============================================================
// Loading & Rendering Tasks
// ============================================================

async function loadTasks() {
    loadingEl.style.display = "flex";
    emptyStateEl.style.display = "none";
    taskListEl.innerHTML = "";

    try {
        const filterParam = currentFilter !== "all" ? `?status=${currentFilter}` : "";
        const data = await apiRequest(`/api/tasks${filterParam}`);
        tasks = data.tasks;
        renderTasks();
    } catch (err) {
        showToast("Failed to load tasks: " + err.message, "error");
    } finally {
        loadingEl.style.display = "none";
    }
}

function renderTasks() {
    taskListEl.innerHTML = "";

    if (tasks.length === 0) {
        emptyStateEl.style.display = "block";
        return;
    }

    emptyStateEl.style.display = "none";

    tasks.forEach((task) => {
        const el = createTaskElement(task);
        taskListEl.appendChild(el);
    });
}

function createTaskElement(task) {
    const item = document.createElement("div");
    const priorityClass = PRIORITY_CLASSES[task.priority] || "priority-med";
    item.className = `task-item ${priorityClass}${task.status === "completed" ? " completed" : ""}`;
    item.dataset.id = task.id;

    const isCompleted = task.status === "completed";
    const priorityLabel = PRIORITY_LABELS[task.priority] || "Medium";

    item.innerHTML = `
        <div class="task-checkbox">
            <input type="checkbox" ${isCompleted ? "checked" : ""}
                   title="${isCompleted ? "Mark as pending" : "Mark as completed"}"
                   aria-label="Toggle task status">
        </div>
        <div class="task-content">
            <div class="task-title-row">
                <span class="task-title">${escapeHtml(task.title)}</span>
                <span class="task-badge ${isCompleted ? "badge-completed" : "badge-pending"}">
                    <img src="icons/${isCompleted ? "icon_done" : "icon_scroll"}.png" alt="" />
                    ${isCompleted ? "Done" : "Pending"}
                </span>
                <span class="priority-badge ${priorityClass}">${priorityLabel}</span>
            </div>
            ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ""}
            <div class="task-meta-row">
                <div class="task-meta">Created ${formatDate(task.created_at)}</div>
                ${getDeadlineBadgeHTML(task.deadline)}
            </div>
        </div>
        <div class="task-actions">
            <button class="btn-icon edit-btn" title="Edit task"><img src="icons/icon_pencil.png" alt="Edit" /></button>
            <button class="btn-icon delete btn-delete" title="Delete task"><img src="icons/icon_trash.png" alt="Delete" /></button>
        </div>
    `;

    // Toggling the checkbox flips the task status
    item.querySelector('input[type="checkbox"]').addEventListener("change", () => {
        toggleTask(task.id);
    });

    // Clicking the pencil opens inline edit mode
    item.querySelector(".edit-btn").addEventListener("click", () => {
        startEdit(task);
    });

    // Clicking trash opens the delete confirmation modal
    item.querySelector(".btn-delete").addEventListener("click", () => {
        openDeleteModal(task.id, task.title);
    });

    return item;
}

// ============================================================
// Creating a New Task
// ============================================================

async function handleAddTask(e) {
    e.preventDefault();
    clearFieldError();

    let title = titleInput.value.trim();
    const description = descInput.value.trim() || null;
    const priority = parseInt(priorityInput.value);
    const deadline = detectedDeadline || null;

    // Stripping the detected date keywords from the title before sending
    // so "Workout tomorrow at 6am" becomes just "Workout"
    if (deadline && detectedDateText) {
        title = title.replace(detectedDateText, "").replace(/\s{2,}/g, " ").trim();
    }

    // Quick frontend validation before hitting the API
    if (!title) {
        showFieldError("Title is required");
        titleInput.classList.add("input-error");
        titleInput.focus();
        return;
    }

    try {
        await apiRequest("/api/tasks", "POST", { title, description, priority, deadline });
        showToast("Task added!", "success");
        addForm.reset();
        priorityInput.value = 2;
        updatePriorityDisplay();
        dismissDateChip();
        await loadTasks();
    } catch (err) {
        showToast(err.message, "error");
    }
}

// ============================================================
// Toggling Task Status (pending ↔ completed)
// ============================================================

async function toggleTask(taskId) {
    try {
        await apiRequest(`/api/tasks/${taskId}/toggle`, "PATCH");
        await loadTasks();
    } catch (err) {
        showToast("Failed to toggle task: " + err.message, "error");
    }
}

// ============================================================
// Inline Editing — replaces task content with an edit form
// ============================================================

function startEdit(task) {
    const item = document.querySelector(`.task-item[data-id="${task.id}"]`);
    if (!item) return;

    // Swapping the content area with edit inputs
    const contentEl = item.querySelector(".task-content");
    const actionsEl = item.querySelector(".task-actions");

    contentEl.innerHTML = `
        <div class="edit-form">
            <input type="text" class="edit-title" value="${escapeAttr(task.title)}" maxlength="200" placeholder="Title">
            <textarea class="edit-description" rows="2" maxlength="500" placeholder="Description (optional)">${task.description ? escapeHtml(task.description) : ""}</textarea>
            <div class="edit-priority-wrap">
                <label>Priority</label>
                <input type="range" class="edit-priority" min="1" max="3" value="${task.priority || 2}" step="1" />
                <span class="priority-value ${PRIORITY_CLASSES[task.priority] || 'priority-med'}">${PRIORITY_LABELS[task.priority] || 'Medium'}</span>
            </div>
            <div class="edit-actions">
                <button class="btn btn-primary btn-sm save-edit-btn" type="button">Save</button>
                <button class="btn btn-secondary btn-sm cancel-edit-btn" type="button">Cancel</button>
            </div>
        </div>
    `;

    actionsEl.style.display = "none";

    const editTitle = contentEl.querySelector(".edit-title");
    const editPriority = contentEl.querySelector(".edit-priority");
    const editPriorityLabel = contentEl.querySelector(".priority-value");

    editTitle.focus();
    editTitle.setSelectionRange(editTitle.value.length, editTitle.value.length);

    // Live updating the priority label as user drags the slider
    editPriority.addEventListener("input", () => {
        const val = parseInt(editPriority.value);
        editPriorityLabel.textContent = PRIORITY_LABELS[val] || "Medium";
        editPriorityLabel.className = `priority-value ${PRIORITY_CLASSES[val] || "priority-med"}`;
    });

    // Save button handler
    contentEl.querySelector(".save-edit-btn").addEventListener("click", () => {
        saveEdit(task.id, contentEl);
    });

    // Cancel just re-renders the task list to restore the original view
    contentEl.querySelector(".cancel-edit-btn").addEventListener("click", () => {
        loadTasks(); // Re-render to restore original
    });

    // Pressing Enter in the title field saves instead of submitting a form
    editTitle.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            saveEdit(task.id, contentEl);
        }
    });
}

async function saveEdit(taskId, contentEl) {
    const title = contentEl.querySelector(".edit-title").value.trim();
    const description = contentEl.querySelector(".edit-description").value.trim() || null;
    const priority = parseInt(contentEl.querySelector(".edit-priority").value);

    if (!title) {
        showToast("Title cannot be empty", "error");
        contentEl.querySelector(".edit-title").classList.add("input-error");
        return;
    }

    try {
        await apiRequest(`/api/tasks/${taskId}`, "PUT", { title, description, priority });
        showToast("Task updated!", "success");
        await loadTasks();
    } catch (err) {
        showToast("Failed to update: " + err.message, "error");
    }
}

// ============================================================
// Delete Task — confirmation modal flow
// ============================================================

function openDeleteModal(taskId, taskTitle) {
    deleteTargetId = taskId;
    deleteMessage.textContent = `Are you sure you want to delete "${taskTitle}"?`;
    deleteModal.style.display = "flex";
}

function closeDeleteModal() {
    deleteModal.style.display = "none";
    deleteTargetId = null;
}

async function confirmDelete() {
    if (deleteTargetId === null) return;

    try {
        await apiRequest(`/api/tasks/${deleteTargetId}`, "DELETE");
        showToast("Task deleted", "success");
        closeDeleteModal();
        await loadTasks();
    } catch (err) {
        showToast("Failed to delete: " + err.message, "error");
    }
}

// ============================================================
// Filters — switches between All, Pending, Completed views
// ============================================================

function setFilter(filter) {
    currentFilter = filter;

    document.querySelectorAll(".filter-btn").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.filter === filter);
    });

    loadTasks();
}

// ============================================================
// Field Validation — shows/clears error messages on title input
// ============================================================

function showFieldError(msg) {
    titleError.textContent = msg;
}

function clearFieldError() {
    titleError.textContent = "";
    titleInput.classList.remove("input-error");
}

titleInput.addEventListener("input", () => {
    clearFieldError();
});

// ============================================================
// Natural Language Date Parser
// This is the system that detects keywords like "tomorrow", "5pm",
// "next monday at 6am" etc in the title input and auto-sets deadlines
// It supports compound keywords so "tomorrow at 6am" works as one unit
// ============================================================

const MONTH_NAMES = ["january","february","march","april","may","june","july","august","september","october","november","december"];
const MONTH_SHORT = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"];
const DAY_NAMES = ["sunday","monday","tuesday","wednesday","thursday","friday","saturday"];

function parseNaturalDate(text) {
    const lower = text.toLowerCase();
    const now = new Date();
    let date = null, matchedText = null;
    let match;

    // Step 1: Parse the DATE portion
    // Going through all possible keyword patterns from most specific to least

    // "today" / "tonight" / "this evening" / "this afternoon" / "this morning"
    if ((match = lower.match(/\b(today|tonight|this\s+evening|this\s+afternoon|this\s+morning)\b/))) {
        date = new Date(now); matchedText = match[0];
        if (/tonight|evening/.test(match[0])) date.setHours(21, 0, 0, 0);
        else if (/afternoon/.test(match[0])) date.setHours(14, 0, 0, 0);
        else if (/morning/.test(match[0])) date.setHours(9, 0, 0, 0);
        else date.setHours(0, 0, 0, 0);
    }
    // "tomorrow" / "tmr" / "tmrw"
    else if ((match = lower.match(/\b(tomorrow|tmr|tmrw)\b/))) {
        date = new Date(now); date.setDate(date.getDate() + 1); date.setHours(0, 0, 0, 0); matchedText = match[0];
    }
    // "day after tomorrow"
    else if ((match = lower.match(/\bday\s+after\s+tomorrow\b/))) {
        date = new Date(now); date.setDate(date.getDate() + 2); date.setHours(0, 0, 0, 0); matchedText = match[0];
    }
    // "daily" / "every day" / "everyday" → treat as today
    else if ((match = lower.match(/\b(daily|every\s*day|everyday)\b/))) {
        date = new Date(now); date.setHours(0, 0, 0, 0); matchedText = match[0];
    }
    // "this weekend" → next Saturday
    else if ((match = lower.match(/\bthis\s+weekend\b/))) {
        date = new Date(now);
        let diff = 6 - date.getDay(); if (diff <= 0) diff += 7;
        date.setDate(date.getDate() + diff); date.setHours(0, 0, 0, 0); matchedText = match[0];
    }
    // "end of week" / "eow" → Friday
    else if ((match = lower.match(/\b(end\s+of\s+week|eow)\b/))) {
        date = new Date(now);
        let diff = 5 - date.getDay(); if (diff <= 0) diff += 7;
        date.setDate(date.getDate() + diff); date.setHours(0, 0, 0, 0); matchedText = match[0];
    }
    // "end of day" / "eod" → today 17:00
    else if ((match = lower.match(/\b(end\s+of\s+day|eod)\b/))) {
        date = new Date(now); date.setHours(17, 0, 0, 0); matchedText = match[0];
    }
    // "next monday", "next friday", etc
    else if ((match = lower.match(/\bnext\s+(sunday|monday|tuesday|wednesday|thursday|friday|saturday)\b/))) {
        const target = DAY_NAMES.indexOf(match[1]);
        date = new Date(now);
        let diff = target - date.getDay(); if (diff <= 0) diff += 7;
        date.setDate(date.getDate() + diff); date.setHours(0, 0, 0, 0); matchedText = match[0];
    }
    // "this monday", "this friday" → current week
    else if ((match = lower.match(/\bthis\s+(sunday|monday|tuesday|wednesday|thursday|friday|saturday)\b/))) {
        const target = DAY_NAMES.indexOf(match[1]);
        date = new Date(now);
        let diff = target - date.getDay(); if (diff < 0) diff += 7;
        date.setDate(date.getDate() + diff); date.setHours(0, 0, 0, 0); matchedText = match[0];
    }
    // "in X days/weeks"
    else if ((match = lower.match(/\bin\s+(\d+)\s+(day|days|week|weeks)\b/))) {
        date = new Date(now);
        const n = parseInt(match[1]);
        if (match[2].startsWith("week")) date.setDate(date.getDate() + n * 7);
        else date.setDate(date.getDate() + n);
        date.setHours(0, 0, 0, 0); matchedText = match[0];
    }
    // "7th june", "7 june", "7th jun"
    else if ((match = lower.match(/\b(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b/))) {
        const day = parseInt(match[1]);
        let mIdx = MONTH_NAMES.indexOf(match[2]); if (mIdx === -1) mIdx = MONTH_SHORT.indexOf(match[2]);
        date = new Date(now.getFullYear(), mIdx, day);
        if (date < now) date.setFullYear(date.getFullYear() + 1);
        matchedText = match[0];
    }
    // "june 7", "jun 7th"
    else if ((match = lower.match(/\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?\b/))) {
        const day = parseInt(match[2]);
        let mIdx = MONTH_NAMES.indexOf(match[1]); if (mIdx === -1) mIdx = MONTH_SHORT.indexOf(match[1]);
        date = new Date(now.getFullYear(), mIdx, day);
        if (date < now) date.setFullYear(date.getFullYear() + 1);
        matchedText = match[0];
    }
    // Standalone time: "5pm", "5:30pm", "noon", "midnight"
    else if ((match = lower.match(/\b(noon|midnight)\b/))) {
        date = new Date(now);
        date.setHours(match[1] === "noon" ? 12 : 0, 0, 0, 0);
        matchedText = match[0];
    }
    else if ((match = lower.match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b/))) {
        date = new Date(now);
        let h = parseInt(match[1]); const m = match[2] ? parseInt(match[2]) : 0;
        if (match[3] === "pm" && h < 12) h += 12;
        if (match[3] === "am" && h === 12) h = 0;
        date.setHours(h, m, 0, 0); matchedText = match[0];
    }

    if (!date || isNaN(date.getTime())) return null;

    // Step 2: Check for a TIME modifier after the date keyword
    // This is what makes "tomorrow at 6am" and "next monday @ 9:30pm" work
    // It looks for "at" or "@" followed by a time right after the matched keyword
    const afterKeyword = lower.substring(lower.indexOf(matchedText) + matchedText.length);
    let timeMatch;
    if ((timeMatch = afterKeyword.match(/^\s+(?:at\s+|@\s*)(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b/))) {
        let h = parseInt(timeMatch[1]); const m = timeMatch[2] ? parseInt(timeMatch[2]) : 0;
        if (timeMatch[3] === "pm" && h < 12) h += 12;
        if (timeMatch[3] === "am" && h === 12) h = 0;
        date.setHours(h, m, 0, 0);
        matchedText = matchedText + timeMatch[0]; // extend matched text
    } else if ((timeMatch = afterKeyword.match(/^\s+(?:at\s+|@\s*)(noon|midnight)\b/))) {
        date.setHours(timeMatch[1] === "noon" ? 12 : 0, 0, 0, 0);
        matchedText = matchedText + timeMatch[0];
    }

    // Step 3: Build the ISO string that gets sent to the backend
    const y = date.getFullYear();
    const mo = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    let iso = `${y}-${mo}-${d}`;
    if (date.getHours() !== 0 || date.getMinutes() !== 0) {
        iso += `T${String(date.getHours()).padStart(2,"0")}:${String(date.getMinutes()).padStart(2,"0")}`;
    }

    return { iso, date, matchedText };
}

function formatDeadlineLabel(iso) {
    const d = new Date(iso.includes("T") ? iso : iso + "T00:00");
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const diffDays = Math.round((target - today) / 86400000);

    let label;
    if (diffDays === 0) label = "Today";
    else if (diffDays === 1) label = "Tomorrow";
    else if (diffDays === -1) label = "Yesterday";
    else label = d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });

    if (iso.includes("T")) {
        const [, time] = iso.split("T");
        const [h, m] = time.split(":").map(Number);
        const ampm = h >= 12 ? "PM" : "AM";
        const h12 = h % 12 || 12;
        label += `, ${h12}:${String(m).padStart(2,"0")} ${ampm}`;
    }
    return label;
}

function onTitleInput() {
    const text = titleInput.value;
    const result = parseNaturalDate(text);

    // Updating the highlight overlay so the keyword gets visually marked
    updateHighlightOverlay(text, result);

    if (result) {
        detectedDeadline = result.iso;
        detectedDateText = result.matchedText;
        dateChipText.innerHTML = CALENDAR_ICON + " " + formatDeadlineLabel(result.iso);
        dateChip.style.display = "flex";
        dateChip.classList.add("chip-pop");
        setTimeout(() => dateChip.classList.remove("chip-pop"), 300);
    } else {
        // Dynamic: clearing everything immediately when keyword is removed
        detectedDeadline = null;
        detectedDateText = null;
        dateChip.style.display = "none";
    }
}

function updateHighlightOverlay(text, result) {
    if (!titleHighlight) return;
    if (!text) {
        titleHighlight.innerHTML = "";
        return;
    }
    if (result && result.matchedText) {
        const idx = text.toLowerCase().indexOf(result.matchedText);
        if (idx !== -1) {
            const before = escapeHtml(text.substring(0, idx));
            const match = escapeHtml(text.substring(idx, idx + result.matchedText.length));
            const after = escapeHtml(text.substring(idx + result.matchedText.length));
            titleHighlight.innerHTML = `${before}<mark class="date-highlight">${match}</mark>${after}`;
            return;
        }
    }
    titleHighlight.innerHTML = escapeHtml(text);
}

function dismissDateChip() {
    detectedDeadline = null;
    detectedDateText = null;
    if (dateChip) dateChip.style.display = "none";
    if (titleHighlight) titleHighlight.innerHTML = "";
}

// ============================================================
// Deadline Badge — renders the deadline label on task cards
// ============================================================

function getDeadlineBadgeHTML(deadline) {
    if (!deadline) return "";
    const d = new Date(deadline.includes("T") ? deadline : deadline + "T00:00");
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const diffDays = Math.round((target - today) / 86400000);

    let cls = "deadline-future";
    if (diffDays < 0) cls = "deadline-overdue";
    else if (diffDays === 0) cls = "deadline-today";

    return `<span class="deadline-badge ${cls}">${CALENDAR_ICON} ${formatDeadlineLabel(deadline)}</span>`;
}

// ============================================================
// Calendar Popup & Date Filter
// This powers the Upcoming button's calendar modal
// It fetches which dates have tasks, renders a month grid,
// and lets the user click a date to filter down to just those tasks
// ============================================================

let calViewYear, calViewMonth;
let taskDateSet = new Set();  // YYYY-MM-DD strings that have tasks
let activeFilterDate = null;  // currently filtered date string

async function openCalendarPopup() {
    if (!calendarModal) return;
    const now = new Date();
    calViewYear = now.getFullYear();
    calViewMonth = now.getMonth();

    calendarModal.style.display = "flex";

    // Fetch task dates
    try {
        const data = await apiRequest("/api/tasks/upcoming");
        taskDateSet = new Set(Object.keys(data.groups || {}));
    } catch { taskDateSet = new Set(); }

    renderCalendar();
}

function closeCalendarPopup() {
    if (calendarModal) calendarModal.style.display = "none";
}

function navigateCalendar(dir) {
    calViewMonth += dir;
    if (calViewMonth < 0)  { calViewMonth = 11; calViewYear--; }
    if (calViewMonth > 11) { calViewMonth = 0;  calViewYear++; }
    renderCalendar();
}

function renderCalendar() {
    if (!calGrid || !calTitle) return;

    const monthNames = ["January","February","March","April","May","June",
        "July","August","September","October","November","December"];
    calTitle.textContent = `${monthNames[calViewMonth]} ${calViewYear}`;

    const firstDay = new Date(calViewYear, calViewMonth, 1).getDay();
    const daysInMonth = new Date(calViewYear, calViewMonth + 1, 0).getDate();
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;

    let html = "";

    // Blank cells before first day
    for (let i = 0; i < firstDay; i++) {
        html += '<span class="cal-day cal-empty"></span>';
    }

    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${calViewYear}-${String(calViewMonth+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
        const hasTask = taskDateSet.has(dateStr);
        const isToday = dateStr === todayStr;
        const isActive = dateStr === activeFilterDate;

        let cls = "cal-day";
        if (isToday) cls += " cal-today";
        if (hasTask) cls += " cal-has-task";
        if (isActive) cls += " cal-active";

        html += `<span class="${cls}" data-date="${dateStr}">${d}</span>`;
    }

    calGrid.innerHTML = html;

    // Wire click handlers for days with tasks
    calGrid.querySelectorAll(".cal-has-task").forEach((cell) => {
        cell.addEventListener("click", () => {
            selectCalendarDate(cell.dataset.date);
        });
    });
}

function selectCalendarDate(dateStr) {
    activeFilterDate = dateStr;
    closeCalendarPopup();

    // Show active filter indicator
    const d = new Date(dateStr + "T00:00");
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffDays = Math.round((d - today) / 86400000);

    let label;
    if (diffDays === 0) label = CALENDAR_ICON + " Today";
    else if (diffDays === 1) label = CALENDAR_ICON + " Tomorrow";
    else label = CALENDAR_ICON + " " + d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });

    if (dfaLabel) dfaLabel.innerHTML = label;
    if (dateFilterActive) dateFilterActive.style.display = "flex";

    // Hide the upcoming button
    const btn = document.getElementById("upcoming-btn");
    if (btn) btn.style.display = "none";

    // Filter tasks
    filterTasksByDate(dateStr);
}

function clearDateFilter() {
    activeFilterDate = null;
    if (dateFilterActive) dateFilterActive.style.display = "none";

    const btn = document.getElementById("upcoming-btn");
    if (btn) btn.style.display = "";

    // Restore normal view
    loadTasks();
}

async function filterTasksByDate(dateStr) {
    try {
        const data = await apiRequest("/api/tasks/upcoming");
        const groups = data.groups || {};
        tasks = groups[dateStr] || [];
        renderTasks();
    } catch (err) {
        showToast("Failed to filter: " + err.message, "error");
    }
}


// ============================================================
// Toast Notifications — those little popups in the top right
// ============================================================

function showToast(message, type = "info") {
    const icons = { success: "icon_done", error: "icon_cross", info: "icon_sparkles" };
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<img src="icons/${icons[type] || icons.info}.png" alt="" />${escapeHtml(message)}`;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("toast-exit");
        setTimeout(() => toast.remove(), 250);
    }, 3000);
}

// ============================================================
// Utility Functions
// ============================================================

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function formatDate(dateStr) {
    if (!dateStr) return "";
    // SQLite timestamps come as "YYYY-MM-DD HH:MM:SS.ffffff" — convert to ISO
    const iso = dateStr.replace(" ", "T") + (dateStr.includes("T") ? "" : "Z");
    const d = new Date(iso);
    if (isNaN(d.getTime())) return dateStr; // fallback to raw string
    return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
}

// ============================================================
// Mascot Blink Animation — makes the mascot feel alive
// Random intervals between blinks, 30% chance of a double-blink
// ============================================================

function startMascotBlink() {
    const openImg = document.getElementById("mascot-open");
    const blinkImg = document.getElementById("mascot-blink");
    if (!openImg || !blinkImg) return;

    // Use visibility for instant swap — no transition delay
    blinkImg.style.visibility = "hidden";
    openImg.style.visibility = "visible";

    function doBlink() {
        // Instant close
        openImg.style.visibility = "hidden";
        blinkImg.style.visibility = "visible";

        // Instant open after 150ms (natural blink duration)
        setTimeout(() => {
            blinkImg.style.visibility = "hidden";
            openImg.style.visibility = "visible";

            // 30% chance of a quick double-blink for lifelike feel
            if (Math.random() < 0.3) {
                setTimeout(() => {
                    openImg.style.visibility = "hidden";
                    blinkImg.style.visibility = "visible";
                    setTimeout(() => {
                        blinkImg.style.visibility = "hidden";
                        openImg.style.visibility = "visible";
                    }, 100);
                }, 120);
            }
        }, 150);

        // Next blink: 3-7 seconds (randomized for organic rhythm)
        const nextBlink = 3000 + Math.random() * 4000;
        setTimeout(doBlink, nextBlink);
    }

    // First blink after 1.5 seconds
    setTimeout(doBlink, 1500);
}
