# REJ example

`HelloPlugin-demo.jar` is an **original, non-deployable demonstration fixture** for testing REJ. It includes a small compiled Java 21 class and a `plugin.yml` metadata example, but it is **not** a real Paper/Bukkit plugin and should not be installed on a Minecraft server.

Run from the project root:

```bat
py -3 -m rej inspect examples\HelloPlugin-demo.jar
py -3 -m rej class examples\HelloPlugin-demo.jar org.example.HelloPlugin
```

`HelloPlugin.java` is the original source for the demonstration class.
