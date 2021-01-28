from collections import deque
from urllib.parse import urlsplit, urljoin

import requests
from lxml import etree


class SchoologyClient:

    _HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'}
    _HOST = 'https://app.schoology.com/'

    def __init__(self, username, password, school, school_id):
        self.username = username
        self.password = password
        self.school = school
        self.school_id = school_id

        self.credentials = {
            'mail': self.username,
            'pass': self.password,
            'school': self.school,
            'school_nid': self.school_id,
            'remember-school': False
        }
        self.visit_history = deque(maxlen=10)
        self.session = requests.session()
        self.session.headers.update(self._HEADERS)
        self.session.hooks['response'].append(self._event_hooks)

        try:
            self._connection_status = self._login()
        except RecursionError as exc:
            print(exc)
            print("Credentials incorrect.")

    def _login(self):
        self.session.get(self._HOST)
        return self.visit_history[-1].status_code == 200 and self.visit_history[-1].url == self._HOST

    def _event_hooks(self, r, *args, **kwargs):
        scheme, netloc, path, query, frag = urlsplit(r.url)
        print(r.url)
        if path == '/login' and r.status_code == 200:
            self.session.cookies.update(r.cookies.get_dict())
            init_root = etree.fromstring(r.text, parser=etree.HTMLParser(encoding='utf8'))
            try:
                self.form_build_id = init_root.xpath("//input[@name='form_build_id']")
            except AttributeError:
                pass
            if self.form_build_id:
                self.credentials['form_build_id'] = self.form_build_id[0].get('value')
            try:
                self.form_id = init_root.xpath("//input[@name='form_id']")
            except AttributeError:
                pass
            if self.form_id:
                self.credentials['form_id'] = self.form_id[0].get('value')
            self.session.post(r.url, data=self.credentials)
        else:
            self.visit_history.append(r)
            return r

    @property
    def is_connected(self):
        return self._connection_status

    def get_usage_analytics(self):
        response = self.session.get(urljoin(self._HOST, 'school_analytics'))
        print(response.text) # TODO: - Finish
