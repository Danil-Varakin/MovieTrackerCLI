class MovieTrackerError(Exception):
    """Base application error with a CLI exit code."""

    exit_code = 1

    def __init__(self, message: str, *, exit_code: int | None = None) -> None:
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class AuthorizationError(MovieTrackerError):
    exit_code = 1


class NotFoundError(MovieTrackerError):
    exit_code = 2


class NetworkError(MovieTrackerError):
    exit_code = 3


class InvalidRatingError(MovieTrackerError):
    exit_code = 4


class DuplicateWatchlistError(MovieTrackerError):
    exit_code = 5


class WatchlistCorruptedError(MovieTrackerError):
    exit_code = 6


class UnsupportedFeatureError(MovieTrackerError):
    exit_code = 7
