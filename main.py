from flask import Flask, render_template, redirect,\
    url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, \
    logout_user, current_user, login_required
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from forms import LoginForm, RegisterForm, ItemForm
from werkzeug.security import generate_password_hash, check_password_hash
import stripe
import os
from flask_mail import Mail, Message
import psycopg2

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
# app.config.from_pyfile('config.py')

Bootstrap(app)
user_list = []

login_manager = LoginManager(app)

# this part is just to redirect after stripe to /success or /cancel
# different for local versus heroku hosted
YOUR_DOMAIN = os.environ["YOUR_DOMAIN"]

# just can't get heroku to work with postgresql db
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["SQLALCHEMY_DATABASE_URI"]
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL2",  os.environ["SQLALCHEMY_DATABASE_URI"])


db = SQLAlchemy(app)
BASE_URL = 'https://api.stripe.com'

stripe_keys = {"stripe_secret_key":os.environ["STRIPE_SECRET_KEY"],
               "stripe_pub_key":os.environ["STRIPE_PUB_KEY"]}
#### live keys above, test keys below
# stripe_keys = {"stripe_secret_key":os.environ["STRIPE_TEST_SECRET_KEY"],
#                "stripe_pub_key":os.environ["STRIPE_TEST_PUB_KEY"]}
stripe.api_key = stripe_keys["stripe_secret_key"]

# TEST CARDS TO USE ON STRIPE
# Payment succeeds
# 4242 4242 4242 4242
# Payment requires authentication
# 4000 0025 0000 3155
# Payment is declined
# 4000 0000 0000 9995

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ["SENDER_EMAIL"]
app.config['MAIL_PASSWORD'] = os.environ['GMAIL_APP_PASSWORD']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)



class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, nullable=True, primary_key=True)
    username = db.Column(db.String) # email
    password = db.Column(db.String)
    firstname = db.Column(db.String)
    lastname = db.Column(db.String)
    address1 = db.Column(db.String)
    address2 = db.Column(db.String)
    city = db.Column(db.String)
    postcode = db.Column(db.String)

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, nullable=True, primary_key=True)
    item = db.Column(db.String)
    num_items = db.Column(db.Integer)
    user_id = db.Column(db.Integer)

class Items(db.Model):
    __tablename__ = 'items'
    item_id = db.Column(db.Integer, nullable=True, primary_key=True)
    item_name = db.Column(db.String)
    item_image = db.Column(db.String)
    item_desc = db.Column(db.String)
    item_px = db.Column(db.Float)

# Cart.item is a string, is same as Items.item_id tho that's an integer

# trying to comment these out as someone said it crashes heroku when using postgres
# db.create_all()
# db.session.commit()

# item = Items(item_name="#9590",
#              item_image="https://img.seadn.io/files/ac380a556035c340e2c354d940c4f918.png?auto=format&fit=max&w=384",
#              item_desc="CryptoPunk #9590",
#              item_px=1.15)
# db.session.create(item)
# db.session.commit()

# to_del = User.query.get(1)
# db.session.delete(to_del)
# db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    return User.query.get(user_id)

def total_price():
    cart_stuff = Cart.query.filter_by(user_id=current_user.id).all()
    all_items = Items.query.all()
    total_price = 0
    for thing in all_items:
        for to_buy in cart_stuff:
            if str(to_buy.item) == str(thing.item_id):
                total_price += thing.item_px * to_buy.num_items
    return total_price

@app.route('/')
def homepage():
    all_items = Items.query.all()
    return render_template("index3.html", user=current_user, all_items=all_items)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user == None:
            pass
            flash("Email not found, please Register")
            render_template("login2.html", form=form)
        else:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('homepage'))
            else:
                flash("Incorrect password")
                render_template("login2.html", form=form)
    return render_template("login2.html", form=form)

@app.route('/register', methods=["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        firstname = form.firstname.data
        lastname = form.lastname.data
        username = form.username.data
        password = generate_password_hash(form.password.data)
        address1 = form.address1.data
        address2 = form.address2.data
        city = form.city.data
        postcode = form.postcode.data
        new_user = User(username=username,
                        password=password,
                        firstname=firstname,
                        lastname=lastname,
                        address1=address1,
                        address2=address2,
                        city=city,
                        postcode=postcode)
        if User.query.filter_by(username=username).first() is None:
            db.session.add(new_user)
            db.session.commit()
            # below logs newly registered user straight in
            user = User.query.filter_by(username=username).first()
            login_user(user)
            return redirect(url_for('homepage'))
        else:
            flash("That email is already registered, login instead?")
    return render_template("register2.html", form=form)

@app.route('/cart', methods=["GET","POST"])
def order_cart():
    if current_user.is_authenticated == False:
        # can only view/add to cart if logged in
        return redirect(url_for("login"))
    if request.method=="POST":
        if list(request.form.to_dict().values())[0] == "Delete Item":
            item_delete = list(request.form.to_dict().keys())[0]
            to_delete = Cart.query.filter_by(item=item_delete, user_id=current_user.id).first()
            db.session.delete(to_delete)
            db.session.commit()
            return redirect(url_for('order_cart'))
        print(request.form)
        item_add = list(request.form.to_dict().keys())[0]
        # form_stuff returns the item that was clicked
        print(item_add)

        # now need to check how many items already in cart for this user,
        # and add 1 to whichever was clicked
        prev_order = Cart.query.filter_by(item=item_add, user_id=current_user.id).first()
        if prev_order is None:
            new_order=Cart(item=item_add, num_items=1, user_id=current_user.id)
            db.session.add(new_order)
            db.session.commit()
        else:
            prev_order.num_items = prev_order.num_items +1
            #prev_order is actually a line object
            db.session.commit()
    purchases= Cart.query.filter_by(user_id=current_user.id).all()
    all_items = Items.query.all()
    checkout_price = total_price()
    return render_template("cart.html", purchases=purchases, all_items=all_items, checkout_price=checkout_price)

@app.route('/logout')
@login_required
def logging_out():
    logout_user()
    return redirect(url_for('login'))
    return render_template("logout.html")

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    purchases= Cart.query.filter_by(user_id=current_user.id).all()
    line_items = []
    for custy_order in purchases:
        item_desc_ = Items.query.filter_by(item_id=int(custy_order.item)).first().item_desc
        item_px_ = int(100*Items.query.filter_by(item_id=int(custy_order.item)).first().item_px)
        order_dets = {
            'price_data': {
                'currency': 'gbp',
                'product_data': {
                    'name': item_desc_,
                },
                'unit_amount': item_px_,
            },
            'quantity': custy_order.num_items,
        }
        line_items.append(order_dets)
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items = line_items,
            mode='payment',
            success_url= YOUR_DOMAIN + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url= YOUR_DOMAIN + '/cancel?session_id={CHECKOUT_SESSION_ID}',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)

@app.route('/success', methods=['GET'])
def success():
    try:
        session = stripe.checkout.Session.retrieve(request.args.get('session_id'))
        customer = stripe.Customer.retrieve(session.customer)
        if session.status != "complete":
            return redirect(url_for("order_cart"))
    except:
        return redirect(url_for("order_cart"))

    purchases = Cart.query.filter_by(user_id=current_user.id).all()
    all_items = Items.query.all()
    buyer = User.query.filter_by(id=current_user.id).first()
    checkout_price = total_price()
    # so...if session.status == complete, display the order and
    # shipping address, then empty the cart
    final_orders = []
    email_body = ""
    for purchase in purchases:
        # this lets me put the number of items into success.html,
        # whilst deleting from the cart since they've been purchased
        this_item = Items.query.filter_by(item_id=int(purchase.item)).first()
        image_link_full = this_item.item_image.split("?")[0]
        email_body += f"<img src='{this_item.item_image}'><br><a href='{image_link_full}'>Download Link</a><br><br>"
        final_order=purchase
        final_orders.append(final_order)
        db.session.delete(purchase)
    db.session.commit()

    sender_email = os.environ["SENDER_EMAIL"]
    sender_password = os.environ["SENDER_PASSWORD"]

    #start with "Subject:Hello this is the subject line\n\nThis is then the body"
    send_message = f"Hi {buyer.firstname},<br><br>Your order is:<br><br>{email_body}<br><br>Enjoy" \
                   f"!<br><br>Don't forget to RightClickSave!"
    send_to_email = buyer.username
    msg = Message("Thank you for your order from RightClickSave",
                  sender = sender_email,
                  recipients = [send_to_email],
                  bcc = [sender_email],
                  html = send_message)
    # msg.body = send_message
    if purchases != []:  # catches case where user refreshes page
        mail.send(msg)

    return render_template("success.html", purchases=final_orders, buyer=buyer,
                           all_items=all_items, checkout_price=checkout_price)

@app.route('/cancel', methods=['GET'])
def cancel():
    try:
        session = stripe.checkout.Session.retrieve(request.args.get('session_id'))
        if session.status != "complete":
            return redirect(url_for("order_cart"))
    except:
        return redirect(url_for("order_cart"))
    purchases= Cart.query.filter_by(user_id=current_user.id).all()
    return render_template("cancel.html", purchases=purchases)

@app.route('/admin', methods=['GET','POST'])
def admin():
    form = ItemForm()
    try: # checks that user is id=1, ie. admin
        if current_user.id != 1:
            return redirect(url_for('homepage'))
    except:
        return redirect(url_for('homepage'))

    if form.validate_on_submit():
        new_item = Items(item_name=form.item_name.data,
                        item_image=form.item_image.data,
                        item_desc=form.item_desc.data,
                        item_px=form.item_price.data)
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('admin'))

    if request.method=="POST":
        try:
            item_to_delete = int(list(request.form.to_dict().keys())[0])
            del_this_object = Items.query.filter_by(item_id = item_to_delete).first()
            db.session.delete(del_this_object)
            db.session.commit()
        except:
            pass
        return redirect(url_for('admin'))

    all_items = Items.query.all()
    return render_template('admin.html', all_items=all_items, form=form)

@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)