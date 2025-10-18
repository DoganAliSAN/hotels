
var calls = {};
var DEFAULT_RETRY_ATTEMPTS = 5;
var NOTIFICATION_ID = "proxy_auth_lock";
chrome.webRequest.onAuthRequired.addListener(
  function (details) {

    if (!details.isProxy) return {};
    var id = details.requestId;
    calls[id] = (calls[id] || 0) + 1;
    var retry = parseInt(5) || DEFAULT_RETRY_ATTEMPTS;
    if (calls[id] >= retry) {
      return { cancel: true };
    }
    var login = "q5coGiY";
    var password = "XrjoFc4C5xwkdPO";

    if (login && password) {
      return {
        authCredentials: {
          username: login,
          password: password
        }
      };
    }
    return {};
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);
    