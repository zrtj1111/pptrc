# -*- coding: utf-8 -*-
# @Time    : 2024/7/19 下午4:35 下午4:35
# @Author  : Zr
# @Comment :
import os

if __name__ == '__main__':
    from pptrc import LocalPPTRSMgr, Browser

    s = LocalPPTRSMgr(log_level='debug', log_file=os.path.join(os.path.dirname(__file__), 'test.log'))
    s.stop()
    s.start()

    b = Browser()
    b.launch(headless=False)
    p = b.getPage()
    p.goto('http://www.douban.com')
