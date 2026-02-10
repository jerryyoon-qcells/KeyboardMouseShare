"""
Constants used throughout the Keyboard Mouse Share application.
"""

# Network settings
DEFAULT_PORT = 19999
DEFAULT_DISCOVERY_TIMEOUT = 60  # seconds
DEFAULT_CONNECTION_TIMEOUT = 30  # seconds
MDNS_SERVICE_TYPE = "_kms._tcp.local."

# Passphrase settings
DEFAULT_PASSPHRASE_LENGTH = 6
MAX_PASSPHRASE_ATTEMPTS = 3
PASSPHRASE_LOCKOUT_DURATION = 300  # 5 minutes in seconds
PASSPHRASE_HASH_ALGORITHM = "sha256"

# Layout and geometry
MIN_DEVICES = 1
MAX_DEVICES = 16  # Practical limit for MVP
DEFAULT_MOUSE_POLLING_RATE = 60  # Hz
CURSOR_EDGE_THRESHOLD = 5  # pixels
CURSOR_TRANSITION_COOLDOWN = 0.1  # seconds

# Performance targets
TARGET_KEYBOARD_LATENCY = 100  # milliseconds (p95)
TARGET_MOUSE_LATENCY = 50  # milliseconds (p95, challenging)
MIN_EVENT_SUCCESS_RATE = 0.95  # 95%

# Logging
DEFAULT_LOG_FORMAT = "json"
DEFAULT_LOG_LEVEL = "INFO"
AUDIT_LOG_RETENTION_DAYS = 7

# Application metadata
APP_NAME = "Keyboard Mouse Share"
APP_VERSION = "1.0.0-dev"
MIN_PYTHON_VERSION = "3.11"

# Supported platforms
SUPPORTED_PLATFORMS = ["Windows", "Darwin"]  # Windows and macOS
WINDOWS_MIN_VERSION = 10
MACOS_MIN_VERSION = "10.15"  # Catalina

# Size/memory constraints
MAX_MEMORY_FOOTPRINT = 100 * 1024 * 1024  # 100 MB
MAX_CPU_USAGE = 5.0  # percent under normal operation

# Feature version compatibility
SUPPORTED_FEATURES = {
    "1.0.0": [
        "INPUT_SHARING",
        "KEYBOARD_ROUTING",
        "PASSPHRASE_AUTH",
    ],
}

# Error codes
ERROR_CODES = {
    "DISCOVERY_TIMEOUT": 1001,
    "CONNECTION_FAILED": 1002,
    "AUTH_FAILED": 1003,
    "INVALID_PASSPHRASE": 1004,
    "DUPLICATE_DEVICE": 1005,
    "ROLE_CONFLICT": 1006,
    "UNSUPPORTED_FEATURE": 1007,
}
