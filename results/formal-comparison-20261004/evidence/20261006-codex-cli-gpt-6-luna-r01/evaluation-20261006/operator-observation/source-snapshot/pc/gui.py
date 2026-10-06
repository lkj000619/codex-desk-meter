"""Tk desktop fixture meter with explicit USB sender setup and manual refresh."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .pipeline import FixtureCollector, parse_time, utc_now
from .sender import send_payload


AUTO_REFRESH_MS = 60_000


class MeterGui:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Codex Desk Meter — offline fixture")
        self.root.geometry("980x620")
        self.collector = FixtureCollector()
        self.port = tk.StringVar(value="")
        self.alias = tk.StringVar(value="waveshare-meter-1")
        self.initialize = tk.BooleanVar(value=False)
        self.auto_send = tk.BooleanVar(value=False)
        self.state = tk.StringVar(value="Ready. Fixture mode; no provider account is contacted.")
        self.tabs = ttk.Notebook(root)
        self.dashboard = ttk.Frame(self.tabs)
        self.global_page = ttk.Frame(self.tabs)
        self.status_page = ttk.Frame(self.tabs)
        self.tabs.add(self.dashboard, text="Dashboard")
        self.tabs.add(self.global_page, text="Global reset")
        self.tabs.add(self.status_page, text="Status / errors")
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.usage_view = self._tree(self.dashboard, ("provider", "window", "used", "remaining", "unit", "observed", "reset"))
        self.global_view = self._tree(self.global_page, ("source", "latest", "elapsed", "captured", "forecast"))
        self.error_view = self._tree(self.status_page, ("adapter", "state", "error", "last_good"))
        controls = ttk.Frame(root)
        controls.pack(fill="x", padx=10)
        ttk.Label(controls, text="COM port").pack(side="left")
        ttk.Entry(controls, textvariable=self.port, width=10).pack(side="left", padx=(4, 12))
        ttk.Label(controls, text="Device alias").pack(side="left")
        ttk.Entry(controls, textvariable=self.alias, width=24).pack(side="left", padx=(4, 12))
        ttk.Checkbutton(controls, text="Initialize only after confirming receiver is empty", variable=self.initialize).pack(side="left", padx=4)
        ttk.Checkbutton(controls, text="Send each automatic refresh", variable=self.auto_send).pack(side="left", padx=4)
        ttk.Button(controls, text="Refresh fixtures", command=self.refresh).pack(side="right", padx=4)
        ttk.Button(controls, text="Refresh and send", command=lambda: self.refresh(send=True)).pack(side="right", padx=4)
        ttk.Label(root, textvariable=self.state, anchor="w").pack(fill="x", padx=14, pady=(8, 10))
        self.refresh()
        self.root.after(AUTO_REFRESH_MS, self._automatic_refresh)

    def _tree(self, parent: ttk.Frame, columns: tuple[str, ...]) -> ttk.Treeview:
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        for column in columns:
            tree.heading(column, text=column.replace("_", " ").title())
            tree.column(column, width=120, minwidth=75, stretch=True)
        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    @staticmethod
    def _elapsed(value: str | None) -> str:
        if not value:
            return "unknown"
        seconds = max(0, int((utc_now() - parse_time(value, "timestamp")).total_seconds()))
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m ago"

    def refresh(self, send: bool = False) -> None:
        result = self.collector.collect()
        for tree in (self.usage_view, self.global_view, self.error_view):
            tree.delete(*tree.get_children())
        for snapshot in result.usage:
            if snapshot["windows"]:
                for window in snapshot["windows"]:
                    observed = snapshot["observed_at"] or "unknown"
                    self.usage_view.insert("", "end", values=(
                        snapshot["provider_id"], window["label"], window["percent_used"],
                        window["percent_remaining"], window["unit"], observed, window["resets_at"] or "unknown"))
            else:
                self.usage_view.insert("", "end", values=(snapshot["provider_id"], "—", "—", "—", snapshot["unit"], snapshot["observed_at"] or "unknown", "—"))
        for reset in result.global_resets:
            if reset["source"] != "codex-resets.com":
                continue
            latest = reset["latest_reset_at"] or "No reset history"
            self.global_view.insert("", "end", values=(reset["source"], latest,
                self._elapsed(reset["latest_reset_at"]), reset["captured_at"],
                "Forecast is not a schedule"))
        if not self.global_view.get_children():
            self.global_view.insert("", "end", values=("codex-resets.com", "Default — no history", "unknown", "unknown", "—"))
        for snapshot in result.usage:
            self.error_view.insert("", "end", values=(snapshot["provider_id"], snapshot["status"], snapshot["error_code"] or "—", snapshot["last_good_at"] or "unknown"))
        for failure in result.failures:
            self.error_view.insert("", "end", values=(failure["adapter_id"], "error", failure["code"], "preserved if available"))
        errors = len(result.failures)
        self.state.set(f"Fixture refresh complete: {len(result.usage)} snapshots, {len(result.global_resets)} reset sources, {errors} adapter errors. Source times are preserved.")
        if send:
            self._send(result.payload)
        elif self.auto_send.get():
            self._send(result.payload, quiet=True)

    def _send(self, payload: dict, quiet: bool = False) -> None:
        try:
            receipt = send_payload(payload, self.port.get(), self.alias.get(), initialize_empty_receiver=self.initialize.get())
            self.initialize.set(False)
            self.state.set(f"Frame {receipt['sequence']} written ({receipt['bytes']} bytes). Host receipt is not a device ACK.")
        except Exception as exc:
            self.state.set(f"Send stopped: {exc}")
            if not quiet:
                messagebox.showerror("USB send failed", str(exc))

    def _automatic_refresh(self) -> None:
        self.refresh()
        self.root.after(AUTO_REFRESH_MS, self._automatic_refresh)


def main() -> None:
    root = tk.Tk()
    MeterGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
