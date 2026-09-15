# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this fork is for

Cavalier-bar is a personal fork of [NickvisionApps/Cavalier](https://github.com/NickvisionApps/Cavalier) (via an intermediate fork, `WatashiAD/Cavalier-extra`), based on upstream commit `edc8f05` ("Add more CAVA customization options" — input method dropdown, gravity slider, 8-band equalizer, finer sensitivity steps). It intentionally excludes that fork's later README/screenshot churn and an unrelated stray commit that added an InvokeAI Colab notebook.

The goal of this fork is to make Cavalier usable as a thin, docked, always-on-screen audio-wave bar (via an external window manager rule, e.g. devilspie2) rather than only as a normal floating window. Changes so far, all in `NickvisionCavalier.GNOME/Blueprints/window.blp`:
- `height-request` lowered from `232` to `40` on `Adw.ApplicationWindow` (upstream hardcodes both `width-request`/`height-request` to `232`, which silently clamps any window-manager-driven resize back to that floor). The real achieved minimum ended up around `78px`, not `40` — see Known gotchas.
- Header's `Gtk.MenuButton` removed (actions still reachable via existing accelerators: `Ctrl+,` Preferences, `Ctrl+?` shortcuts, `Ctrl+Q` quit, `F1` about) and its `Gtk.Revealer` switched from `crossfade` to `slide_down` so `AutohideHeader` actually collapses the header instead of just fading it.
- `Gtk.WindowHandle` removed entirely (see Known gotchas — it made right-click close the window).

Work in this repo should assume the target is still a normal Cavalier build/install (dotnet, native or flatpak), just with a lower minimum window size and whatever other docked-bar-friendly tweaks get added later (additional CLI/config options for positioning, etc).

## Build & run

The repo's own `CONTRIBUTING.md` documents a [Cake](https://cakebuild.net/)-based build via the `CakeScripts` git submodule — **that submodule is currently inaccessible** (`NickvisionApps/CakeScripts` 404s over both `git clone` and the GitHub API, likely made private; the same broken reference exists in current upstream `NickvisionApps/Cavalier`, `Denaro`, `Tagger`, so it's not specific to this fork). Don't spend time on `git submodule update --init` — it will fail.

This doesn't actually block building: `NickvisionCavalier.GNOME.csproj` wires blueprint-compiler, `glib-compile-resources`, and `.po` translation compilation into its own MSBuild `PreBuild`/`PostBuild`/`PostPublish` targets, so plain dotnet commands work standalone:

| Command | Result |
|---|---|
| `dotnet build` (inside `NickvisionCavalier.GNOME/`) | Compiles blueprints/resources/translations and builds the app. |
| `dotnet run` (inside `NickvisionCavalier.GNOME/`) | Builds and runs in place (not installed — some icons/desktop integration may be missing). |

Native (non-flatpak) build dependencies, all available directly via `apt` on Ubuntu 24.04/Mint 22.3: `dotnet-sdk-10.0` (the project targets `net10.0`, not the `net8.0` upstream's own docs mention — `dotnet-sdk-8.0` alone isn't enough), `libgtk-4-dev`, `libadwaita-1-dev`, `blueprint-compiler`.

At runtime the app also needs a standalone `cava` binary on `PATH` (it shells out to it — see `NickvisionCavalier.Shared/Models/CAVA.cs`). Ubuntu's packaged `cava` is `0.7.4`, older than the `>=0.9.1` this app expects; build from source instead:
```
git clone https://github.com/karlstav/cava.git
cd cava && ./autogen.sh && ./configure --prefix="$HOME/.local" && make && make install
```
Needs `libfftw3-dev libiniparser-dev libasound2-dev libpulse-dev libncurses-dev libtool automake autoconf pkg-config` (all via apt).

To build/run as a flatpak instead (needed to override a Flathub-installed `org.nickvision.cavalier` in place), use `flatpak-builder` against `flatpak/org.nickvision.cavalier.json` — this manifest pins `org.gnome.Platform`/`Sdk` version 45 (flagged EOL by Flathub, but still installs and runs) and the `dotnet8` SDK extension (stale — the project now targets net10.0; hasn't been an issue in practice but worth knowing). The app id is unchanged (`org.nickvision.cavalier`), so a flatpak build from this repo replaces/collides with any Flathub install of upstream Cavalier under the same id. Note: on a very new GPU (e.g. RDNA4 `gfx1201`), the flatpak's bundled Mesa/LLVM may be too old to recognize the GPU target and silently falls back to a software rendering path — harmless for a small docked bar, but a real perf hit for a full-size window. The native build uses the host's own (current) Mesa, avoiding this.

There is no test suite in this repo.

## Known gotchas (found while building the docked-bar variant)

- **`Gtk.WindowHandle` and right-click**: this widget (used so a CSD-less window can still be dragged) forwards a secondary click to the window manager's system context menu (move/resize/**close**). On an undecorated, WM-pinned bar that's never meant to be dragged, that surfaced as right-clicking the bar closing it. Fixed by removing the `WindowHandle` from `window.blp` entirely — don't re-add one without also handling this.
- **`Gtk.Revealer` with `transition-type: crossfade`** only animates opacity; it never collapses the reserved layout space. `AutohideHeader` toggling `reveal-child` on the header's revealer had no visible effect on window height until the transition type was changed to `slide_down`.
- **`width-request`/`height-request` on `Adw.ApplicationWindow`** is a real floor GTK enforces, including against an external WM script (devilspie2) requesting a smaller size — it silently clamps back up. Even after lowering it to `40` and removing the menu button/`WindowHandle`, the real achieved minimum height is ~`78px` (some overhead remains from the header `Gtk.Revealer` + `Gtk.Overlay` chrome). Don't assume the blueprint's `height-request` value is the actual achievable minimum.
- **External (WM-level) window repositioning confuses GTK's own dialog placement.** devilspie2 moves/resizes the main window via raw X11 calls, bypassing GTK entirely. GTK's internal idea of "where my window is" goes stale, so a transient child dialog (e.g. Preferences, opened via `Ctrl+,`) computes its centered position from the stale value and can open far off-screen. Fix used here: add a second devilspie2 rule matching the dialog by window name (e.g. `"Preferences"`) that explicitly repositions it too — don't rely on GTK's automatic centering for any dialog owned by a window devilspie2 touches.
- **`CS0649` warnings on `[Gtk.Connect]` fields are expected noise**, not a sign of broken bindings — gircore populates those fields via reflection at runtime (`builder.Connect(this)`), which the C# compiler can't see, so it flags every such field as "never assigned" even when binding works correctly. This is true throughout the whole app (`MainWindow.cs` included), not just `PreferencesDialog.cs`.
- **Force-closing a dialog (e.g. `wmctrl -c`) can write stale/default values back into `config.json`** for whatever row hadn't finished its own init at that point — this looks like config corruption but only reproduces via an abnormal close; a normal close (Escape, the dialog's own × button) was verified safe. The `InputMethod`/`InputSource`/`Gravity`/8-band EQ fields added in `edc8f05` haven't been verified end-to-end (i.e. whether they actually reach `cava`'s config and change its behavior) — treat them as unverified if debugging audio-input issues.

## Architecture

.NET/C# app using an MVC split across two projects (gir.core bindings for GTK4/Libadwaita on the GNOME side):

- **NickvisionCavalier.Shared** — platform-independent core.
  - `Models/CAVA.cs` — manages the external `cava` process (spawned as a subprocess; audio spectrum data is read from its output) and its config file.
  - `Models/Renderer.cs` — turns CAVA's spectrum data into the actual visualization (drawing modes, colors, mirroring, direction) independent of any UI toolkit.
  - `Models/Configuration.cs`, `ColorProfile.cs`, `DrawingMode.cs`, `Mirror.cs`, `DrawingDirection.cs`, `Theme.cs` — persisted settings (this is what's serialized to `config.json` under the app's config dir) and the enums driving `Renderer`.
  - `Controllers/*` — mediate between `Models` and the GNOME `Views`.
- **NickvisionCavalier.GNOME** — GTK4/Libadwaita frontend.
  - `Blueprints/*.blp` — UI definitions in Blueprint markup, compiled by `blueprint-compiler` at build time (`window.blp` is the main window shell; `preferences_dialog.blp` holds all the settings UI).
  - `Views/MainWindow.cs`, `DrawingView.cs` — bind to `MainWindowController`/`DrawingViewController`; `DrawingView` hosts the `GtkDrawingArea` that `Renderer` paints into.
  - `Views/PreferencesDialog.cs` — settings UI, backed by `PreferencesViewController`.
  - `Controls/*` — toolkit-generic widgets (not wired to controllers), meant to be portable to other platforms if they're ever added.
  - `flatpak/org.nickvision.cavalier.json` — flatpak manifest; also builds `fftw3f` and `iniparser` as dependency modules for CAVA-side processing.

Follows Microsoft's standard C# coding/identifier-naming conventions (see `.editorconfig` for indentation per file type: tabs in `.sln`/`.resx`, 4-space in `.cs`/`.sh`/`.py`/`.json`/`.cake`, 2-space in `.csproj`/`.xml`/`.css`/`.md`/`.blp`/`.yml`).
