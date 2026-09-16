#!/usr/bin/env python3
"""KiKit tabs plugin: spacing tabs except on each board's south (-Y) edge."""

from kikit.annotations import TabAnnotation
from kikit.panelize_ui_impl import dummyFramingSubstrate
from kikit.plugin import TabsPlugin


class NoSouthTabs(TabsPlugin):
    """Generate normal spacing tabs, then remove tabs pointing to board -Y."""

    def buildTabAnnotations(self, panel):
        tabs = self.preset["tabs"]
        ghost_substrates = dummyFramingSubstrate(panel.substrates, self.preset)
        panel.buildTabAnnotationsSpacing(
            tabs["spacing"], tabs["hwidth"], tabs["vwidth"], ghost_substrates
        )

        for substrate in panel.substrates:
            substrate.annotations = [
                annotation
                for annotation in substrate.annotations
                if not (
                    isinstance(annotation, TabAnnotation)
                    and ( annotation.direction[1] < -0.5 or annotation.direction[1] > 0.5 )
                )
            ]
