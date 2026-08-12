import re
from datetime import datetime
from typing import Optional

# Docker resource names (containers, networks, volumes, images without tag)
# Must start with alphanumeric, then allow alphanumeric, underscore, dot, hyphen.
_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")

# Docker image references may include registry, name, tag, digest.
# Just reject anything starting with '-' to prevent option injection.
_IMAGE_REF_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.\-/:@]*$")

# Docker CLI relative time: 10s, 10m, 1h, 1h30m, etc.
_RELATIVE_TIME_RE = re.compile(r"^(\d+[smh])+$")


def validate_docker_name(value: str, field: str = "name") -> str:
    if not value or not _NAME_RE.match(value):
        raise ValueError(f"invalid {field}: {value!r}")
    return value


def validate_image_ref(value: str, field: str = "image") -> str:
    if not value or not _IMAGE_REF_RE.match(value):
        raise ValueError(f"invalid {field}: {value!r}")
    return value


def validate_no_dash(value: str, field: str = "argument") -> str:
    """Reject values that start with '-' to prevent CLI option injection."""
    if not value:
        raise ValueError(f"empty {field}")
    if value.startswith("-"):
        raise ValueError(f"{field} cannot start with '-': {value!r}")
    return value


def parse_time_param(value: str | None) -> str | None:
    """Parse a time parameter accepted by the Docker CLI and return it in a
    canonical form. Supports RFC-3339 / ISO-8601 timestamps and Docker relative
    times such as 10s, 10m, 1h30m. Returns None when the input is invalid."""
    if not value:
        return None
    if _RELATIVE_TIME_RE.match(value):
        return value
    try:
        return datetime.fromisoformat(value).isoformat()
    except ValueError:
        return None


def validate_since_until(since: Optional[str], until: Optional[str]) -> tuple[str | None, str | None]:
    return parse_time_param(since), parse_time_param(until)
