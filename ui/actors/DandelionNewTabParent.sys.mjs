/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

/**
 * Parent half of about:dandelion.
 *
 * The page runs unprivileged in the privilegedabout process, so everything
 * that needs Places or the search service happens here. This is the trust
 * boundary: treat every message as coming from a page that renders content
 * taken from arbitrary websites.
 */

const lazy = {};

ChromeUtils.defineESModuleGetters(lazy, {
  NewTabUtils: "resource://gre/modules/NewTabUtils.sys.mjs",
});

// Enough to fill the grid without turning the page into a history browser.
const TOP_SITE_COUNT = 8;

export class DandelionNewTabParent extends JSWindowActorParent {
  async receiveMessage(message) {
    switch (message.name) {
      case "Dandelion:Init":
        return this.#init();
      case "Dandelion:Search":
        return this.#searchURL(message.data?.query);
      default:
        return undefined;
    }
  }

  get #isPrivate() {
    return this.browsingContext.usePrivateBrowsing;
  }

  /**
   * Overriding AboutNewTab.newTabURL takes private windows too -- upstream
   * only falls back to about:privatebrowsing while the URL is not overridden
   * (browser/base/content/utilityOverlay.js). So about:dandelion is also the
   * private new tab page, and must not put browsing history on it.
   *
   * The check lives here rather than in the page because the page is the
   * untrusted side: if it is ever wrong, no history should have crossed the
   * boundary in the first place.
   */
  async #init() {
    if (this.#isPrivate) {
      return { isPrivate: true, topSites: [] };
    }

    let links = await lazy.NewTabUtils.activityStreamLinks.getTopSites({
      numItems: TOP_SITE_COUNT,
      includeFavicon: false,
    });

    let topSites = (links ?? [])
      .filter(link => link?.url)
      .slice(0, TOP_SITE_COUNT)
      .map(link => ({ url: link.url, title: link.title || "" }));

    return { isPrivate: false, topSites };
  }

  /**
   * Resolves a query against the default engine and hands back the URL for the
   * page to navigate to.
   *
   * Engines submitting by POST are not supported here; they would need the
   * navigation to happen on this side with the post data attached. Returning
   * null leaves the page's field inert rather than silently searching wrongly.
   */
  async #searchURL(query) {
    if (typeof query != "string") {
      return null;
    }
    let trimmed = query.trim();
    if (!trimmed) {
      return null;
    }

    let engine = await Services.search.getDefault();
    let submission = engine?.getSubmission(trimmed);
    if (!submission?.uri || submission.postData) {
      return null;
    }
    return submission.uri.spec;
  }
}
