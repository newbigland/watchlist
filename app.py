import os
import click
from flask import Flask, url_for, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(app.root_path, 'data.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev' # 这个秘钥用于签名
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # 值是login视图函数名


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


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


@app.cli.command()
@click.option('--drop', is_flag=True, help="Create after drop.")
def initdb(drop):
    '''Initialize the database.'''
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')


@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    '''create user.'''
    db.create_all()
    user = User.query.first()
    if user is not None:
        click.echo('Updating user ...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user ...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    click.echo('Done.')


@app.context_processor
def inject_user():
    '''模板上下文处理函数,这个函数返回的变量（以字典键值对的形式）
    将会统一注入到每一个模板的上下文环境中，因此可以直接在模板中使用。'''
    user = User.query.first()
    return dict(user=user)


@login_manager.user_loader
def load_user(user_id):
    '''定义用户加载回调函数'''
    user = User.query.get(int(user_id))
    return user


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))
        user = User.query.first()
        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index'))
        flash('Invalid username or password.')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index'))


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


@app.route('/settings', methods=['GET','POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']
        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))
        current_user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))
    return render_template('settings.html')


@app.route('/', methods=['GET','POST'])
def index():
    if request.method =="POST":
        if not current_user.is_authenticated: #如果当前用户未认证
            return redirect(url_for('index'))
        title = request.form.get('title')  # 获取表单数据,传入表单中输入字段的name值
        year = request.form.get('year')
        if not title or not year or len(year) > 4 or len(title) > 60: # 验证输入数据
            flash('Invalid input.')  # 显示错误提示信息,此函数用来在视图函数里向模板传递提示消息
            return redirect(url_for('index')) # 重定向到主页
        # 保存表单数据到数据库
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Movie Item Created.') # 显示成功创建的提示
        return redirect(url_for('index'))
    # 否则是GET请求，返回渲染后的页面
    user = User.query.first()
    movies = Movie.query.all()  # 读取所有电影记录
    return render_template('index.html', user=user, movies=movies)


@app.route('/movie/edit/<int:movie_id>', methods=['GET','POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == "POST":
        title = request.form['title']
        year = request.form['year']
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit'), movie_id=movie_id)  # 重定向到编辑页面

        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Movie Item Updated.')
        return redirect(url_for('index'))  # 重定向到主页

    return render_template('edit.html', movie=movie)  # GET请求时渲染编辑页面，编辑查询出的电影记录


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required  # 添加了这个装饰器后，如果未登录的用户访问对应的URL，Flask-Login会把用户重定向到登录页面，并显示一个错误提示。
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item Deleted.')
    return redirect(url_for('index'))
