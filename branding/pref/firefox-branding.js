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
