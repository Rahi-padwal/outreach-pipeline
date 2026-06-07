from colorama import Fore, Style


def review_contacts(contacts: list) -> bool:
    """
    Print a formatted table of all contacts and ask the user
    to confirm before any emails are sent. Returns True only
    on explicit 'yes'.
    """
    bar = "=" * 80
    print(f"\n{Fore.YELLOW}{bar}")
    print("  CHECKPOINT - Review before sending")
    print(f"{bar}{Style.RESET_ALL}\n")

    col = f"{Fore.WHITE}"
    header = f"  {'#':<4} {'Name':<22} {'Title':<28} {'Company':<20} {'Email'}"
    print(Fore.CYAN + header + Style.RESET_ALL)
    print("  " + "-" * 76)

    for i, c in enumerate(contacts, 1):
        name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
        title = (c.get("title") or "")[:27]
        company = (c.get("company") or "")[:19]
        email = c.get("email", "")
        print(f"  {col}{i:<4} {name:<22} {title:<28} {company:<20} {email}{Style.RESET_ALL}")

    print(f"\n  {Fore.YELLOW}Total: {len(contacts)} contact(s) will receive an email.{Style.RESET_ALL}")
    print(f"\n  {Fore.RED}This action cannot be undone.{Style.RESET_ALL}")

    answer = input("\n  Proceed? Type 'yes' to send: ").strip().lower()
    return answer == "yes"
