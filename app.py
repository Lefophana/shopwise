import os
from datetime import date
from flask import Flask, request, redirect, render_template_string
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            sell_price FLOAT NOT NULL DEFAULT 0,
            cost_price FLOAT NOT NULL DEFAULT 0,
            qty INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            product_name TEXT,
            qty INTEGER,
            total FLOAT,
            profit FLOAT,
            sale_date DATE DEFAULT CURRENT_DATE
        );
    """)
    db.commit()
    cur.close(); db.close()

init_db()

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;margin:0;background:#f2f2f2}
.header{background:#d32f2f;color:white;text-align:center;padding:15px}
.nav{background:#222;color:white;text-align:center;padding:10px}
.nav a{color:white;margin:0 12px;text-decoration:none;font-weight:bold}
.top{background:#b3e5fc;text-align:center;padding:10px;font-weight:bold}
table{width:95%;margin:10px auto;background:white;border-collapse:collapse}
th,td{border:1px solid #ccc;padding:8px;text-align:center}
input[type=number]{width:55px;padding:5px}
button{padding:6px 10px;cursor:pointer}
.sell{background:#ff9800;border:none}
.addstock{background:#2196f3;color:white;border:none}
.addbox{background:#ff9800;padding:15px;text-align:center;margin:10px}
.low{color:red;font-weight:bold}
</style></head><body>
<div class="header"><h1 style="margin:0">🛒 ShopWise</h1><div>Tembisa | Best Prices Daily</div></div>
<div class="nav"><a href="/">Home</a><a href="/stock">Shop</a><a href="/history">History</a><a href="/end-day">End Day</a></div>
<div class="top">🔥 Sales: R{{sales}} | 💰 Profit: R{{profit}} | 📦 Stock: R{{stock_value}}</div>
<table><tr><th>Name</th><th>Price</th><th>Qty</th><th>Sell</th><th>+ Stock</th><th>Edit</th><th>Delete</th></tr>
{% for p in products %}
<tr>
<td><b>{{p.name}}</b>{% if p.qty<=5 %}<br><span class="low">⚠️ LOW!</span>{% endif %}</td>
<td>R{{p.sell_price}}<br><small>Cost R{{p.cost_price}}</small></td>
<td>{{p.qty}}</td>
<td><form method="POST" action="/sell/{{p.id}}" style="margin:0">
<input type="number" name="qty" value="1" min="1" max="{{p.qty}}"> <button class="sell">Sell</button>
</form></td>
<td><form method="POST" action="/add-stock/{{p.id}}" style="margin:0">
<input type="number" name="qty" value="5" min="1"> <button class="addstock">+ Add</button>
</form></td>
<td><a href="/edit/{{p.id}}">Edit</a></td>
<td><a href="/delete/{{p.id}}" onclick="return confirm('Delete {{p.name}}?')">Delete</a></td>
</tr>
{% endfor %}</table>
<div class="addbox"><b>Add New Product</b><br><br>
<form method="POST" action="/add" style="display:inline">
Name <input name="name" required> Sell <input type="number" step="0.01" name="sell" required>
Cost <input type="number" step="0.01" name="cost" required> Qty <input type="number" name="qty" required> <button>Add</button>
</form></div>
{% if history %}<h3 style="text-align:center">History</h3><table><tr><th>Product</th><th>Qty</th><th>Total</th><th>Date</th></tr>
{% for h in history %}<tr><td>{{h.product_name}}</td><td>{{h.qty}}</td><td>R{{h.total}}</td><td>{{h.sale_date}}</td></tr>{% endfor %}</table>{% endif %}
</body></html>
"""

def get_totals():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT COALESCE(SUM(total),0) as s, COALESCE(SUM(profit),0) as p FROM sales WHERE sale_date=%s", (date.today(),))
    r = cur.fetchone()
    cur.execute("SELECT COALESCE(SUM(qty*cost_price),0) as v FROM products")
    v = cur.fetchone()
    cur.close(); db.close()
    return r['s'], r['p'], v['v']

@app.route("/")
@app.route("/stock")
def stock():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM products ORDER BY id ASC") # FIX: always same order, no jumping
    products = cur.fetchall(); cur.close(); db.close()
    s,p,v = get_totals()
    return render_template_string(HTML, products=products, sales=s, profit=p, stock_value=v, history=None)

@app.route("/sell/<int:pid>", methods=["POST"])
def sell(pid):
    qty = int(request.form.get("qty", 1))
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM products WHERE id=%s", (pid,))
    pr = cur.fetchone()
    if pr and pr['qty'] >= qty and qty > 0:
        total = pr['sell_price'] * qty
        profit = (pr['sell_price'] - pr['cost_price']) * qty
        cur.execute("UPDATE products SET qty=qty-%s WHERE id=%s", (qty, pid))
        cur.execute("INSERT INTO sales (product_name, qty, total, profit, sale_date) VALUES (%s,%s,%s,%s,%s)", (pr['name'], qty, total, profit, date.today()))
        db.commit()
    cur.close(); db.close()
    return redirect("/stock")

@app.route("/add-stock/<int:pid>", methods=["POST"])
def add_stock(pid):
    qty = int(request.form.get("qty", 5))
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE products SET qty=qty+%s WHERE id=%s", (qty, pid))
    db.commit(); cur.close(); db.close()
    return redirect("/stock")

@app.route("/add", methods=["POST"])
def add():
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO products (name,sell_price,cost_price,qty) VALUES (%s,%s,%s,%s)",
                (request.form['name'], float(request.form['sell']), float(request.form['cost']), int(request.form['qty'])))
    db.commit(); cur.close(); db.close()
    return redirect("/stock")

@app.route("/history")
def history():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM products ORDER BY id ASC")
    products = cur.fetchall()
    cur.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 100")
    hist = cur.fetchall(); cur.close(); db.close()
    s,p,v = get_totals()
    return render_template_string(HTML, products=products, sales=s, profit=p, stock_value=v, history=hist)

@app.route("/delete/<int:pid>")
def delete(pid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (pid,)); db.commit(); cur.close(); db.close()
    return redirect("/stock")

@app.route("/edit/<int:pid>", methods=["GET","POST"])
def edit(pid):
    db = get_db(); cur = db.cursor()
    if request.method == "POST":
        cur.execute("UPDATE products SET name=%s, sell_price=%s, cost_price=%s, qty=%s WHERE id=%s",
                    (request.form['name'], float(request.form['sell']), float(request.form['cost']), int(request.form['qty']), pid))
        db.commit(); cur.close(); db.close()
        return redirect("/stock")
    cur.execute("SELECT * FROM products WHERE id=%s", (pid,))
    pr = cur.fetchone(); cur.close(); db.close()
    return f'''<h2>Edit {pr['name']}</h2><form method="POST">Name <input name="name" value="{pr['name']}"><br>
    Sell <input name="sell" value="{pr['sell_price']}"><br>Cost <input name="cost" value="{pr['cost_price']}"><br>
    Qty <input name="qty" value="{pr['qty']}"><br><button>Save</button></form>'''

@app.route("/end-day")
def end_day():
    s,p,v = get_totals()
    return f"<h1>End Of Day</h1><h2>Sales Today: R{s}</h2><h2>Profit Today: R{p}</h2><h2>Stock Value: R{v}</h2><br><a href='/stock'>Back to Shop</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
