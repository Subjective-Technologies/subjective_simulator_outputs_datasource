import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from subjective_abstract_data_source_package import SubjectiveDataSource

from trading_contracts.order import Fill, validate_order
from trading_contracts.plugin_support import icon_for


class SubjectiveSimulatorOutputsDataSource(SubjectiveDataSource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def connection_schema(cls):
        return {"fee_pct": {"type": "number", "label": "Fee Percent", "default": 0}}

    @classmethod
    def request_schema(cls):
        return {"orders": {"type": "array", "label": "Orders", "required": True}, "mark_price": {"type": "text", "label": "Mark Price", "required": True}}

    @classmethod
    def output_schema(cls):
        return {"fills": {"type": "array", "label": "Paper Fills"}, "errors": {"type": "array", "label": "Errors"}}

    @classmethod
    def icon(cls):
        return icon_for(__file__)

    def run(self, request):
        request = request or {}
        mark_price = str(request.get("mark_price") or "0")
        fee_pct = Decimal(str(request.get("fee_pct", self._connection.get("fee_pct", 0))))
        fills, errors = [], []
        for candidate in request.get("orders") or ([request["order"]] if request.get("order") else []):
            try:
                order = validate_order(candidate)
                price = Decimal(mark_price)
                qty = order.get("qty") or (format(Decimal(order["quote_amt"]) / price, "f") if price else "0")
                fee = Decimal(str(qty)) * price * fee_pct / Decimal("100")
                fills.append(Fill(order["order_id"], order["client_order_id"], f"paper:{order['client_order_id']}", "PAPER_FILLED", str(qty), mark_price, format(fee, "f"), {}).to_dict())
            except Exception as exc:
                errors.append({"order": candidate, "error": str(exc)})
        return {"fills": fills, "errors": errors}
