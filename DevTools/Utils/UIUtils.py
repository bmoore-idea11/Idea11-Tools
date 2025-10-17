import os
import platform
import time


class ColorUi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"
    STRIKETHROUGH = "\033[9m"

    COLORS = {
         "Black": "\033[30m",
        "Red": "\033[31m",
        "Green": "\033[32m",
        "Yellow": "\033[33m",
        "Blue": "\033[34m",
        "Magenta": "\033[35m",
        "Cyan": "\033[36m",
        "White": "\033[37m",
        # Bright
        "BrightBlack": "\033[90m",
        "BrightRed": "\033[91m",
        "BrightGreen": "\033[92m",
        "BrightYellow": "\033[93m",
        "BrightBlue": "\033[94m",
        "BrightMagenta": "\033[95m",
        "BrightCyan": "\033[96m",
        "BrightWhite": "\033[97m",
        # Extended 256-color accents
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
        "Peach": "\033[38;5;217m",
        "Aqua": "\033[38;5;51m",
        "Steel": "\033[38;5;67m",
        "Tan": "\033[38;5;180m",
        "Chocolate": "\033[38;5;130m",
        "Indigo": "\033[38;5;75m",
        "HotPink": "\033[38;5;205m",
    }

    @classmethod
    def colorize(cls, text, color=None, **styles):
        style_codes = []
        if styles.get("bold"): style_codes.append(cls.BOLD)
        if styles.get("italic"): style_codes.append(cls.ITALIC)
        if styles.get("underline"): style_codes.append(cls.UNDERLINE)
        if styles.get("dim"): style_codes.append(cls.DIM)
        if styles.get("blink"): style_codes.append(cls.BLINK)
        if styles.get("reverse"): style_codes.append(cls.REVERSE)
        if styles.get("hidden"): style_codes.append(cls.HIDDEN)
        if styles.get("strikethrough"): style_codes.append(cls.STRIKETHROUGH)

        color_code = cls.COLORS.get(color, color or "")
        return f"{''.join(style_codes)}{color_code}{text}{cls.RESET}"

    @classmethod
    def print_multi(cls, *segments, end="\n"):
        out = []
        for s in segments:
            if not s: continue
            text, color = s[0], s[1] if len(s) > 1 else None
            style_flags = {
                "bold": len(s) > 2 and s[2],
                "italic": len(s) > 3 and s[3],
                "underline": len(s) > 4 and s[4],
                "dim": len(s) > 5 and s[5],
                "blink": len(s) > 6 and s[6],
                "reverse": len(s) > 7 and s[7],
                "hidden": len(s) > 8 and s[8],
                "strikethrough": len(s) > 9 and s[9],
            }
            out.append(cls.colorize(text, color, **style_flags))
        print("".join(out), end=end)

# --- the crucial part ---
for _name, _code in ColorUi.COLORS.items():
    setattr(ColorUi, _name, _code)

class UiUtils:
    productionVersion = 1.0
    developmentVersion = 1.1

    @staticmethod
    def logo():
        a = ColorUi.colorize("<", ColorUi.DeepPurple, bold=True)
        b = ColorUi.colorize("PerlsDeveloperTools", ColorUi.Violet, bold=True)
        c = ColorUi.colorize(">", ColorUi.DeepPurple, bold=True)
        return f"{a}{b}{c}"
    
    @staticmethod
    def error():
        a = ColorUi.colorize("<", ColorUi.DeepPurple, bold=True)
        b = ColorUi.colorize("ERROR", ColorUi.Red, bold=True)
        c = ColorUi.colorize(">", ColorUi.DeepPurple, bold=True)
        return f"{a}{b}{c}"
    
    @staticmethod
    def working():
        a = ColorUi.colorize("<", ColorUi.DeepPurple, bold=True)
        b = ColorUi.colorize("WORKING", ColorUi.Blue, bold=True)
        c = ColorUi.colorize(">", ColorUi.DeepPurple, bold=True)
        return f"{a}{b}{c}"
    
    @staticmethod
    def success():
        a = ColorUi.colorize("<", ColorUi.DeepPurple, bold=True)
        b = ColorUi.colorize("SUCCESS", ColorUi.Gold, bold=True)
        c = ColorUi.colorize(">", ColorUi.DeepPurple, bold=True)
        return f"{a}{b}{c}"
    
    @staticmethod
    def input():
        a = ColorUi.colorize("<", ColorUi.DeepPurple, bold=True)
        b = ColorUi.colorize("INPUT", ColorUi.Green, bold=True)
        c = ColorUi.colorize(">", ColorUi.DeepPurple, bold=True)
        return f"{a}{b}{c}"
    

    @staticmethod
    def MenuFactory(commands=None, title="Main Menu"):
        """Render a colorized boxed menu with a lighter purple title accent."""
        if commands is None:
            commands = [
                ("1", "Data Tools"),
                ("2", "Network Tools"),
                ("3", "Exit"),
            ]

        print()
       
        ColorUi.print_multi(
            ("╔══════════ ", ColorUi.NeonPurple, True),
            (title, ColorUi.Lavender, True, False, True),  
            (" ═════════╗", ColorUi.NeonPurple, True),
        )

        # Menu options
        for key, desc in commands:
            ColorUi.print_multi(
                ("║ ", ColorUi.DeepPurple, True),
                (f"{key}. ", ColorUi.Lavender, True),
                (
                    desc,
                    ColorUi.BrightMagenta if "soon" in desc.lower() else ColorUi.Violet,
                    True,
                ),
            )

        # Bottom border
        ColorUi.print_multi(
            ("╚══════════════════════════════╝", ColorUi.NeonPurple, True)
        )


    @staticmethod
    def PrntBanner():
        UiUtils.clear_screen()
        banner_lines = [
            "",
            "▗▄▄▄ ▗▄▄▄▖▗▖  ▗▖▗▄▄▄▖▗▖    ▗▄▖ ▗▄▄▖ ▗▄▄▄▖▗▄▄▖     ▗▄▄▄▖▗▄▖  ▗▄▖ ▗▖    ▗▄▄▖",
            "▐▌  █▐▌   ▐▌  ▐▌▐▌   ▐▌   ▐▌ ▐▌▐▌ ▐▌▐▌   ▐▌ ▐▌      █ ▐▌ ▐▌▐▌ ▐▌▐▌   ▐▌   ",
            "▐▌  █▐▛▀▀▘▐▌  ▐▌▐▛▀▀▘▐▌   ▐▌ ▐▌▐▛▀▘ ▐▛▀▀▘▐▛▀▚▖      █ ▐▌ ▐▌▐▌ ▐▌▐▌    ▝▀▚▖",
            "▐▙▄▄▀▐▙▄▄▖ ▝▚▞▘ ▐▙▄▄▖▐▙▄▄▖▝▚▄▞▘▐▌   ▐▙▄▄▖▐▌ ▐▌      █ ▝▚▄▞▘▝▚▄▞▘▐▙▄▄▖▗▄▄▞▘",
            "",
            "Developed by perlau with <3",
        ]
        colors = [ColorUi.DeepPurple, ColorUi.Violet, ColorUi.NeonPurple, ColorUi.Lavender]
        for i, line in enumerate(banner_lines):
            ColorUi.print_multi((line, colors[i % len(colors)], True))

        print()
        ColorUi.print_multi(
            (f"Production Version: {UiUtils.productionVersion} | "
             f"Development Version: {UiUtils.developmentVersion}", ColorUi.Violet, True, False, True)
        )

    @staticmethod
    def clear_screen():
        os.system("cls" if platform.system() == "Windows" else "clear")
        
    def menu_data():
        while True:
            UiUtils.clear_screen()
            UiUtils.PrntBanner()
            UiUtils.MenuFactory(
                [
                    ("1", "ORC → YAML Converter"),
                    ("2", "Back to Main Menu"),
                ],
                title="Data Menu",
            )
            choice = input(ColorUi.colorize("\nChoice: ", ColorUi.BrightWhite, bold=True)).strip()
            if choice == "1":
                return 1
            elif choice == "2":
                return 2


    def menu_network():
        while True:
            UiUtils.clear_screen()
            UiUtils.PrntBanner()
            UiUtils.MenuFactory(
                [
                    ("1", "Port Scanner"),
                    ("2", "Back to Main Menu"),
                ],
                title="Network Menu",
            )
            choice = input(ColorUi.colorize("\nChoice: ", ColorUi.BrightWhite, bold=True)).strip()
            if choice == "1":
                return 1
            elif choice == "2":
                return 2
