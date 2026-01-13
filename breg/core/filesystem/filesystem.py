from pathlib import Path
from typing import IO, Any


class Filesystem:
    _base_path: Path

    def __init__(self, base_path: Path = Path.cwd()):
        self._base_path = base_path.resolve()

    def set_base(self, base_path: Path) -> None:
        """Set the base path for the filesystem.

        Args:
            base_path (Path): The new base path.
        """
        self._base_path = base_path.resolve()

    def base(self) -> Path:
        """Get the current base path of the filesystem.

        Returns:
            Path: The current base path.
        """
        return self._base_path

    def path(self, *subpaths: str) -> Path:
        """Get the absolute path by joining the base path with the provided subpaths.
        If the first subpath is absolute, it returns that path resolved.

        Args:
            *subpaths (str): Subpaths to join with the base path.

        Returns:
            Path: The absolute path.
        """
        sub_paths = Path(*subpaths)
        if sub_paths.is_absolute():
            return sub_paths.resolve()
        return self._base_path.joinpath(*subpaths).resolve()

    def open(
        self,
        *subpaths: str,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        """Open a file located at the path formed by joining the base path with the provided subpaths.
        If the first subpath is absolute, it opens that path.

        Args:
            *subpaths (str): Subpaths to join with the base path.
            mode (str, optional): The mode in which to open the file. Defaults to "r".
            **kwargs: Additional keyword arguments to pass to the open function.

        Returns:
            IO[Any]: The file object.
        """
        file_path = self.path(*subpaths)
        return file_path.open(
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )
