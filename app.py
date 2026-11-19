import sqlite3, os
from flask import Flask, request, redirect, g

app = Flask(__name__)
DB = "shop.db"

def get_db():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(e):
    db = getattr(g, '_db', None)
    if db: db.close()

def init_db():
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sell_price REAL, cost_price REAL, qty INTEGER)")
    db.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, qty INTEGER, total REAL, date TEXT DEFAULT CURRENT_TIMESTAMP)")
    db.commit(); db.close()
init_db()

def get_totals():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT COALESCE(SUM(qty*sell_price),0) as s, COALESCE(SUM(qty*cost_price),0) as c, COALESCE(SUM(qty),0) as q FROM products")
    r = cur.fetchone()
    sales = r['s'] or 0
    profit = sales - (r['c'] or 0)
    value = r['c'] or 0
    return sales, profit, value

STYLE = """
<style>
body{font-family:Arial;background:#f0f2f5;margin:0;padding:15px}
.top{background:#16a34a;color:white;padding:20px;border-radius:15px;text-align:center}
.top h1{margin:0;font-size:28px}
.cards{display:flex;gap:10px;margin:15px 0}
.card{flex:1;background:white;padding:15px;border-radius:12px;text-align:center;box-shadow:0 2px 5px #ccc}
.card b{font-size:22px;display:block}
.green{color:#16a34a}.blue{color:#2563eb}.orange{color:#ea580c}
.box{background:white;padding:15px;border-radius:12px;margin-top:15px;box-shadow:0 2px 5px #ccc}
input{width:100%;padding:10px;margin:5px 0;border:1px solid #ddd;border-radius:8px;box-sizing:border-box}
.btn{background:#16a34a;color:white;border:none;padding:12px;width:100%;border-radius:10px;font-size:16px;font-weight:bold}
.btn2{background:#2563eb;color:white;padding:8px 12px;border-radius:8px;text-decoration:none;display:inline-block;margin:2px}
.btn3{background:#ea580c;color:white;padding:8px 12px;border-radius:8px;text-decoration:none;display:inline-block;margin:2px}
.btn4{background:#dc2626;color:white;padding:8px 12px;border-radius:8px;text-decoration:none;display:inline-block;margin:2px}
.item{background:white;padding:12px;border-radius:12px;margin:10px 0;box-shadow:0 2px 5px #ccc}
a{color:#2563eb}
</style>
"""

@app.route("/")
def home():
    s,p,v = get_totals()
    return f'''{STYLE}<div class="top"><h1>🛒 ShopWise</h1><p>Your Shop, Made Simple</p></div><div class="cards"><div class="card">Sales Today<b class="green">R{s:.2f}</b></div><div class="card">Profit Today<b class="blue">R{p:.2f}</b></div><div class="card">Stock Value<b class="orange">R{v:.2f}</b></div></div><div class="box"><a class="btn2" href="/stock">📦 Go to Stock</a> <a class="btn2" href="/end-day">📊 End of Day</a></div><div class="box"><h3>➕ Add Product</h3><form method="POST" action="/add">Name<input name="name" placeholder="e.g Bread"><br>Sell Price<input name="sell" type="number" step="0.01" placeholder="20"><br>Cost Price<input name="cost" type="number" step="0.01" placeholder="12"><br>Qty<input name="qty" type="number" placeholder="10"><br><button class="btn">Add Product</button></form></div>'''

@app.route("/add", methods=["POST"])
def add():
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO products (name,sell_price,cost_price,qty) VALUES (?,?,?,?)",(request.form['name'],float(request.form['sell']),float(request.form['cost']),int(request.form['qty'])))
    db.commit(); cur.close()
    return redirect("/stock")

@app.route("/stock")
def stock():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    s,p,v = get_totals()
    h = f'''{STYLE}<div class="top"><h1>📦 My Stock</h1></div><div class="cards"><div class="card">Sales<b class="green">R{s:.2f}</b></div><div class="card">Profit<b class="blue">R{p:.2f}</b></div><div class="card">Stock<b class="orange">R{v:.2f}</b></div></div><a class="btn2" href="/">⬅ Back Home</a> <a class="btn2" href="/end-day">📊 End of Day</a>'''
    for r in rows:
        h += f'''<div class="item"><b>{r['name']}</b><br>Sell: R{r['sell_price']} | Cost: R{r['cost_price']} | Qty: {r['qty']}<br><br><a class="btn2" href="/sell/{r['id']}">💰 Sell 1</a> <a class="btn3" href="/edit/{r['id']}">✏️ Edit</a> <a class="btn4" href="/delete/{r['id']}">🗑️ Delete</a></div>'''
    if not rows:
        h += '<div class="box">No products yet. Go home and add one!</div>'
    return h

@app.route("/sell/<int:pid>")
def sell(pid):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM products WHERE id=?",(pid,))
    pr = cur.fetchone()
    if pr and pr['qty']>0:
        cur.execute("UPDATE products SET qty=qty-1 WHERE id=?",(pid,))
        cur.execute("INSERT INTO sales (product_id,qty,total) VALUES (?,?,?)",(pid,1,pr['sell_price']))
        db.commit()
    cur.close()
    return redirect("/stock")

@app.route("/delete/<int:pid>")
def delete(pid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM products WHERE id=?",(pid,)); db.commit(); cur.close()
    return redirect("/stock")

@app.route("/edit/<int:pid>", methods=["GET","POST"])
def edit(pid):
    db = get_db(); cur = db.cursor()
    if request.method=="POST":
        cur.execute("UPDATE products SET name=?, sell_price=?, cost_price=?, qty=? WHERE id=?",(request.form['name'],float(request.form['sell']),float(request.form['cost']),int(request.form['qty']),pid))
        db.commit(); cur.close()
        return redirect("/stock")
    cur.execute("SELECT * FROM products WHERE id=?",(pid,))
    pr = cur.fetchone(); cur.close()
    return f'''{STYLE}<div class="top"><h1>✏️ Edit {pr['name']}</h1></div><div class="box"><form method="POST">Name<input name="name" value="{pr['name']}"><br>Sell<input name="sell" value="{pr['sell_price']}"><br>Cost<input name="cost" value="{pr['cost_price']}"><br>Qty<input name="qty" value="{pr['qty']}"><br><button class="btn">Save Changes</button></form></div>'''

@app.route("/end-day")
def end_day():
    s,p,v = get_totals()
    return f'''{STYLE}<div class="top"><h1>📊 End Of Day</h1></div><div class="box" style="text-align:center"><h2>Sales Today: <span class="green">R{s:.2f}</span></h2><h2>Profit Today: <span class="blue">R{p:.2f}</span></h2><h2>Stock Value: <span class="orange">R{v:.2f}</span></h2><br><a class="btn2" href="/">⬅ Back Home</a> <a class="btn2" href="/stock">📦 Stock</a></div>'''

if __name__=="__main__":
    app.run(debug=True)
