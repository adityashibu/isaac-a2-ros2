# A2 Warehouse Autonomy — Presentation

An interactive HTML slide deck for the Unitree A2 warehouse navigation project:
an interactive 3D robot on the title, the architecture (sense / plan / act),
demo clips, and an interactive 2D SLAM map plus 3D RTAB-Map point cloud.

## Run locally

Serve the folder over HTTP (do not open `index.html` as a `file://` URL) and
open your browser:

```
cd presentation
./run.sh
```

`run.sh` starts a local server on `127.0.0.1` (default port 8000, falls back to
another if busy) and opens the deck. Press Ctrl-C to stop. An internet
connection is needed for the three.js library loaded from a CDN.

## Navigate

Arrow keys or space move between slides; the dots jump to a slide. Drag the
title robot to rotate it, and use the 2D/3D toggle on the mapping slide.

## Files

- `index.html` — the deck (the 3D robot model is embedded inside it)
- `cloud_data.js` — the downsampled RTAB-Map point cloud
- `assets/` — demo clips, the SLAM map, and the RViz costmap image
