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
