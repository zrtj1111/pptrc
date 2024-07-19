/**
 *  Author: Zr
 *  Email: zrtj1111@hotmail.com
 *  Create: 2024-7-19
 */

const fs = require("fs");

function isNoneOrFalse(val) {
  var has = Object.prototype.hasOwnProperty;
  var toString = Object.prototype.toString;

  // Null and Undefined...
  if (val == null) return true;

  // Booleans...
  if ("boolean" == typeof val) return !val;

  // Numbers...
  if ("number" == typeof val) return val === 0;

  // Strings...
  if ("string" == typeof val) return val.length === 0;

  // Functions...
  if ("function" == typeof val) return val.length === 0;

  // Arrays...
  if (Array.isArray(val)) return val.length === 0;

  // Errors...
  if (val instanceof Error) return val.message === "";

  // Objects...
  if (val.toString == toString) {
    switch (val.toString()) {
      // Maps, Sets, Files and Errors...
      case "[object File]":
      case "[object Map]":
      case "[object Set]": {
        return val.size === 0;
      }

      // Plain objects...
      case "[object Object]": {
        for (var key in val) {
          if (has.call(val, key)) return false;
        }

        return true;
      }
    }
  }

  // Anything else...
  return false;
}

module.exports.randomInt = (m, n) => {
  return Math.floor(Math.random() * (n - m + 1)) + m;
};
module.exports.sleep = async (millisecond) => {
  return new Promise((resolve) => setTimeout(resolve, millisecond));
};
module.exports.getJsonData = (file) => {
  try {
    var data = fs.readFileSync(file);
    return JSON.parse(data.toString());
  } catch (error) {
    console.log(error);
  }

  return null;
};
module.exports.pad = (num, length) => {
  return (Array(length).join("0") + num).slice(-length);
};
module.exports.mkdirsSync = (dirname) => {
  if (fs.existsSync(dirname)) {
    return true;
  } else {
    if (mkdirsSync(path.dirname(dirname))) {
      fs.mkdirSync(dirname);
      return true;
    }
  }
};

module.exports.isNoneOrFalse = isNoneOrFalse;
