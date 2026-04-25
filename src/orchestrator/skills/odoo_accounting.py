#!/usr/bin/env python3
"""
Agent Skill: Odoo Accounting
Reads invoices and expenses from Odoo via JSON-RPC API.
Creates draft invoices (HITL-gated; never auto-posts).
"""

import json
import sys
import xmlrpc.client
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Optional

try:
    from .base_skill import BaseSkill, run_skill
except ImportError:
    from base_skill import BaseSkill, run_skill


class OdooClient:
    """Thin wrapper around Odoo JSON-RPC (xmlrpc.client)"""

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self._uid: Optional[int] = None

    def authenticate(self) -> int:
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self._uid = common.authenticate(self.db, self.username, self.password, {})
        if not self._uid:
            raise RuntimeError("Odoo authentication failed — check credentials")
        return self._uid

    @property
    def uid(self) -> int:
        if self._uid is None:
            self.authenticate()
        return self._uid

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        return models.execute_kw(
            self.db, self.uid, self.password,
            model, method, list(args), kwargs
        )

    def search_read(self, model: str, domain: list, fields: list, limit: int = 100) -> List[Dict]:
        return self.execute(model, "search_read", domain, fields=fields, limit=limit)


class OdooAccountingSkill(BaseSkill):
    """Reads Odoo accounting data and creates draft invoices with HITL approval"""

    def _get_client(self, params: Dict[str, Any]) -> OdooClient:
        import os
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parents[3] / ".env")

        url = params.get("odoo_url") or os.getenv("ODOO_URL", "http://localhost:8069")
        db = params.get("odoo_db") or os.getenv("ODOO_DB", "odoo")
        username = params.get("odoo_username") or os.getenv("ODOO_USERNAME", "admin")
        password = params.get("odoo_password") or os.getenv("ODOO_PASSWORD", "admin")
        return OdooClient(url, db, username, password)

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action", "revenue_summary")

        if action == "revenue_summary":
            return self.get_revenue_summary(params)
        elif action == "expense_summary":
            return self.get_expense_summary(params)
        elif action == "create_draft_invoice":
            return self.create_draft_invoice(params)
        else:
            return {"error": f"Unknown action: {action}. Use: revenue_summary, expense_summary, create_draft_invoice"}

    # -------------------------------------------------------------------------

    def get_revenue_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read posted customer invoices for a period"""
        client = self._get_client(params)
        client.authenticate()

        period_start = params.get("period_start") or date.today().replace(day=1).isoformat()
        period_end = params.get("period_end") or date.today().isoformat()

        domain = [
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("invoice_date", ">=", period_start),
            ("invoice_date", "<=", period_end),
        ]
        fields = ["name", "partner_id", "amount_total", "currency_id", "invoice_date", "payment_state"]

        invoices = client.search_read("account.move", domain, fields)

        total = sum(inv.get("amount_total", 0) for inv in invoices)
        paid = sum(inv.get("amount_total", 0) for inv in invoices if inv.get("payment_state") == "paid")

        return {
            "period": f"{period_start} → {period_end}",
            "invoice_count": len(invoices),
            "total_revenue": round(total, 2),
            "total_paid": round(paid, 2),
            "outstanding": round(total - paid, 2),
            "invoices": [
                {
                    "name": inv["name"],
                    "partner": inv["partner_id"][1] if inv.get("partner_id") else "Unknown",
                    "amount": inv["amount_total"],
                    "date": inv["invoice_date"],
                    "payment_state": inv["payment_state"],
                }
                for inv in invoices
            ],
        }

    def get_expense_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read posted vendor bills for a period"""
        client = self._get_client(params)
        client.authenticate()

        period_start = params.get("period_start") or date.today().replace(day=1).isoformat()
        period_end = params.get("period_end") or date.today().isoformat()

        domain = [
            ("move_type", "=", "in_invoice"),
            ("state", "=", "posted"),
            ("invoice_date", ">=", period_start),
            ("invoice_date", "<=", period_end),
        ]
        fields = ["name", "partner_id", "amount_total", "currency_id", "invoice_date", "payment_state"]

        bills = client.search_read("account.move", domain, fields)
        total = sum(b.get("amount_total", 0) for b in bills)
        paid = sum(b.get("amount_total", 0) for b in bills if b.get("payment_state") == "paid")

        return {
            "period": f"{period_start} → {period_end}",
            "bill_count": len(bills),
            "total_expenses": round(total, 2),
            "total_paid": round(paid, 2),
            "outstanding": round(total - paid, 2),
            "bills": [
                {
                    "name": b["name"],
                    "vendor": b["partner_id"][1] if b.get("partner_id") else "Unknown",
                    "amount": b["amount_total"],
                    "date": b["invoice_date"],
                    "payment_state": b["payment_state"],
                }
                for b in bills
            ],
        }

    def create_draft_invoice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a DRAFT customer invoice — never posts automatically"""
        client = self._get_client(params)
        client.authenticate()

        partner_name = params.get("partner_name")
        amount = params.get("amount")
        description = params.get("description", "Service")

        if not partner_name or not amount:
            return {"error": "partner_name and amount are required"}

        # Find or create partner
        partners = client.search_read(
            "res.partner",
            [("name", "ilike", partner_name)],
            ["id", "name"],
            limit=1
        )
        if not partners:
            partner_id = client.execute("res.partner", "create", {"name": partner_name})
        else:
            partner_id = partners[0]["id"]

        # Find default income account
        accounts = client.search_read(
            "account.account",
            [("account_type", "=", "income")],
            ["id", "name"],
            limit=1
        )
        account_id = accounts[0]["id"] if accounts else False

        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": partner_id,
            "state": "draft",
            "invoice_line_ids": [(0, 0, {
                "name": description,
                "quantity": 1,
                "price_unit": float(amount),
                "account_id": account_id,
            })],
        }

        invoice_id = client.execute("account.move", "create", invoice_vals)

        # Write approval request to vault
        approval = {
            "type": "odoo_invoice_approval",
            "action": "post_invoice",
            "odoo_invoice_id": invoice_id,
            "partner": partner_name,
            "amount": amount,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "note": "DRAFT only. Move this file to Approved/ to post the invoice in Odoo.",
        }
        approval_path = self.vault_path / "Pending_Approval" / f"ODOO_INVOICE_{invoice_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        approval_path.parent.mkdir(exist_ok=True)
        self.write_file(approval_path, json.dumps(approval, indent=2))

        return {
            "status": "draft_created",
            "invoice_id": invoice_id,
            "partner": partner_name,
            "amount": amount,
            "approval_file": str(approval_path),
            "note": "Invoice is DRAFT. Approve in vault to post.",
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: odoo_accounting.py '<json_params>'"}, indent=2))
        sys.exit(1)
    run_skill(OdooAccountingSkill, sys.argv[1])
