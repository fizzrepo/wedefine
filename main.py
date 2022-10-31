from ipaddress import ip_address
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'
db = SQLAlchemy(app)
bcrpt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(800), nullable=False)
    admin = db.Column(db.Boolean, default=False)

    is_active = True
    get_id = lambda self: self.id
    is_authenticated = True
    is_anonymous = False

    def __repr__(self):
        return '<User %r>' % self.username

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(64), unique=False)
    definition = db.Column(db.String, unique=True)
    ip_address = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<Word %r>' % self.word

class BannedIP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String, unique=True)
    reason = db.Column(db.String, unique=False)

    def __repr__(self):
        return '<BannedIP %r>' % self.ip_address

db.create_all()


if not User.query.filter_by(username='admin').first():
    admin = User(username='admin', password=bcrpt.generate_password_hash('admin'), admin=True)
    db.session.add(admin)
    db.session.commit()

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id)) 

def check_ip(request):
    ip = request.remote_addr
    banned_ip = BannedIP.query.filter_by(ip_address=ip).first()
    if banned_ip:
        return banned_ip.reason
    else:
        return False

@app.route('/')
def index():
    if check_ip(request):
        ip = request.remote_addr
        return render_template('banned.html', ip=ip, reason=check_ip(request))
    words = Word.query.order_by(Word.id.desc()).limit(10).all()
    topwords = Word.query.order_by(Word.id.desc()).limit(10).all()
    return render_template('index.html', recentwords = words, topwords = topwords)

@app.route('/<word>')
def word(word):
    wordxd = Word.query.filter_by(word=word)
    if wordxd is None:
        return render_template('error.html')
    defs = []
    for w in wordxd:
        defs.append(w.definition)
    
    return render_template('defined.html', word=word, definition=defs)

@app.route('/define', methods=['POST'])
def add():
    word = request.form['word'].lower()
    definition = request.form['definition']
    if word == '' or definition == '':
        return redirect('/')
    new_word = Word(word=word, definition=definition, ip_address=request.remote_addr)
    db.session.add(new_word)
    try:
        db.session.commit()
    except:
        return redirect('/')
    return redirect(word)

@app.route('/search', methods=['POST'])
def search_endpoint():
    try:
        word = request.form['word'].lower()
        return redirect(word)
    except:
        return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user is None:
        return render_template('login.html', error='Invalid username or password')
    if bcrpt.check_password_hash(user.password, password):
        login_user(user)
        return redirect('/')
    return render_template('login.html', error='Invalid username or password')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/admin')
@login_required
def admin():
    if current_user.admin:
        return render_template('admin.html', user=current_user, words=Word.query.all())
    return redirect('/')

@app.route('/admin/delete/<id>')
@login_required
def delete(id):
    if current_user.admin:
        word = Word.query.filter_by(id=id).first()
        db.session.delete(word)
        db.session.commit()
        return redirect('/admin')
    return redirect('/')

@app.route('/admin/banip/', methods=['GET', 'POST'])
@login_required
def banip():
    if current_user.admin:
        if request.method == 'GET':
            ip = request.args.get('ip')
            return render_template('banip.html', user=current_user, ip2ban=ip, ipbans=BannedIP.query.all())
        ip = request.form['ip']
        reason = request.form['reason']
        if ip == '':
            return redirect('/admin/banip')
        try:
            ip_address(ip)
        except:
            return redirect('/admin/banip')
        if not reason: reason = 'No reason provided'
        new_ip = BannedIP(ip_address=ip, reason=reason)
        db.session.add(new_ip)
        db.session.commit()
        return redirect('/admin')
    return redirect('/')

@app.route('/admin/unbanip/<id>')
@login_required
def unbanip(id):
    if current_user.admin:
        ip = BannedIP.query.filter_by(id=id).first()
        db.session.delete(ip)
        db.session.commit()
        return redirect('/admin/banip')
    return redirect('/')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
    