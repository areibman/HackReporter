# server.py
from fastmcp import FastMCP
import os

mcp = FastMCP(name="HackReporter")


@mcp.tool
def hello(name: str) -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run()
