# Define all app-wide constants here

# Status constants
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_PENDING = "pending"
STATUS_DELETED = "deleted"

# Role constants
ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_GUEST = "guest"

# API path prefixes
API_PREFIX = "/api"
API_V1_PREFIX = f"{API_PREFIX}/v1"

# Cache TTL values (in seconds)
CACHE_TTL_SHORT = 60 * 5  # 5 minutes
CACHE_TTL_MEDIUM = 60 * 30  # 30 minutes
CACHE_TTL_LONG = 60 * 60 * 24  # 1 day

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
