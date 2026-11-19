import sqlite3, os
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
DB = "shop.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, sell REAL, cost REAL, qty INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product TEXT, profit REAL, total REAL, day TEXT)")
    # Add starter products only if empty
    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        conn.execute("INSERT INTO products (name,sell,cost,qty) VALUES ('Coke',20,14,18),('Bread',15,10,7),('Chips',12,8,40)")
    conn.commit()
    conn.close()

init_db()

HTML = """
<h1 style="text-align:center;background:#ff6b35;color:white;padding:20px;">🏪 ShopWise<br><small>Tembisa | Best Prices Daily</small></h1>
<div style="text-align:center;background:#d1ecf1;padding:15px;font-size:20px;">
🔥 Sales: R{{sales}} | 💰 Profit: R{{profit}} | 📦 Stock: R{{stock}}
<br><a href="/history">📜 History</a> | <a href="/end_day">📊 End Day</a> | <a href="/">Home</a>
</div>
<table border=1 width=100% style="text-align:center;font-size:18px;">
<tr><th>Name</th><th>Price</th><th>Qty</th><th>Sell</th><th>+ Stock</th><th>Edit</th><th>Delete</th></tr>
{% for p in products %}
<tr>
<td>{{p['name']}}{% if p['qty']<=5 %} <br>⚠️ LOW!{% endif %}</td>
<td>R{{p['sell']}}<br><small>Cost R{{p['cost']}}</small></td>
<td>{{p['qty']}}</td>
<td><a href="/sell/{{p['id']}}"><button style="background:orange;padding:8px;">Sell 1</button></a></td>
<td><a href="/add/{{p['id']}}"><button style="background:#007bff;color:white;padding:8px;">+5</button></a></td>
<td><a href="/edit/{{p['id']}}"><button style="background:green;color:white;">Edit</button></a></td>
<td><a href="/delete/{{p['id']}}"><button style="background:red;color:white;">Delete</button></a></td>
</tr>
{% endfor %}
</table>
<br><div style="background:orange;padding:20px;text-align:center;"><h3>Add New Product</h3>
<form action="/add_product" method="post">
Name <input name="name" required> Sell Price <input name="sell" type="number" required> Cost <input name="cost" type="number" required> Qty <input name="qty" type="number" required>
<button>Add</button></form></div>
"""

@app.route("/")
def home():
    return redirect("/stock")

@app.route("/stock")
def stock():
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    import datetime
    today = datetime.date.today().isoformat()
    s = conn.execute("SELECT COALESCE(SUM(total),0), COALESCE(SUM(profit),0) FROM sales WHERE day=?", (today,)).fetchone()
    stock_val = sum(p['qty']*p['sell'] for p in products)
    conn.close()
    return render_template_string(HTML, products=products, sales=int(s[0]), profit=int(s[1]), stock=int(stock_val))

@app.route("/sell/<int:pid>")
def sell(pid):
    import datetime
    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if p and p['qty']>0:
        conn.execute("UPDATE products SET qty=qty-1 WHERE id=?", (pid,))
        conn.execute("INSERT INTO sales (product,profit,total,day) VALUES (?,?,?,?)", (p['name'], p['sell']-p['cost'], p['sell'], datetime.date.today().isoformat()))
        conn.commit()
    conn.close()
    return redirect("/stock")

@app.route("/add/<int:pid>")
def add(pid):
    conn = get_db()
    conn.execute("UPDATE products SET qty=qty+5 WHERE id=?", (pid,)); conn.commit(); conn.close()
    return redirect("/stock")

@app.route("/add_product", methods=["POST"])
def add_product():
    conn = get_db()
    conn.execute("INSERT INTO products (name,sell,cost,qty) VALUES (?,?,?,?)", (request.form['name'], float(request.form['sell']), float(request.form['cost']), int(request.form['qty'])))
    conn.commit(); conn.close()
    return redirect("/stock")

@app.route("/delete/<int:pid>")
def delete(pid):
    conn = get_db(); conn.execute("DELETE FROM products WHERE id=?", (pid,)); conn.commit(); conn.close()
    return redirect("/stock")

@app.route("/edit/<int:pid>")
def edit(pid):
    conn = get_db(); p = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone(); conn.close()
    return f'''<h2>Edit {p['name']}</h2><form action="/update/{pid}" method="post">
    Name <input name="name" value="{p['name']}"><br>
    Sell <input name="sell" value="{p['sell']}"><br>
    Cost <input name="cost" value="{p['cost']}"><br>
    Qty <input name="qty" value="{p['qty']}"><br><button>Save</button></form>'''

@app.route("/update/<int:pid>", methods=["POST"])
def update(pid):
    conn = get_db(); conn.execute("UPDATE products SET name=?,sell=?,cost=?,qty=? WHERE id=?", (request.form['name'], float(request.form['sell']), float(request.form['cost']), int(request.form['qty']), pid)); conn.commit(); conn.close()
    return redirect("/stock")

@app.route("/history")
def history():
    conn = get_db()
    rows = conn.execute("SELECT day, COUNT(*) as items, SUM(total) as sales, SUM(profit) as profit FROM sales GROUP BY day ORDER BY day DESC").fetchall()
    conn.close()
    h = "<h1>📜 Sales History - Never Lost!</h1><a href='/stock'>Back</a><br><br><table border=1><tr><th>Date</th><th>Items Sold</th><th>Sales</th><th>Profit</th></tr>"
    for r in rows:
        h += f"<tr><td>{r['day']}</td><td>{r['items']}</td><td>R{int(r['sales'])}</td><td>R{int(r['profit'])}</td></tr>"
    h += "</table>"
    return h

@app.route("/end_day")
def end_day():
    import datetime
    conn = get_db()
    today = datetime.date.today().isoformat()
    s = conn.execute("SELECT COALESCE(SUM(total),0), COALESCE(SUM(profit),0) FROM sales WHERE day=?", (today,)).fetchone()
    conn.close()
    return f"<h1>📊 End of Day - {today}</h1><h2>Sales: R{int(s[0])} | Profit: R{int(s[1])}</h2><p>This is SAVED in History forever. Tomorrow starts new day.</p><a href='/stock'>Back to Shop</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
