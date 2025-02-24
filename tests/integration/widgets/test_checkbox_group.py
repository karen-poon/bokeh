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
from bokeh._testing.util.selenium import RECORD, find_element_for, find_elements_for
from bokeh.layouts import column
from bokeh.models import (
    CheckboxGroup,
    Circle,
    ColumnDataSource,
    CustomAction,
    CustomJS,
    Plot,
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
class Test_CheckboxGroup:
    @pytest.mark.parametrize('inline', [True, False])
    def test_displays_options_list_of_string_labels_setting_inline(self, inline, bokeh_model_page: BokehModelPage) -> None:
        group = CheckboxGroup(labels=LABELS, inline=inline)

        page = bokeh_model_page(group)

        labels = find_elements_for(page.driver, group, "label")
        assert len(labels) == 3

        for i, label in enumerate(labels):
            assert label.text == LABELS[i]
            input = label.find_element_by_tag_name('input')
            assert input.get_attribute('value') == str(i)
            assert input.get_attribute('type') == 'checkbox'

    @flaky(max_runs=10)
    def test_server_on_change_round_trip(self, bokeh_server_page: BokehServerPage) -> None:
        group = CheckboxGroup(labels=LABELS)
        def modify_doc(doc):
            source = ColumnDataSource(dict(x=[1, 2], y=[1, 1], val=["a", "b"]))
            plot = Plot(height=400, width=400, x_range=Range1d(0, 1), y_range=Range1d(0, 1), min_border=0)
            plot.add_glyph(source, Circle(x='x', y='y', size=20))
            plot.add_tools(CustomAction(callback=CustomJS(args=dict(s=source), code=RECORD("data", "s.data"))))
            def cb(active):
                source.data['val'] = (active + [0, 0])[:2] # keep col length at 2, padded with zero
            group.on_click(cb)
            doc.add_root(column(group, plot))

        page = bokeh_server_page(modify_doc)

        el = find_element_for(page.driver, group, 'input[value="2"]')
        el.click()

        page.click_custom_action()

        results = page.results
        assert results['data']['val'] == [2, 0]

        el = find_element_for(page.driver, group, 'input[value="0"]')
        el.click()

        page.click_custom_action()

        results = page.results
        assert results['data']['val'] == [0, 2]

        # XXX (bev) disabled until https://github.com/bokeh/bokeh/issues/7970 is resolved
        #assert page.has_no_console_errors()

    def test_js_on_change_executes(self, bokeh_model_page: BokehModelPage) -> None:
        group = CheckboxGroup(labels=LABELS)
        group.js_on_click(CustomJS(code=RECORD("active", "cb_obj.active")))

        page = bokeh_model_page(group)

        el = find_element_for(page.driver, group, 'input[value="2"]')
        el.click()

        results = page.results
        assert results['active'] == [2]

        el = find_element_for(page.driver, group, 'input[value="0"]')
        el.click()

        results = page.results
        assert results['active'] == [0, 2]

        el = find_element_for(page.driver, group, 'input[value="2"]')
        el.click()

        results = page.results
        assert results['active'] == [0]

        assert page.has_no_console_errors()
