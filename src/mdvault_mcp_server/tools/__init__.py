__all__ = [
    "register_context_tools",
    "register_daily_tools",
    "register_list_tools",
    "register_macro_tools",
    "register_management_tools",
    "register_read_tools",
    "register_search_tools",
    "register_tasks_projects_tools",
    "register_update_tools",
    "register_zettelkasten_tools",
]

_IMPORTS = {
    "register_context_tools": ".context",
    "register_daily_tools": ".daily",
    "register_list_tools": ".list",
    "register_macro_tools": ".macros",
    "register_management_tools": ".management",
    "register_read_tools": ".read",
    "register_search_tools": ".search",
    "register_tasks_projects_tools": ".tasks_projects",
    "register_update_tools": ".update",
    "register_zettelkasten_tools": ".zettelkasten",
}


def __getattr__(name: str):
    if name in _IMPORTS:
        import importlib

        module = importlib.import_module(_IMPORTS[name], __package__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
