# -*- coding: utf-8 -*-
# @Time    : 2023/11/25 14:53
# @Author  : Zr
# @Comment :

import base64
import json
import logging
import os
import sys
import socket
import time
import traceback
import copy
import chardet
from .log import getLogger, getFileLogger


def _bytes_to_str(b):
    if not b:
        return b
    cd = chardet.detect(b)
    return str(b, encoding=cd['encoding'])


def _default_executable_path(product):
    if product == 'chrome':
        if sys.platform == 'win32':
            chrome_deault_path = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
            edge_default_path = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
            if os.path.exists(chrome_deault_path):
                return chrome_deault_path
            elif os.path.exists(edge_default_path):
                return edge_default_path
            raise Exception('no chrome or edge found')
        elif sys.platform == 'linux':
            raise
        elif sys.platform == 'darwin':
            raise
    else:
        raise


def VIEWPORT(width, height, device_scale_factor=1, is_mobile=False, has_touch=False, is_landscape=False):
    return {
        "width": width,
        "height": height,
        "deviceScaleFactor": device_scale_factor,
        "isMobile": is_mobile,
        "hasTouch": has_touch,
        "isLandscape": is_landscape
    }


def _LAUNCH_OPTIONS(product='chrome',
                    ignore_https_errors=False,
                    headless=True,
                    executable_path=None,
                    slow_mo=None,
                    lang=None,
                    timeout=None,
                    userdatadir=None,
                    devtools=False,
                    window_size=None,
                    window_position=None,
                    maximize_window=False,
                    args=None,
                    ignore_default_args=None,
                    disable_extensions=None,
                    extensions=None):
    args = list() if args is None else args
    ignore_default_args = list() if ignore_default_args is None else ignore_default_args
    _opts = {}

    _opts['product'] = product
    _opts['executablePath'] = executable_path or _default_executable_path(product)
    _opts['headless'] = headless
    _opts['ignoreHttpsErrors'] = ignore_https_errors
    _opts['devtools'] = devtools
    _opts['extensions'] = extensions

    if slow_mo:
        _opts['slowMo'] = slow_mo

    # disable default_viewport:
    _opts['defaultViewport'] = None

    if lang:
        args.append('--lang=%s' % lang.replace('_', '-'))

    if userdatadir:
        _opts['userDataDir'] = userdatadir

    if timeout:
        _opts['timeout'] = timeout

    ##for args
    if window_size and not maximize_window:
        _ws = '--window-size=%s' % window_size
        if _ws in args:
            args.remove(_ws)
        args.append('--window-size=%s' % window_size)

    if window_position:
        args.append('--window-position=%s' % window_position)

    if maximize_window:
        if "--start-maximized" in args:
            args.remove('--start-maximized')

        args.append('--start-maximized')

    if headless:
        if "--disable-gpu" in args:
            args.remove("--disable-gpu")
        args.append("--disable-gpu")

    args.append("--no-default-browser-check")
    args.append("--disable-features=site-per-process")  # for iframe selector

    _opts['args'] = args

    ignore_default_args.append("--enable-automation")
    if not disable_extensions:
        ignore_default_args.append("--disable-extensions")

    if extensions:
        if disable_extensions:
            args.append("--disable-extensions-except=%s" % ",".join(extensions))
        else:
            args.append("--load-extension=%s" % ",".join(extensions))

    ignore_default_args.append("--enable-blink-features=IdleDetection")
    _opts['ignoreDefaultArgs'] = ignore_default_args

    return _opts


class BrowserProxy():

    def __init__(self, host, port, log_level, log_file):
        self._host = host
        self._port = port
        self._head_len = 8
        self._chunk = 4096
        self._log_level = log_level

        if log_file:
            self._logger = getFileLogger(file=log_file, level=log_level)
        else:
            self._logger = getLogger(level=log_level)

        if not self._port:
            raise Exception('port is None')

        self._connection = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self._connection.connect((self._host, self._port))

    def __del__(self):
        self._close()

    def _print_message(self, obj, tag='message'):
        self._logger.debug('==================%s==================:', tag)
        if type(obj) is dict:
            self._logger.debug(json.dumps(obj, indent=2, ensure_ascii=False))
        elif type(obj) is list:
            for o in obj:
                self._print_message(o)
        else:
            self._logger.debug(obj)
        self._logger.debug('================end %s================:', tag)

    def _close(self):
        try:
            if self._connection:
                self._connection.close()
        except Exception:
            self._logger.warn("error happened when closing browser proxy connection:\n" + traceback.format_exc())

    def _fire(self, id, action, **kwargs):
        if not action:
            raise Exception('ERROR: _fire function argument action is None.')

        send = {
            "id": id,
            "action": action,
            "ctx": kwargs
        }

        if self._logger.level == logging.DEBUG:
            self._print_message(send, "send data")

        send = json.dumps(send).encode('utf-8')
        send_len = str(len(send)).zfill(self._head_len).encode('utf-8')
        self._connection.send(send_len + send)
        total_size = int(self._connection.recv(self._head_len))

        data = []
        recv_size = 0
        while recv_size < total_size:
            buf = self._connection.recv(self._chunk)
            data.append(buf)
            recv_size = recv_size + len(buf)

        if data:
            data = b''.join(data)
            _jd = json.loads(data)

            if self._logger.level == logging.DEBUG:
                _jd2 = copy.copy(_jd)
                if _jd2.get('html'):
                    _jd2['html'] = '*'
                if _jd2.get('img_b64'):
                    _jd2['img_b64'] = '*'
                self._print_message(_jd2, "recv")

            _file = _jd.get('file')
            if _file:
                with open(_file, 'rb') as f:
                    _jd = json.load(f)

                os.remove(_file)

            return _jd

        return None

    def wrap_fire(self, id, action, **kwargs):
        r = self._fire(id, action, **kwargs)
        if not r:
            raise Exception('ERROR: _fire(*args, **kwargs): pptrs return None')

        if r.get("retCode") < 0:
            raise Exception('ERROR: _fire(*args, **kwargs): pptrs return -2, retMsg=%s' % r.get("retMsg"))

        return r.get("retCode"), r.get("retMsg"), r.get("data")


class Browser(BrowserProxy):
    def __init__(self, browser_id=None, host='127.0.0.1', port=9999, log_level='debug', log_file=None):
        super(Browser, self).__init__(host=host, port=port, log_level=log_level, log_file=log_file)
        self.browser_id = browser_id

    def launch(self,
               product='chrome',
               ignore_https_errors=False,
               headless=True,
               executable_path=None,
               slow_mo=None,
               lang=None,
               timeout=None,
               userdatadir=None,
               devtools=False,
               window_size=None,
               window_position='0,0',
               maximize_window=False,
               args=None,
               ignore_default_args=None,
               disable_extensions=True,
               extensions=None):
        options = _LAUNCH_OPTIONS(product=product,
                                  ignore_https_errors=ignore_https_errors,
                                  headless=headless,
                                  executable_path=executable_path,
                                  slow_mo=slow_mo,
                                  lang=lang,
                                  timeout=timeout,
                                  userdatadir=userdatadir,
                                  devtools=devtools,
                                  window_size=window_size,
                                  window_position=window_position,
                                  maximize_window=maximize_window,
                                  args=args,
                                  ignore_default_args=ignore_default_args,
                                  disable_extensions=disable_extensions,
                                  extensions=extensions)

        ret_code, ret_msg, data = self.wrap_fire(id=self.browser_id, action='launch', options=options)
        self.browser_id = data.get('wsEndpoint')

        self._logger.debug('launch succeed, wsEndpoint: %s' % self.browser_id)

        return self

    def newPage(self):
        ret_code, ret_msg, data = self.wrap_fire(id=self.browser_id, action='newPage')
        page_index = data.get('pageIndex')
        page = Page(browser=self, page_index=page_index)

        return page

    def wsEndpoint(self):
        return self.browser_id

    def pagesCount(self):
        ret_code, ret_msg, data = self.wrap_fire(id=self.browser_id, action='pagesCount')
        return data.get('pages')

    def getPage(self, page_index=0):
        pc = self.pagesCount()
        if page_index < 0 or page_index > pc:
            raise Exception('error page_index, pages count is %d' % pc)
        return Page(browser=self, page_index=page_index)

    def quit(self):
        self.wrap_fire(id=self.browser_id, action='quit')


class Page():
    def __init__(self, browser, page_index):
        self.browser = browser
        self.page_index = page_index

        '''
        self.navigation_options = {
            'waitUntil': 'load',
            'timeout': 60000,
            'referer': ''
        }

        self.selector_options = {
            'timeout': 30000,
            'visible': True,
            'hidden': False
        }
        '''

    def wrap_fire(self, action, **kwargs):
        return self.browser.wrap_fire(id=self.browser.browser_id, action=action, pageIndex=self.page_index, **kwargs)

    def frames(self, silent=True):
        _frames = None
        try:
            ret_code, ret_msg, data = self.wrap_fire(action='frames')
            keys = data.get('keys')
            _frames = [Frame(key=key, browser=self.browser) for key in keys]
        except:
            if not silent:
                raise

        return _frames

    def findFrame(self, url):
        for f in self.frames():
            if f.url().find(url, 0) >= 0:
                return f

    def waitForFrame(self, url, timeout=3000, retry=5):
        for i in range(retry):
            f = self.findFrame(url)
            if f:
                return f
            time.sleep(timeout / 1000)

    def querySelector(self, selector, silent=True):
        try:
            ret_code, ret_msg, data = self.wrap_fire(action='$', selector=selector)
            key = data.get('key')
            return Elem(key=key, browser=self.browser)
        except:
            if not silent:
                raise
            else:
                return None

    def querySelectorAll(self, selector, silent=True):
        try:
            ret_code, ret_msg, data = self.wrap_fire(action='$$', selector=selector)
            keys = data.get('keys')
            return [Elem(key=key, browser=self.browser) for key in keys]
        except:
            if not silent:
                raise
            else:
                return None

    def waitForSelector(self, selector, hidden=False, timeout=30000, visible=False, silent=True):
        options = {
            "hidden": hidden,
            'timeout': timeout,
            'visible': visible
        }
        try:
            ret_code, ret_msg, data = self.wrap_fire(action='waitForSelector', selector=selector, options=options)
            key = data.get('key')
            return Elem(key=key, browser=self.browser)
        except:
            if not silent:
                raise
            else:
                return None

    def set_default_navigation_timeout(self, timeout):
        self.wrap_fire(action='setDefaultNavigationTimeout', timeout=timeout)

    def bringToFront(self):
        self.wrap_fire(action='bringToFront')

    def setDefaultNavigationTimeout(self, timeout):
        '''
        timeout: milliseconds
        '''
        self.wrap_fire(action='setDefaultNavigationTimeout', timeout=timeout)

    def setUserAgent(self, userAgent):
        self.wrap_fire(action='setUserAgent', userAgent=userAgent)

    def evaluateOnNewDocument(self, script):
        if script:
            script = _bytes_to_str(base64.b64encode(bytes(script, encoding='utf-8')))

        ret_code, ret_msg, data = self.wrap_fire(action='evaluateOnNewDocument', script=script)
        return data.get('result')

    def evaluate(self, script):
        if script:
            script = _bytes_to_str(base64.b64encode(bytes(script, encoding='utf-8')))

        ret_code, ret_msg, data = self.wrap_fire(action='evaluate', script=script)
        return data.get('result')

    def getHtml(self):
        ret_code, ret_msg, data = self.wrap_fire(action='html')
        _html = base64.b64decode(data.get('html')).decode()
        return _html

    def getUrl(self):
        ret_code, ret_msg, data = self.wrap_fire(action='url')
        return data.get('url')

    def setCookies(self, cookies):
        if type(cookies) is dict:
            cookies = [cookies]

        self.wrap_fire(action='setCookies', cookies=cookies)

    def getCookies(self):
        ret_code, ret_msg, data = self.wrap_fire(action='getCookies')
        return data.get('cookies')

    def goto(self, url, waitUntil='load', timeout=30000, referer=''):
        options = {
            "waitUntil": waitUntil,
            'timeout': timeout,
            'referer': referer
        }

        ret_code, ret_msg, data = self.wrap_fire(action='goto', url=url, options=options)
        return data.get('status')

    def goBack(self, waitUntil='load', timeout=30000, referer=''):
        options = {
            "waitUntil": waitUntil,
            'timeout': timeout,
            'referer': referer
        }

        self.wrap_fire(action='goBack', options=options)

    def goForward(self, waitUntil='load', timeout=30000, referer=''):
        options = {
            "waitUntil": waitUntil,
            'timeout': timeout,
            'referer': referer
        }

        self.wrap_fire(action='goForward', options=options)

    def waitForNavigation(self, waitUntil='load', timeout=30000, silent=True):
        try:
            self.wrap_fire(action='waitForNavigation', options={
                'waitUntil': waitUntil,
                'timeout': timeout
            })
        except:
            if silent:
                return None
            else:
                raise

    def click(self, selector, button='left', clickCount=1, delay=0, offset={'x': 0, 'y': 0}):
        options = {
            'button': button,
            'clickCount': clickCount,
            'delay': delay,
            'offset': offset
        }
        if offset['x'] == 0 and offset['y'] == 0:
            options.pop('offset')
        self.wrap_fire(action='click', selector=selector, options=options)

    def tap(self, selector):
        self.wrap_fire(action='tap', selector=selector)

    def type(self, selector, text, delay=0):
        self.wrap_fire(action='type', selector=selector, text=text, options={'delay': delay})

    def sendCharacter(self, text):
        self.wrap_fire(action='sendCharacter', text=text)

    def press(self, key):
        self.wrap_fire(action='press', key=key)

    def pdf(self, path,
            scale=1,
            displayHeaderFooter=False,
            headerTemplate=None,
            footerTemplate=None,
            printBackground=False,
            landscape=False,
            pageRanges='',
            format='Letter',
            width=None,
            height=None,
            margin=None,
            preferCSSPageSize=False,
            omitBackground=False,
            timeout=30000
            ):
        options = {
            "path": path,
            "scale": scale,
            "displayHeaderFooter": displayHeaderFooter,
            "headerTemplate": headerTemplate,
            "footerTemplate": footerTemplate,
            "printBackground": printBackground,
            "landscape": landscape,
            "pageRanges": pageRanges,
            "format": format,
            'width': width,
            'height': height,
            "margin": margin,
            "preferCSSPageSize": preferCSSPageSize,
            "omitBackground": omitBackground,
            "timeout": timeout
        }

        options = {k: v for k, v in options.items() if v is not None}
        self.wrap_fire(action='pdf', options=options)

    def close(self):
        '''
        close active tab, if only one tab, quit chrome.
        '''
        self.wrap_fire(action='closePage')

    def scroll(self, x=None, y=None):
        ret_code, ret_msg, data = self.wrap_fire(action='scroll', x=x, y=y)
        return data.get('scrollOffset')

    def scrollToEnd(self, x=None, y=None, delay=0):
        while True:
            r1 = self.evaluate(
                '''window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight''')
            r2 = self.evaluate('''document.documentElement.scrollHeight || document.body.scrollHeight''')
            r3 = self.scroll(x=x, y=y)

            if r2 - r3 - r1 < 1:
                break

            if delay > 0:
                time.sleep(delay)

    def scrollToTop(self, x=None, y=None, delay=0):
        if not y:
            y = -1 * self.evaluate('''window.innerHeight''')
        while True:
            r3 = self.scroll(x=x, y=y)
            if r3 < 1:
                break

            if delay > 0:
                time.sleep(delay)

    def scrollToView(self, selector):
        elem = self.querySelector(selector)
        while not elem.isIntersectingViewport():
            self.scroll()

    def eval(self, selector, attr='innerText', silent=True):
        try:
            ret_code, ret_msg, data = self.wrap_fire(action='$eval', selector=selector, attr=attr)
            return data.get('result')
        except:
            if silent:
                return None
            else:
                raise

    def evalAll(self, selector, attr='innerText', silent=True):
        try:
            ret_code, ret_msg, data = self.wrap_fire(action='$$eval', selector=selector, attr=attr)
            return data.get('result')
        except:
            if silent:
                return []
            else:
                raise

    def screenShot(self, path, omitBackground=False):
        self.wrap_fire(action='screenShot', path=path, omitBackground=omitBackground)


class Elem():
    def __init__(self, key, browser):
        self.browser = browser
        self.key = key

    def __repr__(self):
        return '<class.Elem, key=%s>' % self.key

    def wrap_fire(self, action, **kwargs):
        return self.browser.wrap_fire(id=self.browser.browser_id, action=action, key=self.key, **kwargs)

    def querySelector(self, selector, silent=True):
        try:
            ret_code, ret_msg, data = self.wrap_fire(action='e_$', selector=selector)
            key = data.get('key')
            return Elem(key=key, browser=self.browser)
        except:
            if silent:
                return None
            else:
                raise

    def querySelectorAll(self, selector, silent=True):
        try:
            ret_code, ret_msg, data = self.wrap_fire(action='e_$$', selector=selector)
            keys = data.get('keys')
            return [Elem(key=key, browser=self.browser) for key in keys]
        except:
            if silent:
                return None
            else:
                raise

    def click(self, button='left', clickCount=1, delay=0, offset=None):
        if not offset:
            offset = {'x': 0, 'y': 0}

        options = {
            'button': button,
            'clickCount': clickCount,
            'delay': delay,
            'offset': offset
        }
        if offset['x'] == 0 and offset['y'] == 0:
            options.pop('offset')
        self.wrap_fire(action='e_click', options=options)

    def getProperty(self, attr='value'):
        ret_code, ret_msg, data = self.wrap_fire(action='e_getProperty', attr=attr)
        value = data.get('value')
        if value:
            value = base64.b64decode(data.get('value')).decode()
        return value

    def isIntersectingViewport(self):
        ret_code, ret_msg, data = self.wrap_fire(action='e_isIntersectingViewport')
        return data.get('result')

    def scrollIntoView(self):
        ret_code, ret_msg, data = self.wrap_fire(action='e_scrollIntoView')
        return data.get('result')


class Frame():
    def __init__(self, key, browser):
        self.browser = browser
        self.key = key

    def __repr__(self):
        return '<class.Frame key=%s>' % self.key

    def wrap_fire(self, action, **kwargs):
        return self.browser.wrap_fire(id=self.browser.browser_id, action=action, frameKey=self.key, **kwargs)

    def url(self):
        ret_code, ret_msg, data = self.wrap_fire(action='f_url')
        url = data.get('url')
        return url

    def querySelector(self, selector, silent=True):

        try:
            ret_code, ret_msg, data = self.wrap_fire(action='f_$', selector=selector)
            key = data.get('key')
            return Elem(key=key, browser=self.browser)
        except:
            if not silent:
                raise
            else:
                return None

    def querySelectorAll(self, selector, silent=True):
        try:
            ret_code, ret_msg, data = self.wrap_fire(action='f_$$', selector=selector)
            keys = data.get('keys')
            return [Elem(key=key, browser=self.browser) for key in keys]
        except:
            if not silent:
                raise
            else:
                return None

    def waitForNavigation(self, waitUntil='load', timeout=30000, silent=True):
        try:
            self.wrap_fire(action='f_waitForNavigation', options={
                'waitUntil': waitUntil,
                'timeout': timeout
            })
        except:
            if silent:
                return None
            else:
                raise

    def waitForSelector(self, selector, hidden=False, timeout=30000, visible=False, silent=True):
        options = {
            "hidden": hidden,
            'timeout': timeout,
            'visible': visible
        }
        try:
            ret_code, ret_msg, data = self.wrap_fire(action='f_waitForSelector', selector=selector, options=options)
            key = data.get('key')
            return Elem(key=key, browser=self.browser)
        except:
            if not silent:
                raise
            else:
                return None

    def click(self, selector, button='left', clickCount=1, delay=0, offset: dict = None):
        if not offset:
            offset = {'x': 0, 'y': 0}

        options = {
            'button': button,
            'clickCount': clickCount,
            'delay': delay,
            'offset': offset
        }
        if offset['x'] == 0 and offset['y'] == 0:
            options.pop('offset')
        self.wrap_fire(action='f_click', selector=selector, options=options)

    def evaluate(self, script):
        if script:
            script = _bytes_to_str(base64.b64encode(bytes(script, encoding='utf-8')))

        ret_code, ret_msg, data = self.wrap_fire(action='f_evaluate', script=script)
        return data.get('result')

    def eval(self, selector, attr='innerText'):
        ret_code, ret_msg, data = self.wrap_fire(action='f_$eval', selector=selector, attr=attr)
        return data.get('result')
