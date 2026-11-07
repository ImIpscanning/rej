"""REJ Desktop: native Tkinter GUI for safe JAR inspection and MCP setup.

The GUI is optional and uses only Python's standard Tkinter library.
Slow archive scans are dispatched off the Tk main thread.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import queue
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from . import __version__
from .archive import compare_jars, inspect_jar, inspect_class
from .integrations import claude_config, codex_config, claude_command, codex_command, connection_status

BG = "#0B1020"
PANEL = "#151B2E"
PANEL2 = "#1E2740"
TEXT = "#EDF1FF"
MUTED = "#9CA9C7"
ACCENT = "#8B5CF6"
ACCENT_HOVER = "#A78BFA"
GREEN = "#34D399"
BORDER = "#2C3550"


class REJDesktop(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"REJ Desktop {__version__} | Reverse Engineer Java")
        self.geometry("1190x760")
        self.minsize(890, 600)
        self.configure(bg=BG)
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="rej-scan")
        self._results: queue.Queue = queue.Queue()
        self._report: dict | None = None
        self._jar_path = tk.StringVar()
        self._compare_path = tk.StringVar()
        self._filter = tk.StringVar()
        self._status = tk.StringVar(value="Ready  •  Static analysis only")
        self._mode = tk.StringVar(value="Claude Code")
        self._setup_style()
        self._build()
        self.after(100, self._poll)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, font=("Segoe UI", 10, "bold"), padding=(18, 11), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", PANEL2)], foreground=[("selected", TEXT)])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, font=("Consolas", 10), rowheight=28, borderwidth=0)
        style.map("Treeview", background=[("selected", "#373471")], foreground=[("selected", "#FFFFFF")])
        style.configure("Treeview.Heading", background=PANEL2, foreground=TEXT, relief="flat", font=("Segoe UI", 10, "bold"))
        style.configure("TScrollbar", background=PANEL2, troughcolor=PANEL, arrowsize=12)

    def _label(self, parent: tk.Misc, text: str, size: int = 11, color: str = TEXT, bold: bool = False, **kwargs) -> tk.Label:
        return tk.Label(parent, text=text, font=("Segoe UI", size, "bold" if bold else "normal"), fg=color, bg=kwargs.pop("bg", PANEL), **kwargs)

    def _button(self, parent: tk.Misc, text: str, command, primary: bool = False) -> tk.Button:
        color = ACCENT if primary else PANEL2
        button = tk.Button(parent, text=text, command=command, relief="flat", bd=0,
                           bg=color, activebackground=ACCENT_HOVER if primary else BORDER,
                           fg="#FFFFFF", activeforeground="#FFFFFF", cursor="hand2",
                           padx=18, pady=10, font=("Segoe UI", 10, "bold"))
        return button

    def _build(self) -> None:
        header = tk.Frame(self, bg=BG, padx=28, pady=19)
        header.pack(fill="x")
        tk.Label(header, text="◆", bg=BG, fg=ACCENT, font=("Segoe UI", 29, "bold")).pack(side="left", padx=(0, 13))
        heading = tk.Frame(header, bg=BG)
        heading.pack(side="left")
        self._label(heading, "REJ  /  REVERSE ENGINEER JAVA", 20, TEXT, True, bg=BG).pack(anchor="w")
        self._label(heading, "Desktop Inspector   •   Read-only JAR analysis", 10, MUTED, bg=BG).pack(anchor="w", pady=(3, 0))
        self._label(header, f"v{__version__}    ●  LOCAL MODE", 10, GREEN, True, bg=BG).pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        self.scan_tab = tk.Frame(self.tabs, bg=PANEL, padx=18, pady=18)
        self.diff_tab = tk.Frame(self.tabs, bg=PANEL, padx=18, pady=18)
        self.ai_tab = tk.Frame(self.tabs, bg=PANEL, padx=22, pady=20)
        self.rea_tab = tk.Frame(self.tabs, bg=PANEL, padx=22, pady=20)
        self.tabs.add(self.scan_tab, text="  JAR Explorer  ")
        self.tabs.add(self.diff_tab, text="  Compare Builds  ")
        self.tabs.add(self.ai_tab, text="  MCP / AI Agents  ")
        self.tabs.add(self.rea_tab, text="  REA Companion  ")
        self._build_scan()
        self._build_diff()
        self._build_ai()
        self._build_rea()

        foot = tk.Frame(self, bg=BG, padx=26, pady=12)
        foot.pack(fill="x")
        self._label(foot, "●", 12, GREEN, True, bg=BG).pack(side="left")
        self._label(foot, "  ", 10, MUTED, bg=BG).pack(side="left")
        tk.Label(foot, textvariable=self._status, bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="left")
        self._label(foot, "REJ is not a malware scanner", 10, MUTED, bg=BG).pack(side="right")

    def _build_scan(self) -> None:
        self._label(self.scan_tab, "Inspect Java archives and Minecraft plugins", 15, TEXT, True).pack(anchor="w")
        self._label(self.scan_tab, "Open a local .jar, explore classes and export an evidence report.", 10, MUTED).pack(anchor="w", pady=(4, 15))
        toolbar = tk.Frame(self.scan_tab, bg=PANEL)
        toolbar.pack(fill="x", pady=(0, 16))
        entry = tk.Entry(toolbar, textvariable=self._jar_path, bg=PANEL2, fg=TEXT, insertbackground=TEXT,
                         relief="flat", font=("Consolas", 10), highlightthickness=1, highlightbackground=BORDER)
        entry.pack(side="left", fill="x", expand=True, ipady=12, padx=(0, 7))
        self._button(toolbar, "Browse JAR", self._browse).pack(side="left", padx=(0, 7))
        self._button(toolbar, "Analyze", self._scan, True).pack(side="left", padx=(0, 7))
        self._button(toolbar, "Export JSON", self._export).pack(side="left")
        center = tk.PanedWindow(self.scan_tab, orient="horizontal", bg=BORDER, sashwidth=6, bd=0)
        center.pack(fill="both", expand=True)
        left = tk.Frame(center, bg=PANEL)
        center.add(left, minsize=340, width=540)
        right = tk.Frame(center, bg=PANEL)
        center.add(right, minsize=290)
        self._label(left, "CLASSES", 10, MUTED, True).pack(anchor="w", pady=(0, 6))
        filter_entry = tk.Entry(left, textvariable=self._filter, bg=PANEL2, fg=TEXT, insertbackground=TEXT,
                                relief="flat", font=("Segoe UI", 10), highlightbackground=BORDER, highlightthickness=1)
        filter_entry.pack(fill="x", ipady=9, pady=(0, 10), padx=(0, 12))
        self._filter.trace_add("write", lambda *_: self._populate())
        cols = ("java", "methods")
        self.tree = ttk.Treeview(left, columns=cols, show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Class / Package")
        self.tree.heading("java", text="Java")
        self.tree.heading("methods", text="Methods")
        self.tree.column("#0", width=300, minwidth=180, stretch=True)
        self.tree.column("java", width=70, minwidth=65, anchor="center", stretch=False)
        self.tree.column("methods", width=72, minwidth=65, anchor="center", stretch=False)
        tree_scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y", padx=(0, 12))
        self.tree.pack(fill="both", expand=True, padx=(0, 0))
        self.tree.bind("<<TreeviewSelect>>", self._selected_class)
        self._label(right, "INSPECTION DETAILS", 10, MUTED, True).pack(anchor="w", padx=(14, 0), pady=(0, 8))
        self.details = tk.Text(right, bg=PANEL2, fg=TEXT, relief="flat", bd=0, wrap="word",
                               padx=18, pady=16, font=("Consolas", 10), spacing2=3)
        self.details.pack(fill="both", expand=True, padx=(12, 0))
        self._show_text(self.details, "Open a JAR to begin.\n\nSelect a class to see:\n  • class version\n  • superclass and interfaces\n  • fields and methods\n  • JVM descriptors")

    def _build_diff(self) -> None:
        self._label(self.diff_tab, "Compare two plugin releases", 15, TEXT, True).pack(anchor="w")
        self._label(self.diff_tab, "Identify added, removed or byte-changed Java classes.", 10, MUTED).pack(anchor="w", pady=(4, 20))
        self._label(self.diff_tab, "OLD JAR", 10, MUTED, True).pack(anchor="w")
        old = tk.Frame(self.diff_tab, bg=PANEL)
        old.pack(fill="x", pady=(5, 18))
        tk.Entry(old, textvariable=self._jar_path, relief="flat", bg=PANEL2, fg=TEXT, insertbackground=TEXT,
                 font=("Consolas", 10)).pack(side="left", fill="x", expand=True, ipady=12)
        self._button(old, "Choose", self._browse).pack(side="left", padx=(8, 0))
        self._label(self.diff_tab, "NEW JAR", 10, MUTED, True).pack(anchor="w")
        new = tk.Frame(self.diff_tab, bg=PANEL)
        new.pack(fill="x", pady=(5, 18))
        tk.Entry(new, textvariable=self._compare_path, relief="flat", bg=PANEL2, fg=TEXT, insertbackground=TEXT,
                 font=("Consolas", 10)).pack(side="left", fill="x", expand=True, ipady=12)
        self._button(new, "Choose", lambda: self._browse(self._compare_path)).pack(side="left", padx=(8, 0))
        self._button(self.diff_tab, "Compare JARs", self._diff, True).pack(anchor="w", pady=(0, 18))
        self.diff_output = tk.Text(self.diff_tab, relief="flat", bg=PANEL2, fg=TEXT,
                                   padx=18, pady=15, wrap="word", font=("Consolas", 10))
        self.diff_output.pack(fill="both", expand=True)
        self._show_text(self.diff_output, "Select two JARs, then click Compare JARs.")

    def _build_ai(self) -> None:
        self._label(self.ai_tab, "Connect REJ to Claude Code and Codex", 15, TEXT, True).pack(anchor="w")
        self._label(self.ai_tab, "Four read-only MCP tools. Local stdio transport. No tokens or cloud services required by REJ.", 10, MUTED).pack(anchor="w", pady=(4, 20))
        selector = tk.Frame(self.ai_tab, bg=PANEL)
        selector.pack(fill="x")
        for mode in ("Claude Code", "Codex"):
            tk.Radiobutton(selector, text=mode, value=mode, variable=self._mode,
                           command=self._refresh_config, bg=PANEL, fg=TEXT,
                           selectcolor=PANEL2, activebackground=PANEL, activeforeground=TEXT,
                           font=("Segoe UI", 11, "bold"), cursor="hand2").pack(side="left", padx=(0, 26))
        self._label(self.ai_tab, "CONFIGURATION", 10, MUTED, True).pack(anchor="w", pady=(20, 8))
        self.config_output = tk.Text(self.ai_tab, bg=PANEL2, fg="#D9CBFF", relief="flat",
                                      padx=20, pady=15, font=("Consolas", 11), wrap="word", height=12)
        self.config_output.pack(fill="x")
        bar = tk.Frame(self.ai_tab, bg=PANEL)
        bar.pack(fill="x", pady=14)
        self._button(bar, "Copy Config", self._copy_config, True).pack(side="left", padx=(0, 9))
        self._button(bar, "Copy Install Command", self._copy_command).pack(side="left")
        self._label(self.ai_tab, "Install: Python 3.11+, download REJ, then register the shown local MCP command in your client. Restart the client and verify /mcp.",
                    10, MUTED, wraplength=900, justify="left").pack(anchor="w", pady=(6, 12))
        self._label(self.ai_tab, "Tools: rej_inspect_jar  •  rej_list_classes  •  rej_inspect_class  •  rej_compare_jars", 10, GREEN).pack(anchor="w")
        self._refresh_config()

    def _build_rea(self) -> None:
        self._label(self.rea_tab, "REA Companion", 15, TEXT, True).pack(anchor="w")
        self._label(self.rea_tab, "REJ and Reverse Engineer Anything are separate projects. They can be installed on the same PC.", 11, MUTED,
                    wraplength=850, justify="left").pack(anchor="w", pady=(6, 20))
        box = tk.Frame(self.rea_tab, bg=PANEL2, padx=20, pady=20)
        box.pack(fill="x")
        self._label(box, "LOCAL TOOL DETECTION", 11, TEXT, True, bg=PANEL2).pack(anchor="w")
        self.rea_status = tk.StringVar()
        tk.Label(box, textvariable=self.rea_status, bg=PANEL2, fg=GREEN, justify="left",
                 font=("Consolas", 11)).pack(anchor="w", pady=(12, 16))
        buttons = tk.Frame(box, bg=PANEL2)
        buttons.pack(anchor="w")
        self._button(buttons, "Refresh", self._refresh_rea, True).pack(side="left", padx=(0, 12))
        self._button(buttons, "Open REA Documentation", lambda: webbrowser.open("https://github.com/morluto/rea")).pack(side="left")
        self._label(self.rea_tab, "CURRENT LIMITATION", 10, MUTED, True).pack(anchor="w", pady=(26, 8))
        self._label(self.rea_tab, "REA does not currently offer a Java JAR decompiler through REJ. This panel only checks availability and links to its documentation; no inter-process analysis bridge is claimed.",
                    11, MUTED, wraplength=860, justify="left").pack(anchor="w")
        self._refresh_rea()

    def _browse(self, variable: tk.StringVar | None = None) -> None:
        selected = filedialog.askopenfilename(title="Choose Java JAR", filetypes=[("Java archives", "*.jar"), ("All files", "*.*")])
        if selected:
            (variable or self._jar_path).set(selected)

    def _run_async(self, fn, on_success) -> None:
        self._status.set("Working  •  Analyzing local archive...")
        def completed(future):
            try:
                self._results.put((on_success, future.result(), None))
            except Exception as exc:
                self._results.put((on_success, None, exc))
        self._executor.submit(fn).add_done_callback(completed)

    def _poll(self) -> None:
        while True:
            try:
                callback, value, exc = self._results.get_nowait()
            except queue.Empty:
                break
            if exc:
                self._status.set("Error  •  See details")
                messagebox.showerror("REJ analysis error", str(exc))
            else:
                callback(value)
                self._status.set("Ready  •  Analysis complete")
        self.after(100, self._poll)

    def _scan(self) -> None:
        path = self._jar_path.get().strip()
        if not path:
            messagebox.showwarning("Choose a JAR", "Please select a .jar archive first.")
            return
        self._run_async(lambda: inspect_jar(path), self._loaded)

    def _loaded(self, report: dict) -> None:
        self._report = report
        summary = report["summary"]
        metadata = report.get("metadata", {})
        info = ["REJ INSPECTION", "=" * 40, f"File: {Path(report['file']).name}",
                f"SHA-256: {report['sha256']}", f"Classes: {summary['class_count']}",
                f"Resources: {summary['resource_count']}", f"Parsing warnings: {summary['error_count']}",
                f"Java versions: {', '.join(summary['java_versions']) or 'Unknown'}",
                f"Plugin platform: {metadata.get('platform', 'Not detected')}", "", "PLUGIN METADATA", "-" * 40,
                json.dumps(metadata.get("plugin", {}), indent=2, ensure_ascii=False)]
        self._show_text(self.details, "\n".join(info))
        self._populate()

    def _populate(self) -> None:
        if not hasattr(self, "tree"):
            return
        for key in self.tree.get_children():
            self.tree.delete(key)
        if not self._report:
            return
        query = self._filter.get().casefold()
        for item in self._report["classes"]:
            if query not in item["name"].casefold():
                continue
            self.tree.insert("", "end", iid=item["path"], text=item["name"],
                             values=(item["java_version"].replace("Java ", ""), item["method_count"]))

    def _selected_class(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection or not self._report:
            return
        name = self.tree.item(selection[0], "text")
        path = self._report["file"]
        def show(data):
            output = [f"CLASS {data['name']}", "=" * 42,
                      f"Java: {data['java_version']}", f"Superclass: {data['superclass']}",
                      f"Interfaces: {', '.join(data['interfaces']) or '-'}", "", "FIELDS", "-" * 40]
            output.extend(f"{' '.join(f['flags'])} {f['name']} : {f['descriptor']}" for f in data["fields"])
            output += ["", "METHODS", "-" * 40]
            output.extend(f"{' '.join(m['flags'])} {m['name']}{m['descriptor']}" for m in data["methods"])
            self._show_text(self.details, "\n".join(output))
        self._run_async(lambda: inspect_class(path, name), show)

    def _diff(self) -> None:
        first, second = self._jar_path.get().strip(), self._compare_path.get().strip()
        if not first or not second:
            messagebox.showwarning("Choose two JARs", "Select an old JAR and a new JAR.")
            return
        self._run_async(lambda: compare_jars(first, second), self._diff_loaded)

    def _diff_loaded(self, report: dict) -> None:
        output = ["JAR VERSION COMPARISON", "=" * 48, f"Old: {Path(report['old']).name}",
                  f"New: {Path(report['new']).name}", ""]
        for field in ("added", "removed", "modified"):
            output += [f"{field.upper()} ({len(report[field])})", "-" * 48]
            output += [f"  {name}" for name in report[field][:300]]
            if len(report[field]) > 300:
                output += [f"  ... {len(report[field]) - 300} more"]
            output += [""]
        output += [f"Unchanged classes: {report['unchanged_count']}"]
        self._show_text(self.diff_output, "\n".join(output))

    def _export(self) -> None:
        if not self._report:
            messagebox.showinfo("No report", "Analyze a JAR first.")
            return
        destination = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], title="Export REJ report")
        if destination:
            Path(destination).write_text(json.dumps(self._report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            self._status.set(f"Saved JSON report: {destination}")

    def _show_text(self, widget: tk.Text, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def _refresh_config(self) -> None:
        content = claude_config() if self._mode.get() == "Claude Code" else codex_config()
        self._show_text(self.config_output, content)

    def _copy(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self._status.set("Copied to clipboard")

    def _copy_config(self) -> None:
        self._copy(claude_config() if self._mode.get() == "Claude Code" else codex_config())

    def _copy_command(self) -> None:
        self._copy(claude_command() if self._mode.get() == "Claude Code" else codex_command())

    def _refresh_rea(self) -> None:
        statuses = connection_status()
        lines = [f"{'FOUND' if found else 'NOT DETECTED':<14}  {tool}" for tool, found in statuses.items()]
        self.rea_status.set("\n".join(lines))

    def _on_close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()


def main() -> None:
    try:
        app = REJDesktop()
    except tk.TclError as exc:
        raise SystemExit(f"Unable to start REJ Desktop. A graphical display with Tkinter is required: {exc}") from exc
    app.mainloop()


if __name__ == "__main__":
    main()
