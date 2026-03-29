import cdsapi
import os

c = cdsapi.Client()

# Campania bounding box: N, W, S, E
BBOX = [41.5, 13.8, 39.9, 15.8]

os.makedirs("era5_campania", exist_ok=True)

for year in range(1990, 2024):
    outfile = f"era5_campania/precip_{year}.nc"
    if os.path.exists(outfile):
        print(f"Skipping {year}, already downloaded")
        continue
    print(f"Downloading {year}...")
    c.retrieve(
        'reanalysis-era5-land',
        {
            'variable': ['total_precipitation'],
            'year': [str(year)],
            'month': [f'{m:02d}' for m in range(1, 13)],
            'day': [f'{d:02d}' for d in range(1, 32)],
            'time': ['07:00'],  # one time step per day — enough for daily totals
            'area': BBOX,
            'data_format': 'netcdf',
            'download_format': 'unarchived',
        },
        outfile
    )
