/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

// Branding-specific preferences for Dandelion.
//
// The file name is fixed by browser/branding/branding-common.mozbuild, which
// packages pref/firefox-branding.js for every brand.

pref("startup.homepage_override_url", "");
pref("startup.homepage_welcome_url", "");
pref("startup.homepage_welcome_url.additional", "");

// The time interval between checks for a new version, in seconds.
pref("app.update.interval", 86400); // 24 hours
// How long to wait before showing the update UI prominently, in seconds.
pref("app.update.promptWaitTime", 86400);

// Where a user can go if every update installation attempt fails, and where
// the "More information about this update" link points.
pref("app.update.url.manual", "https://github.com/ChristianRelf/Dandelion");
pref("app.update.url.details", "https://github.com/ChristianRelf/Dandelion");

// How many days a binary may go without an update check.
pref("app.update.checkInstallTime.days", 2);

// Show the update badge on the app menu button immediately.
pref("app.update.badgeWaitTime", 0);

// Pasting into the web console is blocked until it has been used this many
// times, as a self-XSS guard.
pref("devtools.selfxss.count", 5);

// ---------------------------------------------------------------------------
// Dandelion defaults
//
// These are defaults, not locks: everything here remains changeable in
// Settings or about:config. They exist so that a fresh profile behaves the way
// Dandelion is meant to, rather than the way Firefox is.
// ---------------------------------------------------------------------------

// Vertical tabs in the sidebar are Dandelion's default shape, rather than a
// horizontal strip. The sidebar revamp is what implements them, so it has to
// be on for the vertical layout to exist at all.
pref("sidebar.revamp", true);
pref("sidebar.verticalTabs", true);
pref("sidebar.visibility", "always-show");

// Enhanced Tracking Protection at its strictest setting. This is the single
// biggest privacy difference between a default Firefox and Dandelion, and it
// is the reason to prefer a Gecko base in the first place.
pref("browser.contentblocking.category", "strict");

// Global Privacy Control asserts an opt-out of sale and sharing, and unlike
// Do Not Track it carries legal weight in several jurisdictions.
pref("privacy.globalprivacycontrol.enabled", true);

// Dandelion collects nothing. There is no telemetry endpoint to receive it,
// so leaving these on would only send data to Mozilla.
pref("datareporting.healthreport.uploadEnabled", false);
pref("datareporting.policy.dataSubmissionEnabled", false);
pref("toolkit.telemetry.unified", false);
pref("toolkit.telemetry.archive.enabled", false);
pref("app.shield.optoutstudies.enabled", false);
pref("browser.discovery.enabled", false);

// Sponsored placements on the new tab page are advertising. A browser that
// ships strict tracking protection should not be selling the new tab.
pref("browser.newtabpage.activity-stream.showSponsored", false);
pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);

// ---------------------------------------------------------------------------
// Mozilla services
//
// Dandelion ships no account service, no VPN and no companion apps, so the UI
// that sells them is not merely off-brand, it points at nothing.
// ---------------------------------------------------------------------------

// Firefox Accounts is Mozilla's identity service and it is what Sync is built
// on. Turning it off removes the sign-in button, the account menu, the Sync
// setup flow, send-tab and the onboarding sign-in screens together, because
// they all gate on this one pref -- it is the same switch Mozilla's own
// DisableFirefoxAccounts enterprise policy throws.
//
// Dandelion has no sync service to offer in its place, so this removes
// cross-device syncing outright rather than replacing it.
//
// A restart is required after changing this.
pref("identity.fxaccounts.enabled", false);

// UITour lets a privileged mozilla.org page drive this browser's interface --
// open panels, highlight widgets, read prefs. It exists to run Mozilla's own
// onboarding tours, which Dandelion does not ship, so leaving it on grants a
// third-party origin control over the chrome for no benefit.
pref("browser.uitour.enabled", false);

// Cross-promotion for Mozilla VPN, Focus and the mobile apps, shown on
// about:protections and in the toolbar.
pref("browser.vpn_promo.enabled", false);
pref("browser.promo.focus.enabled", false);
pref("browser.contentblocking.report.show_mobile_app", false);
pref("browser.contentblocking.report.hide_vpn_banner", true);

// ---------------------------------------------------------------------------
// Help and support
//
// Every help link routes to Dandelion's wiki, so no help link reaches Mozilla.
// ---------------------------------------------------------------------------

// Upstream appends a help topic to this. Dandelion's wiki has no page per
// topic, so the two places that do the appending drop it and land on the wiki
// itself rather than on a 404 -- see the utilityOverlay.js and
// moz-support-link.mjs patches. Once the wiki has a page per topic, restore
// the concatenation there and remove both patches.
pref("app.support.baseURL", "https://github.com/ChristianRelf/Dandelion/wiki/");

// Feedback belongs on the issue tracker rather than the wiki, which is the
// one place a report can actually be acted on.
pref("app.feedback.baseURL", "https://github.com/ChristianRelf/Dandelion/issues");

// "Learn more" on the permission prompts.
pref("browser.geolocation.warning.infoURL", "https://github.com/ChristianRelf/Dandelion/wiki/Location");
pref("browser.xr.warning.infoURL", "https://github.com/ChristianRelf/Dandelion/wiki/Virtual-reality");
pref("browser.lna.warning.infoURL", "https://github.com/ChristianRelf/Dandelion/wiki/Local-network");

// The about:protections cards.
pref("browser.contentblocking.report.lockwise.how_it_works.url", "https://github.com/ChristianRelf/Dandelion/wiki/Passwords");
pref("browser.contentblocking.report.social.url", "https://github.com/ChristianRelf/Dandelion/wiki/Tracking-protection");
pref("browser.contentblocking.report.cookie.url", "https://github.com/ChristianRelf/Dandelion/wiki/Tracking-protection");
pref("browser.contentblocking.report.tracker.url", "https://github.com/ChristianRelf/Dandelion/wiki/Tracking-protection");
pref("browser.contentblocking.report.fingerprinter.url", "https://github.com/ChristianRelf/Dandelion/wiki/Tracking-protection");
pref("browser.contentblocking.report.cryptominer.url", "https://github.com/ChristianRelf/Dandelion/wiki/Tracking-protection");
