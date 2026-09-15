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

To build/run as a flatpak instead (needed to override a Flathub-installed `org.nickvision.cavalier` in place), use `flatpak-builder` against `flatpak/org.nickvision.cavalier.json` — this manifest pins `org.gnome.Platform`/`Sdk` version 50 and the `dotnet10` SDK extension (matching the project's `net10.0` TargetFramework; confirmed available on the `flathub` remote at 10.0.8/branch 25.08). The app id is unchanged (`org.nickvision.cavalier`), so a flatpak build from this repo replaces/collides with any Flathub install of upstream Cavalier under the same id. Note: on a very new GPU (e.g. RDNA4 `gfx1201`), the flatpak's bundled Mesa/LLVM may be too old to recognize the GPU target and silently falls back to a software rendering path — harmless for a small docked bar, but a real perf hit for a full-size window. The native build uses the host's own (current) Mesa, avoiding this.

There is no test suite in this repo.

`Nickvision.Aura` 2023.11.4 (pinned in both `.csproj`s) is deprecated on NuGet — it's the last version ever published, successor is `Nickvision.Desktop`. It transitively pulls in `Tmds.DBus`/`Tmds.DBus.Protocol` 0.15.0, which has a known high-severity vulnerability (CVE-2026-39959, local D-Bus signal spoofing/DoS). Since Aura won't be updated, both `.csproj`s carry an explicit top-level `PackageReference` pinning `Tmds.DBus`/`Tmds.DBus.Protocol` to `0.95.1` (latest stable as of 2026-09) to force NuGet's nearest-wins resolution past the vulnerable transitive version — verified this doesn't break Aura's own D-Bus usage (its single-instance IPC, both the client "sent a command" and server "listening" paths) despite the 0.15→0.95 jump.

### Other NuGet dependency notes

- `SkiaSharp`/`SkiaSharp.NativeAssets.Linux` bumped 2.88.6 → 4.152.0 (SkiaSharp's own versioning scheme change, not as big a jump as the numbers suggest). The `SKFilterQuality` enum used by `Renderer.cs` for background/foreground image scaling was dropped from the *compile-time* API surface in this range (it's still physically present in the runtime assembly for binary compat, so old builds don't crash, but new code can't reference it — shows up as `CS0103`, not `CS0619`/obsolete). Replaced `ScalePixels(..., SKFilterQuality.Medium)` with `ScalePixels(..., new SKSamplingOptions(SKFilterMode.Linear, SKMipmapMode.Linear))`, the closest equivalent. Verified by running the app and screenshotting the rendered bar.
- `GetText.NET` bumped 1.9.14 → 10.0.1 with zero source changes needed, despite the version jump looking alarming.
- `GirCore.Adw-1` bumped 0.5.0-preview.3 → 0.8.1. Version 0.8.0 reworked `Gtk.Builder` into a composite-template/source-generator pattern (`[GObject.Subclass<T>]` + `[Gtk.Template<TLoader>]`), dropping `Gtk.Builder.GetPointer()`/`.Connect()` (which every window/dialog here used) and changing `.Handle` on gir.core objects from a raw `nint` to a typed `GObject.Internal.ObjectHandle` (fixed via `.DangerousGetHandle()` in `Helpers/GtkHelpers.cs`). All four affected classes (`MainWindow`, `DrawingView`, `PreferencesDialog`, `CommandHelpDialog`) were migrated:
  - Each `.blp`'s root object (e.g. `Adw.ApplicationWindow _root { ... }`) became `template $ClassName: Adw.ApplicationWindow { ... }`, which blueprint-compiler emits as `<template class="ClassName" ...>`, matching `[GObject.Subclass<T>(qualifiedName: nameof(ClassName))]`.
  - `[Gtk.Connect]` fields lost `readonly` — the generator assigns them post-construction, not inside a constructor body.
  - The old `private Ctor(Gtk.Builder builder, ...) : base(builder.GetPointer("_root"), false) { ...; builder.Connect(this); ... }` pattern became `private void Setup(...)` (same body, minus the now-automatic `builder.Connect(this)` line) plus a `public static ClassName Create(...)` factory (`NewWithProperties([]); Setup(...);`) — GObject.Subclass instances must be constructed through the registered GType, not an arbitrary C# constructor, so every `new ClassName(...)` call site became `ClassName.Create(...)`.
  - Added `Helpers/TranslatedTemplateLoader.cs`, a custom `Gtk.TemplateLoader` (its `static Load(string)` is the only requirement) that reuses `Builder.ReadTranslatedXml` — this preserves the app's existing gettext pre-translation step (walking `translatable="yes"` nodes and substituting via `Nickvision.Aura`'s Gettext before GTK ever parses the XML) which the native template loader would otherwise bypass. `Helpers/Builder.cs` still exists as-is for the one remaining ad hoc case, `shortcuts_dialog.ui` (a plain `Gtk.ShortcutsWindow`, no custom subclass needed).
  - Verified via a full clean rebuild and by running the app: the bar renders, Preferences opens with all ~60 connected widgets showing live controller-bound values, the keyboard-shortcuts window and the `--help`-triggered `CommandHelpDialog` both open through Aura's D-Bus single-instance command path, and all of the above stays correctly translated under `LANG=de_DE.UTF-8`.

## Known gotchas (found while building the docked-bar variant)

- **`Gtk.WindowHandle` and right-click**: this widget (used so a CSD-less window can still be dragged) forwards a secondary click to the window manager's system context menu (move/resize/**close**). On an undecorated, WM-pinned bar that's never meant to be dragged, that surfaced as right-clicking the bar closing it. Fixed by removing the `WindowHandle` from `window.blp` entirely — don't re-add one without also handling this.
- **`Gtk.Revealer` with `transition-type: crossfade`** only animates opacity; it never collapses the reserved layout space. `AutohideHeader` toggling `reveal-child` on the header's revealer had no visible effect on window height until the transition type was changed to `slide_down`.
- **`width-request`/`height-request` on `Adw.ApplicationWindow`** is a real floor GTK enforces, including against an external WM script (devilspie2) requesting a smaller size — it silently clamps back up. Even after lowering it to `40` and removing the menu button/`WindowHandle`, the real achieved minimum height is ~`78px` (some overhead remains from the header `Gtk.Revealer` + `Gtk.Overlay` chrome). Don't assume the blueprint's `height-request` value is the actual achievable minimum.
- **External (WM-level) window repositioning confuses GTK's own dialog placement.** devilspie2 moves/resizes the main window via raw X11 calls, bypassing GTK entirely. GTK's internal idea of "where my window is" goes stale, so a transient child dialog (e.g. Preferences, opened via `Ctrl+,`) computes its centered position from the stale value and can open far off-screen. Fix used here: add a second devilspie2 rule matching the dialog by window name (e.g. `"Preferences"`) that explicitly repositions it too — don't rely on GTK's automatic centering for any dialog owned by a window devilspie2 touches.
- **`CS0649` warnings on `[Gtk.Connect]` fields are expected noise**, not a sign of broken bindings — gircore populates those fields via reflection at runtime (`builder.Connect(this)`), which the C# compiler can't see, so it flags every such field as "never assigned" even when binding works correctly. This is true throughout the whole app (`MainWindow.cs` included), not just `PreferencesDialog.cs`.
- **Force-closing a dialog (e.g. `wmctrl -c`) can write stale/default values back into `config.json`** for whatever row hadn't finished its own init at that point — this looks like config corruption but only reproduces via an abnormal close; a normal close (Escape, the dialog's own × button) was verified safe. The `InputMethod`/`InputSource`/`Gravity`/8-band EQ fields added in `edc8f05` haven't been verified end-to-end (i.e. whether they actually reach `cava`'s config and change its behavior) — treat them as unverified if debugging audio-input issues.
- **`config.json` is only read at startup** — there's no file watcher, so editing it (by hand or by script, e.g. `scripts/wallpaper-accent/`) while the app is running has no effect until the process is killed and relaunched. Any tooling that writes config needs to restart the app itself if it wants the change to show up live.
- **Global keyboard accelerators are active even with the header/controls hidden** (`ShowControls: false`, `AutohideHeader: true` — the normal state for this fork's docked-bar mode). They're registered in `PreferencesDialog.cs` via `SetAccelsForAction` and include single-letter keys like `D` (next drawing mode), `F` (toggle fill), `M` (next mirror), `B` (bar pairs +), `R` (roundness +), `G` (next direction), etc. — a stray keypress while the bar window has focus silently changes and persists config. Worth knowing before treating an unexplained visual change as a bug.
- **Killing the app binary doesn't reliably reap its `cava` child process** — `pkill -f .../NickvisionCavalier.GNOME` can leave an orphaned `cava -p ...` running, which then holds the audio input and confuses the next launch. Kill both explicitly (see `restart_if_running()` in `scripts/wallpaper-accent/wallpaper_accent.py` for the pattern).
- **`tools/` is gitignored** (leftover from the abandoned Cake-based build, see "Build & run" above — Cake tooling restores into `tools/`). New scripts/tooling for this fork go under `scripts/` instead, or they'll silently fail to `git add`.

## Tools

- `scripts/wallpaper-accent/wallpaper_accent.py` — sets the bar's foreground gradient from the current desktop wallpaper (reads `org.cinnamon.desktop.background picture-uri` via `gsettings`, so it works with any tool that updates that key, e.g. a time-of-day wallpaper extension). It writes a dedicated `"Wallpaper Accent"` color profile into `config.json` (via `ActiveProfile`) rather than overwriting `"Default"`, so a hand-picked profile is never clobbered — cycle back to it with `P`/`Shift+P`. It only borrows the wallpaper's *hue*; saturation/brightness are fixed high (`ACCENT_SATURATION`/`ACCENT_VALUE` constants), because a color sampled literally from the wallpaper is typically desaturated like any photo and blends into the backdrop it's drawn over instead of standing out — this was verified by trial (a first version using literal sampled RGB was visually camouflaged against the source wallpaper). Requires `python3` (Pillow) and `gsettings`; both are already present via linuxbrew's Python + the Cinnamon desktop on this machine. Run manually (`python3 scripts/wallpaper-accent/wallpaper_accent.py`) — the paired `cavalier-wallpaper-accent.service`/`.timer` systemd user units in the same directory exist for periodic automation but are intentionally **not installed/enabled** (user preference, as of this writing); they'd need `systemctl --user enable --now cavalier-wallpaper-accent.timer` after symlinking into `~/.config/systemd/user/`.

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
