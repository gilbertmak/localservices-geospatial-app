# Local Services Geospatial Update

A Streamlit demo for reviewing and synchronizing local-service points of interest (POIs).

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit Community Cloud uses the root `requirements.txt` as the single dependency manifest,
following its [dependency-file precedence rules](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
It includes GeoPandas for service-area generation and Folium/Streamlit-Folium for interactive maps.

For test execution, install the development requirements instead:

```bash
python -m pip install -r requirements-dev.txt
```

The app opens with a login prompt in the sidebar.

Demo credentials:

- Email: `demo@swatmobility.com`
- Password: `swat-demo`

## User flow

1. Sign in from the sidebar.
2. In **Create new Service Area/POI**, select Bangkok, Johor Bahru, Singapore, or **(create new service area)**.
3. If creating a new service area, enter a unique service-area name.
4. Review the Southeast Asia map and upload a `.csv`, `.xlsx`, or `.xls` file.
5. Include these required columns: `location name`, `latitude`, and `longitude`.
6. Review the validated POIs and the derived service-area shape.
7. Request synchronization to the separate simulated POI and service-area databases.
8. In **Update POI**, use the service-area database dropdown to download the current POI snapshot or expand the re-upload workflow.

## Demo boundary

Authentication, POI records, service-area geometry, and synchronization are intentionally emulated
in Streamlit session state. No production identity provider, database, external API, or real user
data is connected.

For each upload, GeoPandas creates WGS84 point geometries, joins all POIs into a convex-hull polygon,
projects it to a local UTM CRS, buffers it by 1,000 metres, and stores the resulting service-area
geometry separately from the POI rows. The most north, east, south, and west POIs remain available
as audit details, but no POI is excluded from the service-area hull.

The footer uses Streamlit's sticky `st.bottom` layout container.

The initial POI map view is centered and zoomed to Southeast Asia. POIs use a deep-violet
(`#6D28D9`) marker with a white outline so they remain visible against OpenStreetMap's green,
blue, and pink land-use colors. POI markers open a detail popup and are intentionally non-draggable.

The planned movable-POI interaction is documented in
[`subagent decisions/movable-poi-map-plan.md`](subagent%20decisions/movable-poi-map-plan.md).

## Validation

```bash
python -m compileall app.py
pytest -q
streamlit run app.py --server.headless true
```

The implementation follows Streamlit's documented APIs for [sidebar widgets](https://docs.streamlit.io/develop/api-reference/layout/st.sidebar),
[session state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state),
[file uploads](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader),
[tabs](https://docs.streamlit.io/develop/api-reference/layout/st.tabs),
[expanders](https://docs.streamlit.io/develop/api-reference/layout/st.expander),
[status containers](https://docs.streamlit.io/develop/api-reference/status/st.status),
[download buttons](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button),
[sticky footers](https://docs.streamlit.io/develop/api-reference/layout/st.bottom), and
[Folium maps](https://python-visualization.github.io/folium/latest/),
and the [Streamlit-Folium component](https://github.com/randyzwitch/streamlit-folium).
