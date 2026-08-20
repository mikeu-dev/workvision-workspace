"""
Spatial algorithms and geometry utilities for WorkVision AI.
"""

from typing import List, Tuple, Optional


def calculate_foot_point(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
    """
    Calculates the bottom-center coordinate of a bounding box.
    This foot-point serves as the ground plane anchor to mitigate high-angle perspective distortion.
    """
    foot_x = (x1 + x2) / 2.0
    foot_y = float(y2)
    return foot_x, foot_y


def is_point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
    """
    Ray Casting Algorithm to determine if a 2D point (x, y) is inside a polygon.
    Polygon is defined as a list of (x, y) coordinate vertices.
    """
    x, y = point
    n = len(polygon)
    if n < 3:
        return False

    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        x_inters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= x_inters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def calculate_iou(box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]) -> float:
    """
    Calculates Intersection over Union (IoU) between two bounding boxes: (x1, y1, x2, y2).
    """
    x1_inter = max(box1[0], box2[0])
    y1_inter = max(box1[1], box2[1])
    x2_inter = min(box1[2], box2[2])
    y2_inter = min(box1[3], box2[3])

    inter_w = max(0.0, x2_inter - x1_inter)
    inter_h = max(0.0, y2_inter - y1_inter)
    inter_area = inter_w * inter_h

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    union_area = box1_area + box2_area - inter_area
    if union_area <= 0:
        return 0.0

    return inter_area / union_area


class PolygonZone:
    """
    A named spatial zone defined by a polygon in camera pixel coordinate space.
    """
    def __init__(self, zone_id: str, zone_code: str, zone_type: str, points: List[Tuple[float, float]]):
        self.zone_id = zone_id
        self.zone_code = zone_code
        self.zone_type = zone_type
        self.points = points

    def contains(self, foot_point: Tuple[float, float]) -> bool:
        return is_point_in_polygon(foot_point, self.points)
