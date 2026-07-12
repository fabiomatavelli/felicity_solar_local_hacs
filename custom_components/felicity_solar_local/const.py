"""Constants for the Felicity Solar Local integration."""

DOMAIN = "felicity_solar_local"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_PERSISTENT_CONNECTION = "persistent_connection"

DEFAULT_PORT = 53970
DEFAULT_UPDATE_INTERVAL = 5
DEFAULT_PERSISTENT_CONNECTION = True

# Floor when reconnecting every poll (persistent connection disabled) - keeps connection
# churn against the battery's embedded TCP stack reasonable.
MIN_UPDATE_INTERVAL = 10
# Floor when the connection is kept open across polls - skipping the reconnect overhead
# makes much faster polling safe.
MIN_UPDATE_INTERVAL_PERSISTENT = 5

DEFAULT_TIMEOUT = 5.0
# Best-effort timeout for flushing stray trailing bytes before reusing an open connection.
STRAY_BYTES_FLUSH_TIMEOUT = 0.05

# OS-level TCP keepalive tuning applied to persistent connections only (see api.py's
# _enable_keepalive). One-shot mode reconnects every poll, so there's no idle socket to
# probe. Not every platform supports every knob - these are best-effort tightening, not
# hard requirements.
TCP_KEEPALIVE_IDLE = 10  # seconds idle before the first probe
TCP_KEEPALIVE_INTERVAL = 5  # seconds between probes
TCP_KEEPALIVE_COUNT = 3  # probes before the OS considers the connection dead

QUERY_COMMAND = b"wifilocalMonitor:get dev real infor"
ACK_BYTE = b"."
