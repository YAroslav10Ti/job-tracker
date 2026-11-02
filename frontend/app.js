const API_URL = "http://127.0.0.1:8000/api/jobs/";

const TOKEN_KEY = "access_token";

const STATUSES = [
  "Заинтересован",
  "Подана заявка",
  "Собеседование",
  "Отклонена",
];

const statusClasses = {
  "Заинтересован": "interested",
  "Подана заявка": "applied",
  "Собеседование": "interview",
  "Отклонена": "rejected",
};

let jobs = [];
let editingId = null;
let messageTimer = null;

const authSection = document.getElementById("auth-section");
const appSection = document.getElementById("app-section");

const loginTab = document.getElementById("login-tab");
const registerTab = document.getElementById("register-tab");

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");

const loginButton = document.getElementById("login-button");
const registerButton = document.getElementById("register-button");

const authMessage = document.getElementById("auth-message");

const logoutButton = document.getElementById("logout-button");

const jobList = document.getElementById("job-list");
const form = document.getElementById("job-form");
const formSection = document.getElementById("form-section");

const searchInput = document.getElementById("search");
const statusFilter = document.getElementById("status-filter");

const message = document.getElementById("message");

const addButton = document.getElementById("add-button");
const cancelButton = document.getElementById("cancel-button");
const closeFormButton = document.getElementById("close-form-button");

const formTitle = document.getElementById("form-title");
const saveButton = document.getElementById("save-button");

const totalStat = document.getElementById("stat-total");
const appliedStat = document.getElementById("stat-applied");
const interviewStat = document.getElementById("stat-interview");

const visibleCount = document.getElementById("visible-count");


// --------------------------------------------------
// Вспомогательные функции
// --------------------------------------------------

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };

    return entities[character];
  });
}


function normalizeStatus(status) {
  return STATUSES.includes(status) ? status : "Заинтересован";
}


function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}


function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}


function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}


function showMessage(text, type = "success") {
  clearTimeout(messageTimer);

  message.textContent = text;
  message.className = `message message-${type}`;
  message.hidden = false;

  messageTimer = setTimeout(() => {
    message.hidden = true;
  }, 5000);
}


function showAuthMessage(text, type = "error") {
  authMessage.textContent = text;
  authMessage.className = `message message-${type}`;
  authMessage.hidden = false;
}


function clearAuthMessage() {
  authMessage.hidden = true;
  authMessage.textContent = "";
}


// --------------------------------------------------
// Переключение экранов авторизации
// --------------------------------------------------

function showAuthScreen() {
  authSection.hidden = false;
  appSection.hidden = true;

  jobs = [];
  editingId = null;

  form.reset();
  formSection.hidden = true;

  jobList.innerHTML = "";

  showLoginForm();
}


function showAppScreen() {
  authSection.hidden = true;
  appSection.hidden = false;
}


function showLoginForm() {
  loginForm.hidden = false;
  registerForm.hidden = true;

  loginTab.classList.add("active");
  registerTab.classList.remove("active");

  clearAuthMessage();
}


function showRegisterForm() {
  loginForm.hidden = true;
  registerForm.hidden = false;

  loginTab.classList.remove("active");
  registerTab.classList.add("active");

  clearAuthMessage();
}


loginTab.addEventListener("click", showLoginForm);
registerTab.addEventListener("click", showRegisterForm);


// --------------------------------------------------
// Работа с API
// --------------------------------------------------

async function apiRequest(url, options = {}) {
  const {
    auth = true,
    ...fetchOptions
  } = options;

  const headers = {
    ...(fetchOptions.body ? {
      "Content-Type": "application/json",
    } : {}),
    ...fetchOptions.headers,
  };

  // Добавляем JWT к защищённым запросам.
  if (auth) {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      throw new Error("Необходимо войти в аккаунт.");
    }

    headers.Authorization = `Bearer ${token}`;
  }

  let response;

  try {
    response = await fetch(url, {
      ...fetchOptions,
      headers,
    });
  } catch (error) {
    throw new Error(
      "Не удалось подключиться к серверу. Проверь, запущен ли FastAPI."
    );
  }

  // JWT отсутствует, неправильный или истёк.
  if (response.status === 401 && auth) {
    handleUnauthorized();

    throw new Error("Сессия завершена. Войди в аккаунт снова.");
  }

  if (!response.ok) {
    let detail = `Ошибка HTTP ${response.status}`;

    try {
      const data = await response.json();

      if (typeof data.detail === "string") {
        detail = data.detail;
      } else if (Array.isArray(data.detail)) {
        detail = data.detail
          .map((item) => item.msg || "Некорректные данные")
          .join("; ");
      }
    } catch {
      // Ответ сервера не содержит JSON.
    }

    const error = new Error(detail);
    error.status = response.status;

    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  const responseText = await response.text();

  return responseText ? JSON.parse(responseText) : null;
}


// --------------------------------------------------
// Авторизация
// --------------------------------------------------

async function login(event) {
  event.preventDefault();

  const email = loginForm.elements.email.value.trim();
  const password = loginForm.elements.password.value;

  if (!email || !password) {
    showAuthMessage("Заполни email и пароль.");
    return;
  }

  loginButton.disabled = true;
  loginButton.textContent = "Входим...";

  try {
    const data = await apiRequest(`${API_URL}login`, {
      method: "POST",
      auth: false,
      body: JSON.stringify({
        email,
        password,
      }),
    });

    if (!data.access_token) {
      throw new Error("Сервер не вернул access_token.");
    }

    saveToken(data.access_token);

    loginForm.reset();
    clearAuthMessage();

    showAppScreen();

    await loadJobs();

  } catch (error) {
    showAuthMessage(error.message);
  } finally {
    loginButton.disabled = false;
    loginButton.textContent = "Войти";
  }
}


async function register(event) {
  event.preventDefault();

  const email = registerForm.elements.email.value.trim();
  const password = registerForm.elements.password.value;

  if (!email || !password) {
    showAuthMessage("Заполни все поля.");
    return;
  }

  if (password.length < 8) {
    showAuthMessage("Пароль должен содержать минимум 8 символов.");
    return;
  }

  registerButton.disabled = true;
  registerButton.textContent = "Создаём аккаунт...";

  try {
    await apiRequest(`${API_URL}register`, {
      method: "POST",
      auth: false,
      body: JSON.stringify({
        email,
        password,
      }),
    });

    registerForm.reset();

    showLoginForm();

    showAuthMessage(
      "Аккаунт успешно создан. Теперь войди в систему.",
      "success"
    );

  } catch (error) {
    showAuthMessage(error.message);
  } finally {
    registerButton.disabled = false;
    registerButton.textContent = "Создать аккаунт";
  }
}


loginForm.addEventListener("submit", login);
registerForm.addEventListener("submit", register);


// --------------------------------------------------
// Выход из аккаунта
// --------------------------------------------------

function logout() {
  clearToken();

  jobs = [];
  editingId = null;

  form.reset();
  formSection.hidden = true;

  searchInput.value = "";
  statusFilter.value = "";

  showAuthScreen();

  showAuthMessage("Ты вышел из аккаунта.", "success");
}


logoutButton.addEventListener("click", logout);


function handleUnauthorized() {
  clearToken();
  showAuthScreen();

  showAuthMessage(
    "Твоя сессия завершена. Пожалуйста, войди снова."
  );
}


// --------------------------------------------------
// Статистика
// --------------------------------------------------

function updateStats() {
  totalStat.textContent = jobs.length;

  appliedStat.textContent = jobs.filter(
    (job) => normalizeStatus(job.status) === "Подана заявка"
  ).length;

  interviewStat.textContent = jobs.filter(
    (job) => normalizeStatus(job.status) === "Собеседование"
  ).length;
}


// --------------------------------------------------
// Ссылки на вакансии
// --------------------------------------------------

function getSafeUrl(value) {
  if (!value) return null;

  try {
    const parsed = new URL(value);

    if (
      parsed.protocol === "http:" ||
      parsed.protocol === "https:"
    ) {
      return parsed.href;
    }
  } catch {
    return null;
  }

  return null;
}


// --------------------------------------------------
// Поиск и фильтрация
// --------------------------------------------------

function getFilteredJobs() {
  const query = searchInput.value
    .trim()
    .toLocaleLowerCase("ru");

  const selectedStatus = statusFilter.value;

  return jobs.filter((job) => {
    const searchableText = [
      job.company,
      job.position,
      job.notes,
      job.last_date,
    ]
      .join(" ")
      .toLocaleLowerCase("ru");

    const matchesSearch = searchableText.includes(query);

    const matchesStatus =
      !selectedStatus ||
      normalizeStatus(job.status) === selectedStatus;

    return matchesSearch && matchesStatus;
  });
}


// --------------------------------------------------
// Отображение вакансий
// --------------------------------------------------

function renderJobs() {
  updateStats();

  const filteredJobs = getFilteredJobs();

  visibleCount.textContent =
    `${filteredJobs.length} из ${jobs.length}`;

  if (jobs.length === 0) {
    jobList.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon" aria-hidden="true">✦</div>
        <h3>Пока нет вакансий</h3>
        <p>
          Добавь первую вакансию, чтобы начать отслеживать поиск работы.
        </p>
        <button
          class="button button-primary"
          type="button"
          data-action="add"
        >
          Добавить первую вакансию
        </button>
      </div>
    `;

    return;
  }

  if (filteredJobs.length === 0) {
    jobList.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon" aria-hidden="true">⌕</div>
        <h3>Ничего не найдено</h3>
        <p>
          Попробуй изменить поисковый запрос или выбрать другой статус.
        </p>
        <button
          class="button button-secondary"
          type="button"
          data-action="reset"
        >
          Сбросить фильтры
        </button>
      </div>
    `;

    return;
  }

  jobList.innerHTML = filteredJobs
    .map((job) => {
      const company = escapeHtml(job.company);
      const position = escapeHtml(job.position);

      const status = normalizeStatus(job.status);
      const statusClass = statusClasses[status];

      const lastDate = escapeHtml(
        job.last_date || "Неизвестно"
      );

      const notes = escapeHtml(job.notes || "");

      const safeUrl = getSafeUrl(job.url);
      const id = Number(job.id);

      const notesHtml = notes
        ? `<p class="job-notes">${notes}</p>`
        : `<p class="job-notes notes-empty">Заметок пока нет</p>`;

      const urlHtml = safeUrl
        ? `
          <a
            class="job-link"
            href="${escapeHtml(safeUrl)}"
            target="_blank"
            rel="noopener noreferrer"
          >
            Открыть вакансию ↗
          </a>
        `
        : "";

      return `
        <article class="job-card">
          <div class="job-card-header">
            <div class="job-title-group">
              <h3>${position}</h3>
              <p class="company-name">${company}</p>
            </div>

            <span class="status status-${statusClass}">
              ${escapeHtml(status)}
            </span>
          </div>

          <div class="job-meta">
            <span class="deadline-label">
              <span aria-hidden="true">◷</span>
              Дедлайн: <strong>${lastDate}</strong>
            </span>

            ${urlHtml}
          </div>

          ${notesHtml}

          <div class="job-card-footer">
            <span class="job-id">
              Вакансия #${escapeHtml(job.id)}
            </span>

            <div class="job-actions">
              <button
                class="button button-small button-secondary"
                type="button"
                data-action="edit"
                data-id="${id}"
              >
                Редактировать
              </button>

              <button
                class="button button-small button-danger"
                type="button"
                data-action="delete"
                data-id="${id}"
              >
                Удалить
              </button>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}


// --------------------------------------------------
// Загрузка вакансий
// --------------------------------------------------

async function loadJobs() {
  jobList.innerHTML = `
    <div class="loading-state">
      Загружаем вакансии...
    </div>
  `;

  try {
    const data = await apiRequest(API_URL);

    if (!Array.isArray(data)) {
      throw new Error(
        "API вернул неожиданный формат. Ожидался список вакансий."
      );
    }

    jobs = data;

    renderJobs();

  } catch (error) {
    // При 401 apiRequest уже переключил пользователя на вход.
    if (error.status === 401 || !getToken()) {
      return;
    }

    jobList.innerHTML = `
      <div class="empty-state error-state">
        <h3>Не удалось загрузить вакансии</h3>
        <p>${escapeHtml(error.message)}</p>
        <button
          class="button button-secondary"
          type="button"
          data-action="reload"
        >
          Попробовать снова
        </button>
      </div>
    `;

    showMessage(error.message, "error");
  }
}


// --------------------------------------------------
// Открытие формы
// --------------------------------------------------

function openForm(job = null) {
  form.reset();

  editingId = job ? job.id : null;

  formTitle.textContent = job
    ? "Редактировать вакансию"
    : "Добавить вакансию";

  saveButton.textContent = job
    ? "Сохранить изменения"
    : "Сохранить вакансию";

  if (job) {
    form.elements.company.value = job.company ?? "";
    form.elements.position.value = job.position ?? "";
    form.elements.url.value = job.url ?? "";

    form.elements.status.value = normalizeStatus(job.status);

    form.elements.last_date.value =
      job.last_date ?? "Неизвестно";

    form.elements.notes.value = job.notes ?? "";

  } else {
    form.elements.status.value = "Заинтересован";
    form.elements.last_date.value = "Неизвестно";
  }

  formSection.hidden = false;

  form.elements.company.focus();

  formSection.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}


function closeForm() {
  form.reset();

  editingId = null;

  formSection.hidden = true;
}


addButton.addEventListener("click", () => openForm());

cancelButton.addEventListener("click", closeForm);

closeFormButton.addEventListener("click", closeForm);


// --------------------------------------------------
// Создание и редактирование вакансии
// --------------------------------------------------

async function saveJob(event) {
  event.preventDefault();

  if (!form.reportValidity()) {
    return;
  }

  const jobData = {
    company: form.elements.company.value.trim(),
    position: form.elements.position.value.trim(),
    url: form.elements.url.value.trim() || null,
    status: normalizeStatus(form.elements.status.value),
    last_date:
      form.elements.last_date.value.trim() || "Неизвестно",
    notes: form.elements.notes.value.trim(),
  };

  if (!jobData.company || !jobData.position) {
    showMessage(
      "Заполни название компании и должность.",
      "error"
    );

    return;
  }

  const isEditing = editingId !== null;

  const requestUrl = isEditing
    ? `${API_URL}${editingId}`
    : API_URL;

  const method = isEditing ? "PATCH" : "POST";

  saveButton.disabled = true;
  saveButton.textContent = "Сохраняем...";

  try {
    await apiRequest(requestUrl, {
      method,
      body: JSON.stringify(jobData),
    });

    closeForm();

    await loadJobs();

    showMessage(
      isEditing
        ? "Изменения сохранены."
        : "Вакансия добавлена."
    );

  } catch (error) {
    showMessage(error.message, "error");

  } finally {
    saveButton.disabled = false;

    saveButton.textContent =
      editingId !== null
        ? "Сохранить изменения"
        : "Сохранить вакансию";

    if (formSection.hidden) {
      saveButton.textContent = "Сохранить вакансию";
    }
  }
}


form.addEventListener("submit", saveJob);


// --------------------------------------------------
// Удаление вакансии
// --------------------------------------------------

async function deleteJob(id) {
  const job = jobs.find(
    (item) => Number(item.id) === Number(id)
  );

  if (!job) {
    showMessage("Вакансия не найдена.", "error");
    return;
  }

  const confirmed = window.confirm(
    `Удалить вакансию «${job.position}» в компании «${job.company}»?`
  );

  if (!confirmed) return;

  try {
    await apiRequest(`${API_URL}${id}`, {
      method: "DELETE",
    });

    if (Number(editingId) === Number(id)) {
      closeForm();
    }

    await loadJobs();

    showMessage("Вакансия удалена.");

  } catch (error) {
    showMessage(error.message, "error");
  }
}


// --------------------------------------------------
// Обработка кнопок внутри списка
// --------------------------------------------------

jobList.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]");

  if (!button) return;

  const action = button.dataset.action;
  const id = button.dataset.id;

  if (action === "add") {
    openForm();

  } else if (action === "edit") {
    const job = jobs.find(
      (item) => Number(item.id) === Number(id)
    );

    if (job) {
      openForm(job);
    }

  } else if (action === "delete") {
    deleteJob(id);

  } else if (action === "reset") {
    searchInput.value = "";
    statusFilter.value = "";

    renderJobs();

  } else if (action === "reload") {
    loadJobs();
  }
});


// --------------------------------------------------
// Поиск и фильтрация
// --------------------------------------------------

searchInput.addEventListener("input", renderJobs);

statusFilter.addEventListener("change", renderJobs);


// --------------------------------------------------
// Запуск приложения
// --------------------------------------------------

async function initApp() {
  const token = getToken();

  if (!token) {
    showAuthScreen();
    return;
  }

  showAppScreen();

  await loadJobs();
}


initApp();