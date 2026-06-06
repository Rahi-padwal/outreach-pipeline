import sys
from colorama import Fore, Style, init

# Strip ANSI on Windows terminals that don't support it natively;
# colorama handles the conversion so we always get colour output.
init(autoreset=True)


def banner():
    print(Fore.CYAN + r"""
   ___  _   _ _____ ____  _____   _    ____ _   _
  / _ \| | | |_   _|  _ \| ____| / \  / ___| | | |
 | | | | | | | | | | |_) |  _|  / _ \| |   | |_| |
 | |_| | |_| | | | |  _ <| |___/ ___ \ |___|  _  |
  \___/ \___/  |_| |_| \_\_____/_/   \_\____|_| |_|
""" + Style.RESET_ALL)
    print(Fore.WHITE + "  Cold Outreach Pipeline  |  Apollo -> Prospeo -> Brevo\n" + Style.RESET_ALL)


def stage(num: int, name: str):
    bar = "-" * 54
    print(f"\n{Fore.MAGENTA}{bar}")
    print(f"  STAGE {num}  -  {name}")
    print(f"{bar}{Style.RESET_ALL}")


def info(msg: str):
    print(f"  {Fore.CYAN}>{Style.RESET_ALL} {msg}")


def success(msg: str):
    print(f"  {Fore.GREEN}[OK]{Style.RESET_ALL} {msg}")


def warning(msg: str):
    print(f"  {Fore.YELLOW}[!!]{Style.RESET_ALL} {msg}")


def error(msg: str):
    print(f"  {Fore.RED}[XX]{Style.RESET_ALL} {msg}")
