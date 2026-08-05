import importlib
import os

from app.dal.case_dal import CaseDAL

_dal_instance: CaseDAL | None = None

_DEFAULT_DAL = "app.dal.in_memory_case_dal.InMemoryCaseDAL"


def _import_dal_class(dotted_path: str) -> type[CaseDAL]:
    """Import a CaseDAL subclass from a fully-qualified dotted path."""
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError:
        raise ValueError(
            f"DAL_IMPLEMENTATION must be a dotted path (e.g. 'app.dal.in_memory_case_dal.InMemoryCaseDAL'), "
            f"got: '{dotted_path}'"
        )
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ValueError(
            f"Could not import DAL module '{module_path}': {e}"
        ) from e
    try:
        dal_class = getattr(module, class_name)
    except AttributeError:
        raise ValueError(
            f"Module '{module_path}' has no class '{class_name}'"
        )
    if not (isinstance(dal_class, type) and issubclass(dal_class, CaseDAL)):
        raise ValueError(
            f"'{dotted_path}' is not a CaseDAL subclass"
        )
    return dal_class


def get_dal() -> CaseDAL:
    """Return the singleton CaseDAL instance, importing it based on DAL_IMPLEMENTATION env var."""
    global _dal_instance
    if _dal_instance is None:
        dal_path = os.environ.get("DAL_IMPLEMENTATION", _DEFAULT_DAL)
        dal_class = _import_dal_class(dal_path)
        _dal_instance = dal_class()
    return _dal_instance


def _reset_dal() -> None:
    """Reset the cached DAL instance. Intended for testing only."""
    global _dal_instance
    _dal_instance = None
