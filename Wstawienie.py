import ifcopenshell.geom
import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union
from pathlib import Path
import shutil
import ifcopenshell.util.element
import ifcopenshell.util.unit

IFC_FILE = "SEGMENT.ifc"

TARGET_AZIMUTH = 123.0

TARGET_Z = 3.0

ANTENA_GUID = "3SEmPjtkzBSxSIeRUptjB2"

WORK_DIR = Path("wynik")


def azimuth_from_xy(dx, dy):
    angle = np.degrees(np.arctan2(dx, dy))
    return angle % 360.0


def angular_difference(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def triangle_plane_intersection(v0, v1, v2, z_plane, eps=1e-9):

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

        if abs(z1 - z_plane) < eps and abs(z2 - z_plane) < eps:

            points.append(
                np.array([p1[0], p1[1], z_plane])
            )

            points.append(
                np.array([p2[0], p2[1], z_plane])
            )

            continue

        if abs(z1 - z_plane) < eps:

            points.append(
                np.array([p1[0], p1[1], z_plane])
            )

        if abs(z2 - z_plane) < eps:

            points.append(
                np.array([p2[0], p2[1], z_plane])
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


model = ifcopenshell.open(IFC_FILE)

settings = ifcopenshell.geom.settings()

settings.set(
    settings.USE_WORLD_COORDS,
    True
)

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


size = (
    selected["max"]
    - selected["min"]
)

print()
print("=== ROZMIAR GEOMETRII NOGI ===")

print(
    f"X = {size[0]:.6f}"
)

print(
    f"Y = {size[1]:.6f}"
)

print(
    f"Z = {size[2]:.6f}"
)


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

print()
print("Punkt do wstawienia anteny:")

print(
    f"({x:.6f}, {y:.6f}, {z:.6f})"
)


WORK_DIR.mkdir(
    parents=True,
    exist_ok=True
)

shutil.copy2(
    "SEGMENT.ifc",
    WORK_DIR / "SEGMENT_work.ifc"
)

shutil.copy2(
    "ANTENA.ifc",
    WORK_DIR / "ANTENA_work.ifc"
)

print(
    "\nSkopiowano pliki do folderu:",
    WORK_DIR
)


segment_model = ifcopenshell.open(
    str(WORK_DIR / "SEGMENT_work.ifc")
)

antenna_model = ifcopenshell.open(
    str(WORK_DIR / "ANTENA_work.ifc")
)


target = np.array(
    [
        x,
        y,
        z
    ],
    dtype=float
)

print(
    "\nPunkt wstawienia anteny:"
)

print(
    f"X = {target[0]:.6f}, "
    f"Y = {target[1]:.6f}, "
    f"Z = {target[2]:.6f}"
)


antenna_source = antenna_model.by_guid(
    ANTENA_GUID
)

if antenna_source is None:

    raise RuntimeError(
        f"Nie znaleziono anteny: "
        f"{ANTENA_GUID}"
    )


print(
    "\nZnaleziono antenę:"
)

print(
    f"Name: {antenna_source.Name}"
)

print(
    f"GlobalId: {antenna_source.GlobalId}"
)


antenna_copy = ifcopenshell.util.element.copy_deep(
    segment_model,
    antenna_source
)


unit_scale = (
    ifcopenshell.util.unit.calculate_unit_scale(
        segment_model
    )
)

target_ifc = (
    target / unit_scale
)

print(
    "\n=== JEDNOSTKI ==="
)

print(
    f"unit_scale = {unit_scale}"
)

print(
    "Punkt w jednostkach IFC:"
)

print(
    f"X = {target_ifc[0]:.3f}"
)

print(
    f"Y = {target_ifc[1]:.3f}"
)

print(
    f"Z = {target_ifc[2]:.3f}"
)


placement = antenna_copy.ObjectPlacement

if placement is None:

    placement = segment_model.create_entity(
        "IfcLocalPlacement"
    )

    antenna_copy.ObjectPlacement = placement


placement.PlacementRelTo = None


relative = placement.RelativePlacement

if relative is None:

    relative = segment_model.create_entity(
        "IfcAxis2Placement3D"
    )

    placement.RelativePlacement = relative


relative.Location = segment_model.create_entity(
    "IfcCartesianPoint",
    Coordinates=(
        float(target_ifc[0]),
        float(target_ifc[1]),
        float(target_ifc[2])
    )
)


AZIMUTH_REF = TARGET_AZIMUTH + 90

azimuth_rad = np.radians(
    AZIMUTH_REF
)

relative.Axis = segment_model.create_entity(
    "IfcDirection",
    DirectionRatios=(
        0.0,
        0.0,
        1.0
    )
)

direction_x = np.sin(
    azimuth_rad
)

direction_y = np.cos(
    azimuth_rad
)

relative.RefDirection = segment_model.create_entity(
    "IfcDirection",
    DirectionRatios=(
        float(direction_x),
        float(direction_y),
        0.0
    )
)


print()
print("=== ORIENTACJA ANTENY ===")

print(
    f"Obrót wokół osi Z = "
    f"{TARGET_AZIMUTH:.2f}°"
)

print(
    "Oś obrotu = origin anteny"
)

print(
    "Kierunek końcowy = "
    f"azymut {TARGET_AZIMUTH:.2f}°"
)

print(
    "RefDirection = "
    f"({direction_x:.6f}, "
    f"{direction_y:.6f}, "
    f"0.000000)"
)


output_file = (
    WORK_DIR /
    "SEGMENT_z_antena.ifc"
)

segment_model.write(
    str(output_file)
)


print()
print("=== GOTOWE ===")

print(
    f"Antena wstawiona w: "
    f"({x:.6f}, {y:.6f}, {z:.6f})"
)

print(
    f"Azymut anteny: "
    f"{TARGET_AZIMUTH:.2f}°"
)

print(
    f"Zapisano: {output_file}"
)
