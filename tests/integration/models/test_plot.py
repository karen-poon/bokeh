#-----------------------------------------------------------------------------
# Copyright (c) 2012 - 2021, Anaconda, Inc. All rights reserved.
#
# Powered by the Bokeh Development Team.
#
# The full license is in the file LICENSE.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Boilerplate
#-----------------------------------------------------------------------------
from __future__ import annotations # isort:skip

import pytest ; pytest

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
import time

# External imports
from flaky import flaky

# Bokeh imports
from bokeh._testing.plugins.project import BokehServerPage
from bokeh._testing.util.selenium import find_element_for
from bokeh.events import LODEnd, LODStart, RangesUpdate
from bokeh.layouts import column
from bokeh.models import Button, Plot, Range1d
from bokeh.plotting import figure

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

pytest_plugins = (
    "bokeh._testing.plugins.project",
)


@pytest.mark.selenium
class Test_Plot:
    @flaky(max_runs=10)
    def test_inner_dims_trigger_on_dynamic_add(self, bokeh_server_page: BokehServerPage) -> None:
        button = Button()

        data = {}
        def modify_doc(doc):
            p1 = Plot(height=400, width=400, x_range=Range1d(0, 1), y_range=Range1d(0, 1), min_border=10)
            p2 = Plot(height=400, width=400, x_range=Range1d(0, 1), y_range=Range1d(0, 1), min_border=10)
            layout = column(p1, button)
            def cb(event):
                if p2 not in layout.children:
                    layout.children = [p1, button, p2]
            button.on_event('button_click', cb)
            def iw(attr, old, new): data['iw'] = (old, new)
            def ih(attr, old, new): data['ih'] = (old, new)
            p2.on_change('inner_width', iw)
            p2.on_change('inner_height', ih)
            doc.add_root(layout)

        page = bokeh_server_page(modify_doc)

        find_element_for(page.driver, button, ".bk-btn").click()

        # updates can take some time
        time.sleep(0.5)

        assert data['iw'][0] == 0
        assert isinstance(data['iw'][1], int)
        assert data['iw'][1] < 400

        assert data['ih'][0] == 0
        assert isinstance(data['ih'][1], int)
        assert data['ih'][1] < 400

        # XXX (bev) disabled until https://github.com/bokeh/bokeh/issues/7970 is resolved
        #assert page.has_no_console_errors()

    @flaky(max_runs=10)
    def test_lod_event_triggering(self, bokeh_server_page: BokehServerPage) -> None:
        goodEvents = []
        badEvents = []

        x_range = Range1d(0, 4)
        y_range = Range1d(0, 4)
        p1 = figure(height=400, width=400, x_range=x_range, y_range=y_range, lod_interval=200, lod_timeout=300)
        p1.line([1, 2, 3], [1, 2, 3])
        p2 = figure(height=400, width=400, x_range=x_range, y_range=y_range, lod_interval=200, lod_timeout=300)
        p2.line([1, 2, 3], [1, 2, 3])

        def modify_doc(doc):
            p1.on_event(LODStart, lambda: goodEvents.append("LODStart"))
            p1.on_event(LODEnd, lambda: goodEvents.append("LODEnd"))
            # These 2 should not fire, pan is on p1
            p2.on_event(LODStart, lambda: badEvents.append("LODStart"))
            p2.on_event(LODEnd, lambda: badEvents.append("LODEnd"))

            layout = column(p1, p2)
            doc.add_root(layout)

        page = bokeh_server_page(modify_doc)

        # This can only be called once - calling it multiple times appears to have no effect
        page.drag_canvas_at_position(p1, 100, 100, 200, 200)

        # Wait for drag to happen
        time.sleep(0.1)
        assert goodEvents == ["LODStart"]
        assert badEvents == []

        # Wait for lod_timeout to hit
        time.sleep(0.3)
        assert goodEvents == ["LODStart", "LODEnd"]
        assert badEvents == []

    @flaky(max_runs=10)
    def test_ranges_update_event_trigger_on_pan(self, bokeh_server_page: BokehServerPage) -> None:
        events = []

        x_range = Range1d(0, 4)
        y_range = Range1d(0, 4)
        p = figure(height=400, width=400, x_range=x_range, y_range=y_range)
        p.line([1, 2, 3], [1, 2, 3])

        def modify_doc(doc):
            p.on_event(RangesUpdate, lambda evt: events.append(("RangesUpdate", evt.x0, evt.x1, evt.y0, evt.y1)))
            doc.add_root(p)

        page = bokeh_server_page(modify_doc)

        # This can only be called once - calling it multiple times appears to have no effect
        page.drag_canvas_at_position(p, 100, 100, 200, 200)

        # Wait for drag to happen
        time.sleep(0.2)
        assert events[0][0] == "RangesUpdate"
        assert events[0][1] < -2.3
        assert events[0][2] < 1.7
        assert events[0][3] > 2.1
        assert events[0][4] > 6.1
