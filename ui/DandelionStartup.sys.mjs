/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

/**
 * Dandelion's entry point into the browser.
 *
 * Registered against profile-after-change in components.conf, which is what
 * lets Dandelion run chrome code without patching BrowserGlue. Everything
 * Dandelion needs to do per-profile or per-window is hung off here rather than
 * pasted into Firefox's own startup path.
 */

const lazy = {};

ChromeUtils.defineESModuleGetters(lazy, {
  AboutNewTab: "resource:///modules/AboutNewTab.sys.mjs",
  CustomizableUI: "resource:///modules/CustomizableUI.sys.mjs",
  EveryWindow: "resource:///modules/EveryWindow.sys.mjs",
});

const EVERY_WINDOW_ID = "dandelion-startup";

const NEW_TAB_URL = "about:dandelion";

/**
 * The toolbar layout Dandelion ships, applied once per profile.
 *
 * This is a migration counter, not a feature flag. Each step runs exactly once
 * and only for profiles that have not seen it, so a user who deliberately
 * removes a widget does not get it forced back at the next launch. Bump
 * LAYOUT_VERSION and add a step to apply a new default to existing profiles.
 */
const LAYOUT_VERSION = 1;
const LAYOUT_VERSION_PREF = "dandelion.uiLayout.version";

export class DandelionStartup {
  classID = Components.ID("{0ebd2549-ddd1-436b-9e80-2e72d3bf24ee}");
  QueryInterface = ChromeUtils.generateQI(["nsIObserver"]);

  observe(subject, topic) {
    if (topic == "profile-after-change") {
      this.#init();
    }
  }

  #init() {
    this.#registerNewTabActor();

    // Setting this is what makes every "open a new tab" path land on
    // about:dandelion; upstream reads it through BROWSER_NEW_TAB_URL. Note
    // that it takes private windows too -- upstream only falls back to
    // about:privatebrowsing while the URL is not overridden -- which is why
    // about:dandelion has a private mode of its own.
    lazy.AboutNewTab.newTabURL = NEW_TAB_URL;

    // The layout migration needs CustomizableUI's saved state loaded and a
    // window past delayed startup, so it runs from the window callback rather
    // than straight from profile-after-change. The version pref keeps it to
    // once per profile however many windows open.
    lazy.EveryWindow.registerCallback(
      EVERY_WINDOW_ID,
      () => this.#applyLayout(),
      () => {}
    );
  }

  /**
   * Registering at runtime keeps the actor out of the shared
   * DesktopActorRegistry table, so it costs no patch.
   */
  #registerNewTabActor() {
    ChromeUtils.registerWindowActor("DandelionNewTab", {
      parent: {
        esModuleURI: "resource:///actors/DandelionNewTabParent.sys.mjs",
      },
      child: {
        esModuleURI: "resource:///actors/DandelionNewTabChild.sys.mjs",
        events: {
          // Dispatched by the page, which is untrusted, so these have to be
          // accepted as untrusted events.
          DandelionNewTabInit: { wantUntrusted: true },
          DandelionNewTabSearch: { wantUntrusted: true },
        },
      },
      matches: [`${NEW_TAB_URL}*`],
      remoteTypes: ["privilegedabout"],
    });
  }

  #applyLayout() {
    let applied = Services.prefs.getIntPref(LAYOUT_VERSION_PREF, 0);
    if (applied >= LAYOUT_VERSION) {
      return;
    }

    try {
      if (applied < 1) {
        this.#restoreReloadButton();
      }
      Services.prefs.setIntPref(LAYOUT_VERSION_PREF, LAYOUT_VERSION);
    } catch (e) {
      // A failed migration must not take the window down with it, and must not
      // record itself as done -- leaving the pref behind means the next launch
      // tries again.
      console.error("Dandelion: toolbar layout migration failed", e);
    }
  }

  /**
   * Puts the reload button back.
   *
   * Dandelion ships vertical tabs, and with those on the nav-bar is restored
   * from CustomizableUI's verticalTabsDefaultPlacements, which lists only
   * firefox-view-button and alltabs-button. Back, forward and the address bar
   * survive that because they are removable="false"; stop-reload-button is
   * removable, so it is simply dropped and the browser ships with no way to
   * reload a page by mouse.
   */
  #restoreReloadButton() {
    const WIDGET = "stop-reload-button";
    const AREA = lazy.CustomizableUI.AREA_NAVBAR;

    let placements = lazy.CustomizableUI.getWidgetIdsInArea(AREA);
    if (placements.includes(WIDGET)) {
      return;
    }

    // Sit immediately after forward-button so the cluster reads
    // back -> forward -> reload. Both are removable="false" and so are always
    // present, but fall back to the front of the bar rather than assuming it.
    let forward = placements.indexOf("forward-button");
    let position = forward == -1 ? 0 : forward + 1;

    lazy.CustomizableUI.addWidgetToArea(WIDGET, AREA, position);
  }
}
