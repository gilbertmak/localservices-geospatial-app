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

The same manifest includes the test dependency:

```bash
python -m pytest -q
```

The app opens with a login prompt in the sidebar.

Demo credentials:

- Email: `demo@geospatial.com`
- Password: `geospatial-demo`

## User flow

1. Sign in from the sidebar. After authentication, the workspace welcomes the user by their email ID.
2. Use the sidebar workspace navigation to open **Create new Service Area/POI** or **Update POI**.
3. In **Create new Service Area/POI**, enter a unique new service-area name.
4. Review the Southeast Asia map and upload a `.csv`, `.xlsx` or `.xls` file up to 1 MB.
5. Include these required columns: `location name`, `latitude` and `longitude`.
6. Review the validated POIs and derived service-area shape together in one map preview;
   map-generation progress is shown while the interactive map is prepared, then the map fits
   tightly to the derived boundary.
7. Request synchronization to the separate simulated POI and service-area databases.
8. In **Update POI**, select a synced service area from the sidebar view. Its existing POIs and
   boundary appear together on the map, followed by **Download POI** and **Download boundary**
   exports. The map uses a default zoom capped at level 10 and the selector runs in a fragment
   so changing service areas does not rebuild the full page or disturb scroll position.
9. Continue below the exports to replace the POI rows. The preview combines the newly
   derived shape with the previous service-area shape so existing coverage is retained.

## Demo boundary

Authentication, POI records, service-area geometry and synchronization are intentionally emulated
in Streamlit session state. No production identity provider, database, external API or real user
data is connected.

For each upload, GeoPandas creates WGS84 point geometries, joins all POIs into a convex-hull polygon,
projects it to a local UTM CRS, buffers it by 1,000 metres and stores the resulting service-area
geometry separately from the POI rows. The most north, east, south and west POIs remain available
as audit details, but no POI is excluded from the service-area hull. Re-uploading an existing area
replaces its POI rows while unioning the old and newly derived service-area geometries.

The footer uses Streamlit's sticky `st.bottom` layout container.

The initial POI map view is centered and zoomed to Southeast Asia. POIs use a deep-violet
(`#6D28D9`) marker with a white outline so they remain visible against OpenStreetMap's green,
blue and pink land-use colors. POI markers open a detail popup and are intentionally non-draggable.

## Validation

```bash
python -m compileall app.py
pytest -q
streamlit run app.py --server.headless true
```

The implementation follows Streamlit's documented APIs for [sidebar widgets](https://docs.streamlit.io/develop/api-reference/layout/st.sidebar),
[session state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state),
[file uploads](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader),
[page links](https://docs.streamlit.io/develop/api-reference/widgets/st.page_link),
[status containers](https://docs.streamlit.io/develop/api-reference/status/st.status),
[fragments](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment),
[download buttons](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button),
[sticky footers](https://docs.streamlit.io/develop/api-reference/layout/st.bottom) and
[Folium maps](https://python-visualization.github.io/folium/latest/),
and the [Streamlit-Folium component](https://github.com/randyzwitch/streamlit-folium).
