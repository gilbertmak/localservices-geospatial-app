# Project Manager Handoff

## Task summary

Greenfield Streamlit demo for Local Services Geospatial Update. The local checkout started on
`main` with no commits and no source files. Authentication and backend synchronization are
implemented as local session-state emulations.

## Key facts and acceptance criteria

- The app must protect the main workspace behind a sidebar login.
- Demo credentials must be clearly identified and invalid credentials rejected.
- Authenticated users see **Create new POI** and **Update POI** tabs.
- CSV and Excel uploads require location name, latitude, and longitude columns.
- Upload processing must show progress/status feedback and validate coordinate ranges.
- Validated POIs must render on a Southeast Asia map before confirmation.
- Confirmed POI rows and derived service-area geometry must be stored in separate simulated
  databases and exposed through the update/download flow.
- GeoPandas derives the service area by joining the cardinal extreme POIs and buffering the
  resulting polygon by 1,000 metres in a local metric CRS.
- The update flow must provide an expanded download section and a collapsible re-upload section.
- The footer must say `Created by the SWAT Mobility GIS Team` and include a scroll-to-bottom balloon easter egg.
- README must document setup, demo credentials, limitations, and validation commands.

## Assumptions

- Synthetic service-area data is appropriate for the demo.
- Session-state authentication is not production security.
- Local execution and Streamlit deployment are the target surfaces; no real identity provider or
  database is in scope.
- No external map API key is required for this prototype.

## Risks and dependencies

- Streamlit and Excel parsing dependencies must be installed before runtime validation.
- Demo credentials and session state must not be presented as production authentication.
- Streamlit cannot receive arbitrary Python callbacks from browser scroll events, so the footer
  easter egg is implemented as a trusted client-side `st.components.v2.component`.

## Validation contract

```bash
python -m compileall app.py
pytest -q
streamlit run app.py --server.headless true
```

Expected runtime checks: login gate, invalid login, authenticated tabs, CSV/XLSX validation,
map preview, simulated upload, update download, re-upload, footer copy, and scroll animation.

## Decision table

| Decision point | Recommendation | Confidence | Owner |
|---|---|---:|---|
| Data source | Fully synthetic local data | High | Product Owner |
| Authentication | One shared demo account using session state | High | Product Owner / Security |
| Backend | Replace selected POI and service-area records in separate in-memory simulated databases | High | Development |
| Map | Streamlit `st.map` without external credentials | Medium | Architecture |
| Footer animation | Trusted client-side `st.components.v2.component` JavaScript | High | Development |
