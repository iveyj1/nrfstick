#!/usr/bin/env python3
"""KiKit framing plugin with extra clearance below the bottom board row."""

from itertools import chain

from kikit.panelize_ui_impl import polygonToSubstrate
from kikit.plugin import FramingPlugin
from kikit import units
from shapely.geometry import LineString, Polygon, box


BOTTOM_SPACE = units.readLength("20mm")


def _arg_length(arg, default):
    if not arg:
        return default
    if "=" in arg:
        _, value = arg.split("=", 1)
    else:
        value = arg
    return units.readLength(value.strip())


class AsymmetricFrame(FramingPlugin):
    """Full frame using normal top/side gaps and a larger bottom gap."""

    def __init__(self, preset, userArg):
        super().__init__(preset, userArg)
        self.bottom_space = _arg_length(userArg, BOTTOM_SPACE)

    def _dims(self, panel):
        framing = self.preset["framing"]
        width = framing["width"]
        hspace = framing["hspace"]
        vspace = framing["vspace"]
        minx, miny, maxx, maxy = panel.boardsBBox()

        inner = (minx - hspace, miny - vspace, maxx + hspace, maxy + self.bottom_space)
        outer = (inner[0] - width, inner[1] - width, inner[2] + width, inner[3] + width)
        return (minx, miny, maxx, maxy), inner, outer

    def buildFraming(self, panel):
        board, inner, outer = self._dims(panel)
        frame = Polygon(
            [
                (outer[0], outer[1]),
                (outer[2], outer[1]),
                (outer[2], outer[3]),
                (outer[0], outer[3]),
            ],
            [[
                (inner[0], inner[1]),
                (inner[0], inner[3]),
                (inner[2], inner[3]),
                (inner[2], inner[1]),
            ]],
        )
        panel.appendSubstrate(frame)

        minx, miny, maxx, maxy = board
        vertical_cuts = [
            LineString([(minx, outer[1]), (minx, inner[1])]),
            LineString([(maxx, outer[1]), (maxx, inner[1])]),
            LineString([(minx, inner[3]), (minx, outer[3])]),
            LineString([(maxx, inner[3]), (maxx, outer[3])]),
        ]
        horizontal_cuts = [
            LineString([(outer[0], miny), (inner[0], miny)]),
            LineString([(inner[2], miny), (outer[2], miny)]),
            LineString([(outer[0], maxy), (inner[0], maxy)]),
            LineString([(inner[2], maxy), (outer[2], maxy)]),
        ]
        return chain(vertical_cuts, horizontal_cuts)

    def buildDummyFramingSubstrates(self, substrates):
        framing = self.preset["framing"]
        width = framing["width"]
        hspace = framing["hspace"]
        vspace = framing["vspace"]

        minx, miny, maxx, maxy = substrates[0].bounds()
        for substrate in substrates[1:]:
            sx0, sy0, sx1, sy1 = substrate.bounds()
            minx = min(minx, sx0)
            miny = min(miny, sy0)
            maxx = max(maxx, sx1)
            maxy = max(maxy, sy1)

        return [
            polygonToSubstrate(box(minx, miny - 2 * vspace - width, maxx, miny - 2 * vspace)),
            polygonToSubstrate(box(minx, maxy + 2 * self.bottom_space, maxx, maxy + 2 * self.bottom_space + width)),
            polygonToSubstrate(box(minx - 2 * hspace - width, miny, minx - 2 * hspace, maxy)),
            polygonToSubstrate(box(maxx + 2 * hspace, miny, maxx + 2 * hspace + width, maxy)),
        ]
