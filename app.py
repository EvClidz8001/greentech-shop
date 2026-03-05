from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User, Product, CartItem, Order, OrderItem, Review, BundleItem, SiteContent, Donation
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'greentech-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///greentech.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создание базы данных и добавление начальных данных
with app.app_context():
    db.create_all()
    
    # Добавление товаров если их нет
    if Product.query.count() == 0:
        products = [
            # Отдельные товары
            Product(name="Индикатор почвы «Бумажка»", price=390, 
                   description="Просто вставьте в землю. Если бумажка стала красной — почва закислена (метод: добавьте золу). Желтая — не хватает азота (решение: удобрение крапивой). Метод описан в труде 'Здоровье почвы' (изд. 2023, стр. 45).", 
                   image_url="https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                   category="indicator", rating=4.5, in_stock=True),
            
            Product(name="Умный полив «AquaBot Pro»", price=2490, 
                   description="Вставляется в грунт. Полив активируется через мобильное приложение. Таймер от 1 минуты до 24 часов. Присылает push-уведомление, если влажность почвы ниже 20%. Совместим с iOS/Android.", 
                   image_url="https://images.unsplash.com/photo-1585339147946-6e4514c9b92b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                   category="watering", rating=4.8, in_stock=True),
            
            Product(name="Спрей «Био-Щит»", price=590, 
                   description="Натуральный состав против паутинного клеща и тли. Экстракт пиретрума и масло нима (проверено в лаборатории защиты растений РАН).", 
                   image_url="https://images.unsplash.com/photo-1625772452859-1a03aa1c9f4c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                   category="spray", rating=4.3, in_stock=True),
            
            Product(name="Корневой анализатор «RootScan»", price=3990, 
                   description="Устанавливается на дно горшка. Анализирует состояние корневой системы. Если корням холодно — датчик показывает синий (нужно повысить температуру), если мало света — оранжевый.", 
                   image_url="https://images.unsplash.com/photo-1581092335871-4c7ff3e832a3?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                   category="analyzer", rating=4.6, in_stock=True),
            
            Product(name="UV-лампа «Фотосинтез-660»", price=4990, 
                   description="Ультрафиолетовая лампа полного спектра с пиком 660 нм для ускорения фотосинтеза. Встроенный таймер 12/16 часов.", 
                   image_url="https://images.unsplash.com/photo-1578496479914-7ef3b0193be1?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                   category="light", rating=4.7, in_stock=True),
            
            Product(name="Датчик влажности «Drop Sensor»", price=1290, 
                   description="Анализирует состав влаги и минералов. Передает данные на смартфон через Bluetooth. Предупреждает о засухе за 24 часа.", 
                   image_url="https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                   category="sensor", rating=4.4, in_stock=True),
            
            # Наборы
            Product(name="🌱 Набор «Начинающий садовод»", price=2990, 
                   description="Идеальный старт для тех, кто хочет научиться ухаживать за растениями профессионально. Включает: индикатор почвы, спрей Био-Щит, датчик влажности.", 
                   image_url="https://images.unsplash.com/photo-1463936575829-25148e1db1b8?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                   category="bundle", rating=4.9, in_stock=True, is_bundle=True),
            
            Product(name="🏡 Набор «Домашняя метеостанция»", price=6990, 
                   description="Полный контроль микроклимата ваших растений. Включает: умный полив, датчик влажности, UV-лампу, корневой анализатор.", 
                   image_url="https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                   category="bundle", rating=5.0, in_stock=True, is_bundle=True),
            
            Product(name="🔬 Набор «Профессионал»", price=12990, 
                   description="Все устройства GreenTech в одном наборе для профессионального ухода за коллекцией растений. Экономия 30%.", 
                   image_url="https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                   category="bundle", rating=5.0, in_stock=True, is_bundle=True)
        ]
        db.session.add_all(products)
        db.session.commit()
        
        # Добавление состава наборов
        bundle1 = Product.query.filter_by(name="🌱 Набор «Начинающий садовод»").first()
        bundle2 = Product.query.filter_by(name="🏡 Набор «Домашняя метеостанция»").first()
        bundle3 = Product.query.filter_by(name="🔬 Набор «Профессионал»").first()
        
        products_dict = {p.name: p for p in Product.query.all()}
        
        bundle_items = [
            BundleItem(bundle_id=bundle1.id, product_id=products_dict["Индикатор почвы «Бумажка»"].id),
            BundleItem(bundle_id=bundle1.id, product_id=products_dict["Спрей «Био-Щит»"].id),
            BundleItem(bundle_id=bundle1.id, product_id=products_dict["Датчик влажности «Drop Sensor»"].id),
            
            BundleItem(bundle_id=bundle2.id, product_id=products_dict["Умный полив «AquaBot Pro»"].id),
            BundleItem(bundle_id=bundle2.id, product_id=products_dict["Датчик влажности «Drop Sensor»"].id),
            BundleItem(bundle_id=bundle2.id, product_id=products_dict["UV-лампа «Фотосинтез-660»"].id),
            BundleItem(bundle_id=bundle2.id, product_id=products_dict["Корневой анализатор «RootScan»"].id),
            
            BundleItem(bundle_id=bundle3.id, product_id=products_dict["Индикатор почвы «Бумажка»"].id),
            BundleItem(bundle_id=bundle3.id, product_id=products_dict["Спрей «Био-Щит»"].id),
            BundleItem(bundle_id=bundle3.id, product_id=products_dict["Датчик влажности «Drop Sensor»"].id),
            BundleItem(bundle_id=bundle3.id, product_id=products_dict["Умный полив «AquaBot Pro»"].id),
            BundleItem(bundle_id=bundle3.id, product_id=products_dict["UV-лампа «Фотосинтез-660»"].id),
            BundleItem(bundle_id=bundle3.id, product_id=products_dict["Корневой анализатор «RootScan»"].id),
        ]
        db.session.add_all(bundle_items)
        db.session.commit()
    
    # Добавление администратора
    if User.query.filter_by(username='admin').first() is None:
        admin = User(username='admin', 
                    password=generate_password_hash('admin123'), 
                    is_admin=True)
        db.session.add(admin)
        db.session.commit()
    
    # Добавление тестового пользователя
    if User.query.filter_by(username='user').first() is None:
        user = User(username='user', 
                   password=generate_password_hash('user123'), 
                   is_admin=False)
        db.session.add(user)
        db.session.commit()
    
    # Добавление отзывов
    if Review.query.count() == 0:
        user = User.query.filter_by(username='user').first()
        products = Product.query.all()
        
        reviews = [
            Review(user_id=user.id, product_id=products[0].id, rating=5, 
                  comment="Отличный индикатор! Очень точно показывает состояние почвы."),
            Review(user_id=user.id, product_id=products[1].id, rating=4, 
                  comment="Удобный полив, но приложение иногда тормозит."),
            Review(user_id=user.id, product_id=products[6].id, rating=5, 
                  comment="Набор супер! Все необходимое для начинающего."),
        ]
        db.session.add_all(reviews)
        db.session.commit()

@app.route('/')
def index():
    products = Product.query.limit(6).all()
    bundles = Product.query.filter_by(is_bundle=True).all()
    return render_template('index.html', products=products, bundles=bundles)

@app.route('/catalog')
def catalog():
    category = request.args.get('category', 'all')
    sort = request.args.get('sort', 'name')
    search = request.args.get('search', '')
    
    query = Product.query
    
    if category and category != 'all':
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Product.name.contains(search) | Product.description.contains(search))
    
    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'rating':
        query = query.order_by(Product.rating.desc())
    else:
        query = query.order_by(Product.name.asc())
    
    products = query.all()
    return render_template('catalog.html', products=products, current_category=category, current_sort=sort, search=search)

@app.route('/product/<int:product_id>')
def product(product_id):
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    
    bundle_items = []
    if product.is_bundle:
        bundle_items = BundleItem.query.filter_by(bundle_id=product_id).all()
    
    return render_template('product.html', product=product, reviews=reviews, bundle_items=bundle_items)

@app.route('/add_review/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')
    
    review = Review(user_id=current_user.id, product_id=product_id, rating=rating, comment=comment)
    db.session.add(review)
    
    # Обновление рейтинга товара
    product = Product.query.get(product_id)
    reviews = Review.query.filter_by(product_id=product_id).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews)
    product.rating = round(avg_rating, 1)
    
    db.session.commit()
    flash('Спасибо за отзыв!', 'success')
    return redirect(url_for('product', product_id=product_id))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/profile')
@login_required
def profile():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('profile.html', orders=orders)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)
    
    db.session.commit()
    
    # Подсчет количества товаров в корзине
    cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': cart_count})
    
    flash('Товар добавлен в корзину!', 'success')
    return redirect(request.referrer or url_for('catalog'))

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id == current_user.id:
        quantity = int(request.form.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
        else:
            db.session.delete(cart_item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Корзина пуста', 'error')
        return redirect(url_for('cart'))
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    order = Order(user_id=current_user.id, total_amount=total, status='completed')
    db.session.add(order)
    db.session.flush()
    
    for item in cart_items:
        order_item = OrderItem(order_id=order.id, product_id=item.product_id, 
                              quantity=item.quantity, price=item.product.price)
        db.session.add(order_item)
        db.session.delete(item)
    
    db.session.commit()
    flash('Заказ успешно оформлен!', 'success')
    return redirect(url_for('profile'))

@app.route('/donate', methods=['POST'])
@login_required
def donate():
    amount = float(request.form.get('amount', 0))
    if amount > 0:
        donation = Donation(amount=amount, user_id=current_user.id)
        db.session.add(donation)
        db.session.commit()
        flash(f'Спасибо за пожертвование {amount}₽ в Клуб защиты природы!', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).limit(20).all()
    users = User.query.all()
    donations = Donation.query.order_by(Donation.date.desc()).limit(20).all()
    
    return render_template('admin.html', products=products, orders=orders, users=users, donations=donations)

@app.route('/admin/add_product', methods=['POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    product = Product(
        name=request.form.get('name'),
        price=float(request.form.get('price')),
        description=request.form.get('description'),
        image_url=request.form.get('image_url'),
        category=request.form.get('category'),
        in_stock=bool(request.form.get('in_stock'))
    )
    db.session.add(product)
    db.session.commit()
    flash('Товар добавлен!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/update_product/<int:product_id>', methods=['POST'])
@login_required
def update_product(product_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    product = Product.query.get_or_404(product_id)
    product.name = request.form.get('name', product.name)
    product.price = float(request.form.get('price', product.price))
    product.description = request.form.get('description', product.description)
    product.image_url = request.form.get('image_url', product.image_url)
    product.category = request.form.get('category', product.category)
    product.in_stock = bool(request.form.get('in_stock', product.in_stock))
    
    db.session.commit()
    flash('Товар обновлен!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_product/<int:product_id>')
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Товар удален!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/api/cart_count')
@login_required
def cart_count():
    count = CartItem.query.filter_by(user_id=current_user.id).count()
    return jsonify({'count': count})

if __name__ == '__main__':
    app.run(debug=True)