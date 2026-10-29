from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json
import sqlite3
import os

DB_PATH = Path(__file__).with_name("canteen.db")

MENU = [
    ("Veggie hummus wrap", "Roasted vegetables, hummus, greens", 85, "🥙", "Mains", "Bestseller"),
    ("Dal rice bowl", "Dal, steamed rice, and salad", 95, "🍛", "Mains", "Plant-based"),
    ("Tomato pasta", "Whole wheat pasta with tomato and basil", 110, "🍝", "Mains", "Made fresh"),
    ("Chickpea salad bowl", "Chickpeas, cucumber, tomato, lemon dressing", 85, "🥗", "Mains", "High protein"),
    ("Vegetable pulao", "Fragrant rice, vegetables, and raita", 90, "🍚", "Mains", "Student favorite"),
    ("Seasonal fruit cup", "Fresh fruit from our local supplier", 45, "🍉", "Snacks", "Fresh today"),
    ("Paneer tikka roll", "Grilled paneer, mint chutney, and roti", 90, "🌯", "Snacks", "Popular"),
    ("Masala corn cup", "Sweet corn with lime and mild spices", 40, "🌽", "Snacks", "Quick bite"),
    ("Baked samosa", "Pastry with potato and pea filling", 35, "🥟", "Snacks", "Baked"),
    ("Lemon mint cooler", "Fresh lemon and mint drink", 35, "🍋", "Drinks", "Refreshing"),
    ("Mango lassi", "Yogurt blended with mango", 50, "🥭", "Drinks", "Made fresh"),
    ("Spiced buttermilk", "Chilled yogurt drink with cumin and mint", 30, "🥛", "Drinks", "Cooling favorite"),
]

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sprout Smart Canteen</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f5f7f2;color:#183127;font:15px Arial,sans-serif}
header{background:#124632;color:white;padding:18px 5%;display:flex;justify-content:space-between;align-items:center}
header h1{font-size:21px;margin:0}header span{color:#d9f27e;font-size:13px}
main{max-width:1100px;margin:28px auto;padding:0 20px}
nav{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap}
nav button,.filter button{border:1px solid #dce5dc;background:white;color:#496257;border-radius:9px;padding:10px 14px;cursor:pointer}
nav button.active,.filter button.active{background:#18794e;color:white;border-color:#18794e}
h2{font-size:21px;margin:0 0 8px}p.sub{color:#718077;margin:0 0 20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:14px}
.card{background:white;border:1px solid #e1e9e0;border-radius:14px;padding:16px}
.food-icon{font-size:36px}.tag{color:#18794e;font-size:11px;font-weight:bold}
.card h3{margin:10px 0 5px}.card p{color:#718077;font-size:13px;min-height:32px}
.row{display:flex;justify-content:space-between;align-items:center;gap:8px}
button.action{background:#18794e;color:white;border:0;border-radius:8px;padding:9px 12px;cursor:pointer}
button.action:hover{background:#124632}
.panel{background:white;border:1px solid #e1e9e0;border-radius:14px;padding:18px;margin-bottom:15px}
input,select{padding:10px;border:1px solid #dce5dc;border-radius:8px;margin:5px 0 12px;width:100%}
label{font-size:13px;font-weight:bold}
table{border-collapse:collapse;width:100%;background:white}
th,td{text-align:left;padding:11px;border-bottom:1px solid #e8eee7;font-size:13px}
th{color:#718077} .notice{padding:12px;border-radius:10px;background:#edf5d8;color:#4b6136;font-size:13px}
.hidden{display:none}.cartline{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #e8eee7}
@media(max-width:600px){header{padding:15px}main{padding:0 13px}.card p{min-height:0}}
</style>
</head>
<body>
<header><h1>✳ Sprout <span>SMART CANTEEN</span></h1><span>Greenfield Academy · Demo</span></header>
<main>
  <nav>
    <button class="active" onclick="show('menu',this)">Order food</button>
    <button onclick="show('orders',this)">Orders</button>
    <button onclick="show('waste',this)">Waste tracker</button>
  </nav>

  <section id="menu">
    <h2>Today's menu</h2><p class="sub">Choose a category, add food to your cart, and place a demo order.</p>
    <div class="filter" style="display:flex;gap:7px;flex-wrap:wrap;margin-bottom:15px">
      <button class="active" onclick="filterMenu('All',this)">All items</button>
      <button onclick="filterMenu('Mains',this)">Mains</button>
      <button onclick="filterMenu('Snacks',this)">Snacks</button>
      <button onclick="filterMenu('Drinks',this)">Drinks</button>
    </div>
    <div id="food-list" class="cards"></div>
    <div class="panel" style="margin-top:18px">
      <div class="row"><strong>Your cart</strong><strong id="cart-total">₹0</strong></div>
      <div id="cart-list"></div>
      <label for="student">Student name</label><input id="student" value="Demo Student">
      <label for="pickup">Pickup time</label>
      <select id="pickup"><option>12:30 PM</option><option>12:40 PM</option><option>12:50 PM</option><option>1:00 PM</option></select>
      <button class="action" onclick="placeOrder()">Place demo order</button>
      <p class="sub" style="font-size:11px;margin:10px 0 0">No payment is taken in this prototype.</p>
    </div>
  </section>

  <section id="orders" class="hidden">
    <h2>Recent orders</h2><p class="sub">Orders saved in the local SQLite database.</p>
    <div class="panel"><div id="order-list"></div></div>
  </section>

  <section id="waste" class="hidden">
    <h2>Waste tracker</h2><p class="sub">Log kitchen waste by item and category.</p>
    <div class="panel">
      <label for="w-item">Food item</label><input id="w-item" placeholder="e.g. Rice and lentils">
      <label for="w-category">Category</label>
      <select id="w-category"><option>Plate leftovers</option><option>Prep scraps</option><option>Unsold surplus</option></select>
      <label for="w-quantity">Quantity (kg)</label><input id="w-quantity" type="number" min="0.1" step="0.1" placeholder="e.g. 0.6">
      <button class="action" onclick="logWaste()">Save waste entry</button>
    </div>
    <div class="panel"><div class="row"><strong>Recent entries</strong><strong id="waste-total">0 kg</strong></div>
      <div style="overflow:auto"><table><thead><tr><th>Food</th><th>Category</th><th>Quantity</th><th>Logged by</th><th>Time</th></tr></thead><tbody id="waste-list"></tbody></table></div>
    </div>
  </section>
</main>
<script>
let menu=[], cart=[], selectedCategory="All";
async function api(path, options={}) {
  const response=await fetch("/api"+path,{headers:{"Content-Type":"application/json"},...options});
  const data=await response.json();
  if(!response.ok) throw new Error(data.error||"Request failed");
  return data;
}
function show(id,button){
  document.querySelectorAll("main>section").forEach(s=>s.classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  document.querySelectorAll("nav button").forEach(b=>b.classList.remove("active"));
  button.classList.add("active");
  if(id==="orders") loadOrders();
  if(id==="waste") loadWaste();
}
function filterMenu(category,button){
  selectedCategory=category;
  document.querySelectorAll(".filter button").forEach(b=>b.classList.remove("active"));
  button.classList.add("active");
  drawMenu();
}
function drawMenu(){
  const foods=menu.filter(item=>selectedCategory==="All"||item.category===selectedCategory);
  document.getElementById("food-list").innerHTML=foods.map(item=>
    `<article class="card"><div class="food-icon">${item.emoji}</div>
    <div class="tag">${item.tag}</div><h3>${item.name}</h3><p>${item.description}</p>
    <div class="row"><strong>₹${item.price}</strong><button class="action" onclick="addToCart(${item.id})">＋ Add</button></div></article>`
  ).join("");
}
function addToCart(id){
  const item=menu.find(x=>x.id===id), line=cart.find(x=>x.id===id);
  if(line) line.quantity++; else cart.push({...item,quantity:1});
  drawCart();
}
function drawCart(){
  const total=cart.reduce((sum,x)=>sum+x.price*x.quantity,0);
  document.getElementById("cart-total").textContent="₹"+total;
  document.getElementById("cart-list").innerHTML=cart.map(x=>
    `<div class="cartline"><span>${x.emoji} ${x.name} × ${x.quantity}</span><strong>₹${x.price*x.quantity}</strong></div>`
  ).join("");
}
async function placeOrder(){
  try{
    const result=await api("/orders",{method:"POST",body:JSON.stringify({
      student:document.getElementById("student").value,
      pickup:document.getElementById("pickup").value,
      items:cart.map(x=>({menu_id:x.id,quantity:x.quantity}))
    })});
    cart=[];drawCart();alert(`Order #${result.id} saved. Total: ₹${result.total}`);
  }catch(error){alert(error.message)}
}
async function loadOrders(){
  const rows=await api("/orders");
  document.getElementById("order-list").innerHTML=rows.length?rows.map(o=>
    `<div class="cartline"><span><b>#${o.id}</b> · ${o.items.map(i=>i.name+" × "+i.quantity).join(", ")}<br><small>${o.student} · Pickup ${o.pickup}</small></span><strong>₹${o.total}</strong></div>`
  ).join(""):"No orders yet.";
}
async function logWaste(){
  try{
    await api("/waste",{method:"POST",body:JSON.stringify({
      item:document.getElementById("w-item").value,
      category:document.getElementById("w-category").value,
      quantity:document.getElementById("w-quantity").value,
      logged_by:"Canteen team"
    })});
    document.getElementById("w-item").value="";
    document.getElementById("w-quantity").value="";
    await loadWaste();alert("Waste entry saved.");
  }catch(error){alert(error.message)}
}
async function loadWaste(){
  const rows=await api("/waste");
  const total=rows.reduce((sum,x)=>sum+Number(x.quantity),0);
  document.getElementById("waste-total").textContent=total.toFixed(1)+" kg";
  document.getElementById("waste-list").innerHTML=rows.map(x=>
    `<tr><td>${x.item}</td><td>${x.category}</td><td>${Number(x.quantity).toFixed(1)} kg</td><td>${x.logged_by}</td><td>${x.created_at}</td></tr>`
  ).join("");
}
async function init(){
  menu=await api("/menu");drawMenu();drawCart();
}
init().catch(error=>alert("Could not load the app: "+error.message));
</script>
</body></html>
"""

def init_database():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS menu(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                category TEXT NOT NULL,
                tag TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student TEXT NOT NULL,
                pickup TEXT NOT NULL,
                total INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS order_items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                menu_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price INTEGER NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS waste(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity REAL NOT NULL,
                logged_by TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.executemany(
            """INSERT OR IGNORE INTO menu
            (name,description,price,emoji,category,tag) VALUES(?,?,?,?,?,?)""",
            MENU,
        )

class AppHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body=json.dumps(data,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length=int(self.headers.get("Content-Length","0"))
        if length>20000:
            raise ValueError("Request is too large.")
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        route=urlparse(self.path).path
        if route=="/":
            body=PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif route=="/api/menu":
            with sqlite3.connect(DB_PATH) as db:
                db.row_factory=sqlite3.Row
                rows=db.execute("SELECT * FROM menu ORDER BY id").fetchall()
            self.send_json([dict(row) for row in rows])
        elif route=="/api/orders":
            with sqlite3.connect(DB_PATH) as db:
                db.row_factory=sqlite3.Row
                orders=[dict(row) for row in db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 30")]
                for order in orders:
                    order["items"]=[dict(row) for row in db.execute(
                        "SELECT name,quantity,unit_price FROM order_items WHERE order_id=?",
                        (order["id"],),
                    )]
            self.send_json(orders)
        elif route=="/api/waste":
            with sqlite3.connect(DB_PATH) as db:
                db.row_factory=sqlite3.Row
                rows=db.execute("SELECT * FROM waste ORDER BY id DESC LIMIT 50").fetchall()
            self.send_json([dict(row) for row in rows])
        else:
            self.send_json({"error":"Not found"},404)

    def do_POST(self):
        route=urlparse(self.path).path
        try:
            data=self.read_json()
            if route=="/api/orders":
                student=str(data.get("student","")).strip()[:60]
                pickup=str(data.get("pickup","")).strip()[:40]
                items=data.get("items",[])
                if not student or not pickup or not isinstance(items,list) or not items:
                    raise ValueError("Enter a name, pickup time, and at least one item.")

                with sqlite3.connect(DB_PATH) as db:
                    total=0
                    checked=[]
                    for item in items:
                        menu_id=int(item.get("menu_id",0))
                        quantity=int(item.get("quantity",0))
                        row=db.execute("SELECT id,name,price FROM menu WHERE id=?",(menu_id,)).fetchone()
                        if row is None or not 1<=quantity<=10:
                            raise ValueError("A menu item or quantity is invalid.")
                        total+=row[2]*quantity
                        checked.append((row,quantity))
                    cur=db.execute(
                        "INSERT INTO orders(student,pickup,total) VALUES(?,?,?)",
                        (student,pickup,total),
                    )
                    for row,quantity in checked:
                        db.execute(
                            """INSERT INTO order_items(order_id,menu_id,name,quantity,unit_price)
                            VALUES(?,?,?,?,?)""",
                            (cur.lastrowid,row[0],row[1],quantity,row[2]),
                        )
                self.send_json({"ok":True,"id":cur.lastrowid,"total":total},201)

            elif route=="/api/waste":
                item=str(data.get("item","")).strip()[:100]
                category=str(data.get("category","")).strip()[:40]
                quantity=float(data.get("quantity",0))
                if not item or not category or not 0<quantity<=1000:
                    raise ValueError("Enter a food item and a quantity greater than 0 kg.")
                with sqlite3.connect(DB_PATH) as db:
                    db.execute(
                        "INSERT INTO waste(item,category,quantity,logged_by) VALUES(?,?,?,?)",
                        (item,category,quantity,"Canteen team"),
                    )
                self.send_json({"ok":True},201)
            else:
                self.send_json({"error":"Not found"},404)

        except (ValueError,TypeError,json.JSONDecodeError) as error:
            self.send_json({"error":str(error)},400)

    def log_message(self, format, *args):
        print("%s - %s" % (self.log_date_time_string(), format % args))

if __name__=="__main__":
    init_database()
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), AppHandler)
    print(f"Smart Canteen running on port {port}")
    print("Press Control+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()