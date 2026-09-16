import ifcopenshell
import ifcopenshell.geom
import matplotlib.pyplot as plt
import math


model = ifcopenshell.open("SEGMENT.ifc")

settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)


TARGET_AZIMUTH = 123.0

# Środek konstrukcji
CONSTRUCTION_X = 0.0
CONSTRUCTION_Y = 0.0


def calculate_cylinder_axis(vertices):
    """
    Wyznacza oś pochylonego walca na podstawie vertexów.

    Zakładamy, że vertexy występują tylko na dwóch końcach walca:
    - dolny przekrój
    - górny przekrój

    Zwraca:
        bottom_center = (x, y, z)
        top_center    = (x, y, z)
    """

    # --------------------------------------------
    # Zamiana płaskiej tablicy na punkty XYZ
    # --------------------------------------------

    points = []

    for i in range(0, len(vertices), 3):
        x = vertices[i]
        y = vertices[i + 1]
        z = vertices[i + 2]

        points.append((x, y, z))


    # --------------------------------------------
    # Znajdujemy dwa poziomy Z
    # --------------------------------------------

    z_values = [p[2] for p in points]

    min_z = min(z_values)
    max_z = max(z_values)


    # --------------------------------------------
    # Tolerancja
    # --------------------------------------------

    tolerance = 0.001


    bottom_points = [
        p for p in points
        if abs(p[2] - min_z) < tolerance
    ]

    top_points = [
        p for p in points
        if abs(p[2] - max_z) < tolerance
    ]


    # --------------------------------------------
    # Środek przekroju
    # --------------------------------------------

    def calculate_center(points):

        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        z = sum(p[2] for p in points) / len(points)

        return (x, y, z)


    bottom_center = calculate_center(bottom_points)
    top_center = calculate_center(top_points)


    return bottom_center, top_center


def point_on_axis_at_z(bottom, top, target_z):
    """
    Znajduje punkt na osi walca dla określonego Z.
    """

    x1, y1, z1 = bottom
    x2, y2, z2 = top

    # Parametr t:
    #
    # P = P_bottom + t * (P_top - P_bottom)
    #
    # szukamy takiego t, aby Z = target_z

    if abs(z2 - z1) < 1e-9:
        raise ValueError("Oś walca jest pozioma — brak przecięcia z zadanym Z.")

    t = (target_z - z1) / (z2 - z1)

    x = x1 + t * (x2 - x1)
    y = y1 + t * (y2 - y1)
    z = z1 + t * (z2 - z1)

    return (x, y, z)


def calculate_azimuth(point, origin=(0, 0)):
    """
    Azymut geodezyjny:
        0°   = północ
        90°  = wschód
        180° = południe
        270° = zachód
    """

    x, y, z = point

    origin_x, origin_y = origin

    dx = x - origin_x
    dy = y - origin_y

    azimuth = math.degrees(
        math.atan2(dx, dy)
    ) % 360

    return azimuth


def angular_difference(a, b):
    """
    Najmniejsza różnica między dwoma azymutami.
    """

    return abs((a - b + 180) % 360 - 180)


# ============================================================
# ANALIZA NÓG
# ============================================================

columns = []


for column in model.by_type("IfcColumn"):

    shape = ifcopenshell.geom.create_shape(
        settings,
        column
    )

    vertices = shape.geometry.verts


    # --------------------------------------------
    # OŚ WALCA
    # --------------------------------------------

    bottom_center, top_center = calculate_cylinder_axis(
        vertices
    )


    # --------------------------------------------
    # Punkt osi na wysokości 3 m
    # --------------------------------------------

    point_3m = point_on_axis_at_z(
        bottom_center,
        top_center,
        3.0
    )


    # --------------------------------------------
    # AZYMUT
    # --------------------------------------------

    azimuth = calculate_azimuth(
        point_3m,
        (
            CONSTRUCTION_X,
            CONSTRUCTION_Y
        )
    )


    difference = angular_difference(
        azimuth,
        TARGET_AZIMUTH
    )


    column_data = {
        "column": column,
        "id": column.id(),

        "bottom": bottom_center,
        "top": top_center,

        "point_3m": point_3m,

        "azimuth": azimuth,
        "difference": difference
    }


    columns.append(column_data)


    # --------------------------------------------
    # PRINT
    # --------------------------------------------

    print()
    print("=" * 70)

    print(f"IfcColumn ID: {column.id()}")

    print(
        f"Dół osi:       "
        f"X={bottom_center[0]:.3f}, "
        f"Y={bottom_center[1]:.3f}, "
        f"Z={bottom_center[2]:.3f}"
    )

    print(
        f"Góra osi:      "
        f"X={top_center[0]:.3f}, "
        f"Y={top_center[1]:.3f}, "
        f"Z={top_center[2]:.3f}"
    )

    print(
        f"Oś @ Z=3m:     "
        f"X={point_3m[0]:.3f}, "
        f"Y={point_3m[1]:.3f}, "
        f"Z={point_3m[2]:.3f}"
    )

    print(
        f"Azymut:        "
        f"{azimuth:.3f}°"
    )

    print(
        f"Różnica:       "
        f"{difference:.3f}°"
    )


# ============================================================
# WYBÓR NOGI NAJBLIŻSZEJ 123°
# ============================================================

if columns:

    closest = min(
        columns,
        key=lambda c: c["difference"]
    )


    print()
    print()
    print("#" * 70)
    print("NOGA NAJBLIŻSZA AZYMUTOWI 123°")
    print("#" * 70)

    print(
        f"IfcColumn ID:   {closest['id']}"
    )

    print(
        f"Azymut:         "
        f"{closest['azimuth']:.3f}°"
    )

    print(
        f"Różnica:        "
        f"{closest['difference']:.3f}°"
    )

    print(
        f"Origin anteny:  "
        f"X={closest['point_3m'][0]:.3f}, "
        f"Y={closest['point_3m'][1]:.3f}, "
        f"Z={closest['point_3m'][2]:.3f}"
    )

    print("#" * 70)


# ============================================================
# WYKRES
# ============================================================

for c in columns:

    x, y, z = c["point_3m"]

    plt.scatter(
        x,
        y,
        s=100
    )

    plt.annotate(
        f"ID: {c['id']}\n"
        f"Az: {c['azimuth']:.1f}°",
        (x, y),
        xytext=(8, 8),
        textcoords="offset points"
    )


# Wybrana noga

x, y, z = closest["point_3m"]

plt.scatter(
    x,
    y,
    s=250,
    facecolors="none",
    edgecolors="red",
    linewidths=2
)

plt.annotate(
    f"NAJBLIŻSZA 123°\n"
    f"ID: {closest['id']}\n"
    f"Az: {closest['azimuth']:.2f}°",
    (x, y),
    xytext=(15, -40),
    textcoords="offset points"
)


# Środek konstrukcji

plt.scatter(
    CONSTRUCTION_X,
    CONSTRUCTION_Y,
    marker="x",
    s=100
)

plt.annotate(
    "Środek konstrukcji",
    (
        CONSTRUCTION_X,
        CONSTRUCTION_Y
    ),
    xytext=(8, -30),
    textcoords="offset points"
)


plt.xlabel("X")
plt.ylabel("Y")
plt.title("Oś nóg — punkt na wysokości Z=3m")

plt.axhline(0, linewidth=0.8)
plt.axvline(0, linewidth=0.8)

plt.grid(True)
plt.axis("equal")

plt.show()