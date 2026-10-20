
const API_URL = "http://127.0.0.1:8000/api/jobs/";

const statusLabels = {
  interested: "Заинтересован",
  applied: "Подана заявка",
  interview: "Собеседование",
  rejected: "Отклонена",
  "Заинтересован": "Заинтересован",
  "Подана заявка": "Подана заявка",
  "Собеседование": "Собеседование",
  "Отклонена": "Отклонена",
};

const statusValues = {
  interested: "Заинтересован",
  applied: "Подана заявка",
  interview: "Собеседование",
  rejected: "Отклонена",
};

const statusClasses = {
  "Заинтересован": "interested",
  "Подана заявка": "applied",
  "Собеседование": "interview",
  "Отклонена": "rejected",
};

let jobs = [];
let editingId = null;

const jobList = document.getElementById("job-list");
const form = document.getElementById("job-form");
const searchInput = document.getElementById("search");
const statusFilter = document.getElementById("status-filter");
const message = document.getElementById("message");

const addButton = document.getElementById("add-button");
const cancelButton = document.getElementById("cancel-button");
const formTitle = document.getElementById("form-title");
const saveButton = document.getElementById("save-button");

function normalizeStatus(status) {
  return statusValues[status] || status || "Заинтересован";
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[char]);
}

function showMessage(text) {
  message.textContent = text;
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail;
    const errorText = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(", ")
      : typeof detail === "string"
        ? detail
        : null;

    throw new Error(errorText || `Ошибка сервера: ${response.status}`);
  }

  return data;
}

async function loadJobs() {
  jobList.innerHTML = "<p>Загружаю вакансии...</p>";

  try {
    const data = await apiRequest(API_URL);

    if (!Array.isArray(data)) {
      throw new Error("Сервер вернул данные в неожиданном формате.");
    }

    jobs = data;
    renderJobs();
  } catch (error) {
    jobList.innerHTML = "";
    showMessage(
      `Не удалось загрузить вакансии: ${error.message}. Проверь, запущен ли backend.`
    );
  }
}

function renderJobs() {
  document.getElementById("total-count").textContent = jobs.length;

  document.getElementById("applied-count").textContent =
    jobs.filter((job) => normalizeStatus(job.status) === "Подана заявка").length;

  document.getElementById("interview-count").textContent =
    jobs.filter((job) => normalizeStatus(job.status) === "Собеседование").length;

  const query = searchInput.value.trim().toLowerCase();
  const selectedStatus = statusFilter.value;

  const filteredJobs = jobs.filter((job) => {
    const company = String(job.company ?? "").toLowerCase();
    const position = String(job.position ?? "").toLowerCase();

    const matchesSearch =
      company.includes(query) || position.includes(query);

    const matchesStatus =
      selectedStatus === "all" ||
      normalizeStatus(job.status) === selectedStatus;

    return matchesSearch && matchesStatus;
  });

  if (filteredJobs.length === 0) {
    jobList.innerHTML = `
      <div class="empty-state">
        <h2>${jobs.length === 0 ? "Пока нет вакансий" : "Ничего не найдено"}</h2>
        <p>${
          jobs.length === 0
            ? "Добавь первую вакансию — она сохранится в базе данных."
            : "Попробуй изменить поисковый запрос или фильтр."
        }</p>
      </div>
    `;
    return;
  }

  jobList.innerHTML = filteredJobs.map((job) => {
    const company = escapeHtml(job.company);
    const position = escapeHtml(job.position);
    const notes = escapeHtml(job.notes);
    const status = normalizeStatus(job.status);
    const statusLabel = escapeHtml(statusLabels[status] || status);
    const statusClass = statusClasses[status] || "interested";
    const id = escapeHtml(job.id);

    let link = "";
    if (job.url) {
      const safeUrl = escapeHtml(job.url);
      link = `
        <p>
          <a href="${safeUrl}" target="_blank" rel="noopener noreferrer">
            Открыть вакансию ↗
          </a>
        </p>
      `;
    }

    return `
      <article class="job-card">
        <div class="job-card-header">
          <div>
            <h2>${position}</h2>
            <p class="company-name">${company}</p>
          </div>
          <span class="status status-${statusClass}">
            ${statusLabel}
          </span>
        </div>

        ${notes ? `<p class="job-notes">${notes}</p>` : ""}
        ${link}

        <div class="job-actions">
          <button
            type="button"
            class="secondary-button"
            data-action="edit"
            data-id="${id}"
          >
            Редактировать
          </button>
          <button
            type="button"
            class="secondary-button"
            data-action="delete"
            data-id="${id}"
          >
            Удалить
          </button>
        </div>
      </article>
    `;
  }).join("");
}

function openForm(job = null) {
  editingId = job ? job.id : null;
  form.reset();

  formTitle.textContent = job ? "Редактировать вакансию" : "Новая вакансия";
  saveButton.textContent = job ? "Сохранить изменения" : "Сохранить";

  if (job) {
    form.elements.company.value = job.company ?? "";
    form.elements.position.value = job.position ?? "";
    form.elements.url.value = job.url ?? "";
    form.elements.status.value = normalizeStatus(job.status);
    form.elements.notes.value = job.notes ?? "";
  } else {
    form.elements.status.value = "Заинтересован";
  }

  form.classList.remove("hidden");
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function closeForm() {
  form.classList.add("hidden");
  form.reset();
  editingId = null;
}

addButton.addEventListener("click", () => {
  showMessage("");
  openForm();
});

cancelButton.addEventListener("click", closeForm);

searchInput.addEventListener("input", renderJobs);
statusFilter.addEventListener("change", renderJobs);

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const jobData = {
    company: form.elements.company.value.trim(),
    position: form.elements.position.value.trim(),
    url: form.elements.url.value.trim() || null,
    status: form.elements.status.value,
    notes: form.elements.notes.value.trim(),
  };

  const isEditing = editingId !== null;
  const requestUrl = isEditing ? `${API_URL}${editingId}` : API_URL;

  saveButton.disabled = true;
  showMessage("Сохраняю вакансию...");

  try {
    await apiRequest(requestUrl, {
      method: isEditing ? "PATCH" : "POST",
      body: JSON.stringify(jobData),
    });

    closeForm();
    await loadJobs();
    showMessage(
      isEditing
        ? "Изменения сохранены."
        : "Вакансия сохранена в базе данных."
    );
  } catch (error) {
    showMessage(`Не удалось сохранить вакансию: ${error.message}`);
  } finally {
    saveButton.disabled = false;
  }
});

jobList.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");

  if (!button) return;

  const id = button.dataset.id;
  const action = button.dataset.action;
  const job = jobs.find((item) => String(item.id) === String(id));

  if (!job) return;

  if (action === "edit") {
    showMessage("");
    openForm(job);
    return;
  }

  if (action === "delete") {
    const confirmed = confirm(
      `Удалить вакансию «${job.position}» в компании ${job.company}?`
    );

    if (!confirmed) return;

    try {
      await apiRequest(`${API_URL}${id}`, { method: "DELETE" });
      await loadJobs();
      showMessage("Вакансия удалена.");
    } catch (error) {
      showMessage(`Не удалось удалить вакансию: ${error.message}`);
    }
  }
});

loadJobs();
