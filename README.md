# Local Services Geospatial Update

A Streamlit demo for reviewing and synchronizing local-service points of interest (POIs).

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

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
2. In **Create new POI**, select Bangkok, Johor Bahru, or Singapore.
3. Review the Southeast Asia map and upload a `.csv`, `.xlsx`, or `.xls` file.
4. Include these required columns: `location name`, `latitude`, and `longitude`.
5. Review the validated POIs and the derived service-area shape.
6. Request synchronization to the separate simulated POI and service-area databases.
7. In **Update POI**, use the service-area database dropdown to download the current POI snapshot or expand the re-upload workflow.

## Demo boundary

Authentication, POI records, service-area geometry, and synchronization are intentionally emulated
in Streamlit session state. No production identity provider, database, external API, or real user
data is connected.

For each upload, GeoPandas creates WGS84 point geometries, finds the most north, east, south, and
west POIs, joins those extremes into a convex-hull polygon, projects it to a local UTM CRS, buffers
it by 1,000 metres, and stores the resulting service-area geometry separately from the POI rows.

The footer uses Streamlit's sticky `st.bottom` layout container. The scroll-to-bottom balloon
easter egg uses a trusted `st.components.v2.component` with `isolate_styles=False`; it is a
client-side animation and does not call a production backend.

## Validation

```bash
python -m compileall app.py
pytest -q
streamlit run app.py --server.headless true
```

The implementation follows Streamlit's documented APIs for [sidebar widgets](https://docs.streamlit.io/develop/api-reference/layout/st.sidebar),
[session state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state),
[file uploads](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader),
[maps](https://docs.streamlit.io/develop/api-reference/charts/st.map),
[tabs](https://docs.streamlit.io/develop/api-reference/layout/st.tabs),
[expanders](https://docs.streamlit.io/develop/api-reference/layout/st.expander),
[status containers](https://docs.streamlit.io/develop/api-reference/status/st.status),
[download buttons](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button),
[sticky footers](https://docs.streamlit.io/develop/api-reference/layout/st.bottom), and
[trusted HTML/JavaScript](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component),
[PyDeck charts](https://docs.streamlit.io/develop/api-reference/charts/st.pydeck_chart).
