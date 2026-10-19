"""Small, self-authored evaluation set. A line containing '@@' marks the buggy line (the target).
This is a regression harness, NOT a benchmark: 10 hand-written cases prove nothing about real-world accuracy."""

def py_filler(n, prefix="helper"):
    return "\n".join(f"def {prefix}_{i}(value):\n    total = value + {i}\n    return total * 2\n" for i in range(n))

def js_filler(n):
    return "\n".join(f"function util{i}(v) {{\n  const out = v + {i};\n  return out;\n}}\n" for i in range(n))

CASES = [
    {"id": "py-none-strip", "language": "Python",
     "report": "normalize crashes when the caller passes None. Error: 'NoneType' object has no attribute 'strip'",
     "files": {
         "app/utils/text.py": "import re\n\ndef normalize(text):\n    return text.strip().lower()  # @@\n\ndef slugify(text):\n    return re.sub(r'\\W+', '-', text)\n",
         "app/utils/math_utils.py": "def add(a, b):\n    return a + b\n\ndef mean(xs):\n    return sum(xs) / len(xs)\n",
         "app/services/users.py": py_filler(6, "user"),
     }},
    {"id": "py-trace-keyerror", "language": "Python",
     "report": 'Traceback (most recent call last):\n  File "app/services/billing.py", line 9, in compute_tax\n    rate = RATES[country]\nKeyError: \'BR\'',
     "files": {
         "app/services/billing.py": "RATES = {'US': 0.07, 'DE': 0.19}\n\n\ndef format_amount(x):\n    return f'{x:.2f}'\n\n\ndef compute_tax(amount, country):\n    rate = RATES[country]  # @@\n    return amount * rate\n",
         "app/services/tax_report.py": "def tax_summary(rows):\n    # tax country rate report keyerror handling\n    return {r['country']: r['tax'] for r in rows}\n\n" + py_filler(5, "report"),
     }},
    {"id": "py-large-file", "language": "Python",
     "report": "parse_date raises ValueError for 2024-13-01 instead of returning None",
     "files": {
         "app/dates.py": py_filler(14, "fmt") + "\ndef parse_date(s):\n    y, m, d = s.split('-')\n    return datetime.date(int(y), int(m), int(d))  # @@\n\n" + py_filler(10, "tz"),
     }},
    {"id": "py-snake-camel", "language": "Python",
     "report": "the user name is not trimmed when saving the profile",
     "files": {
         "app/profile.py": "def cleanUserName(rawName):\n    return rawName  # @@\n\ndef get_user(uid):\n    return {'id': uid}\n",
         "app/other.py": py_filler(8, "misc"),
     }},
    {"id": "js-trace-undefined", "language": "JavaScript",
     "report": "TypeError: Cannot read properties of undefined (reading 'map')\n    at renderCart (/srv/app/src/cart.js:12:5)\n    at main (/srv/app/src/index.js:3:1)",
     "files": {
         "src/cart.js": js_filler(2) + "\nexport function renderCart(cart) {\n  return cart.items.map((i) => i.name); // @@\n}\n",
         "src/index.js": "import { renderCart } from './cart.js';\nrenderCart(window.cart);\n",
         "src/list.js": js_filler(6),
     }},
    {"id": "ts-lexical", "language": "TypeScript",
     "report": "login button stays disabled even after the form validation passes",
     "files": {
         "src/form.ts": "export function validateForm(values: Record<string,string>): boolean {\n  return Object.keys(values).length > 3; // @@\n}\n",
         "src/button.ts": "export function isDisabled(loading: boolean): boolean {\n  return loading;\n}\n",
         "src/misc.ts": js_filler(6),
     }},
    {"id": "java-trace-npe", "language": "Java",
     "report": "java.lang.NullPointerException\n\tat com.shop.OrderService.total(OrderService.java:6)\n\tat com.shop.Main.main(Main.java:4)",
     "files": {
         "src/com/shop/OrderService.java": "package com.shop;\n\npublic class OrderService {\n    private Cart cart;\n\n    public double total() {\n        return cart.price() * 1.2; // @@\n    }\n\n    public void reset() {\n        cart = null;\n    }\n}\n",
         "src/com/shop/Main.java": "package com.shop;\n\npublic class Main {\n    public static void main(String[] a) {\n        new OrderService().total();\n    }\n}\n",
         "src/com/shop/Cart.java": "package com.shop;\n\npublic class Cart {\n    public double price() { return 1.0; }\n}\n",
     }},
    {"id": "go-trace-nilmap", "language": "Go",
     "report": "panic: assignment to entry in nil map\n\ngoroutine 1 [running]:\nmain.(*Cache).Set(...)\n\t/app/cache/cache.go:9 +0x1d",
     "files": {
         "cache/cache.go": "package cache\n\ntype Cache struct {\n    data map[string]string\n}\n\nfunc (c *Cache) Set(k, v string) {\n    c.data[k] = v // @@\n}\n\nfunc (c *Cache) Get(k string) string {\n    return c.data[k]\n}\n",
         "cache/util.go": "package cache\n\nfunc keyOf(s string) string {\n    return s\n}\n",
     }},
    {"id": "rust-overflow", "language": "Rust",
     "report": "integer overflow panic when computing factorial of 25",
     "files": {
         "src/math.rs": "pub fn factorial(n: u32) -> u32 {\n    (1..=n).product() // @@\n}\n\npub fn double(n: u32) -> u32 {\n    n * 2\n}\n",
         "src/main.rs": "fn main() {\n    println!(\"hello\");\n}\n",
     }},
    {"id": "py-secret-file", "language": "Python",
     "report": "fetch_profile returns 401 unauthorized from the remote service",
     "files": {
         "app/client.py": "API_KEY = 'sk_live_abcdefghijklmnop'\n\ndef fetch_profile(uid):\n    return http_get(f'/profile/{uid}', headers={'Authorization': 'bearer'})  # @@\n",
         "app/misc.py": py_filler(5, "misc"),
     }},
]


def target_of(case):
    for path, content in case["files"].items():
        for i, line in enumerate(content.splitlines(), 1):
            if "@@" in line:
                return path, i
    raise ValueError(case["id"])
