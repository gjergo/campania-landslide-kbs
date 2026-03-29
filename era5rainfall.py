import cdsapi

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-land',
    {
        'variable': ['total_precipitation'],
        'year': [str(y) for y in range(1980, 2024)],
        'month': [f'{m:02d}' for m in range(1, 13)],
        'day': [f'{d:02d}' for d in range(1, 32)],
        'time': ['00:00', '06:00', '12:00', '18:00'],
        'area': [40.78, 13.84, 40.68, 13.98],  # N, W, S, E — Ischia bbox
        'format': 'netcdf',
    },
    'ischia_precipitation_1980_2023.nc'
)
