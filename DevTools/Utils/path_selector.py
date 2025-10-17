import os
import sys
import glob

# ------------------------------------------------------------
#  Cross-platform readline import
# ------------------------------------------------------------
try:
    import readline  # macOS/Linux
except ImportError:
    try:
        import pyreadline3 as readline  # Windows
    except ImportError:
        readline = None


# ------------------------------------------------------------
#  Import color utilities (fallback if unavailable)
# ------------------------------------------------------------
try:
    from Utils.UIUtils import ColorUi
except ImportError:
    class ColorUi:
        RESET = "\033[0m"
        BOLD = "\033[1m"
        ITALIC = "\033[3m"
        UNDERLINE = "\033[4m"
        BLINK = "\033[5m"
        REVERSE = "\033[7m"
        STRIKETHROUGH = "\033[9m"

        COLORS = {
            # Standard colors
            "Black": "\033[30m",
            "Red": "\033[31m",
            "Green": "\033[32m",
            "Yellow": "\033[33m",
            "Blue": "\033[34m",
            "Magenta": "\033[35m",
            "Cyan": "\033[36m",
            "White": "\033[37m",

            # Bright colors
            "BrightBlack": "\033[90m",
            "BrightRed": "\033[91m",
            "BrightGreen": "\033[92m",
            "BrightYellow": "\033[93m",
            "BrightBlue": "\033[94m",
            "BrightMagenta": "\033[95m",
            "BrightCyan": "\033[96m",
            "BrightWhite": "\033[97m",

            # Extended / custom colors
            "DeepPurple": "\033[38;5;55m",
            "Violet": "\033[38;5;177m",
            "Lavender": "\033[38;5;183m",
            "NeonPurple": "\033[38;5;201m",
            "Teal": "\033[38;5;37m",
            "Orange": "\033[38;5;208m",
            "Coral": "\033[38;5;203m",
            "SkyBlue": "\033[38;5;117m",
            "Mint": "\033[38;5;121m",
            "Rose": "\033[38;5;211m",
            "Amber": "\033[38;5;214m",
            "Grey": "\033[38;5;240m",
            "Lime": "\033[38;5;154m",
            "Crimson": "\033[38;5;197m",
            "Gold": "\033[38;5;220m",
            "SeaGreen": "\033[38;5;84m",
        }

        # Add attributes for direct access (ColorUi.Red etc.)
        for _name, _code in COLORS.items():
            locals()[_name] = _code

        @classmethod
        def colorize(
            cls, text, color=None, *, bold=False, italic=False, underline=False,
            blink=False, reverse=False, strikethrough=False
        ):
            """Return ANSI-colored text."""
            styles = []
            if bold: styles.append(cls.BOLD)
            if italic: styles.append(cls.ITALIC)
            if underline: styles.append(cls.UNDERLINE)
            if blink: styles.append(cls.BLINK)
            if reverse: styles.append(cls.REVERSE)
            if strikethrough: styles.append(cls.STRIKETHROUGH)

            color_code = cls.COLORS.get(color, color or "")
            return f"{''.join(styles)}{color_code}{text}{cls.RESET}"

        @classmethod
        def print_multi(cls, *segments, end="\n"):
            """Print multiple colored text segments with proper resets."""
            output = []
            for seg in segments:
                if not seg:
                    continue
                text = seg[0]
                color = seg[1] if len(seg) > 1 else None
                bold = seg[2] if len(seg) > 2 else False
                italic = seg[3] if len(seg) > 3 else False
                underline = seg[4] if len(seg) > 4 else False
                blink = seg[5] if len(seg) > 5 else False
                reverse = seg[6] if len(seg) > 6 else False
                strikethrough = seg[7] if len(seg) > 7 else False
                output.append(cls.colorize(
                    text, color,
                    bold=bold, italic=italic, underline=underline,
                    blink=blink, reverse=reverse, strikethrough=strikethrough
                ))
                # Always reset between colors
                output.append(cls.RESET)
            print("".join(output), end=end)


# ------------------------------------------------------------
#  Internal helpers
# ------------------------------------------------------------
def _clear_screen():
    os.system("cls" if sys.platform.startswith("win") else "clear")


def _list_matches(matches):
    """Print directory matches in tidy columns."""
    if not matches:
        return
    cols = 4
    width = max(len(os.path.basename(m)) + 1 for m in matches)
    print()
    for i, m in enumerate(matches):
        end = "\n" if (i + 1) % cols == 0 else ""
        print(os.path.basename(m).ljust(width), end=end)
    if len(matches) % cols != 0:
        print()
    print()


def _completer_factory(verbose: bool):
    """Return a readline completer that supports nested path navigation."""
    def complete_path(text, state):
        expanded = os.path.expanduser(text)
        matches = glob.glob(expanded + "*")
        matches = [m + os.sep if os.path.isdir(m) else m for m in matches]

        if not verbose and state == 0:
            _clear_screen()
            sys.stdout.write(ColorUi.colorize("Path >> ", ColorUi.NeonPurple, bold=True))
            sys.stdout.write(text)
            sys.stdout.flush()

        try:
            return matches[state]
        except IndexError:
            return None
    return complete_path


def _enable_tab(verbose: bool):
    """Enable cross-platform Tab completion."""
    if readline is None:
        return None, None

    doc = getattr(readline, "__doc__", "") or ""
    if "libedit" in doc:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    readline.set_completer_delims(" \t\n")
    prev = getattr(readline, "get_completer", lambda: None)()
    readline.set_completer(_completer_factory(verbose))
    return readline, prev


def _disable_tab(rl, prev):
    if rl:
        rl.set_completer(prev)


# ------------------------------------------------------------
#  Prompt text
# ------------------------------------------------------------
prompt_text = (
    ColorUi.colorize("Pathfinder", ColorUi.NeonPurple, bold=True)
    + ColorUi.colorize(" >", ColorUi.BrightWhite, bold=True)
    + ColorUi.colorize(" Enter Path ", ColorUi.BrightYellow, bold=True)
    + ColorUi.colorize("| ", ColorUi.Grey)
    + ColorUi.colorize("Tab", ColorUi.BrightCyan, bold=True)
    + ColorUi.colorize(" to List Directory ", ColorUi.Grey)
    + ColorUi.colorize("| ", ColorUi.Grey)
    + ColorUi.colorize("Type & Tab", ColorUi.BrightGreen, bold=True)
    + ColorUi.colorize(" to Autocomplete:", ColorUi.Grey)
)


# ------------------------------------------------------------
#  Main selector
# ------------------------------------------------------------
def select_path(verbose=False) -> str:
    """
    Interactive standalone path selector with colorized prompt.

    Features:
    - Inline autocompletion
    - Clears screen on each Tab unless verbose mode is active
    - Displays match list in verbose mode
    """
    rl, prev = _enable_tab(verbose)

    if readline and verbose:
        def display_matches(substitution, matches, longest_match_length):
            _list_matches(matches)
            sys.stdout.write(ColorUi.colorize("Path >> ", ColorUi.NeonPurple, bold=True))
            sys.stdout.write(substitution)
            sys.stdout.flush()
        readline.set_completion_display_matches_hook(display_matches)

    try:
        ColorUi.print_multi(
            ("Pathfinder", ColorUi.NeonPurple, True),
            (" >", ColorUi.BrightWhite, True),
            (" Enter Path ", ColorUi.BrightYellow, True),
            ("| ", ColorUi.Grey),
            ("Tab", ColorUi.BrightCyan, True),
            (" to List Directory ", ColorUi.Grey),
            ("| ", ColorUi.Grey),
            ("Type & Tab", ColorUi.BrightGreen, True),
            (" to Autocomplete:", ColorUi.Grey),
            ("\n", None)
        )

        prefix = ColorUi.colorize("Path >> ", ColorUi.Violet, bold=True)
        user_input = input(prefix).strip()
    finally:
        _disable_tab(rl, prev)
        if readline:
            readline.set_completion_display_matches_hook(None)

    path = os.path.abspath(os.path.expanduser(user_input))

    if not verbose:
        _clear_screen()

    return path


# ------------------------------------------------------------
#  Standalone execution test
# ------------------------------------------------------------
if __name__ == "__main__":
    selected = select_path(verbose=True)
    print(ColorUi.colorize(f"\nSelected Path: {selected}", ColorUi.BrightGreen, bold=True))
