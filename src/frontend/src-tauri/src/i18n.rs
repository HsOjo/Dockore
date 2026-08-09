use std::collections::HashMap;
use std::sync::Mutex;

/// Minimal i18n helper for Rust-side notifications. The locale is set from the
/// frontend based on the value stored in `localStorage` under `dockore_ui`.
pub struct I18n {
    translations: HashMap<&'static str, HashMap<&'static str, &'static str>>,
    locale: Mutex<String>,
}

impl I18n {
    pub fn new() -> Self {
        let mut translations: HashMap<&str, HashMap<&str, &str>> = HashMap::new();

        let mut zh = HashMap::new();
        zh.insert(
            "notification_hidden_to_tray",
            "Dockore 已隐藏到托盘，点击托盘图标可重新打开窗口",
        );
        zh.insert(
            "notification_already_running",
            "Dockore 已在后台运行，点击托盘图标打开窗口",
        );
        zh.insert("tray_show_main_window", "显示主窗口");
        zh.insert("tray_quit", "退出");

        let mut en = HashMap::new();
        en.insert(
            "notification_hidden_to_tray",
            "Dockore is hidden in the tray. Click the tray icon to reopen the window.",
        );
        en.insert(
            "notification_already_running",
            "Dockore is already running. Click the tray icon to open the window.",
        );
        en.insert("tray_show_main_window", "Show Main Window");
        en.insert("tray_quit", "Quit");

        translations.insert("zh-CN", zh);
        translations.insert("en", en);

        Self {
            translations,
            locale: Mutex::new("zh-CN".to_string()),
        }
    }

    pub fn set_locale(&self, locale: &str) {
        *self.locale.lock().unwrap() = locale.to_string();
    }

    pub fn t(&self, key: &str) -> String {
        let locale = self.locale.lock().unwrap().clone();
        self.translations
            .get(locale.as_str())
            .and_then(|m| m.get(key).copied())
            .or_else(|| self.translations.get("en").and_then(|m| m.get(key).copied()))
            .unwrap_or(key)
            .to_string()
    }
}
