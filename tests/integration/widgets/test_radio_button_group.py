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

# External imports
from flaky import flaky

# Bokeh imports
from bokeh._testing.plugins.project import BokehModelPage, BokehServerPage
from bokeh._testing.util.selenium import RECORD, find_element_for
from bokeh.layouts import column
from bokeh.models import (
    Circle,
    ColumnDataSource,
    CustomAction,
    CustomJS,
    Plot,
    RadioButtonGroup,
    Range1d,
)

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

pytest_plugins = (
    "bokeh._testing.plugins.project",
)

LABELS = ["Option 1", "Option 2", "Option 3"]


@pytest.mark.selenium
class Test_RadioButtonGroup:
    @flaky(max_runs=10)
    def test_server_on_change_round_trip(self, bokeh_server_page: BokehServerPage) -> None:
        group = RadioButtonGroup(labels=LABELS)
        def modify_doc(doc):
            source = ColumnDataSource(dict(x=[1, 2], y=[1, 1], val=["a", "b"]))
            plot = Plot(height=400, width=400, x_range=Range1d(0, 1), y_range=Range1d(0, 1), min_border=0)
            plot.add_glyph(source, Circle(x='x', y='y', size=20))
            plot.add_tools(CustomAction(callback=CustomJS(args=dict(s=source), code=RECORD("data", "s.data"))))
            def cb(active):
                source.data['val'] = [active, "b"]
            group.on_click(cb)
            doc.add_root(column(group, plot))

        page = bokeh_server_page(modify_doc)

        el = find_element_for(page.driver, group, ".bk-btn:nth-child(3)")
        el.click()

        page.click_custom_action()

        results = page.results
        assert results['data']['val'] == [2, "b"]

        el = find_element_for(page.driver, group, ".bk-btn:nth-child(1)")
        el.click()

        page.click_custom_action()

        results = page.results
        assert results['data']['val'] == [0, "b"]

        # XXX (bev) disabled until https://github.com/bokeh/bokeh/issues/7970 is resolved
        #assert page.has_no_console_errors()

    def test_js_on_change_executes(self, bokeh_model_page: BokehModelPage) -> None:
        group = RadioButtonGroup(labels=LABELS)
        group.js_on_click(CustomJS(code=RECORD("active", "cb_obj.active")))

        page = bokeh_model_page(group)

        el = find_element_for(page.driver, group, ".bk-btn:nth-child(3)")
        el.click()

        results = page.results
        assert results['active'] == 2

        el = find_element_for(page.driver, group, ".bk-btn:nth-child(1)")
        el.click()

        results = page.results
        assert results['active'] == 0

        assert page.has_no_console_errors()
