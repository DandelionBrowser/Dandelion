# Interface

Dandelion's interface lives in `ui/`, which is mounted into the Firefox tree at
`browser/components/dandelion` and listed in `browser/components/moz.build`.

That mount is the important part. It does not make `ui/` a folder of stylesheets
that happen to be copied into the build — it makes it a **Firefox component
directory**, with the same capabilities as `browser/components/firefoxview` or
`browser/components/aboutlogins`. Almost everything an interface needs can be
declared there, and none of it costs a patch.

## What belongs where

| Want | Put it in | Patch needed |
| --- | --- | --- |
| Styling for the browser window | `ui/content/chrome.css` | no |
| A design token | `ui/content/tokens.css` | no |
| Chrome JS that runs per window | a module + `EveryWindow` | no |
| Code that runs once at startup | `components.conf` category | no |
| An `about:` page | `components.conf` + `nsIAboutModule` | no |
| Data for an unprivileged page | a JSWindowActor pair | no |
| Moving a widget between toolbars | `CustomizableUI` at runtime | no |
| A new toolbar or chrome region | — | **yes** |
| Relocating the address bar | — | **yes** |

Reach for the last two only when the first ten cannot do it. See
[PATCHES.md](PATCHES.md) for why.

## The pieces

**`components.conf`** is the bootstrap. A `categories` entry against
`profile-after-change` gets Dandelion's first line of chrome code run without
touching `BrowserGlue`. `DandelionStartup.sys.mjs` is that entry point, and
everything else hangs off it.

**`chrome://dandelion/`** is registered by `jar.mn` and is how chrome code and
Dandelion's own pages reach these files.

**Per-window work** goes through `EveryWindow.registerCallback`, upstream's own
answer to "run this on every browser window". It replaces what would otherwise
be a `<script>` patched into `browser.xhtml`.

**`about:` pages** register as a JS `nsIAboutModule` from `components.conf`. Do
not use the C++ `AboutRedirector`: its map and its `components.conf` are shared
upstream files, which is why `firefoxview` and `pocket` are not self-contained.

**Actors** are registered at runtime with `ChromeUtils.registerWindowActor`, so
they stay out of the shared `DesktopActorRegistry` table. Their files ship via
`FINAL_TARGET_FILES.actors`.

## Rules

**Set Firefox's theming variables, do not override the rules that read them.**
Upstream moves its widgets around constantly. A restyle that names
`--toolbar-bgcolor` follows it; one that targets a selector three levels deep
breaks at the next roll.

**No hardcoded colours, radii or durations outside `tokens.css`.** If a value is
needed twice, it belongs there.

**Dandelion's own pages are not privileged.** `about:dandelion` is served from a
`chrome:` URL but pinned to the `privilegedabout` content process, exactly as
`about:privatebrowsing` is, and deliberately without `IS_SECURE_CHROME_UI`. It
renders titles taken from arbitrary websites, so it gets no more authority than
a web page and reaches privileged data through an actor.

**Decide privacy on the privileged side.** The parent actor refuses to send
browsing history to a private window. Putting that check in the page would mean
trusting the untrusted half.

**Layout defaults are versioned, not reapplied.** `DandelionStartup` records
which layout steps a profile has seen. Reapplying them at every launch would
force widgets back onto a user who removed them.
