"""Local Services Geospatial Update - Streamlit demo application."""

from __future__ import annotations

import hashlib
from html import escape
import io
import re
import time
from pathlib import Path
from typing import Any

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from shapely.ops import unary_union


APP_TITLE = "Local Services Geospatial Update"
DEMO_USERNAME = "demo@geospatial.com"
DEMO_PASSWORD = "geospatial-demo"
REQUIRED_COLUMNS = ("location_name", "latitude", "longitude")
SUPPORTED_EXTENSIONS = ["csv", "xlsx", "xls"]
WGS84_CRS = "EPSG:4326"
SERVICE_AREA_BUFFER_METERS = 1_000
POI_MARKER_RADIUS_METERS = 150 * 0.25
POI_MARKER_COLOR = "#6D28D9"
POI_MARKER_BORDER_COLOR = "#FFFFFF"
DEFAULT_MAP_CENTER = (7.5, 110.0)
DEFAULT_MAP_ZOOM = 4
CREATE_BOUNDARY_MAP_MAX_ZOOM = 13
DOWNLOAD_DEFAULT_MAP_ZOOM = 10
CREATE_NEW_SERVICE_AREA_OPTION = "(create new service area)"
CREATE_VIEW = "Create new Service Area/POI"
UPDATE_VIEW = "Update POI"
WORKSPACE_VIEWS = [CREATE_VIEW, UPDATE_VIEW]

SERVICE_AREAS: dict[str, dict[str, Any]] = {
    "Singapore": {
        "center": (1.3521, 103.8198),
        "pois": [
            ("SWAT Mobility HQ", 1.3009, 103.8456),
            ("Marina Bay Service Hub", 1.2820, 103.8580),
            ("Jurong East Service Hub", 1.3331, 103.7423),
        ],
    },
    "Johor Bahru": {
        "center": (1.4927, 103.7414),
        "pois": [
            ("JB Sentral Service Hub", 1.4637, 103.7644),
            ("Taman Molek Service Hub", 1.5275, 103.7984),
        ],
    },
    "Bangkok": {
        "center": (13.7563, 100.5018),
        "pois": [
            ("Sukhumvit Service Hub", 13.7367, 100.5611),
            ("Chatuchak Service Hub", 13.7998, 100.5506),
        ],
    },
}

COLUMN_ALIASES = {
    "name": "location_name",
    "location": "location_name",
    "location_name": "location_name",
    "poi_name": "location_name",
    "lat": "latitude",
    "latitude": "latitude",
    "lon": "longitude",
    "lng": "longitude",
    "long": "longitude",
    "longitude": "longitude",
}


def _sample_dataframe(area_name: str) -> pd.DataFrame:
    """Build the synthetic POI data used by the emulated backend."""

    return pd.DataFrame(
        SERVICE_AREAS[area_name]["pois"],
        columns=["location_name", "latitude", "longitude"],
    )


def normalize_column_name(column_name: object) -> str:
    """Normalize a spreadsheet header to a predictable snake_case value."""

    normalized = re.sub(r"[^a-z0-9]+", "_", str(column_name).strip().lower())
    return normalized.strip("_")


def normalize_poi_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a validated POI dataframe with the app's canonical columns."""

    source_columns: dict[str, str] = {}
    for original_column in dataframe.columns:
        normalized = normalize_column_name(original_column)
        canonical = COLUMN_ALIASES.get(normalized, normalized)
        source_columns.setdefault(canonical, str(original_column))

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in source_columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Missing required column(s): {missing}.")

    normalized_dataframe = pd.DataFrame(
        {
            column: dataframe[source_columns[column]]
            for column in REQUIRED_COLUMNS
        }
    )
    normalized_dataframe["location_name"] = (
        normalized_dataframe["location_name"].fillna("").astype(str).str.strip()
    )
    normalized_dataframe["latitude"] = pd.to_numeric(
        normalized_dataframe["latitude"], errors="coerce"
    )
    normalized_dataframe["longitude"] = pd.to_numeric(
        normalized_dataframe["longitude"], errors="coerce"
    )

    errors: list[str] = []
    if normalized_dataframe["location_name"].eq("").any():
        errors.append("Every row needs a location name.")
    if normalized_dataframe["latitude"].isna().any():
        errors.append("Latitude values must be numeric.")
    if normalized_dataframe["longitude"].isna().any():
        errors.append("Longitude values must be numeric.")
    if (
        normalized_dataframe["latitude"].notna()
        & ~normalized_dataframe["latitude"].between(-90, 90)
    ).any():
        errors.append("Latitude values must be between -90 and 90.")
    if (
        normalized_dataframe["longitude"].notna()
        & ~normalized_dataframe["longitude"].between(-180, 180)
    ).any():
        errors.append("Longitude values must be between -180 and 180.")
    if normalized_dataframe.empty:
        errors.append("The file contains no POI rows.")

    if errors:
        raise ValueError(" ".join(errors))

    return normalized_dataframe.reset_index(drop=True)


def read_poi_file(file_name: str, file_bytes: bytes) -> pd.DataFrame:
    """Read CSV or Excel bytes and validate the POI contract."""

    extension = Path(file_name).suffix.lower()
    if extension == ".csv":
        dataframe = pd.read_csv(io.BytesIO(file_bytes))
    elif extension in {".xlsx", ".xls"}:
        dataframe = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError("Please upload a CSV or Excel file.")
    return normalize_poi_dataframe(dataframe)


def derive_service_area(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Build a buffered convex hull that contains every uploaded POI."""

    normalized_dataframe = normalize_poi_dataframe(dataframe)
    points = gpd.GeoDataFrame(
        normalized_dataframe,
        geometry=gpd.points_from_xy(
            normalized_dataframe["longitude"], normalized_dataframe["latitude"]
        ),
        crs=WGS84_CRS,
    )

    extreme_indices = {
        "north": points["latitude"].idxmax(),
        "east": points["longitude"].idxmax(),
        "south": points["latitude"].idxmin(),
        "west": points["longitude"].idxmin(),
    }
    extreme_points = points.loc[list(dict.fromkeys(extreme_indices.values()))]
    metric_crs = points.estimate_utm_crs()
    if metric_crs is None:
        raise ValueError("Could not determine a metric projection for these POIs.")

    metric_points = points.to_crs(metric_crs)
    joined_points = unary_union(metric_points.geometry.tolist()).convex_hull
    if joined_points.geom_type in {"Point", "LineString"}:
        joined_points = joined_points.buffer(50)

    buffered_geometry = joined_points.buffer(SERVICE_AREA_BUFFER_METERS)
    if not metric_points.geometry.apply(buffered_geometry.covers).all():
        raise ValueError("The derived service area does not contain every uploaded POI.")
    service_area_geometry = gpd.GeoSeries(
        [buffered_geometry], crs=metric_crs
    ).to_crs(WGS84_CRS).iloc[0]

    extreme_details = {
        direction: {
            "location_name": str(points.loc[index, "location_name"]),
            "latitude": float(points.loc[index, "latitude"]),
            "longitude": float(points.loc[index, "longitude"]),
        }
        for direction, index in extreme_indices.items()
    }
    return {
        "geometry": service_area_geometry,
        "buffer_meters": SERVICE_AREA_BUFFER_METERS,
        "source_poi_count": len(normalized_dataframe),
        "metric_crs": metric_crs.to_string(),
        "area_sq_km": float(buffered_geometry.area / 1_000_000),
        "extreme_points": extreme_details,
    }


def merge_service_area_records(
    existing_record: dict[str, Any],
    updated_record: dict[str, Any],
) -> dict[str, Any]:
    """Union an existing service area with the newly derived upload area."""

    metric_crs = updated_record.get("metric_crs") or existing_record.get("metric_crs")
    if not metric_crs:
        raise ValueError("Could not determine a metric projection for the service areas.")

    metric_geometries = gpd.GeoSeries(
        [existing_record["geometry"], updated_record["geometry"]],
        crs=WGS84_CRS,
    ).to_crs(metric_crs)
    merged_metric_geometry = unary_union(metric_geometries.tolist())
    merged_geometry = gpd.GeoSeries(
        [merged_metric_geometry], crs=metric_crs
    ).to_crs(WGS84_CRS).iloc[0]

    merged_record = dict(updated_record)
    merged_record.update(
        {
            "geometry": merged_geometry,
            "metric_crs": str(metric_crs),
            "area_sq_km": float(merged_metric_geometry.area / 1_000_000),
            "merged_with_existing": True,
            "previous_area_sq_km": float(existing_record.get("area_sq_km", 0.0)),
        }
    )
    return merged_record


def file_signature(file_name: str, file_bytes: bytes) -> str:
    """Create a stable signature so the same upload is not reprocessed repeatedly."""

    digest = hashlib.sha256(file_bytes).hexdigest()
    return f"{file_name}:{digest}"


def initialize_session_state() -> None:
    """Initialize separate simulated POI and service-area databases."""

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "poi_database" not in st.session_state:
        st.session_state.poi_database = {
            area_name: _sample_dataframe(area_name)
            for area_name in SERVICE_AREAS
        }
    if "service_area_database" not in st.session_state:
        st.session_state.service_area_database = {
            area_name: {
                "service_area_name": area_name,
                **derive_service_area(poi_dataframe),
            }
            for area_name, poi_dataframe in st.session_state.poi_database.items()
        }


def service_area_names() -> list[str]:
    """Return the service areas currently registered in the service-area database."""

    return list(st.session_state.service_area_database)


def validate_new_service_area_name(
    name: str,
    existing_names: list[str],
) -> str | None:
    """Return a user-facing validation error for a new service-area name."""

    normalized_name = name.strip()
    if not normalized_name:
        return "Enter a name for the new service area."
    if any(
        existing_name.casefold() == normalized_name.casefold()
        for existing_name in existing_names
    ):
        return (
            "That service area already exists. Enter a different name or choose it "
            "from the dropdown."
        )
    return None


def render_sidebar() -> str | None:
    """Render the login surface and demo connection status."""

    with st.sidebar:
        st.markdown("### Access portal")
        st.divider()

        if st.session_state.authenticated:
            st.caption(st.session_state.username)
            if st.button("Sign out", key="logout", width="stretch"):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.rerun()
            st.divider()
            return st.radio("Workspace", WORKSPACE_VIEWS, key="workspace_view")
        else:
            with st.form("login_form"):
                username = st.text_input("Email", placeholder=DEMO_USERNAME)
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log in", type="primary", width="stretch")

            if submitted:
                if username == DEMO_USERNAME and password == DEMO_PASSWORD:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid demo credentials.")

            st.info(
                f"Demo account\n\nEmail: `{DEMO_USERNAME}`\n\n"
                f"Password: `{DEMO_PASSWORD}`"
            )

        st.divider()
        st.caption("Backend: local simulation")
        st.caption("No production credentials or data are used.")
    return None


def add_non_draggable_poi_marker(
    folium_map: folium.Map,
    location_name: str,
    latitude: float,
    longitude: float,
) -> None:
    """Add a high-priority clickable POI marker with dragging explicitly disabled."""

    escaped_name = escape(location_name)
    popup = folium.Popup(
        f"<b>{escaped_name}</b><br>"
        f"Latitude: {latitude:.6f}<br>Longitude: {longitude:.6f}",
        max_width=260,
    )
    folium.Marker(
        location=[latitude, longitude],
        icon=folium.DivIcon(
            html=(
                f'<div aria-label="{escaped_name}" '
                f'style="background:{POI_MARKER_COLOR}; '
                f'border:2px solid {POI_MARKER_BORDER_COLOR}; '
                'border-radius:50%; width:10px; height:10px; '
                'box-shadow:0 1px 4px rgba(15,23,42,.55);"></div>'
            ),
            icon_size=(14, 14),
            icon_anchor=(7, 7),
        ),
        popup=popup,
        tooltip=location_name,
        pane="poi-pane",
        z_index_offset=1000,
        draggable=False,
    ).add_to(folium_map)


def build_folium_map(
    dataframe: pd.DataFrame | None,
    area_name: str,
    *,
    zoom: int,
    empty_label: str,
    service_area_geometry: Any | None = None,
    fit_bounds_max_zoom: int | None = None,
) -> folium.Map:
    """Build a Folium map with POIs and an optional service-area polygon."""

    if dataframe is None or dataframe.empty:
        latitude, longitude = DEFAULT_MAP_CENTER
        map_dataframe = None
    else:
        map_dataframe = dataframe[["location_name", "latitude", "longitude"]].copy()

    if map_dataframe is not None:
        latitude = float(map_dataframe["latitude"].mean())
        longitude = float(map_dataframe["longitude"].mean())

    folium_map = folium.Map(
        location=[latitude, longitude],
        zoom_start=zoom,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    folium.map.CustomPane(
        "service-area-pane",
        z_index=400,
        pointer_events=False,
    ).add_to(folium_map)
    folium.map.CustomPane("poi-pane", z_index=650, pointer_events=True).add_to(
        folium_map
    )

    if map_dataframe is None:
        folium.Marker(
            location=[latitude, longitude],
            tooltip=empty_label,
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(folium_map)
    else:
        for row in map_dataframe.itertuples(index=False):
            add_non_draggable_poi_marker(
                folium_map,
                str(row.location_name),
                float(row.latitude),
                float(row.longitude),
            )

    if service_area_geometry is not None:
        folium.GeoJson(
            data=service_area_geometry.__geo_interface__,
            name=f"{area_name} service area",
            pane="service-area-pane",
            style_function=lambda _: {
                "color": "#0f766e",
                "weight": 3,
                "fillColor": "#0f766e",
                "fillOpacity": 0.18,
            },
            highlight_function=lambda _: {"weight": 5, "fillOpacity": 0.28},
            tooltip=folium.Tooltip(f"{area_name} service area"),
        ).add_to(folium_map)
        min_x, min_y, max_x, max_y = service_area_geometry.bounds
        bounds = [[min_y, min_x], [max_y, max_x]]
        if fit_bounds_max_zoom is None:
            folium_map.fit_bounds(bounds)
        else:
            folium_map.fit_bounds(bounds, max_zoom=fit_bounds_max_zoom)

    return folium_map


def render_map(
    dataframe: pd.DataFrame | None,
    area_name: str,
    *,
    zoom: int,
    empty_label: str,
    map_key: str,
    service_area_geometry: Any | None = None,
    fit_bounds_max_zoom: int | None = None,
) -> None:
    """Render one combined POI and optional service-area preview with progress."""

    progress = st.progress(0, text="Preparing map preview")
    time.sleep(0.05)
    progress.progress(35, text="Preparing POI and service-area layers")

    folium_map = build_folium_map(
        dataframe,
        area_name,
        zoom=zoom,
        empty_label=empty_label,
        service_area_geometry=service_area_geometry,
        fit_bounds_max_zoom=fit_bounds_max_zoom,
    )
    time.sleep(0.05)
    progress.progress(75, text="Rendering interactive map")
    st_folium(
        folium_map,
        key=map_key,
        height=470,
        width=None,
        use_container_width=True,
        returned_objects=[],
    )
    progress.progress(100, text="Map preview ready")


def service_area_geojson(area_name: str, geometry: Any) -> str:
    """Serialize one service-area boundary as a WGS84 GeoJSON FeatureCollection."""

    service_area = gpd.GeoDataFrame(
        {"service_area_name": [area_name]},
        geometry=[geometry],
        crs=WGS84_CRS,
    )
    return service_area.to_json()


def _process_upload(uploaded_file: Any, key_prefix: str) -> tuple[pd.DataFrame | None, str | None]:
    """Process one uploader and retain its result in Streamlit session state."""

    if uploaded_file is None:
        return None, None

    file_bytes = uploaded_file.getvalue()
    signature = file_signature(uploaded_file.name, file_bytes)
    signature_key = f"{key_prefix}_signature"
    result_key = f"{key_prefix}_poi"
    error_key = f"{key_prefix}_error"

    if st.session_state.get(signature_key) != signature:
        st.session_state[signature_key] = signature
        st.session_state[result_key] = None
        st.session_state[error_key] = None

        try:
            with st.status("Processing POI file", expanded=True) as status:
                progress = st.progress(0, text="Reading uploaded file")
                time.sleep(0.08)
                progress.progress(40, text="Checking required columns")
                dataframe = read_poi_file(uploaded_file.name, file_bytes)
                time.sleep(0.08)
                progress.progress(80, text="Validating coordinates")
                time.sleep(0.08)
                progress.progress(100, text="POI file ready")
                status.update(
                    label=f"Validated {len(dataframe)} POI row(s)",
                    state="complete",
                    expanded=False,
                )
            st.session_state[result_key] = dataframe
        except (ValueError, pd.errors.ParserError, ImportError) as exc:
            st.session_state[error_key] = str(exc)

    return st.session_state.get(result_key), st.session_state.get(error_key)


def _persist_to_simulated_databases(
    area_name: str,
    dataframe: pd.DataFrame,
    service_area_record: dict[str, Any],
) -> None:
    """Persist POIs and derived geometry into their separate demo databases."""

    st.session_state.poi_database[area_name] = dataframe.copy()
    st.session_state.service_area_database[area_name] = {
        "service_area_name": area_name,
        **service_area_record,
    }


def render_upload_workflow(key_prefix: str, heading: str) -> None:
    """Render the reusable create/re-upload POI workflow."""

    st.subheader(heading)
    area_options = service_area_names()
    allow_new_service_area = key_prefix == "create_upload"
    if allow_new_service_area:
        area_options = [*area_options, CREATE_NEW_SERVICE_AREA_OPTION]

    selected_area = st.selectbox(
        "Service area",
        area_options,
        key=f"{key_prefix}_area",
        help="Choose where the uploaded POI data belongs.",
    )
    area_name = selected_area
    area_name_error: str | None = None
    if allow_new_service_area and selected_area == CREATE_NEW_SERVICE_AREA_OPTION:
        new_area_name = st.text_input(
            "New service area name",
            key=f"{key_prefix}_new_area_name",
            placeholder="e.g. Punggol",
            help="Enter a unique name for the new service area.",
        ).strip()
        area_name = new_area_name
        area_name_error = validate_new_service_area_name(
            new_area_name, service_area_names()
        )

    map_container = st.container()
    uploaded_file = st.file_uploader(
        "Upload POI data",
        type=SUPPORTED_EXTENSIONS,
        key=f"{key_prefix}_file",
        help="Accepted formats: CSV, XLSX, XLS. Required columns: location name, latitude, longitude.",
    )
    dataframe, error = _process_upload(uploaded_file, key_prefix)

    service_area_record: dict[str, Any] | None = None
    service_area_error: str | None = None
    if dataframe is not None and error is None and area_name_error is None:
        try:
            derived_record = derive_service_area(dataframe)
            if key_prefix == "update_upload":
                existing_record = st.session_state.service_area_database.get(area_name)
                if existing_record is not None:
                    service_area_record = merge_service_area_records(
                        existing_record, derived_record
                    )
                else:
                    service_area_record = derived_record
            else:
                service_area_record = derived_record
        except (ImportError, ValueError) as exc:
            service_area_error = str(exc)

    with map_container:
        if service_area_record is None:
            st.caption("Map preview · default view: Southeast Asia")
        else:
            st.caption("Map preview · uploaded POIs and derived service area")
        is_update_upload = key_prefix == "update_upload"
        render_map(
            dataframe,
            area_name or selected_area,
            zoom=DOWNLOAD_DEFAULT_MAP_ZOOM if is_update_upload else DEFAULT_MAP_ZOOM,
            empty_label="Southeast Asia preview",
            map_key=f"{key_prefix}_overview_map",
            service_area_geometry=(
                service_area_record["geometry"]
                if service_area_record is not None
                else None
            ),
            fit_bounds_max_zoom=(
                None
                if service_area_record is None
                else (
                    DOWNLOAD_DEFAULT_MAP_ZOOM
                    if is_update_upload
                    else CREATE_BOUNDARY_MAP_MAX_ZOOM
                )
            ),
        )

    if error:
        st.error(f"Upload could not be validated: {error}")
        st.info("Required columns: location name, latitude, longitude.")
        return

    if area_name_error:
        st.error(area_name_error)
        return

    if dataframe is None:
        st.info("Upload a POI file to preview the locations and request a backend update.")
        return

    if service_area_error is not None or service_area_record is None:
        st.error(
            "Service-area geometry could not be created: "
            f"{service_area_error or 'No service-area record was produced.'}"
        )
        return

    st.success(f"{len(dataframe)} POI row(s) are ready for confirmation.")
    st.dataframe(dataframe, width="stretch", hide_index=True)
    st.caption(
        "All uploaded POIs are joined into a convex-hull polygon and buffered by 1 km. "
        "Cardinal extremes are retained as audit details. Re-uploaded areas preserve the "
        "previous service-area coverage by merging the old and new shapes."
    )
    st.caption(
        f"Source POI database rows: {len(dataframe)} · "
        f"Service-area database shape: {service_area_record['area_sq_km']:.2f} km² · "
        f"CRS used for buffer: {service_area_record['metric_crs']}"
    )

    if st.button(
        "Request upload to POI + service-area databases",
        key=f"{key_prefix}_confirm",
        type="primary",
        width="stretch",
    ):
        _persist_to_simulated_databases(area_name, dataframe, service_area_record)
        st.session_state[f"{key_prefix}_submitted"] = True
        st.success(
            f"Upload request accepted for {area_name}. "
            "The POI and service-area databases are now synchronized."
        )

    if st.session_state.get(f"{key_prefix}_submitted"):
        st.caption("Status: synchronized with simulated POI and service-area databases")


@st.fragment
def render_update_download_workflow() -> None:
    """Rerun only the service-area preview so selection retains page scroll."""

    area_name = st.selectbox(
        "Synced service area",
        service_area_names(),
        key="update_download_area",
    )
    current_data = st.session_state.poi_database[area_name]
    service_area_record = st.session_state.service_area_database[area_name]
    st.caption(
        f"Service-area database record · {len(current_data)} POI row(s) · "
        f"{service_area_record['area_sq_km']:.2f} km²"
    )
    render_map(
        current_data,
        area_name,
        zoom=DOWNLOAD_DEFAULT_MAP_ZOOM,
        empty_label="No POIs in this service area",
        map_key="update_download_service_area_map",
        service_area_geometry=service_area_record["geometry"],
        fit_bounds_max_zoom=DOWNLOAD_DEFAULT_MAP_ZOOM,
    )
    download_columns = st.columns(2)
    with download_columns[0]:
        st.download_button(
            "Download POI",
            data=current_data.to_csv(index=False).encode("utf-8"),
            file_name=f"{area_name.lower().replace(' ', '_')}_poi.csv",
            mime="text/csv",
            key="download_poi",
            width="stretch",
        )
    with download_columns[1]:
        st.download_button(
            "Download boundary",
            data=service_area_geojson(area_name, service_area_record["geometry"]),
            file_name=f"{area_name.lower().replace(' ', '_')}_boundary.geojson",
            mime="application/geo+json",
            key="download_boundary",
            width="stretch",
        )


def render_update_tab() -> None:
    """Render download and re-upload controls for existing service areas."""

    st.markdown(
        "Select a service area to download its current backend snapshot then submit "
        "replacement POIs below."
    )

    render_update_download_workflow()
    render_upload_workflow("update_upload", "Replace POI records")


def render_footer() -> None:
    """Render the sticky footer required by the product brief."""

    with st.bottom:
        st.markdown(
            "<div class='lsge-footer'>Created by the SWAT Mobility GIS Team</div>",
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
          .block-container { max-width: 1280px; padding-bottom: 5rem; }
          .lsge-footer {
            border-top: 1px solid #d7dee8;
            color: #64748b;
            font-size: 0.8rem;
            padding: 0.65rem 0;
            text-align: center;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    initialize_session_state()
    workspace_view = render_sidebar()

    if not st.session_state.authenticated:
        st.title(APP_TITLE)
        st.markdown("### A controlled workspace for local-service POI updates")
        st.info("Log in from the sidebar to access the geospatial update workspace.")
        with st.container(border=True):
            st.subheader("What this demo supports")
            st.markdown(
                "Upload a CSV or Excel file containing a location name, latitude and "
                "longitude. Review the POIs on a Southeast Asia map, then request a "
                "synchronization to the simulated backend."
            )
            st.caption("This is a local demo. Authentication and backend writes are emulated in session state.")
    else:
        st.title(APP_TITLE)
        st.markdown(
            "Upload, review and synchronize local-service points of interest across "
            "the service areas managed by the GIS team."
        )
        st.markdown(f"### Welcome, {st.session_state.username}")

        selected_view = workspace_view
        if selected_view == CREATE_VIEW:
            render_upload_workflow("create_upload", CREATE_VIEW)
        else:
            render_update_tab()

    render_footer()


if __name__ == "__main__":
    main()
