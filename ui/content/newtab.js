/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

/* about:dandelion's page script.
 *
 * Runs unprivileged. It cannot reach Places or the search service itself, so
 * it asks DandelionNewTabChild by dispatching events and waits for the answer
 * to come back the same way.
 *
 * Everything here builds nodes and sets textContent. Titles and URLs come from
 * whatever sites the user has visited, so none of it may ever be interpolated
 * into markup. */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("search-form");
  const field = document.getElementById("search-field");
  const topSites = document.getElementById("top-sites");
  const privateNote = document.getElementById("private-note");

  form.addEventListener("submit", event => {
    event.preventDefault();
    const query = field.value;
    if (!query.trim()) {
      return;
    }
    window.dispatchEvent(
      new CustomEvent("DandelionNewTabSearch", { detail: { query } })
    );
  });

  window.addEventListener("DandelionNewTabData", event => {
    const data = event.detail;
    if (!data) {
      return;
    }

    privateNote.hidden = !data.isPrivate;

    const sites = Array.isArray(data.topSites) ? data.topSites : [];
    topSites.textContent = "";
    topSites.hidden = !sites.length;
    for (const site of sites) {
      topSites.appendChild(buildTile(site));
    }
  });

  window.dispatchEvent(new CustomEvent("DandelionNewTabInit"));
});

/**
 * A top site tile.
 *
 * The mark is the first letter of the host rather than a favicon: it needs no
 * network or cache access, cannot fail to load, and keeps the grid visually
 * even.
 */
function buildTile(site) {
  const host = hostOf(site.url);

  const tile = document.createElement("a");
  tile.className = "tile";
  tile.href = site.url;

  const badge = document.createElement("span");
  badge.className = "tile-badge";
  badge.textContent = (host || "?").charAt(0).toUpperCase();

  const label = document.createElement("span");
  label.className = "tile-label";
  label.textContent = site.title || host || site.url;

  // The full URL belongs in the tooltip, not the visible label, so a long or
  // deceptive title cannot push the host out of view.
  tile.title = site.url;

  tile.append(badge, label);
  return tile;
}

function hostOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch (e) {
    return "";
  }
}
