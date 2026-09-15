import ifcopenshell.geom
from ifcopenshell.util.unit import calculate_unit_scale

class IFCValidator:

    def __init__(self, model):
        self.model = model

    def check_missing_attribute(self, attribute, ifc_type="IfcElement"):
        missing = []

        for element in self.model.by_type(ifc_type):
            value = getattr(element, attribute, None)

            if value is None or not str(value).strip():
                missing.append(element)

        return missing

    def check_duplicate_attribute(self, attribute, ifc_type="IfcElement"):
        values = {}

        for element in self.model.by_type(ifc_type):
            value = getattr(element, attribute, None)

            if value:
                if value not in values:
                    values[value] = []

                values[value].append(element)

        duplicates = {
            value: elements
            for value, elements in values.items()
            if len(elements) > 1
        }

        return duplicates

    def check_element_levels(self):

        unit_scale = ifcopenshell.util.unit.calculate_unit_scale(self.model)
        wrong = []
        intersecting = []

        # -------------------------
        # 1. Pobranie leveli
        # -------------------------

        levels = []

        for storey in self.model.by_type("IfcBuildingStorey"):

            placement = storey.ObjectPlacement

            if not placement:
                continue

            z = placement.RelativePlacement.Location.Coordinates[2]

            levels.append({
                "storey": storey,
                "name": storey.Name,
                "z": z*unit_scale,
            })

        # Sortowanie od najniższego do najwyższego
        levels.sort(key=lambda x: x["z"])


        # -------------------------
        # 2. Geometria
        # -------------------------

        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)

        # -------------------------
        # 3. Elementy
        # -------------------------

        for element in self.model.by_type("IfcElement"):

            # Szukamy levelu przypisanego do elementu
            assigned_level = None

            for relation in self.model.by_type(
                    "IfcRelContainedInSpatialStructure"
            ):
                if element in relation.RelatedElements:

                    if relation.RelatingStructure.is_a(
                            "IfcBuildingStorey"
                    ):
                        assigned_level = relation.RelatingStructure
                        break

            if assigned_level is None:
                continue

            # Szukamy danych tego levelu
            level_index = None

            for index, level in enumerate(levels):
                if level["storey"] == assigned_level:
                    level_index = index
                    break

            if level_index is None:
                continue

            level_min_z = levels[level_index]["z"]

            # Górna granica = następny level
            if level_index + 1 < len(levels):
                level_max_z = levels[level_index + 1]["z"]
            else:
                level_max_z = float("inf")

            # -------------------------
            # 4. Pobieramy geometrię
            # -------------------------

            try:
                shape = ifcopenshell.geom.create_shape(
                    settings,
                    element
                )

                vertices = shape.geometry.verts

                if not vertices:
                    continue

                z_values = vertices[2::3]

                element_min_z = min(z_values)
                element_max_z = max(z_values)

            except Exception:
                continue

            # -------------------------
            # 5. Sprawdzamy położenie
            # -------------------------

            # Całkowicie poza levelem
            if (
                    element_max_z <= level_min_z
                    or element_min_z >= level_max_z
            ):
                wrong.append({
                    "element": element,
                    "level": levels[level_index]["name"],
                    "level_min_z": level_min_z,
                    "level_max_z": level_max_z,
                    "element_min_z": element_min_z,
                    "element_max_z": element_max_z
                })

            # Element przecina granicę levelu
            elif (
                    element_min_z <= level_min_z
                    or element_max_z >= level_max_z
            ):
                intersecting.append({
                    "element": element,
                    "level": levels[level_index]["name"],
                    "level_min_z": level_min_z,
                    "level_max_z": level_max_z,
                    "element_min_z": element_min_z,
                    "element_max_z": element_max_z
                })

        return wrong, intersecting


