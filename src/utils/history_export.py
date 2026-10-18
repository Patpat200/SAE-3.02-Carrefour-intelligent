from pathlib import Path


def export_history(entries, path):
    texte = "Historique de l'interface Carrefour connecté\n\n"
    texte += "\n".join(entries) + "\n"
    Path(path).write_text(texte, encoding="utf-8")
