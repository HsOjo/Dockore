class DockerError(Exception):
    """Daemon-level failure (unreachable host, daemon down). Maps to 502."""


class DockerApiError(DockerError):
    """Request-level failure (bad args, conflict, invalid state). Maps to 400."""


class DockerNotFound(DockerApiError):
    """The requested container/image/network/volume does not exist. Maps to 404."""
