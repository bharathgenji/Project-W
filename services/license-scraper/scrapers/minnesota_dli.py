from __future__ import annotations

import csv
import io

import httpx

from shared.logging_config import get_logger
from shared.models.contractor import ContractorLicense

from ..base_scraper import BaseLicenseScraper

logger = get_logger(__name__)

MN_CSV_URL = "https://www.dli.mn.gov/sites/default/files/csv/LicensedContractors.csv"
USER_AGENT = "LeadGenMVP/1.0"


class MinnesotaDLIScraper(BaseLicenseScraper):
    """Minnesota DLI - downloads nightly CSV of all licensed contractors."""

    state_code = "MN"
    source_name = "MN-DLI"
    delay_range = (0.0, 0.0)  # No delay needed for bulk download

    async def search(
        self, trade: str = "", page: int = 0, limit: int = 500
    ) -> list[ContractorLicense]:
        """Download and parse the Minnesota contractor CSV."""
        if page > 0:
            return []  # CSV is a single download, no pagination

        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=60.0,
            follow_redirects=True,
        ) as client:
            try:
                response = await client.get(MN_CSV_URL)
                response.raise_for_status()
                content = response.text
            except Exception as e:
                logger.error("mn_csv_download_error", error=str(e))
                return []

        licenses: list[ContractorLicense] = []
        reader = csv.DictReader(io.StringIO(content))

        for row in reader:
            if len(licenses) >= limit:
                break

            name = row.get("Company Name", "").strip()
            if not name:
                continue

            lic_type = row.get("License Type", "")
            if trade and trade.lower() not in lic_type.lower():
                continue

            licenses.append(ContractorLicense(
                source="MN-DLI",
                license_number=row.get("License Number", "").strip(),
                business_name=name,
                owner_name=row.get("Contact Name", "").strip(),
                trade_classification=lic_type,
                address_street=row.get("Address", "").strip(),
                address_city=row.get("City", "").strip(),
                address_state="MN",
                address_zip=row.get("Zip", "").strip(),
                phone=row.get("Phone", "").strip(),
                status="ACTIVE" if row.get("Status", "").upper() == "ACTIVE" else row.get("Status", "").upper(),
            ))

        logger.info("mn_csv_parsed", total=len(licenses))
        return licenses

    async def get_details(self, license_number: str) -> ContractorLicense | None:
        """Search the CSV for a specific license number."""
        results = await self.search()
        for lic in results:
            if lic.license_number == license_number:
                return lic
        return None
