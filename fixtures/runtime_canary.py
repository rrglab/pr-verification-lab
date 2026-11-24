"""Synthetic QA fixture only; no real accounts, payments, network calls or persistence.
Start: python3 fixtures/runtime_canary.py
Browser: http://localhost:8000/
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = """<!doctype html><html lang="en"><meta charset="utf-8">
<title>Synthetic checkout QA fixture</title>
<h1>Synthetic checkout (no real payment)</h1>
<p>Item price: 100 credits. SAVE20 reduces both displayed and recorded totals
to 80 credits. Invalid coupons must be rejected. Quantity must be 1–5.
No credits have monetary value.</p>
<form id="checkout"><label>Quantity <input name="quantity" type="number" value="1"></label>
<label>Coupon <input name="coupon"></label>
<button>Simulate checkout</button></form>
<pre id="result" role="status"></pre>
<script>
document.querySelector('form').onsubmit = async e => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(e.target));
  const response = await fetch('/checkout', {method:'POST', headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  document.querySelector('#result').textContent = JSON.stringify(await response.json(), null, 2);
};
</script></html>"""


def checkout(data):
    try:
        quantity = int(data.get("quantity", 1))
    except (ValueError, TypeError):
        return 400, {"error": "Invalid quantity"}
    coupon = data.get("coupon", "")
    if quantity < 1 or quantity > 5:
        return 400, {"error": "Invalid quantity"}
    if coupon not in ("", "SAVE20"):
        return 400, {"error": "Invalid coupon"}
    subtotal = quantity * 100
    total = subtotal * 80 // 100 if coupon == "SAVE20" else subtotal
    # Synthetic mutation: display and simulated ledger can disagree.
    return 200, {"displayed_total": total, "recorded_total": subtotal,
                 "quantity": quantity, "simulated": True}


class Handler(BaseHTTPRequestHandler):
    def send_content(self, status, content, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path == "/":
            self.send_content(200, PAGE.encode(), "text/html; charset=utf-8")
        else:
            self.send_content(404, b"Not found", "text/plain")

    def do_POST(self):
        if self.path != "/checkout":
            self.send_content(404, b"Not found", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("Invalid length")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Invalid body")
            status, result = checkout(data)
        except (ValueError, TypeError):
            status, result = 400, {"error": "Invalid request"}
        self.send_content(status, json.dumps(result).encode(), "application/json")


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
