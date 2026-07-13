# Home-Project-App 
from app import (
    MaterialLine,
    generate_shopping_list,
    get_project,
    list_projects,
    search_projects,
    store_links,
)
from data import PROJECTS


def print_catalog(pids):
    current_category = None
    for pid in pids:
        proj = PROJECTS[pid]
        if proj["category"] != current_category:
            current_category = proj["category"]
            print(f"\n-- {current_category} --")
        print(f"  {pid:<22} {proj['name']} ({proj['difficulty']}, ~{proj['est_time_hours']}h)")


def choose_projects() -> list:
    chosen = []
    print("\nWelcome to the Home Project App!")
    print("Browse the full catalog, or type a keyword to search (e.g. 'paint', 'electrical').")

    while True:
        print_catalog(list_projects())
        raw = input(
            "\nEnter a project id to add it, a keyword to search, "
            "'done' to finish, or 'list' to see the catalog again: "
        ).strip()

        if raw.lower() == "done":
            break
        elif raw.lower() == "list":
            continue
        elif raw in PROJECTS:
            if raw not in chosen:
                chosen.append(raw)
                print(f"  Added: {PROJECTS[raw]['name']}")
            else:
                print("  Already added.")
        else:
            results = search_projects(raw)
            if results:
                print(f"\nFound {len(results)} match(es):")
                print_catalog(results)
            else:
                print("  No matches. Try 'list' to browse everything.")

    return chosen


def add_custom_items() -> list:
    extras = []
    print("\nWant to add any extra/custom items not in a project (e.g. 'gloves')?")
    while True:
        name = input("  Item name (blank to skip/finish): ").strip()
        if not name:
            break
        try:
            qty = float(input("  Quantity [1]: ").strip() or "1")
            unit = input("  Unit [each]: ").strip() or "each"
            price = float(input("  Est. price per unit [0]: ").strip() or "0")
        except ValueError:
            print("  Invalid number, skipping that item.")
            continue
        extras.append(MaterialLine(name=name, qty=qty, unit=unit, est_price=price))
    return extras


def show_store_links(shopping_list) -> None:
    print("\nQUICK SEARCH LINKS (per item):")
    for m in shopping_list.materials:
        print(f"\n  {m.name}")
        for store, url in store_links(m.name).items():
            print(f"    {store:<14} {url}")


def export_flow(shopping_list) -> None:
    choice = input("\nExport this list? [csv/json/no]: ").strip().lower()
    if choice == "csv":
        path = input("  File name [shopping_list.csv]: ").strip() or "shopping_list.csv"
        shopping_list.to_csv(path)
        print(f"  Saved to {path}")
    elif choice == "json":
        path = input("  File name [shopping_list.json]: ").strip() or "shopping_list.json"
        with open(path, "w") as f:
            f.write(shopping_list.to_json())
        print(f"  Saved to {path}")


def main():
    project_ids = choose_projects()
    if not project_ids:
        print("\nNo projects selected. Exiting.")
        return

    extras = add_custom_items()
    shopping_list = generate_shopping_list(project_ids, extras)

    print("\n" + shopping_list.to_text())

    if input("\nShow store search links for each item? [y/N]: ").strip().lower() == "y":
        show_store_links(shopping_list)

    export_flow(shopping_list)
    print("\nHappy building!")


if __name__ == "__main__":
    main()
