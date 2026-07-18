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
