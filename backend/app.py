from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime , timezone , timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# ตั้งค่า Offset สำหรับประเทศไทย
thailand_tz = timezone(timedelta(hours=7))

app = Flask(__name__)
# CORS ช่วยให้ Vue.js ที่รันคนละ Port (เช่น 5173) คุยกับ Flask (5000) ได้
CORS(app)

# ตั้งค่า Database SQLite (จะสร้างไฟล์ชื่อ magic_v2.db)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///magic_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)    

# --- คลาสแม่สำหรับเก็บเวลา ---
class TimestampMixin(object):
    # ใช้ lambda เพื่อให้คำนวณเวลาใหม่ทุกครั้งที่มีการบันทึกข้อมูล
    created_at = db.Column(db.DateTime, default=lambda:datetime.now(thailand_tz), nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda:datetime.now(thailand_tz), onupdate= lambda : datetime.now(thailand_tz) , nullable=True)
    is_deleted = db.Column(db.Boolean, default=False) # is_deleted (ถังขยะ): ใช้เมื่อเราต้องการ "ลบ" สินค้านั้นออกไปเลย (ไม่อยากเห็นอีกแล้ว)

# --- โครงสร้างฐานข้อมูล (Models) ---

class User(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    role = db.Column(db.String(20), default='staff')    
    image_url = db.Column(db.String(255), default="default-profile.png")
    
class Product(db.Model , TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer , default=0)
    category = db.Column(db.String(50))
    description = db.Column(db.String(255), nullable=True , default="No description")
    image_url = db.Column(db.String(255), default="default-profile.png")
    deleted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleter = db.relationship('User', foreign_keys=[deleted_by_id])
    is_active = db.Column(db.Boolean, default=True) # is_active (พักการขาย): ใช้เมื่อเราต้องการ "ซ่อน" สินค้าชั่วคราว แต่ข้อมูลยังเป็นสินค้าปกติอยู่


class Order(db.Model , TimestampMixin):
    id = db.Column(db.Integer , primary_key=True)
    total_price = db.Column(db.Numeric(10, 2) , nullable=False)
    items = db.relationship('OrderItem' , backref="order" , lazy=True)

class OrderItem(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_sale = db.Column(db.Numeric(10, 2), nullable=False)
    product = db.relationship('Product')

# --- Initialize Database ---
with app.app_context():
    db.create_all()

# --- API Routes ---
@app.route('/')
def index():
    return jsonify({
        "status": "online",
        "message": "Magic V2 API with Images & Timestamps is ready!",
        "server_time": datetime.now(thailand_tz).strftime('%Y-%m-%d %H:%M:%S')
    })

# API สำหรับสมัครสมาชิก
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 1. เช็คว่ามีข้อมูลส่งมาไหม
    if not data:
        return jsonify({"message": "No data provided"}), 400
        
    username = data.get('username', '').strip() # .strip() ช่วยตัดช่องว่างหัวท้ายออก
    password = data.get('password', '').strip()
    
    # 2. เช็คค่าว่าง (หัวใจหลักที่นายถาม)
    if not username or not password:
        return jsonify({"message": "Username and password cannot be empty"}), 400

    # 3. (แถม) เช็คความยาวขั้นต่ำ เพื่อความปลอดภัย
    if len(username) < 3 or len(password) < 6:
        return jsonify({"message": "Username min 3 chars, Password min 6 chars"}), 400
    
    # 4. เช็คว่าชื่อซ้ำไหม (เหมือนเดิม)
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists"}), 400
    
    # ถ้าผ่านหมดทุึกด่าน ค่อยบันทึก
    new_user = User(username=username)
    new_user.set_password(password)
    
    if 'image_url' in data:
        new_user.image_url = data['image_url']
        
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

# API สำหรับเพิ่มสินค้า
@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.get_json()
    if not data.get('name') or data.get('price') is None or float(data.get('price')) < 0:
        return jsonify({"message": "Valid Name and non-negative Price are required"}), 400
        
    new_product = Product(
        name=data['name'],
        price=data.get('price'),
        stock=data.get('stock', 0),
        category=data.get('category'),
        description = data.get('description'),
        image_url=data.get('image_url', 'default-product.png')
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Product added successfully"}), 201

# API สำหรับดูรายการสินค้าทั้งหมด
@app.route('/api/products', methods=['GET'])
def get_products_list():
    try:
        # ดึงข้อมูลมาปกติ
        products = Product.query.filter_by(is_deleted=False, is_active=True).all()
        
        result = []
        for p in products:
            result.append({
                "id": p.id,
                "name": p.name,
                "price": float(p.price) if p.price else 0.0,
                "stock": p.stock,
                "image": p.image_url or "default.png"
                # ถ้ามีฟิลด์วันที่ ให้เลี่ยงการส่งออกไปก่อน หรือแปลงเป็น string ให้ดี
                # "date": p.created_at.isoformat() if p.created_at else None
            })
        return jsonify(result)
    except Exception as e:
        # ถ้าพังอีก ให้โชว์ Error ออกมาดูเลย
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# API สำหรับอัพเดชรายการสินค้า
@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json()

    # แก้ไขข้อมูลพื้นฐาน (ถ้าใน data ไม่มีค่ามาให้ ให้ใช้ค่าเดิมใน DB)
    product.name = data.get('name', product.name)
    product.price = data.get('price', product.price)
    product.stock = data.get('stock', product.stock)
    product.category = data.get('category', product.category)
    product.description = data.get('description', product.description)
    product.image_url = data.get('image_url', product.image_url)
    product.is_active = data.get('is_active', product.is_active)

    # หมายเหตุ: updated_at จะอัปเดตอัตโนมัติจาก lambda ใน Mixin ที่นายตั้งไว้ตอน db.session.commit()
    
    try:
        db.session.commit()
        return jsonify({
            "message": f"Product '{product.name}' updated successfully",
            "updated_at": product.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

# API สำหรับลบรายการสินค้า
@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    # ตรวจสอบก่อนว่าเคยถูกลบไปหรือยัง
    if product.is_deleted:
        return jsonify({"message": "This product is already in trash"}), 400

    # ทำ Soft Delete ตามโครงสร้างที่นายวางไว้
    product.is_deleted = True
    product.is_active = False # ปิดการขายทันที
    product.deleted_at = datetime.now(thailand_tz)
    
    # สมมติ ID คนลบ (พรุ่งนี้พอมีระบบ Login เราจะเอา current_user.id มาใส่แทนเลข 1)
    product.deleted_by_id = 1 

    try:
        db.session.commit()
        return jsonify({
            "message": f"Product '{product.name}' has been moved to trash",
            "deleted_by": product.deleted_by_id,
            "deleted_at": product.deleted_at.strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/orders', methods=['POST'])
def place_order():
    data = request.get_json() # ส่งมาเป็น { "items": [{"id": 1, "qty": 2}], "staff_id": 1 }
    
    if not data or not data.get('items'):
        return jsonify({"message": "No items in order"}), 400
        
    total = 0
    
    # 1. สร้าง Order หลัก
    new_order = Order(total_price=0) 
    db.session.add(new_order)
    
    # 2. วนลูปตัดสต็อกและเพิ่ม OrderItem
    for item in data['items']:
        product = Product.query.get(item['id'])
        if product and product.stock >= item['qty']:
            # ตัดสต็อก!
            product.stock -= item['qty']
            
            # บันทึกรายละเอียดสินค้าในบิล
            oi = OrderItem(
                order=new_order,
                product_id=product.id,
                quantity=item['qty'],
                price_at_sale=product.price
            )
            total += (product.price * item['qty'])
            db.session.add(oi)
        else:
            db.session.rollback() # ถ้าตัวไหนสต็อกไม่พอ ยกเลิกทั้งบิลทันที
            return jsonify({"message": f"Stock not enough for {product.name if product else 'ID '+str(item['id'])}"}), 400
            
    new_order.total_price = total
    db.session.commit()
    return jsonify({"message": "Sale completed!", "total": total}), 201


if __name__ == '__main__' :
    app.run(debug=True , port=5000)
