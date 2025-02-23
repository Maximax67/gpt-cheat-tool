import qdarktheme

def switch_theme(theme: str):
    """
    Switch the theme of the application.

    :param app: QApplication instance
    :param theme: "dark", "light", or "system"
    """
    if theme == "dark":
        qdarktheme.setup_theme("dark")

    elif theme == "light":
        qdarktheme.setup_theme("light")

    elif theme == "system":
        qdarktheme.setup_theme("auto")
