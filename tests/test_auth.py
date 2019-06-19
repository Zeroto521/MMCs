# -*- coding: utf-8 -*-

from flask import url_for

from tests.base import BaseTestCase


class AuthTestCase(BaseTestCase):

    def test_login_root_user(self):
        response = self.login(username='root')
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)

    def test_login_admin_user(self):
        response = self.login(username='admin')
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)

    def test_login_teacher_user(self):
        response = self.login(username='teacher')
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)

    def test_fail_login(self):
        response = self.login(username='wrong', password='wrong')
        data = response.get_data(as_text=True)
        self.assertIn('Invalid username or password.', data)

    def test_logout_user(self):
        self.login()
        response = self.logout()
        data = response.get_data(as_text=True)
        self.assertIn('Logout success.', data)

    def test_login_protect(self):
        response = self.client.get(
            url_for('admin.index'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('403 Error', data)
        self.assertIn('Forbidden', data)
