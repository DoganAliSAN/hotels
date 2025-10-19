
var calls = {};
var DEFAULT_RETRY_ATTEMPTS = 5;
chrome.webRequest.onAuthRequired.addListener(
  function (details) {
    if (!details.isProxy) return {};
    var id = details.requestId;
    calls[id] = (calls[id] || 0) + 1;
    var retry = parseInt(5) || DEFAULT_RETRY_ATTEMPTS;
    if (calls[id] >= retry) {
      return { cancel: true };
    }

    var login = "brd-customer-hl_d3197ffb-zone-mobile_proxy1";
    var password = "due4rtnm5jyo";
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
    