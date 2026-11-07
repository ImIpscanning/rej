# REJ CLI quick reference

Use `py -3 -m rej` from the repository directory on Windows, or run `rej` after `pip install .`.

```powershell
rej inspect C:\plugins\Example.jar --json inspection.json
rej classes C:\plugins\Example.jar --filter com.example --limit 200
rej class C:\plugins\Example.jar com.example.Main
rej methods C:\plugins\Example.jar onEnable --offset 0 --limit 100
rej bytecode C:\plugins\Example.jar com.example.Main onEnable --limit 100
rej diff C:\plugins\old.jar C:\plugins\new.jar --json diff.json
rej rea-status
rej gui
rej mcp
```

When JVM methods are overloaded, use `--descriptor` with `rej bytecode` to choose exactly one method. For large methods, use `--offset` returned by the previous page to retrieve more instructions. JVM bytecode output shows **opcodes**, not original Java source.

`rej-mcp` runs the same stdio server as `rej mcp`. `rej-gui` launches the GUI when installed via Python package.
