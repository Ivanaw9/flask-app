from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy.orm import sessionmaker
from CreateDatabase import engine, User, Dessert, DessertType, Message, Order, OrderDetails
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a new session
Session = sessionmaker(bind=engine)
db_session = Session()

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'Tiramisu12354'  # Replace with a strong secret key

# Ensure the database tables exist
User.metadata.create_all(engine)

# Add default users if they don't exist
existing_admin = db_session.query(User).filter_by(email="admin@gmail.com").first()
if not existing_admin:
    admin_user = User(
        username="admin",
        name="Admin User",
        email="admin@gmail.com",
        password="admin",
        role="Administrator"
    )
    db_session.add(admin_user)

existing_buyer = db_session.query(User).filter_by(email="buyer1@example.com").first()
if not existing_buyer:
    buyer_user = User(
        username="buyer1",
        name="Buyer One",
        email="buyer1@example.com",
        password="buyerpassword",
        role="Buyer"
    )
    db_session.add(buyer_user)

db_session.commit()
print("Default users added successfully!")

# Configure the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads/desserts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Fetch data from the Dessert table to display on the homepage
    desserts = db_session.query(Dessert).all()
    return render_template('index.html', desserts=desserts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('login'))

        # Query the database for the user
        user = db_session.query(User).filter_by(username=username).first()

        if user is None or user.password != password:
            logging.warning(f"Failed login attempt for username: {username}")  # Log the failed attempt
            flash('Invalid username or password. Please try again.', 'error')  # Show error notification
            return redirect(url_for('login'))

        session['user_id'] = user.user_id
        session['role'] = user.role
        session['logged_in'] = True  # Set logged_in to True
        logging.info(f"User {username} logged in.")  # Log the login action
        flash('Login successful.', 'success')
        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        user_id = session['user_id']
        logging.info(f"User ID {user_id} logged out.")  # Log the logout action
    session.clear()  # Clear all session variables
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('logged_in'):
        flash('You must log in to access the profile page.', 'error')
        return redirect(url_for('login'))

    user = db_session.query(User).filter_by(user_id=session['user_id']).first()
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Handle profile picture update logic here
        profile_picture = request.files.get('profile_picture')
        if profile_picture:
            # Save the file and update the user's profile
            pass
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'Buyer')  # Default role is "Buyer"

        if not username or not name or not email or not password:
            flash('All fields are required: Username, Name, Email, and Password.', 'error')
            return redirect(url_for('register'))

        existing_user = db_session.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, name=name, email=email, password=password, role=role)
        db_session.add(new_user)
        db_session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/home', endpoint='home')
def home():
    desserts = db_session.query(Dessert).all()
    return render_template('index.html', desserts=desserts)

@app.route('/menu', methods=['GET', 'POST'])
def menu():
    if request.method == 'POST':
        if session.get('role') != 'Administrator':  # Check if the user is an admin
            flash('You do not have permission to add a dessert.', 'error')
            return redirect(url_for('menu'))

        name = request.form['name']
        type_ = request.form['type']
        price = request.form['price']
        availability = request.form['availability']

        # Convert the string type to the DessertType enum
        try:
            dessert_type = DessertType[type_.replace(" ", "_").upper()]
        except KeyError:
            flash('Invalid dessert type selected.', 'error')
            return redirect(url_for('menu'))

        # Handle file upload
        if 'dessert_image' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('menu'))

        file = request.files['dessert_image']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('menu'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Save the relative path to the database
            relative_path = os.path.relpath(filepath, 'static')
            new_dessert = Dessert(Name=name, Type=dessert_type, Price=price, availability=availability, dessert_image=relative_path, user_id=session['user_id'])
            db_session.add(new_dessert)
            db_session.commit()

            flash('Dessert added successfully!', 'success')
            return redirect(url_for('menu'))

        flash('Invalid file type. Please upload an image file.', 'error')
        return redirect(url_for('menu'))

    search_query = request.args.get('search', '').strip()
    filter_query = request.args.get('filter', '').strip()

    query = db_session.query(Dessert)
    if search_query:
        query = query.filter((Dessert.Name.ilike(f'%{search_query}%')) | (Dessert.Type.ilike(f'%{search_query}%')))
    if filter_query:
        query = query.filter(Dessert.availability == filter_query)

    desserts = query.all()
    for dessert in desserts:
        if dessert.dessert_image:
            dessert.dessert_image = dessert.dessert_image.replace("\\", "/")
    return render_template('menu.html', desserts=desserts)

@app.route('/update_availability/<int:dessert_id>', methods=['POST'])
def update_availability(dessert_id):
    if session.get('role') != 'Administrator':
        flash('You do not have permission to update availability.', 'error')
        return redirect(url_for('menu'))

    availability = request.form.get('availability')
    dessert = db_session.query(Dessert).filter_by(dessert_id=dessert_id).first()

    if dessert:
        dessert.availability = availability
        db_session.commit()
        flash('Availability updated successfully.', 'success')
    else:
        flash('Dessert not found.', 'error')

    return redirect(url_for('menu'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'user_id' not in session:
        flash('You must log in to access the chat.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        sender_id = session.get('user_id')  # Use the logged-in user's ID as the sender
        receiver_id = 1  # Assuming the administrator has a user_id of 1
        content = request.form.get('message')

        if not content:
            flash('Message content is required.', 'error')
            return redirect(url_for('contact'))

        # Save the message to the database
        new_message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        db_session.add(new_message)
        db_session.commit()

    # Fetch chat history between the user and the admin
    messages = db_session.query(Message).filter(
        (Message.sender_id == session.get('user_id')) | 
        (Message.receiver_id == session.get('user_id'))
    ).order_by(Message.timestamp).all()

    return render_template('contact.html', messages=messages)

@app.route('/contact/confirmation')
def contact_confirmation():
    return render_template('contact_confirmation.html')

@app.route('/messages')
def messages():
    if session.get('role') != 'Administrator':
        flash('You do not have permission to access messages.', 'error')
        return redirect(url_for('index'))

    messages = db_session.query(Message).join(User, Message.sender_id == User.user_id).order_by(Message.timestamp.desc()).all()
    return render_template('messages.html', messages=messages)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        sender_id = session.get('user_id')
        receiver_id = 1  # Assuming admin has user_id = 1
        content = request.form.get('message')

        if not sender_id or not content:
            flash('Message content is required.', 'error')
            return redirect(url_for('chat'))

        new_message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        db_session.add(new_message)
        db_session.commit()

    messages = db_session.query(Message).filter(
        (Message.sender_id == session.get('user_id')) | 
        (Message.receiver_id == session.get('user_id'))
    ).order_by(Message.timestamp).all()

    return render_template('contact.html', messages=messages)

@app.route('/admin/chat', methods=['GET'])
def admin_chat():
    if session.get('role') != 'Administrator':  # Check if the user is an admin
        flash('Access denied.', 'error')
        return redirect(url_for('index'))

    users = db_session.query(User).join(Message, User.user_id == Message.sender_id).distinct().all()
    messages = []
    selected_user_id = users[0].user_id if users else None  # Default to the first user if available
    return render_template('admin_chat.html', users=users, messages=messages, selected_user_id=selected_user_id)

@app.route('/admin/chat/<int:user_id>', methods=['GET', 'POST'])
def admin_chat_user(user_id):
    if session.get('role') != 'Administrator':  # Check if the user is an admin
        flash('Access denied.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        content = request.form.get('message')
        if content:
            new_message = Message(
                sender_id=1,  # Assuming admin has user_id = 1
                receiver_id=user_id,
                content=content,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            db_session.add(new_message)
            db_session.commit()

    messages = db_session.query(Message).filter(
        (Message.sender_id == user_id) | 
        (Message.receiver_id == user_id)
    ).order_by(Message.timestamp).all()

    users = db_session.query(User).join(Message, User.user_id == Message.sender_id).distinct().all()
    return render_template('admin_chat.html', users=users, messages=messages, selected_user_id=user_id)

@app.route('/admin/orders', methods=['GET'])
def admin_orders():
    if session.get('role') != 'Administrator':  # Check if the user is an admin
        flash('Access denied.', 'error')
        return redirect(url_for('index'))

    orders = db_session.query(Order).join(User, Order.user_id == User.user_id).join(Dessert, Order.dessert_id == Dessert.dessert_id).all()
    return render_template('order.html', orders=orders)

@app.route('/admin/order_history', methods=['GET'])
def admin_order_history():
    if session.get('role') != 'Administrator':  # Check if the user is an admin
        flash('Access denied.', 'error')
        return redirect(url_for('index'))

    # Fetch all orders with buyer name and order details
    orders = db_session.query(Order).join(User, Order.user_id == User.user_id).all()
    order_details = db_session.query(OrderDetails).join(Dessert, OrderDetails.dessert_id == Dessert.dessert_id).all()

    return render_template('admin_order_history.html', orders=orders, order_details=order_details)

@app.route('/complete_order/<int:order_id>', methods=['POST'])
def complete_order(order_id):
    if session.get('role') != 'Administrator':  # Ensure only admins can complete orders
        flash('Access denied.', 'error')
        return redirect(url_for('admin_order_history'))

    # Update the order status to "Complete"
    order = db_session.query(Order).filter_by(order_id=order_id).first()
    if order:
        order.status = 'Complete'
        db_session.commit()
        flash(f'Order {order_id} marked as complete.', 'success')
    else:
        flash('Order not found.', 'error')

    return redirect(url_for('admin_order_history'))

@app.route('/user/order_history', methods=['GET'])
def user_order_history():
    if not session.get('logged_in'):  # Check if the user is logged in
        flash('You must log in to view your order history.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch orders and order details for the logged-in user
    orders = db_session.query(Order).filter_by(user_id=user_id).all()
    order_details = db_session.query(OrderDetails).join(Dessert, OrderDetails.dessert_id == Dessert.dessert_id).filter(
        OrderDetails.order_id.in_([order.order_id for order in orders])
    ).all()

    return render_template('user_order_history.html', orders=orders, order_details=order_details)

# Mock data for demonstration
cart = []

def get_cart_items():
    # Example implementation: Return the global cart list
    return cart

def calculate_total(cart_items):
    # Calculate the total price of items in the cart
    return sum(float(item['dessert']['Price']) * item['quantity'] for item in cart_items)

@app.route('/cart')
def cart_view():
    cart_items = get_cart_items()  # Fetch the cart items
    for item in cart_items:
        if item['dessert'].get('dessert_image'):
            item['dessert']['dessert_image'] = item['dessert']['dessert_image'].replace("\\", "/")
    total_price = calculate_total(cart_items)  # Calculate the total price
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/add_to_cart/<int:dessert_id>', methods=['POST'])
def add_to_cart(dessert_id):
    dessert = db_session.query(Dessert).filter_by(dessert_id=dessert_id).first()
    if dessert:
        cart.append({
            'dessert': {
                'Name': dessert.Name,
                'Price': float(dessert.Price),
                'dessert_image': dessert.dessert_image.replace("\\", "/") if dessert.dessert_image else 'default-image.jpg',
                'dessert_id': dessert.dessert_id
            },
            'quantity': 1
        })
    return redirect(url_for('menu'))

@app.route('/update_cart/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    quantity = int(request.form.get('quantity', 1))
    if 0 <= item_id < len(cart):
        cart[item_id]['quantity'] = quantity  # Use the 'quantity' key in the dictionary
    return redirect(url_for('cart_view'))

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if 0 <= item_id < len(cart):
        cart.pop(item_id)  # Remove the item from the cart by index
    return redirect(url_for('cart_view'))

@app.route('/checkout', methods=['POST'])
def checkout():
    global cart
    if not session.get('logged_in'):  # Check if the user is logged in
        logging.error("Unauthorized checkout attempt detected.")  # Log the error
        return redirect(url_for('error_page'))  # Redirect to error page

    user_id = session['user_id']
    logging.info(f"User ID {user_id} checked out with cart items: {cart}.")  # Log the checkout action

    # Get the current maximum order_id
    max_order_id = db_session.query(Order.order_id).order_by(Order.order_id.desc()).first()
    next_order_id = (max_order_id[0] + 1) if max_order_id else 1  # Increment or start from 1

    # Create a new order
    new_order = Order(
        order_id=next_order_id,
        user_id=user_id,
        order_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        status="Pending"
    )
    db_session.add(new_order)
    db_session.commit()  # Commit the order to generate the foreign key

    # Save cart items to the OrderDetails table
    for item in cart:
        order_detail = OrderDetails(
            order_id=next_order_id,
            dessert_id=item['dessert']['dessert_id'],
            quantity=item['quantity']
        )
        db_session.add(order_detail)
    db_session.commit()

    cart = []  # Clear the cart after checkout
    return redirect(url_for('checkout_confirmation'))

@app.route('/error')
def error_page():
    return render_template('error.html'), 403  # Return a 403 Forbidden status code

@app.route('/checkout/confirmation')
def checkout_confirmation():
    return render_template('checkout_confirmation.html')

if __name__ == '__main__':
    app.run(debug=True)
