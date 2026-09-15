# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this fork is for

Cavalier-bar is a personal fork of [NickvisionApps/Cavalier](https://github.com/NickvisionApps/Cavalier) (via an intermediate fork, `WatashiAD/Cavalier-extra`), based on upstream commit `edc8f05` ("Add more CAVA customization options" — input method dropdown, gravity slider, 8-band equalizer, finer sensitivity steps). It intentionally excludes that fork's later README/screenshot churn and an unrelated stray commit that added an InvokeAI Colab notebook.

The goal of this fork is to make Cavalier usable as a thin, docked, always-on-screen audio-wave bar (via an external window manager rule, e.g. devilspie2) rather than only as a normal floating window. The main relevant change so far: `NickvisionCavalier.GNOME/Blueprints/window.blp` had `height-request` lowered from `232` to `40` — upstream hardcodes both `width-request`/`height-request` to `232` on `Adw.ApplicationWindow`, which silently clamps any window-manager-driven resize back to that floor.

Work in this repo should assume the target is still a normal Cavalier build/install (dotnet + flatpak), just with a lower minimum window size and whatever other docked-bar-friendly tweaks get added later (e.g. further stripping chrome, additional CLI/config options for positioning).

## Build & run

Initialize the `CakeScripts` submodule before building anything — it isn't checked out by a plain clone:
```
git submodule update --init
```

Build commands (run from repo root unless noted), via [Cake](https://cakebuild.net/) — install once with `dotnet tool install --global Cake.Tool` or `dotnet tool restore`:

| Command | Result |
|---|---|
| `dotnet cake --target=Run --ui=gnome` | Builds and runs the app in place (not installed — some icons/desktop integration may be missing). |
| `dotnet run` (inside `NickvisionCavalier.GNOME/`) | Same, via plain dotnet. |
| `dotnet cake --target=Publish --prefix=PREFIX --ui=gnome` | Publishes to `_nickbuild`, ready to install into `PREFIX` (e.g. `/usr`, `/app`). Add `--self-contained` to bundle the dotnet runtime. |
| `dotnet cake --target=Install --destdir=DESTDIR` | Copies the published output into `DESTDIR` (defaults to `/`). Run after `Publish`. |

Manual (non-flatpak) build dependencies: dotnet >=8.0, GTK >=4.12, libadwaita >=1.4, blueprint-compiler, glib-compile-resources.

To build/run as a flatpak instead (needed to actually override the Flathub-installed `org.nickvision.cavalier`), use `flatpak-builder` against `flatpak/org.nickvision.cavalier.json` — this manifest pins `org.gnome.Platform`/`Sdk` version 45 and the `dotnet8` SDK extension. The app id is unchanged (`org.nickvision.cavalier`), so a flatpak build from this repo will replace/collide with any Flathub install of upstream Cavalier under the same id.

There is no test suite in this repo.

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
