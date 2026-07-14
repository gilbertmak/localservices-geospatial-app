from io import BytesIO

import pandas as pd
import pytest
from shapely.geometry import Point

from app import (
    CREATE_NEW_SERVICE_AREA_OPTION,
    POI_MARKER_RADIUS_METERS,
    derive_service_area,
    normalize_poi_dataframe,
    read_poi_file,
    validate_new_service_area_name,
)


def test_create_workflow_uses_new_service_area_option_and_smaller_marker_radius() -> None:
    assert CREATE_NEW_SERVICE_AREA_OPTION == "(create new service area)"
    assert POI_MARKER_RADIUS_METERS == 37.5


def test_validate_new_service_area_name_rejects_blank_and_duplicate_names() -> None:
    assert validate_new_service_area_name("  ", ["Singapore"]) == (
        "Enter a name for the new service area."
    )
    assert validate_new_service_area_name(" singapore ", ["Singapore"]) == (
        "That service area already exists. Enter a different name or choose it from the dropdown."
    )
    assert validate_new_service_area_name("Punggol", ["Singapore"]) is None


def test_normalize_poi_dataframe_accepts_common_headers() -> None:
    dataframe = pd.DataFrame(
        {
            "Location Name": ["Test Hub"],
            "Lat": [1.3521],
            "Lng": [103.8198],
        }
    )

    result = normalize_poi_dataframe(dataframe)

    assert list(result.columns) == ["location_name", "latitude", "longitude"]
    assert result.iloc[0].to_dict() == {
        "location_name": "Test Hub",
        "latitude": 1.3521,
        "longitude": 103.8198,
    }


def test_normalize_poi_dataframe_rejects_invalid_coordinates() -> None:
    dataframe = pd.DataFrame(
        {
            "location_name": ["Invalid Hub"],
            "latitude": [95],
            "longitude": [103.8198],
        }
    )

    with pytest.raises(ValueError, match="Latitude values must be between"):
        normalize_poi_dataframe(dataframe)


def test_read_poi_file_reads_csv_bytes() -> None:
    payload = b"location name,latitude,longitude\nCSV Hub,1.3,103.8\n"

    result = read_poi_file("sample.csv", payload)

    assert result.loc[0, "location_name"] == "CSV Hub"
    assert result.loc[0, "latitude"] == 1.3


def test_read_poi_file_rejects_unsupported_extensions() -> None:
    with pytest.raises(ValueError, match="CSV or Excel"):
        read_poi_file("sample.json", BytesIO(b"{}").getvalue())


def test_derive_service_area_uses_all_pois_and_one_km_buffer() -> None:
    dataframe = pd.DataFrame(
        {
            "location_name": ["North", "East", "South", "West"],
            "latitude": [1.40, 1.35, 1.30, 1.35],
            "longitude": [103.82, 103.90, 103.82, 103.75],
        }
    )

    result = derive_service_area(dataframe)

    assert result["geometry"].is_valid
    assert result["geometry"].geom_type == "Polygon"
    assert result["buffer_meters"] == 1000
    assert result["source_poi_count"] == 4
    assert result["extreme_points"]["north"]["location_name"] == "North"
    assert result["extreme_points"]["east"]["location_name"] == "East"
    assert result["extreme_points"]["south"]["location_name"] == "South"
    assert result["extreme_points"]["west"]["location_name"] == "West"
    assert all(
        result["geometry"].covers(Point(row.longitude, row.latitude))
        for row in dataframe.itertuples()
    )


def test_derive_service_area_covers_reference_station_exit_outlier() -> None:
    """Regression case based on an MRT exit outside the old extreme-only hull."""

    dataframe = pd.DataFrame(
        {
            "location_name": [
                "Sembawang Exit C",
                "Changi Airport Exit A",
                "Harbourfront Exit E",
                "Tuas Link Exit B",
                "Marsiling Exit A",
            ],
            "latitude": [1.449157, 1.356341, 1.264972, 1.340940, 1.432802],
            "longitude": [103.819759, 103.989277, 103.821580, 103.636841, 103.774210],
        }
    )

    result = derive_service_area(dataframe)

    assert all(
        result["geometry"].covers(Point(row.longitude, row.latitude))
        for row in dataframe.itertuples()
    )


def test_derive_service_area_handles_a_single_poi() -> None:
    dataframe = pd.DataFrame(
        {
            "location_name": ["Single Hub"],
            "latitude": [1.3521],
            "longitude": [103.8198],
        }
    )

    result = derive_service_area(dataframe)

    assert result["geometry"].is_valid
    assert result["geometry"].area > 0
