import os
from flask import Flask, render_template, request, session, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import csv
from io import StringIO
from flask import make_response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# --- POSTGRESQL CONNECTION ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Hamper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(100))
    display_order = db.Column(db.Integer, default=0) # New field

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_email = db.Column(db.String(120), default="info@xotique.com")
    whatsapp_number = db.Column(db.String(20), default="254700000000")
    instagram_handle = db.Column(db.String(50), default="xotique_luxury")
    tiktok_handle = db.Column(db.String(50), default="xotique_luxury")

class Exhibition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50)) 
    media_type = db.Column(db.String(10), default="image") 
    filename = db.Column(db.String(100), nullable=False)
    display_order = db.Column(db.Integer, default=0) # New field

# --- CONTEXT PROCESSOR ---
@app.context_processor
def inject_config():
    config = Settings.query.first()
    return dict(config=config)

# --- ROUTES ---

@app.route('/')
def index():
    # .asc() ensures 1 comes before 2, 3, etc.
    # .desc() ensures that if orders are tied, the newest upload shows first.
    exhibits = Exhibition.query.order_by(
        Exhibition.display_order.asc(), 
        Exhibition.id.desc()
    ).all()
    return render_template('index.html', events=exhibits)

@app.route('/products')
def products():
    hampers = Hamper.query.order_by(Hamper.display_order.asc()).all()
    return render_template('products.html', hampers=hampers)

# --- AUTHENTICATION ---

@app.route('/x-portal', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('products'))
        flash("Unauthorized", "danger")
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.clear() # Aggressive logout for security
    return redirect(url_for('products'))

# --- ADMIN: EXHIBITION ---

@app.route('/admin/exhibition/add', methods=['GET', 'POST'])
def add_exhibition():
    if not session.get('is_admin'):
        abort(404)  # Hide existence of this route from non-admins
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            file.save(os.path.join('static/images', file.filename))
            new_exhibit = Exhibition(
                title=request.form.get('title'),
                category=request.form.get('category'),
                media_type=request.form.get('media_type'),
                filename=file.filename,
                display_order=request.form.get('display_order', 0, type=int)
            )
            db.session.add(new_exhibit)
            db.session.commit()
            flash("Exhibition added successfully!", "success")
            return redirect(url_for('index'))
    return render_template('add_exhibition.html')

@app.route('/admin/exhibition/delete/<int:id>', methods=['POST'])
def delete_exhibition(id):
    if not session.get('is_admin'):
        abort(404)  # Hide existence of this route from non-admins
    item = Exhibition.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('index'))

# --- ADMIN: PRODUCTS ---

@app.route('/admin/add', methods=['GET', 'POST'])
def add_product():
    if not session.get('is_admin'):
        abort(404)  # Hide existence of this route from non-admins
    if request.method == 'POST':
        image = request.files.get('image')
        image_url = image.filename if image else "default.png"
        if image:
            image.save(os.path.join('static/images', image.filename))
        
        new_hamper = Hamper(
            name=request.form.get('name'),
            price=request.form.get('price'),
            description=request.form.get('description'),
            image_url=image_url,
            display_order=request.form.get('display_order', 0, type=int)
        )
        db.session.add(new_hamper)
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('add_product.html')

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if not session.get('is_admin'):
        abort(404)  # Hide existence of this route from non-admins
    hamper = Hamper.query.get_or_404(id)
    if request.method == 'POST':
        hamper.name = request.form.get('name')
        hamper.price = request.form.get('price')
        hamper.description = request.form.get('description')
        hamper.display_order = request.form.get('display_order', type=int)
        
        image = request.files.get('image')
        if image and image.filename != '':
            image.save(os.path.join('static/images', image.filename))
            hamper.image_url = image.filename
        
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('edit_product.html', hamper=hamper)

@app.route('/admin/delete/<int:id>', methods=['POST'])
def delete_product(id):
    if not session.get('is_admin'):
        abort(404)  # Hide existence of this route from non-admins
    hamper = Hamper.query.get_or_404(id)
    db.session.delete(hamper)
    db.session.commit()
    return redirect(url_for('products'))

@app.route('/admin/settings', methods=['GET', 'POST'])
def manage_settings():
    if not session.get('is_admin'):
        abort(404)  # Hide existence of this route from non-admins
    config = Settings.query.first() or Settings()
    if request.method == 'POST':
        config.contact_email = request.form.get('email')
        config.whatsapp_number = request.form.get('whatsapp').replace('+', '').strip()
        config.instagram_handle = request.form.get('instagram').replace('@', '').strip()
        config.tiktok_handle = request.form.get('tiktok', '').replace('@', '').strip()
        db.session.add(config)
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('settings.html', config=config)

@app.route('/admin/exhibition/manage')
def manage_exhibitions():
    if not session.get('is_admin'):
        abort(404)  # Hide existence of this route from non-admins
    # Fetch all items sorted by their current order
    exhibits = Exhibition.query.order_by(Exhibition.display_order.asc()).all()
    return render_template('manage_exhibitions.html', exhibits=exhibits)

@app.route('/admin/exhibition/edit/<int:id>', methods=['GET', 'POST'])
def edit_exhibition(id):
    if not session.get('is_admin'):
        abort(404)  # Hide existence of this route from non-admins
    item = Exhibition.query.get_or_404(id)
    
    if request.method == 'POST':
        item.title = request.form.get('title')
        item.category = request.form.get('category')
        item.display_order = request.form.get('display_order', type=int)
        
        db.session.commit()
        flash(f"Updated '{item.title}' successfully.", "success")
        return redirect(url_for('manage_exhibitions'))
        
    return render_template('edit_exhibition.html', item=item)

@app.route('/admin/report/export')
def export_report():
    if not session.get('is_admin'):
        abort(404)  # Hide existence of this route from non-admins
    
    # Create an in-memory file
    si = StringIO()
    cw = csv.writer(si)
    
    # Write Header
    cw.writerow(['Type', 'Name/Title', 'Price/Category', 'Display Order', 'Filename'])
    
    # Fetch and Write Products (Hampers)
    hampers = Hamper.query.order_by(Hamper.display_order.asc()).all()
    for h in hampers:
        cw.writerow(['Product', h.name, h.price, h.display_order, h.image_url])
        
    # Fetch and Write Exhibition Items
    exhibits = Exhibition.query.order_by(Exhibition.display_order.asc()).all()
    for e in exhibits:
        cw.writerow(['Exhibit', e.title, e.category, e.display_order, e.filename])
    
    # Prepare the response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=xotique_inventory_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/admin/report/lookbook')
def lookbook():
    if not session.get('is_admin'):
        abort(404)  # Hide existence of this route from non-admins
    
    hampers = Hamper.query.all()
    exhibits = Exhibition.query.all()
    
    return render_template('lookbook.html', hampers=hampers, exhibits=exhibits)

# Move these lines to the top level of your app.py (after db is defined)
with app.app_context():
    db.create_all()
    print("Database tables initialized!")

if __name__ == "__main__":
    app.run()