import os
import click
from flask import Flask, url_for, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(app.root_path, 'data.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))


@app.cli.command()
def forge():
    '''生成假数据'''
    db.create_all()

    name = 'cxw'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')


@app.context_processor
def inject_user():
    '''模板上下文处理函数,这个函数返回的变量（以字典键值对的形式）
    将会统一注入到每一个模板的上下文环境中，因此可以直接在模板中使用。'''
    user = User.query.first()
    return dict(user=user)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/hello')
@app.route('/hi')
def hello():
    return "<h1>Hello Totoro!</h1><img src='http://helloflask.com/totoro.gif'>"


@app.route('/user/<name>')
def user_page(name):
    return 'User: %s' % name


@app.route('/test')
def test_url_for():
    print(url_for('hello'))  # 返回和视图函数最近的装饰器的URL
    print(url_for('user_page', name='cxw'))
    print(url_for('test_url_for'))
    print(url_for('test_url_for', num=3))
    return "test page"


@app.route('/')
def index():
    movies = Movie.query.all()  # 读取所有电影记录
    return render_template('index.html', movies=movies)
