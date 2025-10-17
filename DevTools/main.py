#!/usr/bin/env python3
import sys
import time
import argparse
import os
import glob

from Utils.UIUtils import UiUtils, ColorUi
from Utils.path_selector import select_path
from orc_to_yaml import convert_orc_to_yaml

try:
    import readline
except ImportError:
    import pyreadline as readline


# ---------- Application Metadata ----------

APP_NAME = "DataTools CLI"
APP_VERSION = f"{UiUtils.productionVersion} (Dev {UiUtils.developmentVersion})"


# ---------- Command Handlers ----------

def handle_orc_to_yaml(input_path=None, output_path=None, verbose=False):
    COMMAND_TYPE = "Data"
    UiUtils.clear_screen()

    # Pretty header using multi-color print
    ColorUi.print_multi(
        (f"<PerlsDeveloperTools.{COMMAND_TYPE}>", ColorUi.Red, True),
        (" → ", ColorUi.White, True),
        ("ORC → YAML Converter", ColorUi.BrightCyan, True, False, True),
        ("\n", None)
    )

    # Prompt for input path
    print(ColorUi.colorize("Enter path to ORC file (Tab to autocomplete): ", ColorUi.BrightYellow, bold=True))
    if not input_path:
        input_path = select_path(verbose=verbose)

    if not output_path:
        output_prompt = ColorUi.colorize("Enter optional output path (or leave blank): ", ColorUi.BrightYellow, bold=True)
        output_path = input(output_prompt).strip() or None
        if not verbose:
            UiUtils.clear_screen()

    try:
        result_path = convert_orc_to_yaml(input_path, output_path)
        print(ColorUi.colorize(f"\n✅ Conversion complete: {result_path}", ColorUi.BrightGreen, bold=True))
    except Exception as e:
        print(ColorUi.colorize(f"\n❌ Error: {e}", ColorUi.BrightRed, bold=True))

    input(ColorUi.colorize("\nPress Enter to return to main menu...", ColorUi.BrightBlack))


# ---------- CLI Parser Setup ----------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="datatools",
        description="🧰 Multi-tool CLI for data conversions and transformations.",
        add_help=True,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode.")
    subparsers = parser.add_subparsers(dest="command")

    # orc-to-yaml
    orc_parser = subparsers.add_parser("orc-to-yaml", help="Convert an ORC file to YAML format.")
    orc_parser.add_argument("input", nargs="?", help="Path to the input ORC file.")
    orc_parser.add_argument("-o", "--output", help="Optional path for the output YAML file.")
    orc_parser.set_defaults(func=lambda args: handle_orc_to_yaml(args.input, args.output, args.verbose))

    return parser


# ---------- Interactive App ----------

def interactive_app():
    UiUtils.PrntBanner()
    time.sleep(1.2)

    while True:
        UiUtils.clear_screen()
        UiUtils.PrntBanner()
        UiUtils.MainMenu()

        # Multi-color prompt
        prompt = (
            ColorUi.colorize("\n<PDT>", ColorUi.Red, bold=True)
            + ColorUi.colorize(" >> ", ColorUi.BrightWhite, bold=True)
        )

        choice = input(prompt).strip()

        if choice == "1":
            handle_orc_to_yaml()
        elif choice == "2":
            UiUtils.clear_screen()
            ColorUi.print_multi(
                ("🚧 ", ColorUi.BrightMagenta, True),
                ("CSV → JSON module coming soon.", ColorUi.BrightMagenta, True),
            )
            input(ColorUi.colorize("\nPress Enter to return to main menu...", ColorUi.BrightBlack))
        elif choice == "3":
            UiUtils.clear_screen()
            ColorUi.print_multi(("👋 Goodbye!", ColorUi.BrightGreen, True))
            time.sleep(0.5)
            sys.exit(0)
        else:
            ColorUi.print_multi(("❌ Invalid choice, please try again.", ColorUi.BrightRed, True))
            time.sleep(1)


# ---------- Main Entry ----------

def main():
    parser = build_parser()

    # If no arguments, launch interactive mode
    if len(sys.argv) == 1:
        interactive_app()
        return

    # Otherwise, handle CLI mode
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
