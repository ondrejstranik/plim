# Examples

## Analysing plasmon signals (`runSignalAnalyser`)

The main entry point for offline analysis is
[`plim.main.runSignalAnalyser`](reference/main/runSignalAnalyser.md), which
loads a previously recorded experiment (image, spot positions, flow and
signal data), lets you inspect and select spots in the info table, and fit
their kinetic binding curves.

Run it directly as a script:
```
python -m plim.main.runSignalAnalyser
```

A file dialog lets you pick the experiment's `*.npz` file; the GUI then
shows:

- the **Signal** tab (spot info table, raw signal traces),
- the **Flow** tab (flow rate over time),
- the **Fit** tab, where kinetic models (adsorption, desorption, linear,
  double adsorption) are fitted per spot, with per-parameter box plots and
  a spatial map coloured by the fitted value.

## Acquiring live data (virtual vs. real instrument)

Plim reuses [Viscope's](https://ondrejstranik.github.io/viscope/) instrument
abstraction, so the same acquisition code runs against a virtual
microscope (for development, see
[`runVirtualIFC`](reference/main/runVirtualIFC.md)) or a real one (see
[`runRealIFC`](reference/main/runRealIFC.md) /
[`runRealMSC`](reference/main/runRealMSC.md)) -- only the instrument
classes passed in differ, the GUI and processing code above them stay the
same.

## Try it live, in your browser (Binder)

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ondrejstranik/plim/main?urlpath=desktop)

Click the badge to launch Plim in a virtual desktop in your browser -- no
local installation required. The environment is built by
[mybinder.org](https://mybinder.org/) from the
[`binder/`](https://github.com/ondrejstranik/plim/tree/main/binder)
folder of this repository.

It autostarts
[`binder/binder.py`](https://github.com/ondrejstranik/plim/blob/main/binder/binder.py),
a standalone script version of
[`runVirtualIFC`](reference/main/runVirtualIFC.md). It wires up a fully
virtual integral-field camera setup -- a spectral camera, a black-and-white
camera, a stage and a pump -- into a
[`PlimMicroscope`](reference/virtualSystem/plimMicroscope.md) virtual
system, and opens the same acquisition/analysis GUIs `runVirtualIFC` does
([`AllDeviceGUI`](https://github.com/ondrejstranik/viscope/blob/main/viscope/gui/allDeviceGUI.py)
from Viscope, plus [`PlasmonViewerGUI`](reference/gui/plasmonViewerGUI.md)
and [`PositionTrackGUI`](reference/gui/positionTrackGUI.md)) --
so you can drive the whole live plasmon-sensing pipeline, from spot
identification to kinetic fitting, with no physical hardware at all.

The desktop session comes from
[`jupyter-remote-desktop-proxy`](https://github.com/jupyterhub/jupyter-remote-desktop-proxy),
which serves an XFCE session at the `desktop` URL path. `binder/postBuild`
installs `binder/plim-demo.desktop` as an XFCE autostart entry, so
`binder.py` launches on its own as soon as the desktop session comes up --
nothing needs to be typed in a terminal.
