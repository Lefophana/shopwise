import sqlite3, os, datetime
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
    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        conn.execute("INSERT INTO products (name,sell,cost,qty) VALUES ('Coke',20,14,18),('Bread',15,10,7),('Chips',12,8,40)")
    conn.commit()
    conn.close()

init_db()

HEADER = """
<div style="background:#ff6b35;color:white;padding:20px;text-align:center;">
<h1 style="margin:0;">🏪 ShopWise</h1><p style="margin:0;">Tembisa | Best Prices Daily</p>
</div>
<div style="background:#333;color:white;padding:10px;text-align:center;">
<a href="/" style="color:white;margin:10px;">🏠 Home</a>
<a href="/stock" style="color:white;margin:10px;">🛒 Shop</a>
<a href="/history" style="color:white;margin:10px;">📜 History</a>
<a href="/end_day" style="color:white;margin:10px;">📊 End Day</a>
</div>
"""

@app.route("/")
def home():
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    today = datetime.date.today().isoformat()
    s = conn.execute("SELECT COALESCE(SUM(total),0), COALESCE(SUM(profit),0), COUNT(*) FROM sales WHERE day=?", (today,)).fetchone()
    total = conn.execute("SELECT COALESCE(SUM(total),0), COALESCE(SUM(profit),0) FROM sales").fetchone()
    stock_val = sum(p['qty']*p['sell'] for p in products)
    conn.close()
    return f"""{HEADER}
    <div style="text-align:center;padding:30px;font-family:Arial;">
    <h2>Welcome to ShopWise! 👋</h2>
    <p>Your Shop in Tembisa - Open Today</p>
    <div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;">
    <div style="background:#d1ecf1;padding:20px;border-radius:10px;"><h3>🔥 Today Sales</h3><h2>R{int(s[0])}</h2></div>
    <div style="background:#d4edda;padding:20px;border-radius:10px;"><h3>💰 Today Profit</h3><h2>R{int(s[1])}</h2></div>
    <div style="background:#fff3cd;padding:20px;border-radius:10px;"><h3>📦 Stock Value</h3><h2>R{int(stock_val)}</h2></div>
    </div>
    <br>
    <div style="background:#e8f5e9;padding:15px;border-radius:10px;"><h3>🏆 ALL TIME: Sales R{int(total[0])} | Profit R{int(total[1])}</h3></div>
    <br>
    <a href="/stock"><button style="background:#ff6b35;color:white;padding:15px 30px;font-size:20px;border:none;border-radius:10px;">🛒 Go to Shop - Sell Now</button></a>
    <br><br>
    <a href="/history"><button style="background:#007bff;color:white;padding:12px 25px;border:none;border-radius:10px;">📜 See History</button></a>
    </div>
    """

@app.route("/stock")
def stock():
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    today = datetime.date.today().isoformat()
    s = conn.execute("SELECT COALESCE(SUM(total),0), COALESCE(SUM(profit),0) FROM sales WHERE day=?", (today,)).fetchone()
    stock_val = sum(p['qty']*p['sell'] for p in products)
    conn.close()
    rows=""
    for p in products:
        low = "<br>⚠️ LOW!" if p['qty']<=5 else ""
        rows+=f"""<tr><td>{p['name']}{low}</td><td>R{p['sell']}<br><small>Cost R{p['cost']}</small></td><td>{p['qty']}</td>
        <td><a href="/sell/{p['id']}"><button style="background:orange;padding:8px;">Sell 1</button></a></td>
        <td><a href="/add/{p['id']}"><button style="background:#007bff;color:white;padding:8px;">+5</button></a></td>
        <td><a href="/edit/{p['id']}"><button style="background:green;color:white;">Edit</button></a></td>
        <td><a href="/delete/{p['id']}"><button style="background:red;color:white;">Delete</button></a></td></tr>"""
    return f"""{HEADER}
    <div style="text-align:center;background:#d1ecf1;padding:15px;font-size:20px;">🔥 Sales: R{int(s[0])} | 💰 Profit: R{int(s[1])} | 📦 Stock: R{int(stock_val)}</div>
    <table border=1 width=100% style="text-align:center;font-size:18px;"><tr><th>Name</th><th>Price</th><th>Qty</th><th>Sell</th><th>+ Stock</th><th>Edit</th><th>Delete</th></tr>{rows}</table>
    <br><div style="background:orange;padding:20px;text-align:center;"><h3>Add New Product</h3>
    <form action="/add_product" method="post">Name <input name="name" required> Sell <input name="sell" type="number" required> Cost <input name="cost" type="number" required> Qty <input name="qty" type="number" required><button>Add</button></form></div>
    """

@app.route("/history")
def history():
    conn = get_db()
    rows_db = conn.execute("SELECT day, COUNT(*) as items, SUM(total) as sales, SUM(profit) as profit FROM sales GROUP BY day ORDER BY day DESC").fetchall()
    conn.close()
    rows=""
    for r in rows_db:
        rows+=f"<tr style='font-size:18px;'><td style='padding:10px;'>{r['day']}</td><td>{r['items']}</td><td>R{int(r['sales'])}</td><td style='color:green;font-weight:bold;'>R{int(r['profit'])}</td></tr>"
    if not rows_db:
        rows="<tr><td colspan=4>No sales yet</td></tr>"
    return f"""{HEADER}
    <div style="text-align:center;padding:20px;font-family:Arial;">
    <h1>📜 Sales History - Never Lost!</h1>
    <p>All your sales are saved forever, even if Render sleeps.</p>
    <table border=1 width=90% style="margin:auto;text-align:center;border-collapse:collapse;background:white;">
    <tr style="background:#ff6b35;color:white;"><th style="padding:10px;">Date</th><th>Items Sold</th><th>Sales</th><th>Profit</th></tr>{rows}</table>
    <br><a href="/"><button style="background:#ff6b35;color:white;padding:12px 25px;border:none;border-radius:10px;">🏠 Back Home</button></a>
    </div>
    """

@app.route("/sell/<int:pid>")
def sell(pid):
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
    conn.execute("UPDATE products SET qty=qty+5 WHERE id=?", (pid,))
    conn.commit(); conn.close()
    return redirect("/stock")

@app.route("/add_product", methods=["POST"])
def add_product():
    conn = get_db()
    conn.execute("INSERT INTO products (name,sell,cost,qty) VALUES (?,?,?,?)", (request.form['name'], float(request.form['sell']), float(request.form['cost']), int(request.form['qty'])))
    conn.commit(); conn.close()
    return redirect("/stock")

@app.route("/delete/<int:pid>")
def delete(pid):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit(); conn.close()
    return redirect("/stock")

@app.route("/edit/<int:pid>")
def edit(pid):
    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    conn.close()
    return f'''{HEADER}<div style="text-align:center;padding:20px;"><h2>Edit {p['name']}</h2><form action="/update/{pid}" method="post">Name <input name="name" value="{p['name']}"><br><br>Sell <input name="sell" value="{p['sell']}"><br><br>Cost <input name="cost" value="{p['cost']}"><br><br>Qty <input name="qty" value="{p['qty']}"><br><br><button>Save</button></form></div>'''

@app.route("/update/<int:pid>", methods=["POST"])
def update(pid):
    conn = get_db()
    conn.execute("UPDATE products SET name=?,sell=?,cost=?,qty=? WHERE id=?", (request.form['name'], float(request.form['sell']), float(request.form['cost']), int(request.form['qty']), pid))
    conn.commit(); conn.close()
    return redirect("/stock")

@app.route("/end_day")
def end_day():
    conn = get_db()
    today = datetime.date.today().isoformat()
    s = conn.execute("SELECT COALESCE(SUM(total),0), COALESCE(SUM(profit),0) FROM sales WHERE day=?", (today,)).fetchone()
    conn.close()
    return f"""{HEADER}<div style="text-align:center;padding:30px;"><h1>📊 End of Day - {today}</h1><h2>Sales: R{int(s[0])} | Profit: R{int(s[1])}</h2><p>Saved in History forever. Tomorrow starts new day.</p><a href="/"><button>🏠 Home</button></a></div>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
