// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use rand::Rng;
use std::net::TcpListener;
use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::atomic::{AtomicBool, AtomicU16, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;
#[cfg(windows)]
use std::os::windows::process::CommandExt;
use tauri::{Emitter, Manager, Wry};
use tauri::menu::{Menu, MenuItem, MenuItemBuilder};
use tauri_plugin_notification::NotificationExt;

mod i18n;
use i18n::I18n;

/// Wraps a child process so it is killed when the wrapper is dropped.
struct KillOnDrop(Child);

impl Drop for KillOnDrop {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}

struct BackendHandle {
    child: Arc<Mutex<Option<KillOnDrop>>>,
    ready: Arc<Mutex<bool>>,
    port: AtomicU16,
    token: Mutex<String>,
    started: AtomicBool,
    quitting: AtomicBool,
}

/// Holds references to the tray menu items so their labels can be updated
/// when the application locale changes.
struct TrayMenu {
    show: MenuItem<Wry>,
    quit: MenuItem<Wry>,
}

#[derive(Clone, serde::Serialize)]
struct BuiltinBackendConfig {
    port: u16,
    token: String,
}

#[tauri::command]
fn is_backend_ready(state: tauri::State<'_, BackendHandle>) -> bool {
    *state.ready.lock().unwrap()
}

#[tauri::command]
fn get_builtin_backend_config(state: tauri::State<'_, BackendHandle>) -> BuiltinBackendConfig {
    BuiltinBackendConfig {
        port: state.port.load(Ordering::Relaxed),
        token: state.token.lock().unwrap().clone(),
    }
}

/// Ask the OS for a free loopback port. The listener is dropped immediately so
/// the backend can bind to the same port.
fn pick_free_port() -> u16 {
    let listener = TcpListener::bind("127.0.0.1:0").expect("failed to bind to a free port");
    let port = listener.local_addr().unwrap().port();
    drop(listener);
    port
}

/// Generate a random bearer token for the built-in backend.
fn generate_token() -> String {
    let mut rng = rand::thread_rng();
    (0..32)
        .map(|_| format!("{:02x}", rng.gen::<u8>()))
        .collect()
}

#[tauri::command]
async fn start_builtin_backend(
    app: tauri::AppHandle,
    state: tauri::State<'_, BackendHandle>,
) -> Result<BuiltinBackendConfig, String> {
    // Ensure the backend is only started once.
    if state
        .started
        .compare_exchange(false, true, Ordering::Relaxed, Ordering::Relaxed)
        .is_err()
    {
        return Ok(BuiltinBackendConfig {
            port: state.port.load(Ordering::Relaxed),
            token: state.token.lock().unwrap().clone(),
        });
    }

    let backend_path = app
        .path()
        .resolve("backend/dockore-backend", tauri::path::BaseDirectory::Resource)
        .map_err(|e| e.to_string())?;
    let backend_path = if cfg!(windows) {
        backend_path.with_extension("exe")
    } else {
        backend_path
    };

    if !backend_path.exists() {
        return Err("Bundled backend not found".to_string());
    }

    let port = pick_free_port();
    let token = generate_token();

    state.port.store(port, Ordering::Relaxed);
    *state.token.lock().unwrap() = token.clone();

    let app_data_dir = app
        .path()
        .app_data_dir()
        .map_err(|e| e.to_string())?;
    let data_dir: PathBuf = app_data_dir.join("data");
    std::fs::create_dir_all(&data_dir).map_err(|e| e.to_string())?;

    let parent_pid = std::process::id();
    let backend_base_url = format!("http://127.0.0.1:{}", port);
    let mut cmd = Command::new(&backend_path);
    cmd.env("DOCKORE_PORT", port.to_string())
        .env("DOCKORE_PARENT_PID", parent_pid.to_string())
        .env("DOCKORE_TOKEN", &token)
        .env("DOCKORE_DATA_DIR", &data_dir)
        .env(
            "DOCKORE_CORS_ORIGINS",
            format!("tauri://localhost,http://tauri.localhost,{}", backend_base_url),
        );
    #[cfg(windows)]
    {
        // CREATE_NO_WINDOW: do not allocate a console for the backend process.
        cmd.creation_flags(0x08000000);
    }
    let child = cmd.spawn().map_err(|e| e.to_string())?;

    state.child.lock().unwrap().replace(KillOnDrop(child));

    let app_handle = app.clone();
    let ready = state.ready.clone();
    std::thread::spawn(move || {
        let addr = format!("127.0.0.1:{}", port);
        for _ in 0..120 {
            if std::net::TcpStream::connect(&addr).is_ok() {
                *ready.lock().unwrap() = true;
                app_handle.emit("backend:ready", ()).ok();
                return;
            }
            std::thread::sleep(Duration::from_millis(500));
        }
        eprintln!("Backend failed to become ready on {}", addr);
    });

    Ok(BuiltinBackendConfig { port, token })
}

#[tauri::command]
fn toggle_devtools(window: tauri::WebviewWindow) {
    if window.is_devtools_open() {
        window.close_devtools();
    } else {
        window.open_devtools();
    }
}

#[tauri::command]
fn set_locale(
    locale: String,
    i18n: tauri::State<'_, I18n>,
    tray_menu: tauri::State<'_, TrayMenu>,
) {
    i18n.set_locale(&locale);
    let _ = tray_menu.show.set_text(i18n.t("tray_show_main_window"));
    let _ = tray_menu.quit.set_text(i18n.t("tray_quit"));
}

/// Show and focus the main window. On macOS also ensures the app is visible in
/// the Dock and has its icon set.
fn show_and_focus_main_window(app: &tauri::AppHandle) {
    #[cfg(target_os = "macos")]
    {
        let _ = app.set_activation_policy(tauri::ActivationPolicy::Regular);
        set_dock_icon();
    }
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.set_focus();
    }
}

/// Show a Rust-side notification using the current i18n locale. Errors are logged
/// but not propagated to avoid breaking the single-instance / tray flows.
fn show_notification(app: &tauri::AppHandle, body_key: &str) {
    let i18n = app.state::<I18n>();
    if let Err(e) = app
        .notification()
        .builder()
        .title("Dockore")
        .body(i18n.t(body_key))
        .show()
    {
        eprintln!("Failed to show notification ({}): {}", body_key, e);
    }
}

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_process::init())
        // TODO: tauri.conf.json 中的 updater 端点与 pubkey 为占位值，
        // 发布自动更新前需替换为正式的更新服务与签名公钥。
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_single_instance::init(|app, _argv, _cwd| {
            show_and_focus_main_window(app);
            show_notification(app, "notification_already_running");
        }))
        .manage(BackendHandle {
            child: Arc::new(Mutex::new(None)),
            ready: Arc::new(Mutex::new(false)),
            port: AtomicU16::new(0),
            token: Mutex::new(String::new()),
            started: AtomicBool::new(false),
            quitting: AtomicBool::new(false),
        })
        .manage(I18n::new())
        .setup(|app| {
            #[cfg(target_os = "macos")]
            {
                set_dock_icon();
                let _ = app.notification().request_permission();
            }

            // Build a localized tray menu and tray icon. Left-click shows/focuses the window;
            // right-click opens the menu.
            let i18n = app.state::<I18n>();
            let show_item =
                MenuItemBuilder::with_id("tray-show", i18n.t("tray_show_main_window"))
                    .build(app)?;
            let quit_item = MenuItemBuilder::with_id("tray-quit", i18n.t("tray_quit")).build(app)?;
            let tray_menu = Menu::with_items(app, &[&show_item, &quit_item])?;
            app.manage(TrayMenu {
                show: show_item,
                quit: quit_item,
            });

            let tray_icon = tauri::image::Image::from_bytes(include_bytes!("../icons/icon.png"))
                .map_err(|e| e.to_string())?;
            let _ = tauri::tray::TrayIconBuilder::with_id("tray")
                .icon(tray_icon)
                .tooltip("Dockore")
                .menu(&tray_menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| {
                    match event.id().as_ref() {
                        "tray-show" => show_and_focus_main_window(app),
                        "tray-quit" => {
                            let state = app.state::<BackendHandle>();
                            state.quitting.store(true, Ordering::Relaxed);
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let tauri::tray::TrayIconEvent::Click {
                        button: tauri::tray::MouseButton::Left,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        show_and_focus_main_window(app);
                    }
                })
                .build(app)?;

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                let app = window.app_handle();
                let state = app.state::<BackendHandle>();
                if !state.quitting.load(Ordering::Relaxed) {
                    api.prevent_close();
                    let _ = window.hide();

                    show_notification(app, "notification_hidden_to_tray");

                    #[cfg(target_os = "macos")]
                    {
                        let _ = app.set_activation_policy(tauri::ActivationPolicy::Accessory);
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            is_backend_ready,
            get_builtin_backend_config,
            start_builtin_backend,
            toggle_devtools,
            set_locale
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        match event {
            // Handle both ExitRequested and Exit. On Windows, the default File -> Exit menu
            // uses PostQuitMessage, which triggers Exit rather than ExitRequested.
            tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit => {
                let state = app_handle.state::<BackendHandle>();
                state.quitting.store(true, Ordering::Relaxed);
                let child_opt = state.child.lock().unwrap().take();
                if let Some(child) = child_opt {
                    // Dropping KillOnDrop sends kill() and waits for the process to exit.
                    drop(child);
                }
            }
            #[cfg(target_os = "macos")]
            tauri::RunEvent::Reopen { .. } => {
                show_and_focus_main_window(app_handle);
            }
            _ => {}
        }
    });
}

#[cfg(target_os = "macos")]
fn set_dock_icon() {
    use objc2::ClassType;
    use objc2_app_kit::{NSApplication, NSImage};
    use objc2_foundation::NSData;

    let mtm = objc2_foundation::MainThreadMarker::new().expect("must be on main thread");

    let bytes = include_bytes!("../icons/icon.png");
    let data = NSData::with_bytes(bytes);
    let image = NSImage::initWithData(NSImage::alloc(), &data);

    let app = NSApplication::sharedApplication(mtm);
    unsafe {
        app.setApplicationIconImage(image.as_deref());
    }
}
