#!/usr/bin/env python3
import sys
import time
import argparse
import os
from Utils import portscan
from Utils.UIUtils import UiUtils, ColorUi
from Utils.path_selector import select_path
from Utils.orc_to_yaml import convert_orc_to_yaml
from Utils.master_converter import run_master_converter_interactive


# Keep readline import if you need it in other modules
try:
    import readline
except Exception:
    readline = None


APP_NAME = "DataTools CLI"
APP_VERSION = f"{UiUtils.productionVersion} (Dev {UiUtils.developmentVersion})"
COMMAND_TYPE = "Com"

# ---------- Data handlers ----------
def handle_orc_to_yaml(input_path=None, output_path=None, verbose=False):
    COMMAND_TYPE = "Data"
    UiUtils.clear_screen()
    ColorUi.print_multi(
        (f"<PerlsDeveloperTools.{COMMAND_TYPE}>", ColorUi.Red, True),
        (" -> ", ColorUi.White, True),
        ("ORC → YAML Converter\n", ColorUi.BrightCyan, True, False, True),
    )

    # Ask for ORC input if not given
    if not input_path:
        ColorUi.print_multi(("Enter path to ORC file (Tab to autocomplete): ", ColorUi.BrightYellow, True))
        input_path = select_path(verbose=verbose)

    if not output_path:
        ColorUi.print_multi(("Enter optional output path (or leave blank): ", ColorUi.BrightYellow, True))
        out = input(ColorUi.colorize("Output Path (leave blank to auto): ", ColorUi.BrightWhite, bold=True)).strip()
        output_path = out or None
        if not verbose:
            UiUtils.clear_screen()

    try:
        result_path = convert_orc_to_yaml(input_path, output_path)
        ColorUi.print_multi((f"\n✅ Conversion complete: {result_path}", ColorUi.BrightGreen, True))
    except Exception as e:
        ColorUi.print_multi((f"\n❌ Error: {e}", ColorUi.BrightRed, True))

    input(ColorUi.colorize("\nPress Enter to return to Data menu...", ColorUi.BrightBlack))


# ---------- Menus ----------

def interactive_app():
    UiUtils.clear_screen()
    UiUtils.PrntBanner()
    while True:
        UiUtils.clear_screen()
        UiUtils.PrntBanner()
        UiUtils.MenuFactory(
          
            title="Main Menu",
        )
        choice = input(ColorUi.colorize("\nChoice: ", ColorUi.BrightWhite, bold=True)).strip()
        if choice == "1":
            _selectionData = UiUtils.menu_data()
            if _selectionData == 1:
                handle_orc_to_yaml()
            if _selectionData == 2:
                run_master_converter_interactive()
        elif choice == "2":
            _selection = UiUtils.menu_network()
            if _selection == 1:
                portscan.run_portscan_interactive()
        elif choice == "3":
            UiUtils.clear_screen()
            ColorUi.print_multi(("👋 Goodbye!", ColorUi.BrightGreen, True))
            sys.exit(0)       
        else:
            ColorUi.print_multi(("❌ Invalid choice", ColorUi.BrightRed))
            time.sleep(1)


# ---------- CLI Parser ----------
def build_parser():
    parser = argparse.ArgumentParser(
        prog="datatools",
        description="🧰 Multi-tool CLI for data conversions and network utilities.",
        add_help=True
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode.")
    subparsers = parser.add_subparsers(dest="command")

    # orc-to-yaml (CLI support)
    orc_parser = subparsers.add_parser("orc-to-yaml", help="Convert an ORC file to YAML format.")
    orc_parser.add_argument("input", nargs="?", help="Path to the input ORC file.")
    orc_parser.add_argument("-o", "--output", help="Optional path for the output YAML file.")
    orc_parser.set_defaults(func=lambda args: handle_orc_to_yaml(args.input, args.output, args.verbose))

    # portscan CLI short support
    ps_parser = subparsers.add_parser("portscan", help="Quick portscan from CLI.")
    ps_parser.add_argument("target", help="IP or hostname to scan.")
    ps_parser.add_argument("--start", type=int, default=1, help="Start port (default 1).")
    ps_parser.add_argument("--end", type=int, default=1024, help="End port (default 1024).")
    ps_parser.add_argument("--timeout", type=float, default=1.5, help="Per-port timeout in seconds.")
    ps_parser.set_defaults(func=lambda args: portscan.run_portscan_interactive(cli_args=args))

    return parser


def main():
    parser = build_parser()
    # If no args -> interactive
    if len(sys.argv) == 1:
        interactive_app()
        return

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
