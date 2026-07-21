"""Editorial capture harness for the Substack product-demo assets.

Run with:
    streamlit run assets/substack/capture_app.py --server.port 8508

Scenes:
    ?scene=create
    ?scene=update
    ?scene=reupload
"""

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import (
    APP_TITLE,
    derive_service_area,
    merge_service_area_records,
    render_map,
)


ASSET_ROOT = Path(__file__).resolve().parent
INITIAL_FILE = ASSET_ROOT / "data" / "jurong_east_pudo_initial.csv"
UPDATE_FILE = ASSET_ROOT / "data" / "jurong_east_pudo_update.csv"
AREA_NAME = "Jurong East Pilot"


def load_demo_data() -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    initial_data = pd.read_csv(INITIAL_FILE)
    update_data = pd.read_csv(UPDATE_FILE)
    initial_area = derive_service_area(initial_data)
    merged_area = merge_service_area_records(
        initial_area,
        derive_service_area(update_data),
    )
    return initial_data, update_data, initial_area, merged_area


def render_shell() -> None:
    with st.sidebar:
        st.markdown("### Access portal")
        st.caption("Authenticate to manage local-service POI updates.")
        st.divider()
        st.success("Authenticated")
        st.caption("demo@geospatial.com")
        st.button("Sign out", width="stretch", disabled=True)
        st.divider()
        st.caption("Backend: local simulation")
        st.caption("No production credentials or data are used.")

    st.title(APP_TITLE)
    st.markdown(
        "Upload, review, and synchronize local-service points of interest across "
        "the service areas managed by the GIS team."
    )
    st.caption("Signed in as demo@geospatial.com · Backend: simulated")
    st.markdown(
        "<span class='demo-badge'>PRODUCT PROTOTYPE · SIMULATED PUDO DATA</span>",
        unsafe_allow_html=True,
    )


def render_create(initial_data: pd.DataFrame, initial_area: dict) -> None:
    st.markdown("### Create new Service Area/POI")
    st.selectbox("Service area", [AREA_NAME], disabled=True)
    st.text_input("New service area name", AREA_NAME, disabled=True)
    st.info(f"Uploaded file · {INITIAL_FILE.name} · {len(initial_data)} POI rows")
    st.caption("Map preview · uploaded POIs and derived service area")
    render_map(
        initial_data,
        AREA_NAME,
        zoom=13,
        empty_label="No POIs uploaded",
        map_key="capture_create_map",
        service_area_geometry=initial_area["geometry"],
        fit_bounds_max_zoom=13,
    )
    st.success(f"{len(initial_data)} POI row(s) are ready for confirmation.")
    st.caption(
        "All uploaded POIs are joined into a convex-hull polygon and buffered by 1 km."
    )
    st.button(
        "Request upload to POI + service-area databases",
        type="primary",
        width="stretch",
        disabled=True,
    )


def render_update(initial_data: pd.DataFrame, initial_area: dict) -> None:
    st.markdown("### Update POI")
    st.caption(
        "Select a service area to download its current backend snapshot, or expand "
        "the re-upload section to submit replacement POIs."
    )
    with st.expander("1 · Download current POI data", expanded=True):
        st.selectbox("Synced service area", [AREA_NAME], disabled=True)
        st.caption(
            f"Service-area database record · {len(initial_data)} POI row(s) · "
            f"{initial_area['area_sq_km']:.2f} km²"
        )
        render_map(
            initial_data,
            AREA_NAME,
            zoom=13,
            empty_label="No POIs in this service area",
            map_key="capture_update_map",
            service_area_geometry=initial_area["geometry"],
            fit_bounds_max_zoom=13,
        )
        st.download_button(
            "Download POI CSV",
            data=initial_data.to_csv(index=False).encode("utf-8"),
            file_name=INITIAL_FILE.name,
            mime="text/csv",
            width="stretch",
        )
    with st.expander("2 · Re-upload POI data", expanded=False):
        st.caption("Upload a revised POI file to extend the current service area.")


def render_reupload(update_data: pd.DataFrame, merged_area: dict) -> None:
    st.markdown("### Update POI")
    st.caption(
        "The revised POIs replace the point records while the updated service area "
        "preserves the previous geographic coverage."
    )
    with st.expander("1 · Download current POI data", expanded=False):
        st.caption("Current backend snapshot available for download.")
    with st.expander("2 · Re-upload POI data", expanded=True):
        st.selectbox("Service area", [AREA_NAME], disabled=True)
        st.info(f"Uploaded file · {UPDATE_FILE.name} · {len(update_data)} POI rows")
        st.caption("Map preview · revised POIs and merged service area")
        render_map(
            update_data,
            AREA_NAME,
            zoom=12,
            empty_label="No POIs uploaded",
            map_key="capture_reupload_map",
            service_area_geometry=merged_area["geometry"],
            fit_bounds_max_zoom=12,
        )
        st.success(
            f"{len(update_data)} revised POI row(s) are ready. Previous coverage retained."
        )
        st.button(
            "Request upload to POI + service-area databases",
            type="primary",
            width="stretch",
            disabled=True,
        )
        st.caption("Status: synchronized with simulated POI and service-area databases")


def main() -> None:
    st.set_page_config(
        page_title=f"{APP_TITLE} · Product Demo",
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
          .block-container { max-width: 1280px; padding-bottom: 4rem; }
          .demo-badge {
            background: #ede9fe;
            border: 1px solid #c4b5fd;
            border-radius: 999px;
            color: #5b21b6;
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            margin: 0.25rem 0 1.25rem;
            padding: 0.35rem 0.65rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    initial_data, update_data, initial_area, merged_area = load_demo_data()
    render_shell()

    scene = st.query_params.get("scene", "create")
    if scene == "update":
        render_update(initial_data, initial_area)
    elif scene == "reupload":
        render_reupload(update_data, merged_area)
    else:
        render_create(initial_data, initial_area)


if __name__ == "__main__":
    main()
