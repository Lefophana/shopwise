from flask import Flask, request, redirect, render_template_string, jsonify
from datetime import datetime
import json, os

app = Flask(__name__)
FILE = "shop_data.json"

if os.path.exists(FILE):
    with open(FILE) as f:
        data = json.load(f)
        products = data.get("products", [])
        history = data.get("history", [])
        total_sales = data.get("total_sales", 0)
        total_profit = data.get("total_profit", 0)
        for p in products:
            if "cost" not in p:
                p["cost"] = int(p["price"] * 0.7)
else:
    products = [
        {"name": "Coke", "price": 20, "cost": 14, "qty": 8},
        {"name": "Bread", "price": 15, "cost": 10, "qty": 7},
        {"name": "Chips", "price": 12, "cost": 8, "qty": 40},
    ]
    history = []
    total_sales = 0
    total_profit = 0

def save():
    with open(FILE, "w") as f:
        json.dump({"products": products, "history": history, "total_sales": total_sales, "total_profit": total_profit}, f)

HEADER = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#ff6b00">
<meta name="mobile-web-app-capable" content="yes">
<link rel="manifest" href="/manifest.json">
<div style="background:#ff6b00; color:white; text-align:center; padding:20px; border-radius:10px; font-family:Arial">
<h1 style="margin:0; font-size:35px">🏪 ShopWise</h1>
<p style="margin:0">Tembisa | Best Prices Daily</p>
</div>
"""

@app.route("/manifest.json")
def manifest():
    return jsonify({"name": "ShopWise", "short_name": "ShopWise", "start_url": "/", "display": "standalone", "background_color": "#ff6b00", "theme_color": "#ff6b00"})

@app.route("/")
def home():
    html = HEADER + """
    <div style="background:#ff6b00; color:white; text-align:center; padding:40px 20px; border-radius:10px; margin-top:20px; font-family:Arial">
    <h1 style="font-size:40px; margin:0">Welcome to<br>ShopWise</h1>
    <p style="font-size:20px">Tembisa | Best Prices Daily</p><br>
    <a href="/stock"><button style="background:white; color:#ff6b00; padding:20px 40px; font-size:22px; border:none; border-radius:15px; cursor:pointer; width:100%"><b>🛒 Open My Shop</b></button></a>
    <br><br><a href="/history" style="color:white; font-size:20px">📜 See Sales History</a>
    <br><br><a href="/end_day" style="color:white; font-size:20px">🌙 End Day Report</a>
    </div>
    """
    return render_template_string(html)

@app.route("/stock")
def stock():
    stock_value = sum(p["price"] * p["qty"] for p in products)
    html = HEADER + """
    <div style="font-family:Arial; max-width:900px; margin:auto; padding:10px">
    <div style="background:#add8e6; text-align:center; padding:15px; margin:10px 0; border-radius:10px; font-size:20px">
    <b>🔥 Today Sales: R{{total}} | 💰 Today Profit: R{{profit}} | 📦 Stock: R{{value}}</b><br>
    <a href="/history">📜 History</a> | <a href="/">🏠 Home</a> | <a href="/end_day" style="color:red"><b>🌙 End Day</b></a>
    </div>
    <table border="1" style="width:100%; border-collapse:collapse; text-align:center; font-size:20px">
    <tr style="background:black; color:white"><th style="padding:15px">Name</th><th style="padding:15px">Price</th><th style="padding:15px">Qty</th><th style="padding:15px">Sell</th><th style="padding:15px">+ Stock</th><th style="padding:15px">Delete</th></tr>
    {% for p in products %}
    <tr style="{% if p.qty <= 3 %}background:#ffcccc{% endif %}">
    <td style="padding:15px; font-weight:bold">{{p.name}} {% if p.qty <= 3 %}<br><span style="color:red; font-size:14px">⚠️ LOW! BUY MORE</span>{% endif %}</td>
    <td style="padding:15px">R{{p.price}}<br><span style="font-size:13px; color:grey">Cost R{{p.cost}}</span></td>
    <td style="padding:15px; font-weight:bold; font-size:22px; {% if p.qty <= 3 %}color:red{% endif %}">{{p.qty}}</td>
    <td style="padding:10px"><a href="/sell/{{loop.index0}}"><button style="background:orange; padding:15px 18px; font-size:18px; border:none; border-radius:10px; cursor:pointer"><b>Sell 1</b></button></a></td>
    <td style="padding:10px"><a href="/restock/{{loop.index0}}"><button style="background:#0066ff; color:white; padding:15px 18px; font-size:18px; border:none; border-radius:10px; cursor:pointer"><b>+ 5</b></button></a></td>
    <td style="padding:10px"><a href="/delete/{{loop.index0}}"><button style="background:red; color:white; padding:15px 18px; font-size:18px; border:none; border-radius:10px; cursor:pointer"><b>Delete</b></button></a></td>
    </tr>
    {% endfor %}
    </table>
    <div style="background:#ff6b00; padding:20px; margin-top:20px; border-radius:10px; text-align:center; color:white">
    <h3 style="font-size:25px">Add New Product</h3>
    <form action="/add" method="post">
    Name: <input name="name" required style="padding:12px; font-size:18px; width:80%; margin-bottom:10px"><br>
    Sell Price: <input name="price" type="number" required style="padding:12px; font-size:18px; width:80%; margin-bottom:10px"><br>
    Cost Price: <input name="cost" type="number" required placeholder="What you paid" style="padding:12px; font-size:18px; width:80%; margin-bottom:10px"><br>
    Qty: <input name="qty" type="number" required style="padding:12px; font-size:18px; width:80%; margin-bottom:10px"><br>
    <button style="background:green; color:white; width:100%; padding:15px; font-size:20px; border:none; border-radius:10px">Add Product</button>
    </form>
    </div>
    </div>
    """
    return render_template_string(html, total=total_sales, profit=total_profit, value=stock_value, products=products)

@app.route("/sell/<int:i>")
def sell(i):
    global total_sales, total_profit
    if products[i]["qty"] > 0:
        products[i]["qty"] -= 1
        total_sales += products[i]["price"]
        total_profit += (products[i]["price"] - products[i].get("cost", 0))
        now = datetime.now().strftime("%H:%M %d/%m")
        history.append(f"{now} - {products[i]['name']} - Sold R{products[i]['price']} | Profit R{products[i]['price'] - products[i].get('cost',0)}")
        save()
    return redirect("/stock")

@app.route("/restock/<int:i>")
def restock(i):
    products[i]["qty"] += 5
    save()
    return redirect("/stock")

@app.route("/delete/<int:i>")
def delete(i):
    products.pop(i)
    save()
    return redirect("/stock")

@app.route("/add", methods=["POST"])
def add():
    products.append({"name": request.form["name"], "price": int(request.form["price"]), "cost": int(request.form["cost"]), "qty": int(request.form["qty"])})
    save()
    return redirect("/stock")

@app.route("/history")
def show_history():
    html = HEADER + """
    <div style="font-family:Arial; max-width:900px; margin:auto; text-align:center; padding:10px">
    <h2>📜 Sales History</h2>
    <h3>💰 Today Profit: R{{profit}} | 🔥 Today Sales: R{{total}}</h3>
    <a href="/stock">⬅ Back to Stock</a> | <a href="/">🏠 Home</a> | <a href="/end_day">🌙 End Day</a><br><br>
    {% if history %}
        {% for h in history %}<p style="background:#eee; padding:15px; border-radius:5px; font-size:18px">{{h}}</p>{% endfor %}
    {% else %}<p>No sales yet</p>{% endif %}
    </div>
    """
    return render_template_string(html, history=history, profit=total_profit, total=total_sales)

@app.route("/end_day")
def end_day():
    html = HEADER + """
    <div style="font-family:Arial; max-width:900px; margin:auto; text-align:center; padding:20px">
    <h1>🌙 End Of Day Report</h1>
    <div style="background:#add8e6; padding:30px; border-radius:15px; font-size:24px">
    <b>Today Sales: R{{total}}</b><br><br>
    <b>Today Profit: R{{profit}}</b><br><br>
    <b>Items Left in Stock: {{count}}</b>
    </div><br>
    <p style="font-size:18px">This will reset Today Sales to R0 for tomorrow,<br>but History will stay saved.</p>
    <a href="/confirm_end_day"><button style="background:red; color:white; padding:20px 40px; font-size:22px; border:none; border-radius:15px; width:100%">✅ YES, END DAY & START TOMORROW</button></a>
    <br><br><a href="/stock" style="font-size:18px">⬅ No, Go Back</a>
    </div>
    """
    return render_template_string(html, total=total_sales, profit=total_profit, count=sum(p["qty"] for p in products))

@app.route("/confirm_end_day")
def confirm_end_day():
    global total_sales, total_profit
    now = datetime.now().strftime("%d/%m %H:%M")
    history.append(f"===== 🌙 END OF DAY {now} - Sales R{total_sales} | Profit R{total_profit} =====")
    total_sales = 0
    total_profit = 0
    save()
    return redirect("/stock")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)