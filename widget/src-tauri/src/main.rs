#![cfg_attr(
  all(not(debug_assertions), target_os = "windows"),
  windows_subsystem = "windows"
)]

use std::env;
use tauri::{
    AppHandle, CustomMenuItem, Manager, SystemTray, SystemTrayEvent, SystemTrayMenu,
    SystemTrayMenuItem, WindowEvent,
};
use winreg::enums::*;
use winreg::RegKey;

// --- COMMANDES TAURI POUR LE FRONTEND ---

#[tauri::command]
fn toggle_always_on_top(window: tauri::Window, enabled: bool) -> Result<(), String> {
    // Cette fonction permet à l'utilisateur de configurer dynamiquement si le widget
    // reste au-dessus de toutes les autres fenêtres.
    window
        .set_always_on_top(enabled)
        .map_err(|e| format!("Impossible d'ajuster le premier plan : {}", e))?;
    Ok(())
}

#[tauri::command]
fn set_autostart(enabled: bool) -> Result<(), String> {
    // Permet d'activer ou de désactiver le lancement automatique au démarrage de Windows.
    // On écrit directement dans le registre Windows (HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run)
    // ce qui évite d'avoir à gérer un installateur complexe ou des plugins externes lourds.
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let run_key = hkcu
        .open_subkey_with_flags(
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            KEY_WRITE | KEY_READ,
        )
        .map_err(|e| format!("Échec de l'ouverture du registre : {}", e))?;

    if enabled {
        let current_exe = env::current_exe()
            .map_err(|e| format!("Impossible d'obtenir le chemin de l'exécutable : {}", e))?;
        let exe_path = current_exe.to_str().ok_or("Chemin invalide")?;
        // Entourer le chemin de guillemets au cas où il contiendrait des espaces
        let quoted_path = format!("\"{}\"", exe_path);
        run_key
            .set_value("TodoFlow", &quoted_path)
            .map_err(|e| format!("Échec de l'écriture dans le registre : {}", e))?;
    } else {
        // Suppression discrète de la clé, en ignorant si elle n'existe pas déjà
        let _ = run_key.delete_value("TodoFlow");
    }
    Ok(())
}

#[tauri::command]
fn get_autostart() -> Result<bool, String> {
    // Lit le registre Windows pour vérifier si l'application est configurée pour démarrer automatiquement.
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let run_key = hkcu
        .open_subkey_with_flags(
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            KEY_READ,
        )
        .map_err(|e| format!("Échec de la lecture du registre : {}", e))?;

    let val: Result<String, _> = run_key.get_value("TodoFlow");
    Ok(val.is_ok())
}

// --- GESTION DE LA VISIBILITÉ DE LA FENÊTRE ---

fn toggle_window_visibility(app: &AppHandle) {
    // Bascule l'affichage du widget depuis l'icône de la barre d'état.
    // Comme la fenêtre est configurée avec skipTaskbar:true, l'icône du tray est le
    // seul point de restauration : il doit donc fonctionner dans tous les états.
    let window = match app.get_window("main") {
        Some(w) => w,
        None => return,
    };

    // Une fenêtre réduite est toujours rapportée comme "visible" par Tauri. On la
    // considère donc comme masquée afin de la restaurer correctement (et non la re-masquer).
    let is_minimized = window.is_minimized().unwrap_or(false);
    let is_visible = window.is_visible().unwrap_or(false);

    if is_visible && !is_minimized {
        let _ = window.hide();
    } else {
        // Restauration robuste : dé-minimiser, ré-afficher, puis ramener au premier plan.
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}

// --- CONTEXTE ET INITIALISATION ---

fn main() {
    // Configuration du menu de la barre d'état (System Tray)
    // Permet au widget d'être discret et accessible même s'il est masqué du bureau
    let tray_menu = SystemTrayMenu::new()
        .add_item(CustomMenuItem::new("toggle".to_string(), "Afficher / Masquer"))
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(CustomMenuItem::new("quit".to_string(), "Quitter"));

    let system_tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .system_tray(system_tray)
        .on_system_tray_event(|app, event| match event {
            SystemTrayEvent::LeftClick { .. } => {
                // Un simple clic gauche sur l'icône de la barre des tâches bascule la visibilité
                toggle_window_visibility(app);
            }
            SystemTrayEvent::MenuItemClick { id, .. } => match id.as_str() {
                "quit" => {
                    std::process::exit(0);
                }
                "toggle" => {
                    toggle_window_visibility(app);
                }
                _ => {}
            },
            _ => {}
        })
        .on_window_event(|event| match event.event() {
            WindowEvent::CloseRequested { api, .. } => {
                // Au lieu de fermer et détruire l'application, on la masque dans le system tray.
                // Cela garantit que l'application reste active pour les synchronisations et l'IA.
                event.window().hide().unwrap();
                api.prevent_close();
            }
            _ => {}
        })
        .invoke_handler(tauri::generate_handler![
            toggle_always_on_top,
            set_autostart,
            get_autostart
        ])
        .run(tauri::generate_context!())
        .expect("Erreur lors de l'exécution de l'application Tauri");
}
