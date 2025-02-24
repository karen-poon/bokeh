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
from typing import Tuple

# External imports
from flaky import flaky

# Bokeh imports
from bokeh._testing.plugins.project import BokehModelPage, BokehServerPage, SinglePlotPage
from bokeh._testing.util.selenium import RECORD, enter_text_in_element, find_element_for
from bokeh.application.handlers.function import ModifyDoc
from bokeh.layouts import column
from bokeh.models import (
    Circle,
    ColumnDataSource,
    CustomAction,
    CustomJS,
    Plot,
    Range1d,
    TextInput,
)

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

pytest_plugins = (
    "bokeh._testing.plugins.project",
)

def mk_modify_doc(text_input: TextInput) -> Tuple[ModifyDoc, Plot]:
    plot = Plot(height=400, width=400, x_range=Range1d(0, 1), y_range=Range1d(0, 1), min_border=0)
    def modify_doc(doc):
        source = ColumnDataSource(dict(x=[1, 2], y=[1, 1], val=["a", "b"]))
        plot.add_glyph(source, Circle(x='x', y='y', size=20))
        plot.add_tools(CustomAction(callback=CustomJS(args=dict(s=source), code=RECORD("data", "s.data"))))
        def cb(attr, old, new):
            source.data['val'] = [old, new]
        text_input.on_change('value', cb)
        doc.add_root(column(text_input, plot))
    return modify_doc, plot

@pytest.mark.selenium
class Test_TextInput:
    def test_displays_text_input(self, bokeh_model_page: BokehModelPage) -> None:
        text_input = TextInput()
        page = bokeh_model_page(text_input)

        el = find_element_for(page.driver, text_input, "input")
        assert el.get_attribute('type') == "text"

        assert page.has_no_console_errors()

    def test_displays_title(self, bokeh_model_page: BokehModelPage) -> None:
        text_input = TextInput(title="title")
        page = bokeh_model_page(text_input)

        el = find_element_for(page.driver, text_input, "label")
        assert el.text == "title"
        el = find_element_for(page.driver, text_input, "input")
        assert el.get_attribute('placeholder') == ""
        assert el.get_attribute('type') == "text"

        assert page.has_no_console_errors()

    def test_displays_placeholder(self, bokeh_model_page: BokehModelPage) -> None:
        text_input = TextInput(placeholder="placeholder")
        page = bokeh_model_page(text_input)

        el = find_element_for(page.driver, text_input, "label")
        assert el.text == ""
        el = find_element_for(page.driver, text_input, "input")
        assert el.get_attribute('placeholder') == "placeholder"
        assert el.get_attribute('type') == "text"

        assert page.has_no_console_errors()

    @flaky(max_runs=10)
    def test_server_on_change_no_round_trip_without_enter_or_click(self, bokeh_server_page: BokehServerPage) -> None:
        text_input = TextInput()
        modify_doc, _ = mk_modify_doc(text_input)
        page = bokeh_server_page(modify_doc)

        el = find_element_for(page.driver, text_input, "input")
        enter_text_in_element(page.driver, el, "pre", enter=False)  # not change event if enter is not pressed

        page.click_custom_action()

        results = page.results
        assert results['data']['val'] == ["a", "b"]

        # XXX (bev) disabled until https://github.com/bokeh/bokeh/issues/7970 is resolved
        #assert page.has_no_console_errors()

    #@flaky(max_runs=10)
    # TODO (bev) Fix up after GH CI switch
    @pytest.mark.skip
    @flaky(max_runs=10)
    def test_server_on_change_round_trip(self, bokeh_server_page: BokehServerPage) -> None:
        text_input = TextInput()
        modify_doc, plot = mk_modify_doc(text_input)
        page = bokeh_server_page(modify_doc)

        el = find_element_for(page.driver, text_input, "input")
        enter_text_in_element(page.driver, el, "val1")

        page.click_custom_action()

        results = page.results
        assert results['data']['val'] == ["", "val1"]

        # double click to highlight and overwrite old text
        enter_text_in_element(page.driver, el, "val2", click=2)

        page.click_custom_action()

        results = page.results
        assert results['data']['val'] == ["val1", "val2"]

        # Check clicking outside input also triggers
        enter_text_in_element(page.driver, el, "val3", click=2, enter=False)
        page.click_canvas_at_position(plot, 10, 10)

        page.click_custom_action()

        results = page.results
        assert results['data']['val'] == ["val2", "val3"]

        # XXX (bev) disabled until https://github.com/bokeh/bokeh/issues/7970 is resolved
        #assert page.has_no_console_errors()

    def test_js_on_change_executes(self, single_plot_page: SinglePlotPage) -> None:
        source = ColumnDataSource(dict(x=[1, 2], y=[1, 1]))
        plot = Plot(height=400, width=400, x_range=Range1d(0, 1), y_range=Range1d(0, 1), min_border=0)
        plot.add_glyph(source, Circle(x='x', y='y', size=20))
        text_input = TextInput()
        text_input.js_on_change('value', CustomJS(code=RECORD("value", "cb_obj.value")))

        page = single_plot_page(column(text_input, plot))

        el = find_element_for(page.driver, text_input, "input")
        enter_text_in_element(page.driver, el, "val1")

        results = page.results
        assert results['value'] == 'val1'

        # double click to highlight and overwrite old text
        enter_text_in_element(page.driver, el, "val2", click=2)

        results = page.results
        assert results['value'] == 'val2'

        # Check clicking outside input also triggers
        enter_text_in_element(page.driver, el, "val3", click=2, enter=False)
        page.click_canvas_at_position(plot, 10, 10)
        results = page.results

        assert results['value'] == 'val3'

        assert page.has_no_console_errors()
