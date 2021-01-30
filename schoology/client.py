from collections import deque
from urllib.parse import urlsplit, urljoin
from .seleniumclient import SeleniumClient

import requests
from lxml import etree
import dateutil.parser
import re


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
        print(r.url, r.status_code)
        if path == '/login' and r.status_code == 200:
            self.session.cookies.update(r.cookies.get_dict())
            init_root = etree.fromstring(r.text, parser=etree.HTMLParser(encoding='utf8'))
            self.credentials['form_build_id'] = init_root.xpath("//input[@name='form_build_id']")[0].get('value')
            self.credentials['form_id'] = init_root.xpath("//input[@name='form_id']")[0].get('value')
            self.session.post(r.url, data=self.credentials)
        else:
            self.visit_history.append(r)
            return r

    @property
    def is_connected(self):
        return self._connection_status

    def get_usage_analytics_cookies(self, session):
        sending = [{'name': cookie.name, 'value': cookie.value, 'domain': cookie.domain, 'path': cookie.path} for cookie in session.cookies]
        received = SeleniumClient().get_usage_analytics_cookies(cookies=sending)
        received = received[1:]
        return received

    def get_usage_analytics(self, start_date, end_date):
        with self.session as session:
            response = session.get(urljoin(self._HOST, 'school_analytics'))
            authorization = re.findall(r'(?<="jwtToken":")[A-Za-z0-9._-]+(?=",)', response.text)[0]
            payload = {
                'start_date': 1611705600,
                'end_date': 1611705600,
                'school_id': f"{self.school_id}"
            }
            session.headers.update({
                'accept-language': 'en-US,en;q=0.9',
                'authorization': 'Bearer ' + authorization,
                'referer': urljoin(self._HOST, 'school_analytics'),
                'accept-encoding': 'gzip, deflate, br',
                'content-length': '70',
                'content-type': 'application/json',
                'origin': self._HOST,
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin'
            })
            sele = self.get_usage_analytics_cookies(session=session)
            session.cookies.clear()
            [session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain']) for cookie in sele]

            response = session.post(urljoin(self._HOST, 'usage/exports/school'), json=payload)
            for cookie in session.cookies:
                print(cookie.name)


