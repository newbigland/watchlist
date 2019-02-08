import unittest
#from app import app, db, Movie, User, forge, initdb
from watchlist import app, db
from watchlist.commands import forge, initdb
from watchlist.models import User, Movie


class WatchlistTestCase(unittest.TestCase):

    def setUp(self):
        """准备环境"""

        # 更新配置
        app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
        # 创建数据库和表
        db.create_all()
        # 创建测试数据：一个用户和一个电影
        user = User(name='Test', username='test')
        user.set_password('123')
        movie = Movie(title='Test Movie Title', year='2019')
        # 一次性添加全部模型类实例，用列表方式传参
        db.session.add_all([user, movie])
        db.session.commit()

        self.client = app.test_client()  # 创建测试客户端，模拟浏览器
        self.runner = app.test_cli_runner()  # 创建测试命令运行器

    def tearDown(self):
        """销毁环境"""
        db.session.remove()  # 清除数据库会话
        db.drop_all()  # 删除数据库表

    def test_app_exist(self):
        """测试程序实例是否存在"""
        self.assertIsNotNone(app)

    def test_app_is_testing(self):
        """测试程序是否处于测试模式"""
        self.assertTrue(app.config['TESTING'])

    def test_404_page(self):
        """测试404页面"""
        response = self.client.get('/nothing')
        data = response.get_data(as_text=True)
        self.assertIn('Page Not Found - 404', data)
        self.assertIn('Go Back', data)
        self.assertEqual(response.status_code, 404)

    def test_index_page(self):
        """测试主页"""
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test\'s Watchlist', data)
        self.assertIn('Test Movie Title', data)
        self.assertEqual(response.status_code, 200)

    def login(self):
        """辅助方法，用于登录用户"""
        self.client.post('/login', data=dict(username='test', password='123'), follow_redirects=True)

    def test_create_item(self):
        """测试创建电影条目"""
        self.login()

        response = self.client.post('/', data=dict(title='New Movie', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item Created', data)
        self.assertIn('New Movie', data)

        # 测试创建电影条目操作，但电影标题为空
        response = self.client.post('/', data=dict(title='', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item Created', data)
        self.assertIn('Invalid input', data)

        # 测试创建电影条目操作，但电影年份为空
        response = self.client.post('/', data=dict(title='New Movie', year=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created', data)
        self.assertIn('Invalid input', data)

    def test_update_item(self):
        """测试更新电影条目"""
        self.login()

        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('Edit item', data)
        self.assertIn("Test Movie Title", data)
        self.assertIn('2019', data)

        # 测试更新条目操作，但电影标题为空
        response = self.client.post('/movie/edit/1', data=dict(title='', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated.', data)
        self.assertIn('Invalid input.', data)

        # 测试更新条目操作，但电影年份为空
        response = self.client.post('/movie/edit/1', data=dict(title='New Movie Edited Again', year=''),
                                    follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated.', data)
        self.assertNotIn('New Movie Edited Again', data)
        self.assertIn('Invalid input.', data)

    def test_delete_item(self):
        """测试删除电影条目"""
        self.login()

        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item Deleted.', data)
        self.assertNotIn('Test Movie Title', data)

    def test_login_protect(self):
        """测试登录保护"""
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('<form method="post">', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)

    def test_login(self):
        """测试登录"""
        response = self.client.post('/login', data=dict(username='test', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)
        self.assertIn('Logout', data)
        self.assertIn('Settings', data)
        self.assertIn('Delete', data)
        self.assertIn('Edit', data)
        self.assertIn('<form method="post">', data)

        # 测试使用错误的密码登录
        response = self.client.post('/login', data=dict(username='test', password='456'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # 测试使用错误的用户名登录
        response = self.client.post('/login', data=dict(username='wrong', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # 测试使用空用户名登录
        response = self.client.post('/login', data=dict(username='', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

        # 测试使用空密码登录
        response = self.client.post('/login', data=dict(username='test', password=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

    def test_logout(self):
        """测试登出"""
        self.login()

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Goodbye.', data)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('<form method="post">', data)

    def test_settings(self):
        """测试设置"""
        self.login()

        # 测试设置页面
        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('Settings', data)
        self.assertIn('Your Name', data)

        # 测试更新设置
        response = self.client.post('/settings', data=dict(name='Grey Li', ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Settings updated.', data)
        self.assertIn('Grey Li', data)

        # 测试更新设置，名称为空
        response = self.client.post('/settings', data=dict(name='', ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Settings updated.', data)
        self.assertIn('Invalid input.', data)

    def test_forge_command(self):
        """测试虚拟数据"""
        result = self.runner.invoke(forge)
        self.assertIn("Done.", result.output)
        self.assertNotEqual(Movie.query.count(), 0)

    def test_initdb_command(self):
        """测试初始化数据库"""
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)

    def test_admin_command(self):
        """测试生成管理员账户"""
        db.drop_all()
        db.create_all()
        result = self.runner.invoke(args=['admin', '--username', 'Bob', '--password', '123'])
        self.assertIn('Creating user ...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'Bob')
        self.assertTrue(User.query.first().validate_password('123'))

    def test_admin_command_update(self):
        """测试更新管理员账户"""

        # 使用args参数给出完整的命令参数列表
        result = self.runner.invoke(args=['admin', '--username', 'Peter', '--password', '456'])
        self.assertIn('Updating user ...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'Peter')
        self.assertTrue(User.query.first().validate_password('456'))


if __name__ == '__main__':
    unittest.main()
