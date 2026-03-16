"""Constants for the METAR integration."""

DOMAIN = "hametar"

CONF_STATION_ID = "station_id"
DEFAULT_SCAN_INTERVAL = 5  # minutes
MIN_SCAN_INTERVAL = 1       # minutes
MAX_SCAN_INTERVAL = 10080   # minutes (1 week)

# Aviation Weather Center API
AWC_METAR_URL = "https://aviationweather.gov/api/data/metar"

ATTRIBUTION = "Data provided by the Aviation Weather Center (aviationweather.gov)"

# Platform list
PLATFORMS = ["sensor"]

# Flight category values (used for state validation)
FLIGHT_CATEGORIES = ["VFR", "MVFR", "IFR", "LIFR"]

# Cloud cover codes that indicate a ceiling
CEILING_LAYERS = {"BKN", "OVC", "VV"}
