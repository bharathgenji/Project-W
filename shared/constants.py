from __future__ import annotations

TRADE_KEYWORDS: dict[str, list[str]] = {
    "ELECTRICAL": [
        "electrical", "electric", "wiring", "rewire", "circuit", "panel", "conduit",
        "voltage", "transformer", "switchgear", "outlet", "lighting", "generator",
        "solar", "photovoltaic", "pv system", "ev charger", "ev charging",
        "meter", "service upgrade", "low voltage", "data cabling", "telecom",
        "fire alarm", "security system", "camera", "cctv",
    ],
    "PLUMBING": [
        "plumbing", "plumb", "pipe", "piping", "water heater", "sewer", "drain",
        "drainage", "fixture", "backflow", "irrigation", "faucet", "toilet",
        "water line", "gas line", "water main", "sanitary", "storm drain",
        "grease trap", "interceptor", "water service", "hydrant",
    ],
    "HVAC": [
        "hvac", "heating", "cooling", "air conditioning", "air conditioner", "ac unit",
        "duct", "ductwork", "furnace", "refrigeration", "ventilation", "boiler",
        "heat pump", "thermostat", "exhaust", "mechanical", "air handler",
        "mini split", "chiller", "cooling tower", "vrf system",
    ],
    "ROOFING": [
        "roof", "roofing", "re-roof", "reroof", "shingle", "gutter", "flashing",
        "membrane", "skylight", "flat roof", "pitched roof", "tile roof",
        "metal roof", "tpo", "epdm", "built-up roof", "fascia", "soffit",
    ],
    "CONCRETE": [
        "concrete", "foundation", "slab", "masonry", "block", "paving", "cement",
        "footings", "retaining wall", "sidewalk", "curb", "driveway", "flatwork",
        "rebar", "post-tension", "tilt-up", "precast", "stone",
    ],
    "FRAMING": [
        "framing", "structural", "carpentry", "lumber", "timber", "truss", "joist",
        "beam", "column", "shear wall", "wood frame", "metal stud", "light gauge",
        "deck", "balcony", "staircase", "stair",
    ],
    "DRYWALL": [
        "drywall", "gypsum", "plaster", "insulation", "acoustical", "stucco",
        "lath", "interior finish", "t-bar", "drop ceiling", "suspended ceiling",
    ],
    "PAINTING": [
        "painting", "paint", "coating", "wallpaper", "wall covering", "staining",
        "epoxy coating", "waterproofing", "sealant", "caulking",
    ],
    "FLOORING": [
        "flooring", "floor", "tile", "carpet", "hardwood", "vinyl", "laminate",
        "terrazzo", "epoxy floor", "polished concrete", "wood floor", "LVP", "LVT",
    ],
    "GENERAL": [
        "general contractor", "remodel", "renovation", "addition", "new construction",
        "tenant improvement", "alteration", "build-out", "buildout", "fit-out",
        "commercial build", "residential build", "erect", "construct",
        "self cert", "cbc", "ibc", "adc",
    ],
    "DEMOLITION": [
        "demolition", "demo", "abatement", "asbestos", "removal", "teardown",
        "deconstruction", "strip out",
    ],
    "FIRE_PROTECTION": [
        "fire sprinkler", "sprinkler system", "fire alarm", "fire suppression",
        "fire protection", "fire pump", "standpipe", "ansul", "hood suppression",
    ],
    "SOLAR": [
        "solar panel", "solar array", "photovoltaic", "pv install", "solar install",
        "solar system", "solar roof",
    ],
    "WINDOWS_DOORS": [
        "window", "door", "storefront", "curtain wall", "glazing", "fenestration",
        "skylight", "garage door", "overhead door",
    ],
    "SITE_WORK": [
        "grading", "excavation", "site work", "landscaping", "paving", "parking lot",
        "underground utility", "utility trench", "erosion control",
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
