/**
 *  Author: Zr
 *  Email: zrtj1111@hotmail.com
 *  Create: 2024-7-19
 */

const getLogger = require(__dirname + "/log").getLogger;
const util = require(__dirname + "/util");
const isNoneOrFalse = util.isNoneOrFalse;
const net = require("net");
const puppeteer = require("puppeteer-core");

var logger = null;
var BP_POOL = {};
var BP_TIMER = {};

class BrowserProxy {
  constructor() {
    this.id = null;
    this.browser = null;
    this.pages = null;
    this.frameCache = {};
    this.elemCache = {};
  }

  //==========================browser method============================
  async launch(options = {}) {
    if (!options.args) options.args = new Array();
    this.browser = await puppeteer.launch(options);
    this.id = await this.browser.wsEndpoint();
    this.pages = await this.browser.pages();

    return this;
  }

  quit() {
    this.browser.close();
  }

  async newPage() {
    await this.browser.newPage();
    this.pages = await this.browser.pages();
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        pageIndex: this.pages.length - 1,
      },
    };
  }

  async pagesCount() {
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        pages: this.pages.length,
      },
    };
  }

  _clearElemCache(s) {
    //s is `[PAGE_${pageIndex}`;
    for (const k of Object.keys(this.elemCache)) {
      if (k.indexOf(s) == 0) {
        logger.debug(`Page elemCache found: ${k}`);
        k = null;
      }
    }
  }

  _clearFrameCache(s) {
    // s is `[PAGE_${pageIndex}`;
    for (const k of Object.keys(this.frameCache)) {
      if (k.indexOf(s) == 0) {
        logger.debug(`Page frameCache found: ${k}`);
        k = null;
      }
    }
  }

  //===========================end browser methods============================/

  //============================Page Methods==================================/
  async setUserAgent(ctx) {
    await this.pages[ctx.pageIndex].setUserAgent(ctx.userAgent);
  }

  async $(ctx) {
    /**
     * ctx => selector
     */
    let key = `[PAGE_${ctx.pageIndex}][ELEM_${ctx.selector}]`;
    let elem = await this.pages[ctx.pageIndex].$(ctx.selector);
    if (isNoneOrFalse(elem)) {
      return {
        retCode: -1,
        retMsg: "Element not found",
      };
    }

    this.elemCache[key] = elem;

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        key: key,
      },
    };
  }

  async waitForSelector(ctx) {
    let key = `[PAGE_${ctx.pageIndex}][ELEM_${ctx.selector}]`;
    let elem = await this.pages[ctx.pageIndex].waitForSelector(
      ctx.selector,
      ctx.options
    );
    if (isNoneOrFalse(elem)) {
      return {
        retCode: -1,
        retMsg: "Element not found",
      };
    }

    this.elemCache[key] = elem;

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        key: key,
      },
    };
  }

  async $$(ctx) {
    /**
     * ctx => selector
     */
    //let key = `[PAGE_${ctx.pageIndex}][ELEM_${ctx.selector}]`;
    let elems = await this.pages[ctx.pageIndex].$$(ctx.selector);
    if (isNoneOrFalse(elems)) {
      return {
        retCode: -1,
        retMsg: "Element not found",
      };
    }

    let keys = new Array();
    for (let i = 0; i < elems.length; i++) {
      let key = `[PAGE_${ctx.pageIndex}][ELEM_${ctx.selector}][${i}]`;
      this.elemCache[key] = elems[i];
      keys.push(key);
    }

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        keys: keys,
      },
    };
  }

  async $eval(ctx) {
    let result = await this.pages[ctx.pageIndex].$eval(
      ctx.selector,
      (el, attr) => el[attr],
      ctx.attr
    );

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        result: result,
      },
    };
  }

  async $$eval(ctx) {
    let result = await this.pages[ctx.pageIndex].$$eval(
      ctx.selector,
      (els, attr) => {
        return els.map((el) => el[attr]);
      },
      ctx.attr
    );

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        result: result,
      },
    };
  }

  async setDefaultNavigationTimeout(ctx) {
    /**
     * ctx => timeout|milliseconds
     */
    await this.pages[ctx.pageIndex].setDefaultNavigationTimeout(ctx.timeout);
  }

  async evaluateOnNewDocument(ctx) {
    /**
     * ctx => pageIndex, script
     */
    let script = Buffer.from(ctx.script, "base64").toString();
    await this.pages[ctx.pageIndex].evaluateOnNewDocument((script) => {
      return eval(script);
    }, script);
  }

  async waitForNavigation(ctx) {
    this._clearElemCache(`[PAGE_${ctx.pageIndex}`);
    await this.pages[ctx.pageIndex].waitForNavigation(ctx.options);
  }

  async bringToFront(ctx) {
    /**
     * ctx => pageIndex
     */
    await this.pages[ctx.pageIndex].bringToFront();
  }

  async goto(ctx) {
    /**
     * ctx => pageIndex, url, options{waitUntil,timeout,referer}
     */
    let result = await this.pages[ctx.pageIndex].goto(ctx.url, ctx.options);
    this._clearElemCache(`[PAGE_${ctx.pageIndex}`);
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        status: result.status(),
      },
    };
  }

  async goForward(ctx) {
    await this.pages[ctx.pageIndex].goForward(ctx.options);
    this._clearElemCache(`[PAGE_${ctx.pageIndex}`);
  }

  async goBack(ctx) {
    await this.pages[ctx.pageIndex].goBack(ctx.options);
    this._clearElemCache(`[PAGE_${ctx.pageIndex}`);
  }

  async html(ctx) {
    let html = await this.pages[ctx.pageIndex].content();
    if (html) {
      html = Buffer.from(html).toString("base64");
    }

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        html: html,
      },
    };
  }

  async url(ctx) {
    let url = await this.pages[ctx.pageIndex].url();
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        url: url,
      },
    };
  }

  async setCookies(ctx) {
    /**
     * ctx => pageIndex|int, cookies|[]
     */
    if (ctx.cookies) {
      for (let cookie of ctx.cookies) {
        logger.debug("set cookies= %s", JSON.stringify(cookie));
        await this.pages[ctx.pageIndex].setCookie(cookie);
      }
    } else {
      logger.warn("ctx.cookies is null, pass.");
    }

    return {
      retCode: 1,
      retMsg: "OK",
    };
  }

  async getCookies(ctx) {
    let result = await this.pages[ctx.pageIndex].cookies();
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        cookies: result,
      },
    };
  }

  async closePage(ctx) {
    /**
     * ctx => pageIndex
     */
    this.pages = await this.browser.pages();
    if (this.pages.length == 1) {
      await this.quit();
    } else {
      await this.pages[ctx.pageIndex].close();
    }
  }

  async click(ctx) {
    /**
     * ctx => pageIndex, selector, selector_options
     */
    await this.pages[ctx.pageIndex].click(ctx.selector, ctx.options);
  }

  async tap(ctx) {
    await this.pages[ctx.pageIndex].tap((selector = ctx.selector));
  }

  async type(ctx) {
    await this.pages[ctx.pageIndex].type(ctx.selector, ctx.text, ctx.options);
  }

  async sendCharacter(ctx) {
    await this.pages[ctx.pageIndex].keyboard.sendCharacter(ctx.text);
  }

  async pdf(ctx) {
    await this.pages[ctx.pageIndex].pdf(ctx.options);
  }

  async scroll(ctx) {
    if (isNoneOrFalse(ctx.x)) ctx.x = 0;
    if (isNoneOrFalse(ctx.y))
      ctx.y = await this.pages[ctx.pageIndex].evaluate(
        () => window.innerHeight
      );

    await this.pages[ctx.pageIndex].evaluate(
      (x, y) => {
        window.scrollBy({
          left: x,
          top: y,
          behavior: "smooth",
        });
      },
      ctx.x,
      ctx.y
    );

    let t0 = 0;
    await util.sleep(200);
    let t1 = await this.pages[ctx.pageIndex].evaluate(
      () => document.documentElement.scrollTop || document.body.scrollTop
    );
    while (t0 != t1) {
      await util.sleep(200);
      t0 = t1;
      t1 = await this.pages[ctx.pageIndex].evaluate(
        () => document.documentElement.scrollTop || document.body.scrollTop
      );
    }

    //let h = await this.pages[ctx.pageIndex].evaluate(() => window.innerHeight);
    let scrollOffset = await this.pages[ctx.pageIndex].evaluate(
      () =>
        window.pageYOffset ||
        document.documentElement.scrollTop ||
        document.body.scrollTop
    );
    //let scrollHeight = await this.pages[ctx.pageIndex].evaluate(() => document.documentElement.scrollHeight || document.body.scrollHeight);
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        scrollOffset: scrollOffset,
      },
    };
  }

  async evaluate(ctx) {
    let script = Buffer.from(ctx.script, "base64").toString();
    let result = await this.pages[ctx.pageIndex].evaluate((script) => {
      return eval(script);
    }, script);
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        result: result,
      },
    };
  }

  async press(ctx) {
    await this.pages[ctx.pageIndex].keyboard.press(ctx.key);
    return {
      retCode: 1,
      retMsg: "OK",
    };
  }

  async screenShot(ctx) {
    await this.pages[ctx.pageIndex].screenshot({
      path: ctx.path,
      omitBackground: ctx.omitBackground,
    });

    return {
      retCode: 1,
      retMsg: "OK",
    };
  }

  //============================end page Methods===============================/

  //============================frame Methods==================================/
  async frames(ctx) {
    /**
     * ctx => selector
     */
    let keys = new Array();
    let frames = await this.pages[ctx.pageIndex].frames();
    for (let frame of frames) {
      let buff = Buffer.from(frame.url());
      let id = buff.toString("base64");
      let key = `[PAGE_${ctx.pageIndex}][FRAME_${id}]`;
      this.frameCache[key] = frame;
      keys.push(key);
    }

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        keys: keys,
      },
    };
  }

  async f_url(ctx) {
    let url = this.frameCache[ctx.frameKey].url();
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        url: url,
      },
    };
  }

  async f_$(ctx) {
    /**
     * ctx =>   selector
     *          frameKey
     */
    let key = `${ctx.frameKey}[${ctx.selector}]`;
    let elem = await this.frameCache[ctx.frameKey].$(ctx.selector);
    if (isNoneOrFalse(elem)) {
      return {
        retCode: -1,
        retMsg: "Element not found",
      };
    }

    this.elemCache[key] = elem;

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        key: key,
      },
    };
  }

  async f_$$(ctx) {
    /**
     * ctx =>   selector
     *          frameKey
     */
    let key = `${ctx.frameKey}[${ctx.selector}]`;
    let elems = await this.frameCache[ctx.frameKey].$$(ctx.selector);
    if (isNoneOrFalse(elems)) {
      return {
        retCode: -1,
        retMsg: "Element not found",
      };
    }

    let keys = new Array();
    for (let i = 0; i < elems.length; i++) {
      let key = `${ctx.frameKey}[ELEM_${ctx.selector}][${i}]`;
      this.elemCache[key] = elems[i];
      keys.push(key);
    }

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        keys: keys,
      },
    };
  }

  async f_click(ctx) {
    /**
     * ctx => pageIndex, frameKey, options
     */
    let frame = this.frameCache[ctx.frameKey];
    if (isNoneOrFalse(frame)) {
      return {
        retCode: -1,
        retMsg: "Frame not found in cache.",
      };
    }

    await frame.click(ctx.selector, ctx.options);
  }

  async f_waitForNavigation(ctx) {
    await this.frameCache[ctx.frameKey].waitForNavigation(ctx.options);
    this._clearElemCache(ctx.frameKey);
  }

  async f_waitForSelector(ctx) {
    /**
     * ctx =>   selector
     *          frameKey
     */
    let key = `${ctx.frameKey}[${ctx.selector}]`;
    let elem = await this.frameCache[ctx.frameKey].waitForSelector(
      ctx.selector,
      ctx.options
    );
    if (isNoneOrFalse(elem)) {
      return {
        retCode: -1,
        retMsg: "Element not found",
      };
    }

    this.elemCache[key] = elem;

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        key: key,
      },
    };
  }

  async f_evaluate(ctx) {
    let script = Buffer.from(ctx.script, "base64").toString();
    let result = await this.frameCache[ctx.frameKey].evaluate((script) => {
      return eval(script);
    }, script);
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        result: result,
      },
    };
  }

  async f_$eval(ctx) {
    let result = await this.frameCache[ctx.frameKey].$eval(
      ctx.selector,
      (el, attr) => el[attr],
      ctx.attr
    );

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        result: result,
      },
    };
  }

  async f_$$eval(ctx) {
    let result = await this.frameCache[ctx.frameKey].$$eval(
      ctx.selector,
      (els, attr) => {
        return els.map((el) => el[attr]);
      },
      ctx.attr
    );

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        result: result,
      },
    };
  }

  //============================End Frame Methods=============================/

  //============================Element methods=============================/
  async e_$(ctx) {
    /**
     * ctx => key, selector
     */
    let key = `${ctx.key}[${ctx.selector}]`;
    let elem = this.elemCache[ctx.key];
    if (isNoneOrFalse(elem)) {
      return {
        retCode: -1,
        retMsg: "Element not found in cache, use page.$ to cache again.",
      };
    }
    let elemChild = await elem.$(ctx.selector);
    if (isNoneOrFalse(elemChild)) {
      return {
        retCode: -1,
        retMsg: "Element not found in Element, use page.$ to cache again.",
      };
    }

    this.elemCache[key] = elemChild;

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        key: key,
      },
    };
  }

  async e_$$(ctx) {
    /**
     * ctx => key, selector
     */
    let key = `${ctx.key}[${ctx.selector}]`;
    let elem = this.elemCache[ctx.key];
    if (isNoneOrFalse(elem)) {
      return {
        retCode: -1,
        retMsg: "Element not found in cache, use page.$ to cache again.",
      };
    }

    let elemChildren = await elem.$$(ctx.selector);
    if (isNoneOrFalse(elemChildren)) {
      return {
        retCode: -1,
        retMsg: "Element not found in Element, use page.$ to cache again.",
      };
    }

    let keys = new Array();
    for (let i = 0; i < elemChildren.length; i++) {
      let _k = `${key}[${i}]`;
      this.elemCache[_k] = elemChildren[i];
      keys.push(_k);
    }

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        keys: keys,
      },
    };
  }

  async e_click(ctx) {
    /**
     * ctx => pageIndex,key
     */
    let elem = this.elemCache[ctx.key];
    if (isNoneOrFalse(elem)) {
      return {
        retCode: -1,
        retMsg: "Element not found in cache.",
      };
    }

    await elem.click(ctx.options);
  }

  async e_getProperty(ctx) {
    /**
     * ctx => attr
     */
    let elem = this.elemCache[ctx.key];
    if (isNoneOrFalse(elem)) {
      return {
        retCode: -1,
        retMsg: "Element not found in cache.",
      };
    }

    let ret = await (await elem.getProperty(ctx.attr)).jsonValue();

    if (ret) {
      ret = Buffer.from(ret).toString("base64");
    }

    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        value: ret,
      },
    };
  }

  async e_isIntersectingViewport(ctx) {
    let elem = this.elemCache[ctx.key];
    if (isNoneOrFalse(elem)) {
      return {
        retCode: -1,
        retMsg: "Element not found in cache.",
      };
    }
    let result = await elem.isIntersectingViewport();
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        result: result,
      },
    };
  }

  async e_scrollIntoView(ctx) {
    let elem = this.elemCache[ctx.key];
    if (isNoneOrFalse(elem)) {
      return {
        retCode: -1,
        retMsg: "Element not found in cache.",
      };
    }
    let result = await elem.scrollIntoView();
    return {
      retCode: 1,
      retMsg: "OK",
      data: {
        result: result,
      },
    };
  }

  //============================End Elem Methods=============================/
}

const resetTimer = (id, duration) => {
  let bp = BP_POOL[id];
  if (bp && duration > 0) {
    clearTimeout(BP_TIMER[bp.id]);
    BP_TIMER[bp.id] = setTimeout(
      (bp) => {
        bp.browser.close().then(() => {
          delete BP_POOL[id];
          logger.warn("time out, dipose browser instance. id: <%s>", id);
        });
      },
      duration,
      bp
    );
  }
};

const _write = (socket, resp) => {
  let data = JSON.stringify(resp);
  let num = util.pad(data.length, _headerLength);
  logger.debug("send data size: %d", num);
  socket.write(num + data);
};

const handleEvent = async (socket, data) => {
  logger.debug("recv: %s", data.toString());
  let resp = null;
  let jd = JSON.parse(data);

  try {
    let bp = BP_POOL[jd.id];
    if (jd.action == "launch") {
      if (bp) {
        bp = BP_POOL[jd.id];
      } else {
        bp = new BrowserProxy();
        bp = await bp.launch(jd.ctx.options);
        BP_POOL[bp.id] = bp;
        jd.id = bp.id;
      }
      resp = {
        retCode: 1,
        retMsg: "OK",
        data: {
          wsEndpoint: bp.id,
        },
      };
    } else {
      resp = await bp[jd.action](jd.ctx);
      logger.debug(
        `ElemCache size: ${
          Object.entries(bp.elemCache).length
        }, FrameCache size: ${Object.entries(bp.frameCache).length}`
      );
    }
  } catch (e) {
    resp = {
      retCode: -2,
      retMsg: e.message,
      data: {},
    };
    logger.error(e);
  } finally {
    resetTimer(jd.id, _duration);
    if (jd.action == "quit") {
      clearTimeout(BP_TIMER[jd.id]);
    }

    if (resp == null)
      resp = {
        retCode: 1,
        retMsg: "OK",
        data: {},
      };

    _write(socket, resp);
  }
};

//main
const args = process.argv.splice(2);
var _host = "0.0.0.0";
var _port = 9999;
var _logFile = null;
var _logLevel = "OFF";

const _maxConnections = 100;
const _headerLength = 8;
const _duration = 1800000;

if (!isNoneOrFalse(args)) {
  _host = args[0];
  _port = parseInt(args[1]);

  if (!isNoneOrFalse(args[2])) {
    _logLevel = args[2];
  }

  if (!isNoneOrFalse(args[3])) {
    _logFile = args[3];
  }
}

logger = getLogger(_logLevel, _logFile);
var server = net.createServer();

server.maxConnections = _maxConnections;
server.listen(_port, _host);

server.on("listening", function () {
  logger.info(
    "listening on: %s:%d, maxConnections: %d, headLength: %d, duration:%d, logLevel: %s, logFile: %s",
    _host,
    _port,
    _maxConnections,
    _headerLength,
    _duration,
    _logLevel,
    _logFile
  );
});

server.on("connection", async (socket) => {
  logger.info(
    "client connected: " + socket.remoteAddress + ":" + socket.remotePort
  );
  socket.setEncoding("utf8");

  let recv = "";
  let msgLen = 0;

  socket.on("data", async (data) => {
    //logger.debug(typeof data);
    if (msgLen == 0) {
      msgLen = parseInt(data.substring(0, _headerLength));
      recv += data.substring(_headerLength, data.length);
    } else {
      recv += data;
    }

    if (recv.length == msgLen) {
      await handleEvent(socket, recv);
      recv = "";
      msgLen = 0;
    }
  });

  socket.on("end", function () {
    logger.info("client disconnected");
    server.getConnections((err, count) => {
      logger.info("remaining connections: " + count);
    });
  });

  socket.on("error", function (err) {
    logger.error(err);
  });

  socket.on("timeout", function () {
    logger.warn("socket timeout");
  });
});
