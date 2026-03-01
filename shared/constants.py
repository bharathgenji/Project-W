from __future__ import annotations

TRADE_KEYWORDS: dict[str, list[str]] = {
    "ELECTRICAL": [
        "electrical", "wiring", "circuit", "panel", "conduit", "voltage", "transformer",
        "switchgear", "outlet", "lighting", "generator",
    ],
    "PLUMBING": [
        "plumbing", "pipe", "water heater", "sewer", "drain", "fixture", "backflow",
        "sprinkler", "irrigation", "faucet", "toilet",
    ],
    "HVAC": [
        "hvac", "heating", "cooling", "air conditioning", "duct", "furnace",
        "refrigeration", "ventilation", "boiler", "heat pump", "thermostat",
    ],
    "ROOFING": [
        "roof", "shingle", "gutter", "flashing", "membrane", "skylight",
    ],
    "CONCRETE": [
        "concrete", "foundation", "slab", "masonry", "block", "paving", "cement",
        "footings", "retaining wall",
    ],
    "FRAMING": [
        "framing", "structural", "carpentry", "lumber", "timber", "truss", "joist",
    ],
    "DRYWALL": [
        "drywall", "plaster", "insulation", "acoustical", "stucco",
    ],
    "PAINTING": [
        "painting", "coating", "wallpaper", "finishing", "staining",
    ],
    "FLOORING": [
        "flooring", "tile", "carpet", "hardwood", "vinyl", "laminate", "terrazzo",
    ],
    "GENERAL": [
        "general", "remodel", "renovation", "addition", "new construction",
        "tenant improvement", "alteration", "build-out",
    ],
    "DEMOLITION": [
        "demolition", "abatement", "removal", "teardown",
    ],
    "FIRE_PROTECTION": [
        "fire", "sprinkler system", "alarm system", "suppression", "fire protection",
    ],
}

CONSTRUCTION_NAICS: list[str] = [
    "236220",  # Commercial/Institutional Building Construction
    "238110",  # Poured Concrete
    "238120",  # Structural Steel/Precast Concrete
    "238130",  # Framing
    "238140",  # Masonry
    "238150",  # Glass/Glazing
    "238160",  # Roofing
    "238210",  # Electrical Contractors
    "238220",  # Plumbing, Heating, AC
    "238290",  # Other Building Equipment
    "238310",  # Drywall/Insulation
    "238320",  # Painting/Wall Covering
    "238330",  # Flooring
    "238340",  # Tile/Terrazzo
    "238350",  # Finish Carpentry
    "238390",  # Other Finishing
    "238910",  # Site Preparation
    "238990",  # All Other Specialty Trade
]

NAICS_TO_TRADE: dict[str, str] = {
    "236220": "GENERAL",
    "238110": "CONCRETE",
    "238120": "FRAMING",
    "238130": "FRAMING",
    "238140": "CONCRETE",
    "238150": "GENERAL",
    "238160": "ROOFING",
    "238210": "ELECTRICAL",
    "238220": "HVAC",
    "238290": "GENERAL",
    "238310": "DRYWALL",
    "238320": "PAINTING",
    "238330": "FLOORING",
    "238340": "FLOORING",
    "238350": "FRAMING",
    "238390": "GENERAL",
    "238910": "GENERAL",
    "238990": "GENERAL",
}

PERMIT_TYPE_ALIASES: dict[str, str] = {
    "building": "BUILDING",
    "electrical": "ELECTRICAL",
    "plumbing": "PLUMBING",
    "mechanical": "MECHANICAL",
    "demolition": "DEMOLITION",
    "hvac": "MECHANICAL",
    "fire": "MECHANICAL",
    "sign": "OTHER",
    "grading": "OTHER",
    "fence": "OTHER",
}

SET_ASIDE_TYPES: list[str] = [
    "SMALL_BUSINESS",
    "8A",
    "HUBZONE",
    "WOSB",
    "SDVOSB",
    "NONE",
]
