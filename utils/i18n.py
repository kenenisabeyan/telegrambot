from typing import Dict, Any

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "welcome": (
            "<b>👋 Welcome, {name}!</b>\n\n"
            "<b>🤖 Enterprise Telegram Bot</b>\n"
            "<i>Your all-in-one productivity assistant</i>\n\n"
            "<b>✨ Features:</b>\n"
            "• 🛠️ <b>Bot Manager</b> - Register & manage secondary bots\n"
            "• 📚 <b>FAQ System</b> - Instant answers\n"
            "• ⏰ <b>Smart Reminders</b> - Never miss tasks\n"
            "• 🤖 <b>AI Chat</b> - Multi-persona intelligence\n"
            "• 🌤 <b>Live Weather</b> - Real-time global forecasts\n"
            "• 📊 <b>Analytics</b> - Personal usage statistics\n\n"
            "<i>Type /help or use the buttons below to begin!</i>"
        ),
        "menu_title": "<b>Main Menu</b>\n\nChoose an option below:",
        "lang_changed": "✅ Language changed to English (US)!",
        "lang_select": "<b>🌐 Select Your Interface Language:</b>\n\nChoose a language below:",
        "access_denied": "❌ Access denied. Administrator privileges required.",
        "reminder_set": "✅ Reminder Set!",
        "cancel_done": "❌ Operation cancelled.",
    },
    "es": {
        "welcome": (
            "<b>👋 ¡Bienvenido, {name}!</b>\n\n"
            "<b>🤖 Bot de Telegram Empresarial</b>\n"
            "<i>Tu asistente de productividad todo en uno</i>\n\n"
            "<b>✨ Funcionalidades:</b>\n"
            "• 🛠️ <b>Gestor de Bots</b> - Registra y administra bots secundarios\n"
            "• 📚 <b>Sistema FAQ</b> - Respuestas instantáneas\n"
            "• ⏰ <b>Recordatorios Inteligentes</b> - Nunca olvides tareas\n"
            "• 🤖 <b>Chat con IA</b> - Inteligencia multipersona\n"
            "• 🌤 <b>Clima en Vivo</b> - Pronósticos globales en tiempo real\n"
            "• 📊 <b>Analíticas</b> - Estadísticas personales de uso\n\n"
            "<i>¡Escribe /help o usa los botones a continuación para comenzar!</i>"
        ),
        "menu_title": "<b>Menú Principal</b>\n\nElige una opción a continuación:",
        "lang_changed": "✅ ¡Idioma cambiado a Español!",
        "lang_select": "<b>🌐 Selecciona tu idioma de interfaz:</b>\n\nElige un idioma abajo:",
        "access_denied": "❌ Acceso denegado. Se requieren privilegios de administrador.",
        "reminder_set": "✅ ¡Recordatorio configurado!",
        "cancel_done": "❌ Operación cancelada.",
    },
    "fr": {
        "welcome": (
            "<b>👋 Bienvenue, {name} !</b>\n\n"
            "<b>🤖 Bot Telegram d'Entreprise</b>\n"
            "<i>Votre assistant de productivité tout-en-un</i>\n\n"
            "<b>✨ Fonctionnalités :</b>\n"
            "• 🛠️ <b>Gestionnaire de Bots</b> - Enregistrez et gérez vos bots secondaires\n"
            "• 📚 <b>Système FAQ</b> - Réponses instantanées\n"
            "• ⏰ <b>Rappels Intelligents</b> - Ne manquez jamais vos tâches\n"
            "• 🤖 <b>Chat IA</b> - Intelligence multi-personnalité\n"
            "• 🌤 <b>Météo en Direct</b> - Prévisions mondiales en temps réel\n"
            "• 📊 <b>Analytique</b> - Statistiques d'utilisation\n\n"
            "<i>Tapez /help ou utilisez les boutons ci-dessous pour démarrer !</i>"
        ),
        "menu_title": "<b>Menu Principal</b>\n\nChoisissez une option ci-dessous :",
        "lang_changed": "✅ Langue modifiée en Français !",
        "lang_select": "<b>🌐 Choisissez votre langue d'interface :</b>\n\nSélectionnez ci-dessous :",
        "access_denied": "❌ Accès refusé. Privilèges d'administrateur requis.",
        "reminder_set": "✅ Rappel enregistré !",
        "cancel_done": "❌ Opération annulée.",
    },
    "de": {
        "welcome": (
            "<b>👋 Willkommen, {name}!</b>\n\n"
            "<b>🤖 Enterprise Telegram Bot</b>\n"
            "<i>Ihr All-in-One-Produktivitätsassistent</i>\n\n"
            "<b>✨ Funktionen:</b>\n"
            "• 🛠️ <b>Bot Manager</b> - Registrieren & Verwalten von Bots\n"
            "• 📚 <b>FAQ-System</b> - Sofortige Antworten\n"
            "• ⏰ <b>Erinnerungen</b> - Keine Aufgaben verpassen\n"
            "• 🤖 <b>KI-Chat</b> - Multi-Persona Intelligenz\n"
            "• 🌤 <b>Live-Wetter</b> - Weltweite Echtzeit-Wetterberichte\n"
            "• 📊 <b>Analytik</b> - Persönliche Nutzungsstatistiken\n\n"
            "<i>Geben Sie /help ein oder nutzen Sie die Schaltflächen unten!</i>"
        ),
        "menu_title": "<b>Hauptmenü</b>\n\nWählen Sie unten eine Option:",
        "lang_changed": "✅ Sprache auf Deutsch geändert!",
        "lang_select": "<b>🌐 Wählen Sie Ihre Benutzeroberflächensprache:</b>\n\nWählen Sie unten:",
        "access_denied": "❌ Zugriff verweigert. Administratorrechte erforderlich.",
        "reminder_set": "✅ Erinnerung eingestellt!",
        "cancel_done": "❌ Vorgang abgebrochen.",
    }
}

SUPPORTED_LANGUAGES = {
    "en": "🇺🇸 English",
    "es": "🇪🇸 Español",
    "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch"
}

def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """Retrieve translated string with variable formatting and automated English fallback."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template

