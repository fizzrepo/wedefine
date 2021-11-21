import flask
import flask_sqlalchemy

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = flask_sqlalchemy.SQLAlchemy(app)

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(64), unique=False)
    definition = db.Column(db.String, unique=True)
    def __repr__(self):
        return '<Word %r>' % self.word

db.create_all()

@app.route('/')
def index():
    words = Word.query.order_by(Word.id.desc()).limit(10).all()
    return flask.render_template('index.html', recentwords = words)

@app.route('/<word>')
def word(word):
    wordxd = Word.query.filter_by(word=word)
    if wordxd is None:
        return flask.render_template('error.html')
    defs = []
    for w in wordxd:
        defs.append(w.definition)
    
    return flask.render_template('defined.html', word=word, definition=defs)

@app.route('/define', methods=['POST'])
def add():
    word = flask.request.form['word'].lower()
    definition = flask.request.form['definition']
    if word == '' or definition == '':
        return flask.redirect('/')
    new_word = Word(word=word, definition=definition)
    db.session.add(new_word)
    try:
        db.session.commit()
    except:
        return flask.redirect('/')
    return flask.redirect(word)

if __name__ == '__main__':
    app.run(debug=True)
    