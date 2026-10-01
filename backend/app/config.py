"""Per-tenant config: one entry per branch/vendor. Move to YAML/DB later."""
from dataclasses import dataclass, field

@dataclass
class Tenant:
    brand: str = "Loan Register Cleaner"
    day_first: bool = True
    branches: list = field(default_factory=lambda: ["Andheri", "Borivali", "Thane"])
    drop_words: tuple = ("branch", "br", "west", "east", "north", "south")
    outlier_days: int = 180
    cols: dict = field(default_factory=lambda: {
        "branch": ["branch"], "name": ["customer name", "name", "customer"],
        "amount": ["loan amt", "loan amount", "amount"], "date": ["loan date", "date"],
        "phone": ["phone no", "phone", "mobile"], "status": ["status"], "notes": ["notes", "remarks"]})

TENANTS = {"default": Tenant()}
FIELDS = ["branch", "name", "amount", "date", "phone", "status"]
