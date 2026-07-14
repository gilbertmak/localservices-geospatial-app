# Movable POI Map Plan

## Current status

The read-only map renderer has been migrated to Folium/Leaflet. POIs are currently top-layer,
clickable, and explicitly non-draggable; drag events and edit persistence remain a future stage.

## Decision

Use a Folium/Leaflet editing map for the POI-location editing mode. Folium's `Marker` supports
`draggable=True`, backed by Leaflet's draggable marker behavior. Plotly's map traces support marker
coordinates, styling, and selection, but Streamlit currently exposes selection events rather than
marker-drag events through `st.plotly_chart`; making Plotly markers draggable would require a custom
JavaScript event bridge.

References:

- [Folium Marker API](https://python-visualization.github.io/folium/latest/reference.html)
- [Leaflet marker dragging](https://leafletjs.com/reference)
- [Streamlit Plotly chart events](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart)

## Target user flow

1. User uploads and validates POI data.
2. The map displays one draggable marker per POI with the location name in its tooltip.
3. User drags one or more markers to correct their coordinates.
4. The map reports the changed POI name and new latitude/longitude.
5. The table updates to show pending coordinates, and the service-area polygon is recalculated from
   the edited points.
6. The user confirms the edited POI set; only then are the POI and service-area demo databases
   updated.

## Implementation stages

### Stage 1 — Interaction spike

- Use the current Folium and `streamlit-folium` map implementation as the spike baseline.
- Render a small five-POI test map with stable POI IDs and `draggable=True` markers.
- Verify whether the Streamlit bridge returns `dragend` coordinates reliably on desktop and touch.
- Reject edits with invalid coordinates and preserve the last valid state.

### Stage 2 — Production editing component

- Build a reusable `render_editable_poi_map()` helper.
- Use stable POI IDs rather than row positions so edits remain attached to the correct POI after
  sorting or validation.
- Keep original coordinates and pending coordinates separate until confirmation.
- Show a visible “N POI locations changed” state plus Reset changes and Apply edits actions.

### Stage 3 — Geospatial recalculation and persistence

- Re-run `derive_service_area()` after every accepted coordinate change.
- Keep the invariant that every edited POI is covered by the generated service area.
- Re-render the polygon and update the service-area summary before confirmation.
- Persist only the edited dataframe and its matching derived geometry when the user confirms.

## Acceptance criteria

- Every POI can be selected and moved with pointer or touch input.
- A drag produces a visible latitude/longitude update for the correct POI.
- Reset restores the uploaded coordinates without changing the uploaded POI names.
- The service-area polygon changes after a POI move and continues to cover every POI.
- Confirmation persists the edited coordinates; abandoning the workflow does not.
- Keyboard and non-drag fallback remain available for accessibility and precision editing.

## Risks and dependencies

- Folium generates a Leaflet map, but Python needs a component bridge to receive browser-side
  `dragend` events; `draggable=True` alone is not sufficient for persistence.
- Large POI files may need marker clustering or a focused edit mode to keep dragging usable.
- A custom component must avoid stale event replay across Streamlit reruns and must return a stable
  POI ID with every coordinate change.
- Moving a POI can change the service area substantially; the UI should show the recalculated area
  before any simulated backend confirmation.
