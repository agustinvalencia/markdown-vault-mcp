# pyright: reportUnusedFunction=false
import os
import shutil
import subprocess

from fastmcp import FastMCP

from ..config import VAULT_PATH


def register_macro_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def run_macro(
        name: str,
        args: list[str] | None = None,
        variables: dict[str, str] | None = None,
    ) -> str:
        """Run a predefined macro using the mdv CLI.

        Args:
            name: The name of the macro to run (e.g., 'daily-standup', 'new-project')
            args: Optional list of positional arguments to pass to the macro
            variables: Optional dictionary of variables to pass to the macro (--var k=v)

        Returns:
            Output of the macro execution or error message.
        """
        mdv_path = shutil.which("mdv")
        if not mdv_path:
            return "Error: 'mdv' executable not found in PATH. Please install mdvault CLI."

        command = [mdv_path, "macro", name, "--batch"]
        if variables:
            for k, v in variables.items():
                command.extend(["--var", f"{k}={v}"])
        if args:
            command.extend(args)

        try:
            # Ensure the vault path is passed to the CLI
            env = os.environ.copy()
            if "MARKDOWN_VAULT_PATH" not in env:
                env["MARKDOWN_VAULT_PATH"] = str(VAULT_PATH)

            result = subprocess.run(
                command, capture_output=True, text=True, env=env, check=False
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                return f"Macro '{name}' executed successfully.\n\n{output}"
            else:
                return f"Error executing macro '{name}':\n{result.stderr}\n{result.stdout}"

        except Exception as e:
            return f"Failed to run macro: {e}"
