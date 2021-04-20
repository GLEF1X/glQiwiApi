class Polygon:
    def __init__(self, lat_lon_pair_nw: tuple, lat_lon_pair_se: tuple):
        self.lat_nw, self.lon_nw = lat_lon_pair_nw
        self.lat_se, self.lon_se = lat_lon_pair_se

        self._dict = {
            "latNW": self.lat_nw,
            "lngNW": self.lon_nw,
            "latSE": self.lat_se,
            "lngSE": self.lon_se,
        }

    @property
    def dict(self):
        return {k: str(double) for k, double in self._dict.items()}


__all__ = ("Polygon",)
