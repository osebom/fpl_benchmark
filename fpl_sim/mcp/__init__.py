__all__ = ["bind_context", "mcp"]


def __getattr__(name: str):
    if name in {"bind_context", "mcp"}:
        from fpl_sim.mcp import server

        return getattr(server, name)
    raise AttributeError(name)
