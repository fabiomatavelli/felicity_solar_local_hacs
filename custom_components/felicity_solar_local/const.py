"""Constants for the Felicity Solar Local integration."""

DOMAIN = "felicity_solar_local"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_PERSISTENT_CONNECTION = "persistent_connection"

DEFAULT_PORT = 53970
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_PERSISTENT_CONNECTION = False

# Floor when reconnecting every poll (today's default behavior) - keeps connection churn
# against the battery's embedded TCP stack reasonable.
MIN_UPDATE_INTERVAL = 10
# Floor when the connection is kept open across polls - skipping the reconnect overhead
# makes much faster polling safe.
MIN_UPDATE_INTERVAL_PERSISTENT = 5

DEFAULT_TIMEOUT = 5.0
# Best-effort timeout for flushing stray trailing bytes before reusing an open connection.
STRAY_BYTES_FLUSH_TIMEOUT = 0.05

QUERY_COMMAND = b"wifilocalMonitor:get dev real infor"
ACK_BYTE = b"."
