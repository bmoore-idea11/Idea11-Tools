"""
Utils/portscan.py

Threaded TCP port scanner with:
 - safe limits on ports scanned
 - per-port timeout
 - basic service detection (system service name)
 - banner grabbing (best-effort)
 - CSV export of results
 - interactive wrapper using ColorUi / UiUtils
"""

import socket
import ipaddress
import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# UI imports (optional fallback if UIUtils missing)
try:
    from Utils.UIUtils import ColorUi, UiUtils
except Exception:
    # Minimal fallback implementations
    class ColorUi:
        RESET = "\033[0m"

        @classmethod
        def colorize(cls, text, color="White", bold=False, italic=False, underline=False):
            return text

        @classmethod
        def print_multi(cls, *segments, end="\n"):
            parts = []
            for seg in segments:
                if not seg:
                    continue
                parts.append(seg[0])
            print("".join(parts), end=end)

    class UiUtils:
        @staticmethod
        def clear_screen():
            os.system("cls" if os.name == "nt" else "clear")


# ----------------- Configuration -----------------
MAX_PORTS = 2000       # maximum number of ports allowed per scan
MAX_THREADS = 200      # max concurrent workers
DEFAULT_TIMEOUT = 1.5  # seconds per port timeout


# ----------------- Helper functions -----------------
def _is_valid_target(target: str):
    """
    Resolve and validate target. Returns a tuple (original_input, resolved_ip)
    or raises ValueError.
    """
    if not target:
        raise ValueError("Empty target provided.")
    # If target is an IP literal
    try:
        ip_obj = ipaddress.ip_address(target)
        return target, str(ip_obj)
    except Exception:
        # Try resolving hostname
        try:
            resolved = socket.gethostbyname(target)
            return target, resolved
        except Exception as e:
            raise ValueError(f"Could not resolve target '{target}': {e}")


def _scan_port(host_ip: str, port: int, timeout: float):
    """
    Attempt to connect to host_ip:port.
    Returns dict with results:
      { port, open (bool), service, banner, duration }
    """
    result = {"port": port, "open": False, "service": "", "banner": "", "duration": None}
    start = time.time()
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        err = s.connect_ex((host_ip, port))
        if err == 0:
            result["open"] = True
            # Try to map service name (best-effort)
            try:
                result["service"] = socket.getservbyport(port)
            except Exception:
                result["service"] = ""

            # Banner grabbing: best-effort small recv (and some probes for HTTP)
            try:
                # For common HTTP ports, send a simple GET to elicit a response
                if port in (80, 8080, 8000, 8008, 8888):
                    try:
                        s.sendall(b"HEAD / HTTP/1.0\r\nHost: \r\n\r\n")
                    except Exception:
                        pass
                # short read attempt
                s.settimeout(min(1.0, timeout))
                try:
                    banner = s.recv(1024)
                    if banner:
                        try:
                            result["banner"] = banner.decode(errors="replace").strip()
                        except Exception:
                            result["banner"] = repr(banner)
                except Exception:
                    # no banner or timed out
                    pass
            except Exception:
                pass
    except Exception:
        result["open"] = False
    finally:
        if s:
            try:
                s.close()
            except Exception:
                pass
        result["duration"] = round(time.time() - start, 3)
    return result


def run_portscan(host_ip: str, start_port: int, end_port: int,
                 timeout: float = DEFAULT_TIMEOUT, max_threads: int = MAX_THREADS,
                 progress_hook=None):
    """
    Run a threaded port scan against host_ip.
    Returns a list of result dicts sorted by port.
    progress_hook(done, total, last_result) will be called when each port completes.
    """
    start_port = int(start_port)
    end_port = int(end_port)
    if start_port < 1 or end_port > 65535 or start_port > end_port:
        raise ValueError("Invalid port range (1-65535).")

    total_ports = end_port - start_port + 1
    if total_ports > MAX_PORTS:
        raise ValueError(f"Port range too large ({total_ports} ports). Limit is {MAX_PORTS}.")

    ports = list(range(start_port, end_port + 1))
    workers = min(max_threads, len(ports)) if ports else 1

    results = []
    with ThreadPoolExecutor(max_workers=workers) as exe:
        future_to_port = {exe.submit(_scan_port, host_ip, p, timeout): p for p in ports}

        completed = 0
        for fut in as_completed(future_to_port):
            p = future_to_port[fut]
            try:
                res = fut.result()
            except Exception:
                res = {"port": p, "open": False, "service": "", "banner": "", "duration": None}
            results.append(res)
            completed += 1
            if progress_hook:
                try:
                    progress_hook(completed, len(ports), res)
                except Exception:
                    # ignore hooks that fail
                    pass

    results.sort(key=lambda r: r["port"])
    return results


def export_to_csv(results, target, out_dir=None):
    """Export port scan results to CSV inside ../portscan/ directory."""
    ts = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    safe_target = str(target).replace(":", "_").replace("/", "_")
    filename = f"portscan_{safe_target}_{ts}.csv"

    # Default export directory to ../portscan/
    base_dir = os.path.abspath(os.path.join(os.getcwd(), "portscan"))
    os.makedirs(base_dir, exist_ok=True)  # ensure the folder exists

    # Allow override if user provides custom output dir
    export_dir = out_dir or base_dir
    path = os.path.join(export_dir, filename)

    # Write to CSV
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["port", "open", "service", "banner", "duration"])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "port": r.get("port"),
                "open": r.get("open"),
                "service": r.get("service", ""),
                "banner": r.get("banner", ""),
                "duration": r.get("duration", "")
            })

    return path


# ----------------- Interactive wrapper -----------------
def run_portscan_interactive(cli_args=None):
    """
    Interactive or CLI-driven portscan runner.

    If cli_args provided (argparse Namespace), runs non-interactively.
    Otherwise presents interactive prompts using ColorUi.
    """
    try:
        if cli_args:
            target_input = cli_args.target
            start_port = int(cli_args.start)
            end_port = int(cli_args.end)
            timeout = float(getattr(cli_args, "timeout", DEFAULT_TIMEOUT))
        else:
           
            ColorUi.print_multi((f"{UiUtils.logo()} Portscan Utility", getattr(ColorUi, "NeonPurple", None), True))
            ColorUi.print_multi((f"{UiUtils.input()} Enter target IP or hostname:", getattr(ColorUi, "BrightYellow", None), True))
            target_input = input(ColorUi.colorize("Target: ", getattr(ColorUi, "BrightWhite", None), bold=True)).strip()

            ColorUi.print_multi((f"{UiUtils.logo()} Enter port range (start end), e.g. 1 1024", getattr(ColorUi, "BrightYellow", None)))
            pr = input(ColorUi.colorize("Ports: ", getattr(ColorUi, "BrightWhite", None), bold=True)).strip().split()
            if len(pr) == 0:
                raise ValueError(f"{UiUtils.error()} No ports provided.")
            if len(pr) == 1:
                start_port = int(pr[0])
                end_port = int(pr[0])
            else:
                start_port = int(pr[0])
                end_port = int(pr[1])

            ColorUi.print_multi((f"{UiUtils.logo()} Per-port timeout in seconds (default {DEFAULT_TIMEOUT}): ", getattr(ColorUi, "Grey", None)))
            t = input(ColorUi.colorize("Timeout: ", getattr(ColorUi, "BrightWhite", None), bold=True)).strip()
            timeout = float(t) if t else DEFAULT_TIMEOUT

        # Validate & resolve target
        target_host, target_ip = _is_valid_target(target_input)

        ColorUi.print_multi((f"{UiUtils.success()} Resolved {target_input} -> {target_ip}", getattr(ColorUi, "Grey", None)))
        ColorUi.print_multi((f"{UiUtils.working()} Scanning ports {start_port} to {end_port} (limit {MAX_PORTS})", getattr(ColorUi, "Grey", None)))

        started_at = time.time()
        last_progress_time = started_at

        def progress_hook(done, total, last_result):
            nonlocal last_progress_time
            now = time.time()
            # throttle updates to avoid spamming
            if (now - last_progress_time) > 0.6 or done == total:
                pct = int((done / total) * 100)
                ColorUi.print_multi((f"[{done}/{total}] {pct}% - last port: {last_result['port']} open={last_result['open']}", getattr(ColorUi, "Grey", None)))
                last_progress_time = now

        results = run_portscan(target_ip, start_port, end_port, timeout=timeout, max_threads=MAX_THREADS, progress_hook=progress_hook)

        open_ports = [r for r in results if r.get("open")]
        UiUtils.clear_screen()
        ColorUi.print_multi((f"{UiUtils.success()} Scan completed in {round(time.time() - started_at, 2)}s", getattr(ColorUi, "BrightGreen", None), True))

        if open_ports:
            ColorUi.print_multi((f"{UiUtils.logo()} Found {len(open_ports)} open port(s):", getattr(ColorUi, "BrightYellow", None), True))
            # header
            ColorUi.print_multi((f"{'PORT':>6}  {'SERVICE':<15}  {'DUR(s)':<7}  {'BANNER (truncated)':<60}", getattr(ColorUi, "NeonPurple", None), True))
            for r in open_ports:
                banner = (r.get("banner") or "")
                banner_trunc = (banner[:57] + "...") if banner and len(banner) > 60 else banner
                svc = r.get("service") or ""
                ColorUi.print_multi((f"{r['port']:>6}  {svc:<15}  {str(r.get('duration', '')):<7}  {banner_trunc:<60}", getattr(ColorUi, "BrightWhite", None)))
        else:
            ColorUi.print_multi((f"{UiUtils.error()} No open ports found.", getattr(ColorUi, "BrightGreen", None), True))

        ColorUi.print_multi((f"{UiUtils.working()} Exporting results to CSV...", getattr(ColorUi, "Grey", None)))
        csv_path = export_to_csv(results, target_input)
        ColorUi.print_multi((f"{UiUtils.success()} Saved CSV: {csv_path}", getattr(ColorUi, "BrightCyan", None), True))

        input(ColorUi.colorize("\nPress Enter to return to Network menu...", getattr(ColorUi, "BrightBlack", None)))
    except Exception as e:
        ColorUi.print_multi((f"{UiUtils.error()} Error during portscan: {e}", getattr(ColorUi, "BrightRed", None), True))
        input(ColorUi.colorize("\nPress Enter to return to Network menu...", getattr(ColorUi, "BrightBlack", None)))
