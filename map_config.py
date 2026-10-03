from __future__ import annotations


def poi_specification():
    """
    Five high-value places of interest.
    Positioned so roads and flight corridors remain visible.
    """
    return [
        {
            "name": "hospital",
            "xy": (-55, 48),
            "size": (22, 18, 12),
            "colour": (0.90, 0.25, 0.25, 1.0),
            "poi": True,
        },
        {
            "name": "defence_base",
            "xy": (55, 48),
            "size": (24, 20, 10),
            "colour": (0.25, 0.55, 0.25, 1.0),
            "poi": True,
        },
        {
            "name": "power_plant",
            "xy": (55, -28),
            "size": (22, 18, 16),
            "colour": (0.90, 0.65, 0.15, 1.0),
            "poi": True,
        },
        {
            "name": "communication_centre",
            "xy": (-55, -28),
            "size": (14, 14, 25),
            "colour": (0.25, 0.45, 0.90, 1.0),
            "poi": True,
        },
        {
            "name": "tourist_site",
            "xy": (0, 58),
            "size": (18, 18, 9),
            "colour": (0.65, 0.30, 0.75, 1.0),
            "poi": True,
        },
    ]


def building_specification():
    """
    Normal buildings.
    Designed to create:
    - some broad open avenues
    - a few tighter corridors
    - mixed urban structure
    """
    return [
        # southern cluster
        {"name": "building_01", "xy": (-36, -52), "size": (16, 18, 16), "colour": (0.45, 0.45, 0.48, 1), "poi": False},
        {"name": "building_02", "xy": (-10, -50), "size": (14, 20, 20), "colour": (0.50, 0.50, 0.52, 1), "poi": False},
        {"name": "building_03", "xy": (18, -50), "size": (16, 18, 14), "colour": (0.42, 0.42, 0.45, 1), "poi": False},
        {"name": "building_04", "xy": (42, -50), "size": (14, 18, 18), "colour": (0.46, 0.46, 0.49, 1), "poi": False},

        # middle-lower cluster
        {"name": "building_05", "xy": (-28, -12), "size": (18, 14, 18), "colour": (0.48, 0.48, 0.50, 1), "poi": False},
        {"name": "building_06", "xy": (2, -14), "size": (16, 14, 14), "colour": (0.43, 0.43, 0.46, 1), "poi": False},
        {"name": "building_07", "xy": (30, -8), "size": (16, 14, 24), "colour": (0.40, 0.40, 0.44, 1), "poi": False},

        # middle-upper cluster
        {"name": "building_08", "xy": (-30, 18), "size": (18, 16, 15), "colour": (0.50, 0.50, 0.53, 1), "poi": False},
        {"name": "building_09", "xy": (0, 14), "size": (16, 14, 20), "colour": (0.47, 0.47, 0.49, 1), "poi": False},
        {"name": "building_10", "xy": (30, 16), "size": (16, 16, 20), "colour": (0.44, 0.44, 0.47, 1), "poi": False},

        # side fillers
        {"name": "building_11", "xy": (-72, 8), "size": (10, 28, 18), "colour": (0.41, 0.41, 0.45, 1), "poi": False},
        {"name": "building_12", "xy": (72, 6), "size": (10, 28, 18), "colour": (0.41, 0.41, 0.45, 1), "poi": False},
    ]


def road_specification():
    """
    Roads are visual-only surfaces.
    These make the city easier to read and create clearer structure.
    """
    return [
        {"name": "road_ns_main", "xy": (0, 0), "size": (16, 150, 0.05), "colour": (0.18, 0.18, 0.18, 1.0)},
        {"name": "road_ns_west", "xy": (-45, 0), "size": (12, 145, 0.05), "colour": (0.20, 0.20, 0.20, 1.0)},
        {"name": "road_ns_east", "xy": (45, 0), "size": (12, 145, 0.05), "colour": (0.20, 0.20, 0.20, 1.0)},
        {"name": "road_ew_south", "xy": (0, -45), "size": (145, 14, 0.05), "colour": (0.19, 0.19, 0.19, 1.0)},
        {"name": "road_ew_mid", "xy": (0, 0), "size": (150, 14, 0.05), "colour": (0.18, 0.18, 0.18, 1.0)},
        {"name": "road_ew_north", "xy": (0, 38), "size": (145, 12, 0.05), "colour": (0.20, 0.20, 0.20, 1.0)},
    ]