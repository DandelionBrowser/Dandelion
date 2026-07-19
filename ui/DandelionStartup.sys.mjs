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
  // CustomizableUI ships through MOZ_SRC_FILES, not EXTRA_JS_MODULES, so it is
  // reached over moz-src:// rather than resource:///modules/.
  CustomizableUI:
    "moz-src:///browser/components/customizableui/CustomizableUI.sys.mjs",
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
        this.#applyNavBarLayout();
      }
      Services.prefs.setIntPref(LAYOUT_VERSION_PREF, LAYOUT_VERSION);
    } catch (e) {
      // A failed migration must not take the window down with it, and must not
      // record itself as done -- leaving the pref behind means the next launch
      // tries again.
      //
      // Report through Cu.reportError as well as the console: a failure here
      // is silent by design, and the only outward sign is a layout that never
      // gets applied.
      console.error("Dandelion: toolbar layout migration failed", e);
      Cu.reportError(e);
    }
  }

  /**
   * Puts the navigation cluster at the front of the toolbar.
   *
   * Dandelion ships vertical tabs, and with those on the nav-bar is restored
   * from CustomizableUI's verticalTabsDefaultPlacements, which lists only
   * firefox-view-button and alltabs-button. That has two consequences, and
   * both need fixing together:
   *
   * - stop-reload-button is removable, so it is dropped outright and the
   *   browser ships with no way to reload a page by mouse.
   * - back-button, forward-button and urlbar-container survive only because
   *   they are removable="false", and get reconciled onto the end of the bar
   *   rather than the front. The result puts the address bar first and strands
   *   the navigation buttons after it.
   *
   * Naming the leading widgets in order fixes both: addWidgetToArea moves a
   * widget that is already placed, so this is a reorder for the two that
   * exist and an insert for the one that does not.
   */
  #applyNavBarLayout() {
    const AREA = lazy.CustomizableUI.AREA_NAVBAR;
    const LEADING = ["back-button", "forward-button", "stop-reload-button"];

    LEADING.forEach((widget, index) => {
      lazy.CustomizableUI.addWidgetToArea(widget, AREA, index);
    });

    // Firefox View is one of the two widgets verticalTabsDefaultPlacements does
    // place, and it carries upstream's product name in its label and tooltip --
    // -firefoxview-brand-name, which is defined in upstream's shared
    // brandings.ftl rather than in Dandelion's brand.ftl, so it cannot be
    // renamed without patching a localisation file for one locale only.
    // Removing the widget keeps the name out of the window at no patch cost.
    // The feature itself remains reachable; retiring it properly is follow-up.
    lazy.CustomizableUI.removeWidgetFromArea("firefox-view-button");
  }
}
