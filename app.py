import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, redirect, g

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return db

@app.teardown_appcontext
def close_db(e):
    db = getattr(g, '_db', None)
    if db: db.close()

def init_db():
    try:
        db = psycopg2.connect(DATABASE_URL)
        cur = db.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name TEXT, sell_price REAL, cost_price REAL, qty INTEGER, photo TEXT DEFAULT '')")
        cur.execute("CREATE TABLE IF NOT EXISTS sales (id SERIAL PRIMARY KEY, product_id INTEGER, qty INTEGER, total REAL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        db.commit(); cur.close(); db.close()
    except Exception as e:
        print("DB init error:", e)

init_db()

def totals():
    try:
        db = get_db(); cur = db.cursor()
        cur.execute("SELECT COALESCE(SUM(qty*sell_price),0) as s, COALESCE(SUM(qty*cost_price),0) as c FROM products")
        r = cur.fetchone()
        sales = r['s'] or 0
        profit = sales - (r['c'] or 0)
        cur.execute("SELECT COALESCE(SUM(total),0) as t FROM sales")
        today_sales = cur.fetchone()['t'] or 0
        return today_sales, profit, r['c'] or 0
    except:
        return 0,0,0

def get_photo(name, photo):
    if photo and photo.strip():
        return f'<img src="{photo}" style="width:60px;height:60px;object-fit:cover;border-radius:8px">'
    n = name.lower()
    if 'coke' in n or 'cola' in n or 'drink' in n or 'juice' in n: return '<div style="font-size:40px">🥤</div>'
    if 'chip' in n or 'crisp' in n: return '<div style="font-size:40px">🍟</div>'
    if 'bread' in n: return '<div style="font-size:40px">🍞</div>'
    if 'milk' in n: return '<div style="font-size:40px">🥛</div>'
    if 'egg' in n: return '<div style="font-size:40px">🥚</div>'
    if 'choco' in n or 'sweet' in n or 'candy' in n: return '<div style="font-size:40px">🍫</div>'
    if 'soap' in n: return '<div style="font-size:40px">🧼</div>'
    if 'rice' in n or 'meal' in n or 'pap' in n: return '<div style="font-size:40px">🍚</div>'
    return '<div style="font-size:40px">🛒</div>'

STYLE = """
<style>
*{box-sizing:border-box}
body{font-family:Arial;margin:0;background:#f5f5f5}
.header{background:#e65100;color:white;text-align:center;padding:15px}
.header h1{margin:0;font-size:28px}
.header p{margin:2px}
.nav{background:#111;color:white;text-align:center;padding:10px}
.nav a{color:white;text-decoration:none;margin:0 15px;font-weight:bold}
.wrap{max-width:1000px;margin:auto;padding:15px}
.cards{display:flex;gap:10px}
.card{flex:1;background:#d6f0ff;padding:15px;border-radius:8px;text-align:center}
.card b{font-size:20px;display:block}
.topbar{background:#8ecdf5;padding:10px;text-align:center;font-weight:bold;margin:15px 0}
.searchbox{background:white;padding:15px;text-align:center;border:2px solid #e65100;border-radius:8px;margin:15px 0}
.searchbox input{padding:10px;width:70%;font-size:16px;border:1px solid #999;border-radius:5px}
.searchbox button{padding:10px 20px;background:#e65100;color:white;border:none;font-size:16px;font-weight:bold;border-radius:5px;cursor:pointer}
table{width:100%;border-collapse:collapse;background:white;table-layout:fixed}
th,td{border:1px solid #999;padding:10px;text-align:center;word-wrap:break-word}
th{background:#f0f0f0}
.btn-sell{background:#e65100;color:white;border:none;padding:8px 14px;cursor:pointer}
.btn-add5{background:#2563eb;color:white;border:none;padding:8px 14px;cursor:pointer}
.btn-edit{background:#111;color:white;border:none;padding:6px 12px;cursor:pointer}
.btn-del{background:#dc2626;color:white;border:none;padding:6px 12px;cursor:pointer}
.addbox{background:#f59e0b;padding:20px;text-align:center;margin-top:15px}
.addbox input{padding:7px;width:150px;margin:2px}
.addbox button{padding:7px 14px}
.low{color:#dc2626;font-weight:bold;font-size:13px}
.box{background:white;padding:20px;border-radius:8px;text-align:center}
.bigbtn{background:#e65100;color:white;padding:12px 25px;border:none;font-size:16px;font-weight:bold;cursor:pointer}
</style>
"""

NAV = '<div class="header"><h1>🛒 ShopWise</h1><p>Tembisa | Best Prices Daily</p></div><div class="nav"><a href="/">🏠 Home</a><a href="/shop">🛒 Shop</a><a href="/history">📜 History</a><a href="/end-day">📊 End Day</a></div>'

@app.route("/")
def home():
    s,p,stock = totals()
    return f'''{STYLE}{NAV}<div class="wrap"><div style="text-align:center"><h2>Welcome to ShopWise! 👋</h2><p>Your Shop in Tembisa - Open Today</p></div><div class="cards"><div class="card">🔥 Today Sales<b>R{s:.0f}</b></div><div class="card">💰 Today Profit<b>R{p:.0f}</b></div><div class="card">📦 Stock Value<b>R{stock:.0f}</b></div></div><div class="topbar">🔥 ALL TIME: Sales: R{s:.0f} | Profit: R{p:.0f}</div><div class="box"><form action="/shop"><button class="bigbtn">🛒 Go to Shop - Sell Now</button></form></div></div>'''

@app.route("/shop")
def shop():
    s,p,stock = totals()
    q = request.args.get("q","").strip()
    db = get_db(); cur = db.cursor()
    if q:
        cur.execute("SELECT * FROM products WHERE name ILIKE %s", ('%'+q+'%',))
    else:
        cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    h = f'''{STYLE}{NAV}<div class="wrap"><div class="topbar">🔥 Sales: R{s:.0f} | 💰 Profit: R{p:.0f} | 📦 Stock: R{stock:.0f}</div><div class="searchbox"><form method="GET" action="/shop"><input name="q" value="{q}" placeholder="🔍 Search product... e.g Coke, Chips, Bread"><button>Search</button></form>'''
    if q:
        h += f'<p>Showing results for: <b>{q}</b> - <a href="/shop">Clear Search ❌</a></p>'
    h += '</div><table><tr><th>Photo</th><th>Name</th><th>Price</th><th>Qty</th><th>Sell</th><th>+ Stock</th><th>Edit</th><th>Delete</th></tr>'
    for r in rows:
        low = '<br><span class="low">⚠️ LOW!</span>' if r['qty']<=5 else ''
        photo_html = get_photo(r['name'], r['photo'])
        h += f'''<tr><td>{photo_html}</td><td><b>{r['name']}</b>{low}</td><td>R{r['sell_price']:.1f}<br><small>Cost R{r['cost_price']:.1f}</small></td><td>{r['qty']}</td><td><form method="POST" action="/sell/{r['id']}"><button class="btn-sell">Sell 1</button></form></td><td><form method="POST" action="/addstock/{r['id']}"><button class="btn-add5">+5</button></form></td><td><a href="/edit/{r['id']}"><button class="btn-edit">Edit</button></a></td><td><form method="POST" action="/delete/{r['id']}"><button class="btn-del">Delete</button></form></td></tr>'''
    h += '</table>'
    if not rows:
        if q:
            h += f'<p style="text-align:center">No product found for "{q}" 😢</p>'
        else:
            h += '<p style="text-align:center">No products yet. Add below!</p>'
    h += f'''<div class="addbox"><h3>Add New Product</h3><form method="POST" action="/add">Name <input name="name" required> Sell <input name="sell" type="number" step="0.01" required> Cost <input name="cost" type="number" step="0.01" required> Qty <input name="qty" type="number" required><br><br>Photo Link (optional - leave empty for emoji) <input name="photo" style="width:300px" placeholder="Paste image link here"> <button>Add</button></form><p><small>Tip: If you leave Photo empty, we show 🥤 for Coke, 🍟 for Chips, 🍞 for Bread automatically!</small></p></div></div>'''
    return h

@app.route("/add", methods=["POST"])
def add():
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO products (name,sell_price,cost_price,qty,photo) VALUES (%s,%s,%s,%s,%s)",(request.form['name'],float(request.form['sell']),float(request.form['cost']),int(request.form['qty']),request.form.get('photo','')))
    db.commit(); cur.close()
    return redirect("/shop")

@app.route("/sell/<int:pid>", methods=["POST"])
def sell(pid):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM products WHERE id=%s",(pid,))
    pr = cur.fetchone()
    if pr and pr['qty']>0:
        cur.execute("UPDATE products SET qty=qty-1 WHERE id=%s",(pid,))
        cur.execute("INSERT INTO sales (product_id,qty,total) VALUES (%s,%s,%s)",(pid,1,pr['sell_price']))
        db.commit()
    cur.close()
    return redirect("/shop")

@app.route("/addstock/<int:pid>", methods=["POST"])
def addstock(pid):
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE products SET qty=qty+5 WHERE id=%s",(pid,)); db.commit(); cur.close()
    return redirect("/shop")

@app.route("/delete/<int:pid>", methods=["POST"])
def delete(pid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM products WHERE id=%s",(pid,)); db.commit(); cur.close()
    return redirect("/shop")

@app.route("/edit/<int:pid>", methods=["GET","POST"])
def edit(pid):
    db = get_db(); cur = db.cursor()
    if request.method=="POST":
        cur.execute("UPDATE products SET name=%s, sell_price=%s, cost_price=%s, qty=%s, photo=%s WHERE id=%s",(request.form['name'],float(request.form['sell']),float(request.form['cost']),int(request.form['qty']),request.form.get('photo',''),pid))
        db.commit(); cur.close()
        return redirect("/shop")
    cur.execute("SELECT * FROM products WHERE id=%s",(pid,))
    pr = cur.fetchone(); cur.close()
    photo_val = pr['photo'] or ''
    return f'''{STYLE}{NAV}<div class="wrap"><div class="box"><h2>Edit {pr['name']}</h2><form method="POST">Name <input name="name" value="{pr['name']}"><br><br>Sell <input name="sell" value="{pr['sell_price']}"><br><br>Cost <input name="cost" value="{pr['cost_price']}"><br><br>Qty <input name="qty" value="{pr['qty']}"><br><br>Photo Link <input name="photo" value="{photo_val}" style="width:300px"><br><br><button class="bigbtn">Save</button></form></div></div>'''

@app.route("/history")
def history():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT sales.*, products.name FROM sales LEFT JOIN products ON sales.product_id=products.id ORDER BY sales.id DESC LIMIT 50")
    rows = cur.fetchall()
    h = f'''{STYLE}{NAV}<div class="wrap"><div class="box"><h2>📜 Sales History</h2></div><table><tr><th>Product</th><th>Qty</th><th>Total</th><th>Date</th></tr>'''
    for r in rows:
        h += f"<tr><td>{r['name'] or 'Deleted'}</td><td>{r['qty']}</td><td>R{r['total']:.2f}</td><td>{r['date']}</td></tr>"
    h += '</table></div>'
    return h

@app.route("/end-day")
def end_day():
    s,p,stock = totals()
    return f'''{STYLE}{NAV}<div class="wrap"><div class="box"><h1>📊 End Of Day</h1><h2>Sales Today: R{s:.2f}</h2><h2>Profit Today: R{p:.2f}</h2><h2>Stock Value: R{stock:.2f}</h2><br><a href="/shop"><button class="bigbtn">Back to Shop</button></a></div></div>'''

if __name__=="__main__":
    app.run(debug=True)
