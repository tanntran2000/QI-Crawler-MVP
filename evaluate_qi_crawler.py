"""Portable evaluation runner for the QI-Crawler MVP.

Run from the QI-Crawler project folder:

    python evaluate_qi_crawler.py

Run with external Excel/CSV files:

    python evaluate_qi_crawler.py --inventory "C:\\path\\qi-stock.xlsx" \
        --boq "C:\\path\\tender-boq.xlsx"

The script creates an isolated database and report. It never changes data/egp.db.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import UTC, datetime, timedelta
from importlib import import_module
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

Database = import_module("qi_crawler.db").Database
export_xlsx = import_module("qi_crawler.exporter").export_xlsx
inventory_module = import_module("qi_crawler.inventory")
import_inventory = inventory_module.import_inventory
import_tender_items = inventory_module.import_tender_items
models_module = import_module("qi_crawler.models")
InventoryItem = models_module.InventoryItem
Notice = models_module.Notice
TenderItem = models_module.TenderItem
check_stock = import_module("qi_crawler.stock").check_stock
opportunity_module = import_module("qi_crawler.opportunity")
KeywordGroup = opportunity_module.KeywordGroup
assess_opportunity = opportunity_module.assess_opportunity


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an isolated quantity and inventory evaluation of QI-Crawler."
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        help="Optional external QI inventory .xlsx/.xlsm/.csv file.",
    )
    parser.add_argument(
        "--boq",
        type=Path,
        help="Optional external tender BOQ .xlsx/.xlsm/.csv file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "evaluation_output",
        help="Parent folder for the isolated evaluation result.",
    )
    return parser.parse_args()


def validate_input(path: Path | None, label: str) -> Path | None:
    if path is None:
        return None
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise SystemExit(f"{label} file does not exist: {resolved}")
    if resolved.suffix.lower() not in {".xlsx", ".xlsm", ".csv"}:
        raise SystemExit(f"{label} must be .xlsx, .xlsm or .csv: {resolved}")
    return resolved


def create_run_folder(parent: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    folder = parent.expanduser().resolve() / f"qi-crawler-evaluation-{stamp}"
    folder.mkdir(parents=True, exist_ok=False)
    return folder


def write_demo_inventory(path: Path) -> None:
    path.write_text(
        "SKU,Product Name,Aliases,Quantity Available,Unit,Warehouse,Verified\n"
        "RTR-5G-001,5G Router,router 5g; cellular router,10,pieces,Main Warehouse,yes\n"
        "SW-24-001,Network Switch,24 port switch; managed switch,20,pieces,Main Warehouse,yes\n",
        encoding="ascii",
    )


def write_demo_boq(path: Path) -> None:
    path.write_text(
        "Item Code,Product Name,Quantity,Unit,Specification\n"
        "1,5G Router,8,pieces,Three antenna ports\n"
        "2,Network Switch,25,pieces,24 Gigabit ports\n",
        encoding="ascii",
    )


def create_demo_notice(db: Database) -> int:
    source_url = "https://example.test/tenders/qi-evaluation"
    with db.session() as session:
        notice = Notice(
            source_url=source_url,
            url_hash=hashlib.sha256(source_url.encode("utf-8")).hexdigest(),
            notice_code="QI-EVALUATION-001",
            notice_version="1",
            title="Supply of 5G routers and network switches",
            buyer="Evaluation Buyer",
            package_price=2_000_000_000,
            currency="VND",
            published_at=datetime.now(UTC).date().isoformat(),
            closing_at=(datetime.now(UTC).date() + timedelta(days=30)).isoformat(),
            location="Ho Chi Minh City",
            sector="Information Technology",
            selection_method="Open bidding",
            raw_text=(
                "Supply of 5G routers and managed network switches with installation support."
            ),
            source_kind="evaluation",
            data_quality_status="valid",
        )
        session.add(notice)
        session.flush()
        return notice.id


def print_results(db: Database, notice_id: int) -> tuple[int, int, int]:
    meets = shortage = review = 0
    with db.session() as session:
        items = (
            session.query(TenderItem)
            .filter(TenderItem.notice_id == notice_id)
            .order_by(TenderItem.item_code)
            .all()
        )
        inventory = session.query(InventoryItem).order_by(InventoryItem.sku).all()

        print("\nRESPONSE TABLE")
        print("-" * 92)
        print(
            f"{'Product':28} {'Required':>10} {'Available':>10} "
            f"{'Shortage':>10}  Status"
        )
        print("-" * 92)
        for item in items:
            result = check_stock(item, inventory)
            if result.status == "MEETS_STOCK":
                meets += 1
            elif result.status == "STOCK_SHORTAGE":
                shortage += 1
            else:
                review += 1
            required = "N/A" if result.required_quantity is None else f"{result.required_quantity:g}"
            available = (
                "N/A" if result.available_quantity is None else f"{result.available_quantity:g}"
            )
            missing = "N/A" if result.shortage_quantity is None else f"{result.shortage_quantity:g}"
            print(
                f"{item.product_name[:28]:28} {required:>10} {available:>10} "
                f"{missing:>10}  {result.status}"
            )
    return meets, shortage, review


def print_opportunity_score(db: Database, notice_id: int) -> None:
    with db.session() as session:
        notice = session.get(Notice, notice_id)
        inventory = session.query(InventoryItem).filter(InventoryItem.verified).all()
        if notice is None:
            return
        assessment = assess_opportunity(
            notice,
            (
                KeywordGroup("Network", ("network switch", "router", "5G module"), 30),
            ),
            [],
            inventory,
        )
        print("\nOPPORTUNITY PRIORITY SCORE")
        print("-" * 92)
        print(f"Status            : {assessment.status}")
        print(f"Score             : {assessment.score if assessment.score is not None else 'N/A'}")
        print(f"Matched keywords  : {', '.join(assessment.matched_keywords) or 'none'}")
        print(f"Missing data      : {', '.join(assessment.missing_fields) or 'none'}")
        print(f"Next action       : {assessment.next_action}")
        for component in assessment.components:
            print(
                f"  {component.name:22} {component.score:g}/{component.maximum:g}  "
                f"{component.explanation}"
            )


def main() -> int:
    args = arguments()
    inventory_input = validate_input(args.inventory, "Inventory")
    boq_input = validate_input(args.boq, "BOQ")
    run_dir = create_run_folder(args.output_dir)
    database_path = run_dir / "evaluation.db"
    report_path = run_dir / "qi-crawler-evaluation.xlsx"

    if inventory_input is None:
        inventory_input = run_dir / "demo-inventory.csv"
        write_demo_inventory(inventory_input)
    if boq_input is None:
        boq_input = run_dir / "demo-tender-boq.csv"
        write_demo_boq(boq_input)

    db = Database(f"sqlite:///{database_path.as_posix()}")
    db.create_all()
    notice_id = create_demo_notice(db)
    inventory_summary = import_inventory(db, inventory_input)
    boq_summary = import_tender_items(db, notice_id, boq_input)
    meets, shortage, review = print_results(db, notice_id)
    print_opportunity_score(db, notice_id)
    export_xlsx(db, report_path)

    print("\nEVALUATION SUMMARY")
    print("-" * 92)
    print(f"Isolated database : {database_path}")
    print(f"Inventory source  : {inventory_input}")
    print(f"BOQ source        : {boq_input}")
    print(
        "Inventory import : "
        f"rows={inventory_summary.rows}, inserted={inventory_summary.inserted}, "
        f"updated={inventory_summary.updated}, rejected={inventory_summary.rejected}"
    )
    print(
        "BOQ import       : "
        f"rows={boq_summary.rows}, inserted={boq_summary.inserted}, "
        f"updated={boq_summary.updated}, rejected={boq_summary.rejected}"
    )
    print(f"Result            : meets={meets}, shortage={shortage}, review={review}")
    print(f"Excel report      : {report_path}")
    print("\nOpen the Excel report and review the Notices, Response Table and QI Inventory sheets.")
    print("This is a screening result, not final bid approval.")
    return 0 if inventory_summary.rejected == 0 and boq_summary.rejected == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
