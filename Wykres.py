
import matplotlib.pyplot as plt


# ============================================================
# DANE
# ============================================================

legs = [
    {
        "name": "Noga 1",
        "x": -1.325,
        "y": -0.765,
        "azimuth": 240.0
    },
    {
        "name": "Noga 2",
        "x": 1.325,
        "y": -0.765,
        "azimuth": 120.0
    },
    {
        "name": "Noga 3",
        "x": 0.000,
        "y": 1.530,
        "azimuth": 0.0
    }
]

# Centroid przekroju na Z = 3 m
centroid_x = 1.325000
centroid_y = -0.764989


# ============================================================
# WYKRES
# ============================================================

fig, ax = plt.subplots(figsize=(8, 8))


# ============================================================
# NOGI
# ============================================================

for leg in legs:

    ax.scatter(
        leg["x"],
        leg["y"],
        s=120
    )

    ax.annotate(
        f'{leg["name"]}\n'
        f'azymut = {leg["azimuth"]:.0f}°\n'
        f'({leg["x"]:.3f}, {leg["y"]:.3f})',
        xy=(leg["x"], leg["y"]),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=10
    )


# ============================================================
# CENTROID
# ============================================================

ax.scatter(
    centroid_x,
    centroid_y,
    marker="*",
    s=300,
    label="Centroid przekroju Z = 3 m"
)

ax.annotate(
    f'Centroid\n'
    f'({centroid_x:.6f}, {centroid_y:.6f})',
    xy=(centroid_x, centroid_y),
    xytext=(15, -30),
    textcoords="offset points",
    fontsize=10
)


# ============================================================
# ŚRODEK KONSTRUKCJI
# ============================================================

ax.scatter(
    0,
    0,
    marker="x",
    s=120,
    linewidths=2,
    label="Środek konstrukcji"
)


# ============================================================
# LINIE OD ŚRODKA DO NÓG
# ============================================================

for leg in legs:

    ax.plot(
        [0, leg["x"]],
        [0, leg["y"]],
        linewidth=1
    )


# ============================================================
# FORMAT
# ============================================================

ax.set_xlabel("X [m]")
ax.set_ylabel("Y [m]")

ax.set_title(
    "Położenie nóg konstrukcji i centroidu przekroju"
)

ax.set_aspect("equal", adjustable="box")

ax.grid(True)

ax.legend()

plt.tight_layout()

plt.show()

