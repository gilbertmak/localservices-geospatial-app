# Delivery handoff: Update POI exports

## Changed behavior

- Removed the first `Download current POI data` accordion from Update POI.
- The synced service-area dropdown now sits directly above the combined POI and boundary map.
- Added `Download POI`, exporting the selected service area's current POIs as CSV.
- Added `Download boundary`, exporting the selected boundary as a WGS84 GeoJSON FeatureCollection.
- Kept `Re-upload POI data` below the preview and export controls.

## Validation

- `.venv/bin/python -m pytest -q`: 15 passed.
- `.venv/bin/python -m compileall -q app.py streamlit_app.py assets/substack/capture_app.py tests`: passed.
- `git diff --check`: passed.
- Runtime smoke test: Streamlit served on port 8511 and `/_stcore/health` returned `ok`.
- GeoJSON regression confirms a valid FeatureCollection with one Polygon feature and the service-area name.

## Caveats

- Exports read the session-backed simulated POI and service-area databases. They do not connect to a production backend.
- Existing binary screenshots and GIF/MP4 assets were not regenerated for this layout change.
