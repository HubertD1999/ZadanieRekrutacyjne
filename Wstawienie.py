import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.api
import ifcopenshell.util.unit

import numpy as np

from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union

from pathlib import Path
import shutil


# ============================================================
# USTAWIENIA
# ============================================================

IFC_FILE = "SEGMENT.ifc"
ANTENA_FILE = "ANTENA.ifc"

TARGET_AZIMUTH = 123.0
TARGET_Z = 3.0

ANTENA_GUID = "3SEmPjtkzBSxSIeRUptjB2"

WORK_DIR = Path("wynik")


# ============================================================
# FUNKCJE
# ============================================================

def azimuth_from_xy(dx, dy):
    angle = np.degrees(np.arctan2(dx, dy))
    return angle % 360.0


def angular_difference(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def triangle_plane_intersection(
    v0,
    v1,
    v2,
    z_plane,
    eps=1e-9
):
    vertices = [v0, v1, v2]
    points = []

    edges = [
        (vertices[0], vertices[1]),
        (vertices[1], vertices[2]),
        (vertices[2], vertices[0]),
    ]

    for p1, p2 in edges:

        z1 = p1[2]
        z2 = p2[2]

        if abs(z1 - z_plane) < eps and \
           abs(z2 - z_plane) < eps:

            points.append(
                np.array([
                    p1[0],
                    p1[1],
                    z_plane
                ])
            )

            points.append(
                np.array([
                    p2[0],
                    p2[1],
                    z_plane
                ])
            )

            continue

        if abs(z1 - z_plane) < eps:

            points.append(
                np.array([
                    p1[0],
                    p1[1],
                    z_plane
                ])
            )

        if abs(z2 - z_plane) < eps:

            points.append(
                np.array([
                    p2[0],
                    p2[1],
                    z_plane
                ])
            )

        if (z1 - z_plane) * (z2 - z_plane) < 0:

            t = (z_plane - z1) / (z2 - z1)

            point = p1 + t * (p2 - p1)
            point[2] = z_plane

            points.append(point)

    unique = []

    for p in points:

        if not any(
            np.linalg.norm(p - q) < eps
            for q in unique
        ):
            unique.append(p)

    if len(unique) >= 2:
        return unique[0], unique[1]

    return None


def section_centroid(shape, z_plane):

    verts = np.asarray(
        shape.geometry.verts,
        dtype=float
    ).reshape(-1, 3)

    faces = np.asarray(
        shape.geometry.faces,
        dtype=int
    ).reshape(-1, 3)

    segments = []

    SNAP = 1e-6

    def snap_xy(x, y):
        return (
            round(x / SNAP) * SNAP,
            round(y / SNAP) * SNAP
        )

    for face in faces:

        v0 = verts[face[0]]
        v1 = verts[face[1]]
        v2 = verts[face[2]]

        result = triangle_plane_intersection(
            v0,
            v1,
            v2,
            z_plane
        )

        if result is None:
            continue

        p1, p2 = result

        x1, y1 = snap_xy(
            p1[0],
            p1[1]
        )

        x2, y2 = snap_xy(
            p2[0],
            p2[1]
        )

        if abs(x1 - x2) < SNAP and \
           abs(y1 - y2) < SNAP:
            continue

        segments.append(
            LineString([
                (x1, y1),
                (x2, y2)
            ])
        )

    print(
        f"Znaleziono {len(segments)} "
        f"odcinków przekroju."
    )

    if not segments:
        return None

    merged = unary_union(segments)

    polygons = list(
        polygonize(merged)
    )

    print(
        f"Utworzono {len(polygons)} "
        f"poligonów przekroju."
    )

    if not polygons:
        return None

    polygons_sorted = sorted(
        polygons,
        key=lambda p: p.area,
        reverse=True
    )

    outer = polygons_sorted[0]

    holes = []

    for polygon in polygons_sorted[1:]:

        if outer.contains(polygon):
            holes.append(polygon)

    section = outer

    for hole in holes:
        section = section.difference(hole)

    centroid = section.centroid

    return (
        centroid.x,
        centroid.y,
        z_plane,
        section.area
    )


# ============================================================
# 1. OTWARCIE SEGMENTU
# ============================================================

model = ifcopenshell.open(IFC_FILE)

settings = ifcopenshell.geom.settings()

settings.set(
    settings.USE_WORLD_COORDS,
    True
)


# ============================================================
# 2. ZNALEZIENIE KOLUMN
# ============================================================

columns = model.by_type("IfcColumn")

if not columns:
    raise RuntimeError(
        "Nie znaleziono żadnego IfcColumn."
    )


column_data = []

for column in columns:

    try:

        shape = ifcopenshell.geom.create_shape(
            settings,
            column
        )

    except Exception as e:

        print(
            f"Nie można utworzyć geometrii "
            f"dla {column.GlobalId}: {e}"
        )

        continue

    verts = np.asarray(
        shape.geometry.verts,
        dtype=float
    ).reshape(-1, 3)

    min_xyz = verts.min(axis=0)
    max_xyz = verts.max(axis=0)

    center = (
        min_xyz + max_xyz
    ) / 2.0

    column_data.append({
        "entity": column,
        "shape": shape,
        "center": center,
        "min": min_xyz,
        "max": max_xyz,
    })


if not column_data:
    raise RuntimeError(
        "Nie udało się odczytać geometrii kolumn."
    )


# ============================================================
# 3. ŚRODEK KONSTRUKCJI
# ============================================================

construction_center = np.mean(
    [c["center"] for c in column_data],
    axis=0
)

print()
print("=== KONSTRUKCJA ===")

print(
    f"Środek konstrukcji: "
    f"X={construction_center[0]:.3f}, "
    f"Y={construction_center[1]:.3f}, "
    f"Z={construction_center[2]:.3f}"
)


# ============================================================
# 4. AZYMUTY KOLUMN
# ============================================================

print()
print("=== KOLUMNY ===")

for i, data in enumerate(
    column_data,
    start=1
):

    center = data["center"]

    dx = (
        center[0]
        - construction_center[0]
    )

    dy = (
        center[1]
        - construction_center[1]
    )

    azimuth = azimuth_from_xy(
        dx,
        dy
    )

    difference = angular_difference(
        azimuth,
        TARGET_AZIMUTH
    )

    data["azimuth"] = azimuth
    data["azimuth_difference"] = difference

    column = data["entity"]

    print(
        f"{i:2d}. "
        f"{column.GlobalId} | "
        f"{column.Name} | "
        f"X={center[0]:.3f}, "
        f"Y={center[1]:.3f} | "
        f"azymut={azimuth:.2f}° | "
        f"Δ={difference:.2f}°"
    )


# ============================================================
# 5. WYBÓR NOGI
# ============================================================

selected = min(
    column_data,
    key=lambda x: x["azimuth_difference"]
)

selected_column = selected["entity"]

print()
print("=== WYBRANA NOGA ===")

print(
    f"GlobalId: {selected_column.GlobalId}"
)

print(
    f"Name: {selected_column.Name}"
)

print(
    f"Azymut: {selected['azimuth']:.2f}°"
)

print(
    f"Różnica od {TARGET_AZIMUTH}°: "
    f"{selected['azimuth_difference']:.2f}°"
)


# ============================================================
# 6. PRZEKRÓJ
# ============================================================

print()

print(
    f"=== PRZEKRÓJ NOGI NA Z = "
    f"{TARGET_Z:.3f} ==="
)

result = section_centroid(
    selected["shape"],
    TARGET_Z
)

if result is None:
    raise RuntimeError(
        f"Nie udało się znaleźć przekroju "
        f"na Z={TARGET_Z}."
    )

x, y, z, area = result


# ============================================================
# 7. PUNKT WSTAWIENIA
# ============================================================

target = np.array(
    [
        x,
        y,
        z
    ],
    dtype=float
)

print()
print("=== PUNKT WSTAWIENIA ===")

print(
    f"X = {x:.6f}"
)

print(
    f"Y = {y:.6f}"
)

print(
    f"Z = {z:.6f}"
)

print(
    f"Pole przekroju = {area:.6f} m²"
)


# ============================================================
# 8. KOPIE PLIKÓW
# ============================================================

WORK_DIR.mkdir(
    parents=True,
    exist_ok=True
)

segment_work = (
    WORK_DIR /
    "SEGMENT_work.ifc"
)

antenna_work = (
    WORK_DIR /
    "ANTENA_work.ifc"
)

shutil.copy2(
    IFC_FILE,
    segment_work
)

shutil.copy2(
    ANTENA_FILE,
    antenna_work
)


# ============================================================
# 9. OTWARCIE MODELI
# ============================================================

segment_model = ifcopenshell.open(
    str(segment_work)
)

antenna_model = ifcopenshell.open(
    str(antenna_work)
)


# ============================================================
# 10. ZNALEZIENIE ANTENY
# ============================================================

antenna_source = antenna_model.by_guid(
    ANTENA_GUID
)

if antenna_source is None:

    raise RuntimeError(
        f"Nie znaleziono anteny "
        f"{ANTENA_GUID}."
    )


print()
print("=== ANTENA ŹRÓDŁOWA ===")

print(
    f"Name: {antenna_source.Name}"
)

print(
    f"GlobalId: {antenna_source.GlobalId}"
)

print(
    f"Klasa: {antenna_source.is_a()}"
)


# ============================================================
# 11. ZNALEZIENIE STOREY W SEGMENT
# ============================================================

storeys = segment_model.by_type(
    "IfcBuildingStorey"
)

if not storeys:

    raise RuntimeError(
        "W SEGMENT.ifc nie znaleziono "
        "żadnego IfcBuildingStorey."
    )


print()
print("=== STOREY W SEGMENT ===")

for i, storey in enumerate(
    storeys,
    start=1
):

    print(
        f"{i}. "
        f"{storey.GlobalId} | "
        f"{storey.Name}"
    )


# ------------------------------------------------------------
# Wybieramy pierwszy IfcBuildingStorey.
#
# Jeżeli SEGMENT ma kilka kondygnacji, można później
# zmienić tę linię na wybór konkretnego Storey.
# ------------------------------------------------------------

target_storey = storeys[0]

print()
print(
    f"Antena zostanie przypisana do: "
    f"{target_storey.Name}"
)


# ============================================================
# 12. KOPIOWANIE ANTENY
# ============================================================

print()
print("=== KOPIOWANIE ANTENY ===")

antenna_copy = ifcopenshell.api.run(
    "project.append_asset",
    segment_model,
    library=antenna_model,
    element=antenna_source,
    assume_asset_uniqueness_by_name=False
)

if antenna_copy is None:

    raise RuntimeError(
        "Nie udało się skopiować anteny."
    )


print(
    f"Utworzono: "
    f"{antenna_copy.GlobalId}"
)


# ============================================================
# 13. PRZYPISANIE ANTENY DO BUILDING STOREY
# ============================================================
#
# To jest kluczowa zmiana względem poprzedniej wersji.
#
# Antena nie może być tylko obiektem istniejącym w pliku.
# Musi być podpięta do struktury przestrzennej modelu.
#
# ============================================================

print()
print("=== PRZYPISYWANIE ANTENY DO STOREY ===")

try:

    ifcopenshell.api.run(
        "spatial.assign_container",
        segment_model,
        products=[antenna_copy],
        relating_structure=target_storey
    )

except Exception as e:

    raise RuntimeError(
        "Nie udało się przypisać anteny "
        f"do IfcBuildingStorey: {e}"
    )


print(
    f"Antena przypisana do: "
    f"{target_storey.Name}"
)


# ============================================================
# 14. JEDNOSTKI
# ============================================================

unit_scale = (
    ifcopenshell.util.unit.calculate_unit_scale(
        segment_model
    )
)

print()
print("=== JEDNOSTKI ===")

print(
    f"unit_scale = {unit_scale}"
)


# ============================================================
# 15. MACIERZ POŁOŻENIA
# ============================================================

AZIMUTH_REF = TARGET_AZIMUTH + 90.0

azimuth_rad = np.radians(
    AZIMUTH_REF
)

direction_x = np.sin(
    azimuth_rad
)

direction_y = np.cos(
    azimuth_rad
)


matrix = np.eye(4)


# Oś X anteny
matrix[0, 0] = direction_x
matrix[1, 0] = direction_y
matrix[2, 0] = 0.0


# Oś Y anteny
matrix[0, 1] = -direction_y
matrix[1, 1] = direction_x
matrix[2, 1] = 0.0


# Oś Z
matrix[0, 2] = 0.0
matrix[1, 2] = 0.0
matrix[2, 2] = 1.0


# Punkt wstawienia
matrix[0, 3] = target[0]
matrix[1, 3] = target[1]
matrix[2, 3] = target[2]


print()
print("=== PLACEMENT ANTENY ===")

print(
    f"X = {target[0]:.6f}"
)

print(
    f"Y = {target[1]:.6f}"
)

print(
    f"Z = {target[2]:.6f}"
)

print(
    f"Azymut = {TARGET_AZIMUTH:.2f}°"
)


# ============================================================
# 16. USTAWIENIE PLACEMENTU
# ============================================================

ifcopenshell.api.run(
    "geometry.edit_object_placement",
    segment_model,
    product=antenna_copy,
    matrix=matrix,
    is_si=True,
    should_transform_children=True
)


# ============================================================
# 17. KONTROLA REFERENCJI PRZESTRZENNEJ
# ============================================================

print()
print("=== KONTROLA REFERENCJI ===")

container = None

for rel in segment_model.by_type(
    "IfcRelContainedInSpatialStructure"
):

    if antenna_copy in rel.RelatedElements:

        container = rel.RelatingStructure
        break


if container is None:

    raise RuntimeError(
        "UWAGA: antena nadal nie jest "
        "podpięta do struktury przestrzennej!"
    )


print(
    f"Antena znajduje się w: "
    f"{container.is_a()} "
    f"'{container.Name}'"
)


# ============================================================
# 18. ZAPIS
# ============================================================

output_file = (
    WORK_DIR /
    "SEGMENT_z_antena.ifc"
)

segment_model.write(
    str(output_file)
)


# ============================================================
# 19. GOTOWE
# ============================================================

print()
print("========================================")
print("                 GOTOWE")
print("========================================")

print(
    f"Punkt anteny:"
)

print(
    f"X = {x:.6f}"
)

print(
    f"Y = {y:.6f}"
)

print(
    f"Z = {z:.6f}"
)

print(
    f"Azymut = {TARGET_AZIMUTH:.2f}°"
)

print()
print(
    "Antena została przypisana do "
    f"IfcBuildingStorey: {target_storey.Name}"
)

print()
print(
    "Nie zmieniano reprezentacji geometrii anteny."
)

print(
    "Nie tworzono nowego IfcTriangulatedFaceSet."
)

print()
print(
    f"Zapisano: {output_file}"
)