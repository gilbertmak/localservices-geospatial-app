# Project Manager Handoff

## Task summary

Greenfield Streamlit demo for Local Services Geospatial Update. The local checkout started on
`main` with no commits and no source files. Authentication and backend synchronization are
implemented as local session-state emulations.

## Key facts and acceptance criteria

- The app must protect the main workspace behind a sidebar login.
- Demo credentials must be clearly identified and invalid credentials rejected.
- Authenticated users see **Create new Service Area/POI** and **Update POI** tabs.
- The create workflow can target an existing service area or create a uniquely named new one.
- CSV and Excel uploads require location name, latitude, and longitude columns.
- Upload processing must show progress/status feedback and validate coordinate ranges.
- Validated POIs must render on a Southeast Asia map before confirmation.
- Confirmed POI rows and derived service-area geometry must be stored in separate simulated
  databases and exposed through the update/download flow.
- GeoPandas derives the service area from the convex hull of all uploaded POIs and buffers the
  resulting polygon by 1,000 metres in a local metric CRS; cardinal extremes are retained as
  audit details only.
- The update flow must provide an expanded download section and a collapsible re-upload section.
- The footer must say `Created by the SWAT Mobility GIS Team`; no animation is required.
- README must document setup, demo credentials, limitations, and validation commands.

## Assumptions

- Synthetic service-area data is appropriate for the demo.
- Session-state authentication is not production security.
- Local execution and Streamlit deployment are the target surfaces; no real identity provider or
  database is in scope.
- No external map API key is required for this prototype.

## Risks and dependencies

- Streamlit and Excel parsing dependencies must be installed before runtime validation.
- Streamlit Community Cloud must install the root `requirements.txt`; the repository intentionally
  keeps one authoritative dependency manifest so GeoPandas is available before `app.py` imports it.
- Demo credentials and session state must not be presented as production authentication.
- Movable POI editing is planned separately in `movable-poi-map-plan.md`; no map-editing dependency
  is introduced until the event-bridge spike is validated.

## Validation contract

```bash
python -m compileall app.py
pytest -q
streamlit run app.py --server.headless true
```

Expected runtime checks: login gate, invalid login, authenticated tabs, CSV/XLSX validation,
map preview, simulated upload, update download, re-upload, footer copy, and scroll animation.

Latest geospatial regression: the attached LTAMRTStationExitGEOJSON.geojson reference dataset
contains 597 station exits; the all-POI convex hull covered 597/597 exits, compared with 564/597
under the previous cardinal-extreme-only algorithm.

## Decision table

| Decision point | Recommendation | Confidence | Owner |
|---|---|---:|---|
| Data source | Fully synthetic local data | High | Product Owner |
| Authentication | One shared demo account using session state | High | Product Owner / Security |
| Backend | Replace selected POI and service-area records in separate in-memory simulated databases | High | Development |
| Map | Streamlit `st.map` without external credentials | Medium | Architecture |
| Footer animation | Trusted client-side `st.components.v2.component` JavaScript | High | Development |
