# Substack Product Demo Assets

These assets support the Local Services Geospatial Update case study. All locations and
operational records are simulated. The capture harness uses the production app's GeoPandas,
Folium, marker, buffering, and service-area merge functions so the map output remains faithful
to the prototype.

## Recommended article sequence

1. `cover/local-services-geospatial-cover.png` — editorial cover image.
2. `screenshots/01-login.png` — controlled login and demo boundary.
3. `gifs/local-services-product-demo.gif` — end-to-end product walkthrough.
4. `screenshots/05-create-review.png` — combined POI and derived service-area review.
5. `gifs/service-area-before-after.gif` — original versus merged service-area coverage.
6. `screenshots/08-poi-popup.png` — clickable POI detail and coordinates.
7. `screenshots/06-update-download.png` — current-data download workflow.
8. `screenshots/07-reupload-merged.png` — revised POIs with retained prior coverage.

The MP4 version at `gifs/local-services-product-demo.mp4` is preferable when the publishing
surface supports autoplaying video; it preserves text and map detail better than GIF.

## Suggested captions

- Login: "The prototype makes its security and simulation boundaries explicit before users
  enter the operational workspace."
- Create review: "Six simulated Jurong East PUDO points are reviewed together with the derived
  1 km-buffered service area."
- Download: "Local-services users can inspect and download the current POI snapshot without
  opening a heavyweight GIS tool."
- Re-upload: "The revised point set extends eastward while retaining the original service-area
  coverage."
- POI popup: "POIs remain the top clickable layer and expose their submitted coordinates."

## Simulated datasets

- `data/jurong_east_pudo_initial.csv` — six initial PUDO points.
- `data/jurong_east_pudo_update.csv` — seven revised points, including Toh Guan and Clementi
  North locations that visibly expand the service area.

## Regenerating screenshots

```bash
streamlit run assets/substack/capture_app.py --server.port 8508
```

Open these capture scenes:

- `http://localhost:8508/?scene=create`
- `http://localhost:8508/?scene=update`
- `http://localhost:8508/?scene=reupload`

The purple badge in the capture harness identifies every scene as a product prototype using
simulated PUDO data. Do not remove that disclosure when publishing the assets.
