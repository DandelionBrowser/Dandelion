/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

/**
 * Child half of about:dandelion.
 *
 * The page cannot talk to the parent process directly, so it dispatches events
 * and this relays them. Results come back as an event carrying a structured
 * clone, which is the same shape about:privatebrowsing uses.
 */

export class DandelionNewTabChild extends JSWindowActorChild {
  handleEvent(event) {
    switch (event.type) {
      case "DandelionNewTabInit":
        this.#init();
        break;
      case "DandelionNewTabSearch":
        this.#search(event.detail?.query);
        break;
    }
  }

  async #init() {
    let data = await this.sendQuery("Dandelion:Init");
    this.#dispatch("DandelionNewTabData", data);
  }

  async #search(query) {
    // The page is untrusted, so the query crosses the boundary as a plain
    // string and the parent decides whether it resolves to anything.
    let url = await this.sendQuery("Dandelion:Search", {
      query: typeof query == "string" ? query : "",
    });
    if (url) {
      this.contentWindow?.location.assign(url);
    }
  }

  #dispatch(type, detail) {
    let win = this.contentWindow;
    if (!win) {
      return;
    }
    win.dispatchEvent(
      new win.CustomEvent(type, { detail: Cu.cloneInto(detail, win) })
    );
  }
}
