/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

/**
 * about:dandelion -- Dandelion's new tab page.
 *
 * Registered from Dandelion's own components.conf as a JS nsIAboutModule. The
 * C++ AboutRedirector would have meant patching two shared upstream files, so
 * this route is what keeps the page free of merge debt.
 */

const PAGE_URL = "chrome://dandelion/content/newtab.html";

export function AboutDandelion() {}

AboutDandelion.prototype = {
  QueryInterface: ChromeUtils.generateQI(["nsIAboutModule"]),

  /**
   * These are about:privatebrowsing's flags, and the choice is deliberate.
   *
   * The page is served from a chrome: URL but must NOT be chrome-privileged:
   * URI_MUST_LOAD_IN_CHILD plus URI_CAN_LOAD_IN_PRIVILEGEDABOUT_PROCESS keep
   * it in the privilegedabout content process, the same place upstream puts
   * its own new tab page. It therefore has no access to Places or the search
   * service, and reaches both through DandelionNewTab{Parent,Child} instead.
   *
   * IS_SECURE_CHROME_UI is intentionally absent -- it would grant the page
   * chrome privileges in the parent process, which is far too much authority
   * for a page that renders titles taken from arbitrary websites.
   */
  getURIFlags() {
    return (
      Ci.nsIAboutModule.URI_SAFE_FOR_UNTRUSTED_CONTENT |
      Ci.nsIAboutModule.URI_MUST_LOAD_IN_CHILD |
      Ci.nsIAboutModule.ALLOW_SCRIPT |
      Ci.nsIAboutModule.URI_CAN_LOAD_IN_PRIVILEGEDABOUT_PROCESS
    );
  },

  newChannel(aURI, aLoadInfo) {
    let uri = Services.io.newURI(PAGE_URL);
    let channel = Services.io.newChannelFromURIWithLoadInfo(uri, aLoadInfo);
    // Keep about:dandelion in the address bar rather than the chrome: URL the
    // channel actually loads.
    channel.originalURI = aURI;
    return channel;
  },
};
