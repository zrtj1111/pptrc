/**
 *  Author: Zr
 *  Email: zrtj1111@hotmail.com
 *  Create: 2024-7-19
 */
const log4js = require("log4js");

function getLogger(level, log_file) {
  let _level = level == undefined ? "OFF" : level;
  let _appenders = log_file == undefined ? ["console"] : ["console", "file"];

  log4js.configure({
    appenders: {
      console: {
        type: "console",
        layout: {
          type: "pattern",
          pattern: "%d{yyyy-MM-dd hh:mm:ss} %[[%5p]%] %f{1} %M  %m",
        },
      },
      file: {
        type: "file",
        filename: log_file,
        maxLogSize: 10485760,
        backups: 3,
        encoding: "utf-8",
        layout: {
          type: "pattern",
          pattern: "%d{yyyy-MM-dd hh:mm:ss} [%5p] %f{1} %M  %m",
        },
      },
    },
    categories: {
      default: {
        appenders: _appenders,
        level: _level,
        enableCallStack: true,
      },
    },
  });

  return log4js.getLogger();
}

module.exports.getLogger = getLogger;
