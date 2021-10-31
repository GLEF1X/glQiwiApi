from typing import Tuple, Any, Dict, ItemsView


class Polygon:
    """Polygon class for QiwiMaps class"""

    def __init__(
        self, lat_lon_pair_nw: Tuple[Any, ...], lat_lon_pair_se: Tuple[Any, ...]
    ) -> None:
        self.lat_nw, self.lon_nw = lat_lon_pair_nw
        self.lat_se, self.lon_se = lat_lon_pair_se

        self._dict = {
            "latNW": self.lat_nw,
            "lngNW": self.lon_nw,
            "latSE": self.lat_se,
            "lngSE": self.lon_se,
        }

    @property
    def dict(self) -> Dict[Any, Any]:
        return {k: str(double) for k, double in self._get_items()}

    def _get_items(self) -> ItemsView[str, Any]:
        return self._dict.items()


__all__ = ("Polygon",)
