from flask import request, flash, redirect, url_for, render_template
from flask_login import login_user, login_required, logout_user, current_user

from watchlist import app, db
from watchlist.models import User, Movie


@app.route('/login', methods=['GET', 'POST'])
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


@app.route('/settings', methods=['GET', 'POST'])
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


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        if not current_user.is_authenticated:  # 如果当前用户未登录
            return redirect(url_for('index'))
        title = request.form.get('title')  # 获取表单数据,传入表单中输入字段的name值
        year = request.form.get('year')
        if not title or not year or len(year) > 4 or len(title) > 60:  # 验证输入数据
            flash('Invalid input.')  # 显示错误提示信息,此函数用来在视图函数里向模板传递提示消息
            return redirect(url_for('index'))  # 重定向到主页
        # 保存表单数据到数据库
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Movie Item Created.')  # 显示成功创建的提示
        return redirect(url_for('index'))
    # 否则是GET请求，返回渲染后的页面
    user = User.query.first()
    movies = Movie.query.all()  # 读取所有电影记录
    return render_template('index.html', user=user, movies=movies)


@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == "POST":
        title = request.form['title']
        year = request.form['year']
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie.id))  # 重定向到编辑页面

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