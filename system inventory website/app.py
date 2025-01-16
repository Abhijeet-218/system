from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://///172.16.17.170/rkil-data/IT ADMIN/system database/inventory.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# Define models
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    floor = db.Column(db.String(50))
    department = db.Column(db.String(100))
    host_name = db.Column(db.String(100))
    employee_name = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    antivirus = db.Column(db.String(50))
    operating_system = db.Column(db.String(100))
    product_model = db.Column(db.String(100))
    pc_type = db.Column(db.String(50))
    processor = db.Column(db.String(100))
    ram_size = db.Column(db.String(50))
    hard_disk_type = db.Column(db.String(50))
    hard_disk_size = db.Column(db.String(50))
    hard_disk_sn = db.Column(db.String(100))
    ssd_disk_type = db.Column(db.String(50))
    ssd_disk_size = db.Column(db.String(50))
    ssd_hard_disk_sn = db.Column(db.String(100))
    on_board_lan_card = db.Column(db.String(50))
    adapter_mac_address = db.Column(db.String(100))
    external_lan_card = db.Column(db.String(50))
    external_adapter_mac_address = db.Column(db.String(100))
    ms_office = db.Column(db.String(50))

class Outlook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    floor = db.Column(db.String(50))
    department = db.Column(db.String(100))
    host_name = db.Column(db.String(100))
    employee_name = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    emails = db.relationship('Email', backref='outlook', lazy=True, cascade="all, delete-orphan")

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    outlook_id = db.Column(db.Integer, db.ForeignKey('outlook.id'))
    email_id = db.Column(db.String(100))
    email_type = db.Column(db.String(10))  # IMAP or POP3
    company_name = db.Column(db.String(100))

# Login routes
@app.route('/')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    if username == 'itadmin' and password == 'itadmin#823':
        session['user'] = username
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password', 'danger')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    search_query = request.args.get('search_query', '').lower()
    search_type = request.args.get('search_type', 'system')

    search_results = {"system": [], "outlook": []}

    if search_query:
        if search_type == 'system':
            search_results["system"] = Inventory.query.filter(
                (Inventory.employee_name.ilike(f'%{search_query}%')) |
                (Inventory.host_name.ilike(f'%{search_query}%')) |
                (Inventory.ip_address.ilike(f'%{search_query}%')) |
                (Inventory.operating_system.ilike(f'%{search_query}%')) |
                (Inventory.product_model.ilike(f'%{search_query}%')) |
                (Inventory.department.ilike(f'%{search_query}%')) |
                (Inventory.floor.ilike(f'%{search_query}%'))
            ).all()

        elif search_type == 'outlook':
            # Query to fetch multiple Outlook entries for each email
            search_results["outlook"] = db.session.query(Outlook, Email).join(Email, Email.outlook_id == Outlook.id).filter(
                (Outlook.employee_name.ilike(f'%{search_query}%')) |
                (Outlook.host_name.ilike(f'%{search_query}%')) |
                (Outlook.ip_address.ilike(f'%{search_query}%')) |
                (Outlook.floor.ilike(f'%{search_query}%')) |
                (Outlook.department.ilike(f'%{search_query}%'))
            ).all()

    email_counts = db.session.query(
        Email.email_type, db.func.count(Email.id).label('count')
    ).group_by(Email.email_type).all()

    total_imap_count = sum(count for email_type, count in email_counts if email_type == 'IMAP')
    total_pop3_count = sum(count for email_type, count in email_counts if email_type == 'POP3')

    floor_counts = db.session.query(Inventory.floor, db.func.count(Inventory.id).label('count')).group_by(Inventory.floor).all()
    department_counts = db.session.query(Inventory.department, db.func.count(Inventory.id).label('count')).group_by(Inventory.department).all()
    
    floor_department_counts = db.session.query(Inventory.floor, Inventory.department, db.func.count(Inventory.id).label('count')) \
                                        .group_by(Inventory.floor, Inventory.department) \
                                        .all()
    total_system_count = db.session.query(db.func.count(Inventory.id)).scalar()

    return render_template('dashboard.html', 
                           floor_department_counts=floor_department_counts, 
                           floor_counts=floor_counts,
                           department_counts=department_counts,
                           total_imap_count=total_imap_count,
                           total_pop3_count=total_pop3_count,
                           total_system_count=total_system_count,
                           search_results=search_results,
                           search_query=search_query,
                           search_type=search_type)

# System routes
@app.route('/system')
def system():
    if 'user' not in session:
        return redirect(url_for('login'))
    inventories = Inventory.query.all()
    return render_template('system.html', inventories=inventories)

@app.route('/add_system', methods=['GET', 'POST'])
def add_system():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        inventory = Inventory(**request.form.to_dict())
        db.session.add(inventory)
        db.session.commit()
        flash('System added successfully!', 'success')
        return redirect(url_for('system'))
    return render_template('add_system.html')

@app.route('/update_system/<int:id>', methods=['GET', 'POST'])
def update_system(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    inventory = Inventory.query.get_or_404(id)
    if request.method == 'POST':
        for key, value in request.form.items():
            setattr(inventory, key, value)
        db.session.commit()
        flash('System updated successfully!', 'success')
        return redirect(url_for('system'))
    return render_template('update_system.html', inventory=inventory)

@app.route('/delete_system/<int:id>', methods=['POST'])
def delete_system(id):
    inventory = Inventory.query.get_or_404(id)
    db.session.delete(inventory)
    db.session.commit()
    flash('System deleted successfully!', 'success')
    return redirect(url_for('system'))

# Outlook routes
@app.route('/outlook')
def outlook():
    if 'user' not in session:
        return redirect(url_for('login'))
    outlook_data = Outlook.query.all()
    return render_template('outlook.html', outlook_data=outlook_data)

@app.route('/add_outlook', methods=['GET', 'POST'])
def add_outlook():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Collecting basic Outlook details
        floor = request.form.get('floor')
        department = request.form.get('department')
        host_name = request.form.get('host_name')
        employee_name = request.form.get('employee_name')
        ip_address = request.form.get('ip_address')

        # Collect email details
        email_ids = request.form.getlist('email_id[]')
        email_types = request.form.getlist('email_type[]')
        companies = request.form.getlist('company_name[]')

        # Create multiple Outlook entries, one for each email
        for email_id, email_type, company_name in zip(email_ids, email_types, companies):
            # Create a new Outlook entry for each email
            outlook = Outlook(
                floor=floor,
                department=department,
                host_name=host_name,
                employee_name=employee_name,
                ip_address=ip_address
            )
            db.session.add(outlook)
            db.session.commit()  # Save Outlook first so we have an ID for emails

            # Now add the email associated with this new Outlook entry
            email = Email(
                outlook_id=outlook.id, 
                email_id=email_id, 
                email_type=email_type, 
                company_name=company_name
            )
            db.session.add(email)

        db.session.commit()  # Commit all entries
        flash('Outlook and associated emails added successfully!', 'success')
        return redirect(url_for('outlook'))
    return render_template('add_outlook.html')


@app.route('/outlook_update/<int:id>', methods=['GET', 'POST'])
def update_outlook(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    outlook = Outlook.query.get_or_404(id)
    if request.method == 'POST':
        outlook.floor = request.form['floor']
        outlook.department = request.form['department']
        outlook.host_name = request.form['host_name']
        outlook.employee_name = request.form['employee_name']
        outlook.ip_address = request.form['ip_address']
        
        # Clear existing emails and add new ones
        Email.query.filter_by(outlook_id=id).delete()
        email_ids = request.form.getlist('email_id[]')
        email_types = request.form.getlist('email_type[]')
        companies = request.form.getlist('company_name[]')
        
        for email_id, email_type, company_name in zip(email_ids, email_types, companies):
            email = Email(outlook_id=id, email_id=email_id, email_type=email_type, company_name=company_name)
            db.session.add(email)

        db.session.commit()
        flash('Outlook updated successfully!', 'success')
        return redirect(url_for('outlook'))
    return render_template('outlook_update.html', outlook=outlook)


@app.route('/delete_outlook/<int:id>', methods=['POST'])
def delete_outlook(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    outlook = Outlook.query.get_or_404(id)
    if outlook:
        db.session.delete(outlook)
        db.session.commit()
        flash('Outlook deleted successfully!', 'success')
    return redirect(url_for('outlook'))

# Route for displaying the outlook data
@app.route('/')
def index():
    outlook_data = Outlook.query.all()  # Fetch outlook data from the database
    return render_template('index.html', outlook_data=outlook_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run( host= "0.0.0.0" ,  port= 5000 ,  debug=True)             