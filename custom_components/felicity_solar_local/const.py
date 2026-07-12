"""Constants for the Felicity Solar Local integration."""

DOMAIN = "felicity_solar_local"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_PORT = 53970
DEFAULT_UPDATE_INTERVAL = 30
MIN_UPDATE_INTERVAL = 10

DEFAULT_TIMEOUT = 5.0

QUERY_COMMAND = b"wifilocalMonitor:get dev real infor"
ACK_BYTE = b"."
