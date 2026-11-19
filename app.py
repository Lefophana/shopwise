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

@app.route("/")
def home():
    s,p,v = get_totals()
    return f'''<h1>ShopWise</h1><h2>Sales Today: R{s:.2f}</h2><h2>Profit Today: R{p:.2f}</h2><h2>Stock Value: R{v:.2f}</h2><hr><a href="/stock">Go to Stock</a> | <a href="/end-day">End of Day</a><hr><h3>Add Product</h3><form method="POST" action="/add">Name <input name="name"><br>Sell <input name="sell" type="number" step="0.01"><br>Cost <input name="cost" type="number" step="0.01"><br>Qty <input name="qty" type="number"><br><button>Add</button></form>'''

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
    h = f"<h1>Stock</h1><p>Sales: R{s:.2f} | Profit: R{p:.2f} | Stock Value: R{v:.2f}</p><a href='/'>Back to Shop</a><hr>"
    for r in rows:
        h += f"{r['name']} - Sell R{r['sell_price']} - Cost R{r['cost_price']} - Qty {r['qty']} <a href='/edit/{r['id']}'>Edit</a> <a href='/sell/{r['id']}'>Sell 1</a> <a href='/delete/{r['id']}'>Delete</a><br><br>"
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
    return f'''<h2>Edit {pr['name']}</h2><form method="POST">Name <input name="name" value="{pr['name']}"><br>Sell <input name="sell" value="{pr['sell_price']}"><br>Cost <input name="cost" value="{pr['cost_price']}"><br>Qty <input name="qty" value="{pr['qty']}"><br><button>Save</button></form>'''

@app.route("/end-day")
def end_day():
    s,p,v = get_totals()
    return f"<h1>End Of Day</h1><h2>Sales Today: R{s:.2f}</h2><h2>Profit Today: R{p:.2f}</h2><h2>Stock Value: R{v:.2f}</h2><br><a href='/stock'>Back to Shop</a>"

if __name__=="__main__":
    app.run(debug=True)
