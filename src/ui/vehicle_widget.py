from PyQt6.QtGui import QColor


def couleur_vehicule(vehicle):
    if vehicle.get("urgence"):
        return QColor("red")
    return QColor(vehicle.get("couleur", "blue"))
