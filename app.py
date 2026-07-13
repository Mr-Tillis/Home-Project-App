
from __future__ import annotations

import csv
import json
import urllib.parse
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List

from data import PROJECTS


# ---------------------------------------------------------------------------
# Store search-link templates
# Each item's shopping URL is generated on the fly -- no scraping/API calls,
# just a well-formed search link so the user can jump straight to results.
# ---------------------------------------------------------------------------
STORES = {
    "Home Depot": "https://www.homedepot.com/s/{query}",
    "Lowe's": "https://www.lowes.com/search?searchTerm={query}",
    "Ace Hardware": "https://www.acehardware.com/search?query={query}",
    "Amazon": "https://www.amazon.com/s?k={query}",
}


def store_links(item_name: str) -> Dict[str, str]:
    """Return a dict of {store_name: search_url} for a given item name."""
    q = urllib.parse.quote_plus(item_name)
    return {store: template.format(query=q) for store, template in STORES.items()}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class MaterialLine:
    name: str
    qty: float
    unit: str
    est_price: float  # price per unit

    @property
    def line_total(self) -> float:
        return round(self.qty * self.est_price, 2)


@dataclass
class ShoppingList:
    project_names: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)          # deduped, sorted
    materials: List[MaterialLine] = field(default_factory=list)  # deduped & summed

    @property
    def estimated_total(self) -> float:
        return round(sum(m.line_total for m in self.materials), 2)

    # -- output helpers ----------------------------------------------------
    def to_text(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("HOME PROJECT SHOPPING LIST")
        lines.append(f"Generated: {date.today().isoformat()}")
        lines.append("Projects: " + ", ".join(self.project_names))
        lines.append("=" * 60)

        lines.append("\nTOOLS TO BRING / HAVE ON HAND (not purchased each time):")
        if self.tools:
            for t in self.tools:
                lines.append(f"  [ ] {t}")
        else:
            lines.append("  (none)")

        lines.append("\nMATERIALS TO BUY:")
        for m in self.materials:
            lines.append(
                f"  [ ] {m.name:<38} qty: {m.qty:>4} {m.unit:<6} "
                f"@ ${m.est_price:>6.2f}  = ${m.line_total:>7.2f}"
            )

        lines.append("-" * 60)
        lines.append(f"{'ESTIMATED TOTAL':<52} ${self.estimated_total:>7.2f}")
        lines.append("(Prices are rough national averages -- confirm at checkout.)")
        return "\n".join(lines)

    def to_csv(self, path: str) -> None:
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "Item", "Qty", "Unit", "Est. Unit Price", "Est. Line Total"])
            for t in self.tools:
                writer.writerow(["Tool (bring, not bought)", t, "", "", "", ""])
            for m in self.materials:
                writer.writerow(["Material", m.name, m.qty, m.unit, m.est_price, m.line_total])
            writer.writerow([])
            writer.writerow(["", "", "", "", "TOTAL", self.estimated_total])

    def to_json(self) -> str:
        return json.dumps(
            {
                "projects": self.project_names,
                "tools": self.tools,
                "materials": [m.__dict__ for m in self.materials],
                "estimated_total": self.estimated_total,
            },
            indent=2,
        )


# ---------------------------------------------------------------------------
# Catalog access
# ---------------------------------------------------------------------------
def list_projects() -> List[str]:
    """Return catalog ids sorted by category then name."""
    return sorted(PROJECTS.keys(), key=lambda pid: (PROJECTS[pid]["category"], PROJECTS[pid]["name"]))


def search_projects(keyword: str) -> List[str]:
    """Case-insensitive search across project name/category."""
    kw = keyword.lower().strip()
    return [
        pid
        for pid in PROJECTS
        if kw in PROJECTS[pid]["name"].lower() or kw in PROJECTS[pid]["category"].lower()
    ]


def get_project(pid: str) -> dict:
    return PROJECTS[pid]


# ---------------------------------------------------------------------------
# Shopping list generation
# ---------------------------------------------------------------------------
def generate_shopping_list(
    project_ids: Iterable[str],
    extra_materials: Iterable[MaterialLine] = (),
) -> ShoppingList:
    """
    Combine one or more catalog projects (plus optional ad-hoc extra items)
    into a single de-duplicated shopping list. Materials with the same name
    + unit have their quantities summed rather than listed twice.
    """
    tools_set = set()
    material_map: Dict[tuple, MaterialLine] = {}  # key: (name, unit)
    names = []

    for pid in project_ids:
        proj = PROJECTS[pid]
        names.append(proj["name"])
        tools_set.update(proj["tools"])
        for m in proj["materials"]:
            key = (m["name"], m["unit"])
            if key in material_map:
                material_map[key].qty += m["qty"]
            else:
                material_map[key] = MaterialLine(
                    name=m["name"], qty=m["qty"], unit=m["unit"], est_price=m["est_price"]
                )

    for extra in extra_materials:
        key = (extra.name, extra.unit)
        if key in material_map:
            material_map[key].qty += extra.qty
        else:
            material_map[key] = extra

    return ShoppingList(
        project_names=names,
        tools=sorted(tools_set),
        materials=sorted(material_map.values(), key=lambda m: m.name),
    )
