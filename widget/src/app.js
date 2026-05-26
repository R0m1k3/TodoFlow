// --- CONFIGURATIONS INITIALES ET ÉTATS ---

// Références vers l'API Tauri (uniquement si exécuté sous Tauri)
const tauri = window.__TAURI__;
const appWindow = tauri ? tauri.window.getCurrent() : null;
const invoke = tauri ? tauri.invoke : null;

// État local de l'application
let state = {
  apiUrl: "http://localhost:8000",
  apiKey: "widget-token-secure-789",
  alwaysOnTop: false,
  autostart: false,
  tasks: [],
  pollingInterval: null
};

// --- SÉLECTEURS DOM ---
const statusIndicator = document.getElementById("connection-status");
const taskProgress = document.getElementById("task-progress");
const tasksList = document.getElementById("tasks-list");
const addTaskForm = document.getElementById("add-task-form");
const taskInput = document.getElementById("task-input");

// Paramètres panel
const settingsPanel = document.getElementById("settings-panel");
const btnSettings = document.getElementById("btn-settings");
const btnSettingsClose = document.getElementById("btn-settings-close");
const btnSaveSettings = document.getElementById("btn-save-settings");

// Inputs de configuration
const inputApiUrl = document.getElementById("setting-api-url");
const inputApiKey = document.getElementById("setting-api-key");
const inputAlwaysOnTop = document.getElementById("setting-always-on-top");
const inputAutostart = document.getElementById("setting-autostart");

// Contrôles de fenêtre
const btnMinimize = document.getElementById("btn-minimize");
const btnClose = document.getElementById("btn-close");

// --- INITIALISATION ---

document.addEventListener("DOMContentLoaded", async () => {
  // Chargement des paramètres stockés localement
  loadSettingsFromStorage();
  
  // Remplissage initial des champs du panneau de configuration
  inputApiUrl.value = state.apiUrl;
  inputApiKey.value = state.apiKey;
  inputAlwaysOnTop.checked = state.alwaysOnTop;
  
  // Événements d'ouverture/fermeture des paramètres
  btnSettings.addEventListener("click", () => settingsPanel.classList.add("open"));
  btnSettingsClose.addEventListener("click", () => settingsPanel.classList.remove("open"));
  btnSaveSettings.addEventListener("click", saveSettings);
  
  // Événements Tauri pour le contrôle de la fenêtre de bureau
  if (appWindow) {
    btnMinimize.addEventListener("click", () => appWindow.minimize());
    btnClose.addEventListener("click", () => appWindow.hide()); // Masquer vers le tray au clic sur 'Fermer'
    
    // Récupération de l'état réel du démarrage automatique depuis le registre Windows
    try {
      state.autostart = await invoke("get_autostart");
      inputAutostart.checked = state.autostart;
    } catch (e) {
      console.warn("Impossible de lire l'état de démarrage automatique :", e);
    }
  } else {
    // Si exécuté hors de Tauri (ex: navigateur classique), masquer les boutons de fenêtre
    btnMinimize.style.display = "none";
    btnClose.style.display = "none";
    inputAutostart.closest(".setting-toggle").style.display = "none"; // Cacher l'autostart
  }
  
  // Événement d'ajout de tâche
  addTaskForm.addEventListener("submit", handleAddTask);
  
  // Démarrage de la synchronisation en temps réel (Polling toutes les 4 secondes)
  fetchTasks();
  state.pollingInterval = setInterval(fetchTasks, 4000);
});

// --- ENREGISTREMENT ET CHARGEMENT DES PARAMÈTRES ---

function loadSettingsFromStorage() {
  // Charge la configuration pour assurer la persistance des ordinateurs de travail
  const storedApiUrl = localStorage.getItem("todoflow_api_url");
  const storedApiKey = localStorage.getItem("todoflow_api_key");
  const storedAlwaysOnTop = localStorage.getItem("todoflow_always_on_top");
  
  if (storedApiUrl) state.apiUrl = storedApiUrl;
  if (storedApiKey) state.apiKey = storedApiKey;
  if (storedAlwaysOnTop) {
    state.alwaysOnTop = storedAlwaysOnTop === "true";
    // Appliquer directement la préférence au démarrage
    if (appWindow && invoke) {
      invoke("toggle_always_on_top", { enabled: state.alwaysOnTop }).catch(console.error);
    }
  }
}

async function saveSettings() {
  const newUrl = inputApiUrl.value.trim().replace(/\/$/, ""); // Retirer le slash de fin éventuel
  const newKey = inputApiKey.value.trim();
  const newAlwaysOnTop = inputAlwaysOnTop.checked;
  const newAutostart = inputAutostart.checked;
  
  state.apiUrl = newUrl;
  state.apiKey = newKey;
  state.alwaysOnTop = newAlwaysOnTop;
  
  localStorage.setItem("todoflow_api_url", newUrl);
  localStorage.setItem("todoflow_api_key", newKey);
  localStorage.setItem("todoflow_always_on_top", newAlwaysOnTop.toString());
  
  // Appel des fonctions système Windows natives via Tauri
  if (appWindow && invoke) {
    try {
      await invoke("toggle_always_on_top", { enabled: newAlwaysOnTop });
      await invoke("set_autostart", { enabled: newAutostart });
      state.autostart = newAutostart;
    } catch (e) {
      alert(`Erreur système : ${e}`);
    }
  }
  
  // Fermer le volet et forcer un rafraîchissement immédiat de la liste
  settingsPanel.classList.remove("open");
  fetchTasks();
}

// --- APPELS API (CRUD) ---

async function fetchTasks() {
  // Récupération asynchrone des tâches avec la clé API
  try {
    const response = await fetch(`${state.apiUrl}/api/v1/tasks`, {
      method: "GET",
      headers: {
        "X-API-Key": state.apiKey,
        "Accept": "application/json"
      }
    });
    
    if (!response.ok) throw new Error("Accès refusé ou serveur indisponible");
    
    const tasks = await response.json();
    state.tasks = tasks;
    
    // Mise à jour de l'indicateur lumineux sur le header (Connecté)
    statusIndicator.className = "status-indicator connected";
    statusIndicator.title = "Connecté à la base centralisée";
    
    renderTasksList();
  } catch (error) {
    console.error("Erreur de synchronisation :", error);
    statusIndicator.className = "status-indicator disconnected";
    statusIndicator.title = "Erreur de connexion avec le serveur";
  }
}

async function handleAddTask(e) {
  e.preventDefault();
  const title = taskInput.value.trim();
  if (!title) return;
  
  // Création directe via un appel POST à l'API centralisée
  try {
    const response = await fetch(`${state.apiUrl}/api/v1/tasks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": state.apiKey
      },
      json: true,
      body: JSON.stringify({
        title: title,
        status: "A faire" // Statut initial par défaut
      })
    });
    
    if (!response.ok) throw new Error("Échec de la création de la tâche");
    
    taskInput.value = ""; // Vider le champ après création
    fetchTasks(); // Rafraîchir pour afficher la tâche créée avec son animation
  } catch (error) {
    alert("Impossible d'ajouter la tâche : vérifiez votre connexion ou clé API.");
  }
}

async function toggleTaskDone(taskId, currentStatus) {
  // Permet de cocher ou décocher une tâche
  const targetStatus = currentStatus === "Termine" ? "A faire" : "Termine";
  
  try {
    const response = await fetch(`${state.apiUrl}/api/v1/tasks/${taskId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": state.apiKey
      },
      body: JSON.stringify({
        status: targetStatus
      })
    });
    
    if (!response.ok) throw new Error("Échec de mise à jour");
    fetchTasks();
  } catch (error) {
    console.error("Erreur de mise à jour du statut :", error);
  }
}

async function toggleTaskInProgress(taskId, currentStatus) {
  // Permet de basculer spécifiquement les travaux "En cours" ou "À faire"
  if (currentStatus === "Termine") return; // On ne modifie pas directement les tâches terminées par ici
  
  const targetStatus = currentStatus === "En cours" ? "A faire" : "En cours";
  
  try {
    const response = await fetch(`${state.apiUrl}/api/v1/tasks/${taskId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": state.apiKey
      },
      body: JSON.stringify({
        status: targetStatus
      })
    });
    
    if (!response.ok) throw new Error("Échec de mise à jour");
    fetchTasks();
  } catch (error) {
    console.error("Erreur de mise à jour de l'état de travail :", error);
  }
}

// --- AFFICHAGE ET LOGIQUE DE RENDU ---

function renderTasksList() {
  if (state.tasks.length === 0) {
    tasksList.innerHTML = `
      <div class="empty-state">
        <p>Aucune tâche en cours</p>
        <span class="empty-subtext">Tout est à jour ! Excellent travail.</span>
      </div>
    `;
    taskProgress.style.width = "0%";
    return;
  }
  
  // Calcul et mise à jour de la barre de progression linéaire
  const completedTasks = state.tasks.filter(t => t.status === "Termine").length;
  const progressPercent = Math.round((completedTasks / state.tasks.length) * 100);
  taskProgress.style.width = `${progressPercent}%`;
  
  tasksList.innerHTML = "";
  
  state.tasks.forEach(task => {
    const isCompleted = task.status === "Termine";
    
    // Structure de la carte de tâche
    const card = document.createElement("div");
    card.className = `task-card ${isCompleted ? 'completed' : ''}`;
    
    // Checkbox personnalisée cochable
    const checkbox = document.createElement("div");
    checkbox.className = `custom-checkbox ${isCompleted ? 'checked' : ''}`;
    checkbox.innerHTML = `
      <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
        <path d="M1.5 4L3.75 6.25L8.5 1.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    checkbox.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleTaskDone(task.id, task.status);
    });
    
    // Bloc de contenu (Titre & Date)
    const content = document.createElement("div");
    content.className = "task-content";
    
    const title = document.createElement("span");
    title.className = "task-title";
    title.textContent = task.title;
    title.title = task.title; // Tooltip d'accessibilité
    
    const date = document.createElement("span");
    date.className = "task-date";
    date.textContent = `Créé le ${formatDate(task.created_at)}`;
    
    content.appendChild(title);
    content.appendChild(date);
    
    // Badge de statut (En cours / À faire)
    const badge = document.createElement("span");
    
    if (task.status === "Termine") {
      badge.className = "status-badge done";
      badge.textContent = "Terminé";
    } else if (task.status === "En cours") {
      badge.className = "status-badge in-progress";
      badge.textContent = "En cours";
      badge.title = "Cliquer pour marquer 'À faire'";
      badge.addEventListener("click", () => toggleTaskInProgress(task.id, task.status));
    } else {
      badge.className = "status-badge todo";
      badge.textContent = "À faire";
      badge.title = "Cliquer pour marquer 'En cours'";
      badge.addEventListener("click", () => toggleTaskInProgress(task.id, task.status));
    }
    
    card.appendChild(checkbox);
    card.appendChild(content);
    card.appendChild(badge);
    
    tasksList.appendChild(card);
  });
}

// Formatage de la date en français épuré
function formatDate(dateString) {
  try {
    const date = new Date(dateString);
    
    // Format : "26 mai • 14:15"
    const optionsDay = { day: 'numeric', month: 'short' };
    const dayStr = date.toLocaleDateString('fr-FR', optionsDay);
    
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    
    return `${dayStr} • ${hours}:${minutes}`;
  } catch (e) {
    return dateString;
  }
}
