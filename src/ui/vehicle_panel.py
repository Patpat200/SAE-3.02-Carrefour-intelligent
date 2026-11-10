from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QHeaderView, QLabel,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


class VehiclePanel(QWidget):
    vehicle_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.vehicles = []
        self.selected_id = ""
        self.visible_ids = []
        self.rows = None
        self.vehicles_by_id = {}
        self.road_filter = QComboBox()
        self.road_filter.addItems(["Toutes les voies", "Nord", "Sud", "Est", "Ouest"])
        self.emergency_filter = QCheckBox("Seulement les véhicules d'urgence")
        self.count_label = QLabel("Aucun véhicule reçu")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Véhicule", "Voie", "Type"])
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.details_label = QLabel("Sélectionner un véhicule pour le repérer sur le dessin.")
        self.details_label.setWordWrap(True)
        self.details_label.setTextFormat(Qt.TextFormat.PlainText)
        layout = QVBoxLayout(self)
        for widget in [self.road_filter, self.emergency_filter, self.count_label,
                       self.table, self.details_label]:
            layout.addWidget(widget)
        self.road_filter.currentIndexChanged.connect(self.refresh)
        self.emergency_filter.toggled.connect(self.refresh)
        self.table.itemSelectionChanged.connect(self.select_vehicle)

    def set_vehicles(self, vehicles):
        self.vehicles = vehicles
        self.refresh()

    def refresh(self):
        road = self.road_filter.currentText()
        rows = []
        self.vehicles_by_id = {}
        for index, vehicle in enumerate(self.vehicles):
            identifier = str(vehicle.get("id", "vehicule-" + str(index)))
            self.vehicles_by_id[identifier] = vehicle
            if road != "Toutes les voies" and vehicle.get("voie") != road:
                continue
            if self.emergency_filter.isChecked() and not vehicle.get("urgence"):
                continue
            rows.append((identifier, vehicle.get("voie", "—"),
                         "Urgence" if vehicle.get("urgence") else "Normal"))
        self.count_label.setText(str(len(rows)) + " affiché(s) sur " + str(len(self.vehicles)))
        if rows == self.rows:
            self.update_details()
            return
        self.rows = rows
        self.visible_ids = [row[0] for row in rows]
        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        for ligne, row in enumerate(rows):
            for colonne, texte in enumerate(row):
                item = QTableWidgetItem(texte)
                item.setToolTip(texte)
                self.table.setItem(ligne, colonne, item)
        if self.selected_id in self.visible_ids:
            self.table.selectRow(self.visible_ids.index(self.selected_id))
        else:
            self.table.clearSelection()
        self.table.blockSignals(False)
        self.select_vehicle()

    def select_vehicle(self):
        selected = self.table.selectionModel().selectedRows()
        identifier = self.visible_ids[selected[0].row()] if selected else ""
        self.selected_id = identifier
        self.update_details()
        self.vehicle_selected.emit(identifier)

    def update_details(self):
        identifier = self.selected_id
        vehicle = self.vehicles_by_id.get(identifier)
        if identifier:
            vehicle_type = "Urgence" if vehicle.get("urgence") else "Normal"
            self.details_label.setText(
                "Identifiant : " + identifier + "\n"
                "Voie : " + str(vehicle.get("voie", "—")) + "\n"
                "Type : " + vehicle_type + "\n"
                "Position : " + str(vehicle.get("position", "—")) + "\n"
                "Couleur : " + str(vehicle.get("couleur", "rouge" if vehicle.get("urgence") else "bleu"))
            )
        else:
            self.details_label.setText("Sélectionner un véhicule pour le repérer sur le dessin.")
