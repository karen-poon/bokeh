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
from typing import Tuple

# External imports
from flaky import flaky

# Bokeh imports
from bokeh._testing.plugins.project import BokehServerPage, SinglePlotPage
from bokeh._testing.util.compare import cds_data_almost_equal
from bokeh._testing.util.selenium import RECORD
from bokeh.application.handlers.function import ModifyDoc
from bokeh.layouts import column
from bokeh.models import (
    BoxEditTool,
    ColumnDataSource,
    CustomAction,
    CustomJS,
    Div,
    Plot,
    Range1d,
    Rect,
)

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

pytest_plugins = (
    "bokeh._testing.plugins.project",
)

def _make_plot(dimensions="both", num_objects: int = 0) -> Plot:
    source = ColumnDataSource(dict(x=[1, 2], y=[1, 1], width=[0.5, 0.5], height=[0.5, 0.5]))
    plot = Plot(height=400, width=400, x_range=Range1d(0, 3), y_range=Range1d(0, 3), min_border=0)
    renderer = plot.add_glyph(source, Rect(x='x', y='y', width='width', height='height'))
    tool = BoxEditTool(dimensions=dimensions, num_objects=num_objects, renderers=[renderer])
    plot.add_tools(tool)
    plot.toolbar.active_multi = tool
    code = RECORD("x", "source.data.x", final=False) + \
           RECORD("y", "source.data.y", final=False) + \
           RECORD("width", "source.data.width", final=False) + \
           RECORD("height", "source.data.height")
    plot.add_tools(CustomAction(callback=CustomJS(args=dict(source=source), code=code)))
    plot.toolbar_sticky = False
    return plot

def _make_server_plot(expected, num_objects: int = 0) -> Tuple[ModifyDoc, Plot]:
    plot = Plot(height=400, width=400, x_range=Range1d(0, 3), y_range=Range1d(0, 3), min_border=0)
    def modify_doc(doc):
        source = ColumnDataSource(dict(x=[1, 2], y=[1, 1], width=[0.5, 0.5], height=[0.5, 0.5]))
        renderer = plot.add_glyph(source, Rect(x='x', y='y', width='width', height='height'))
        tool = BoxEditTool(dimensions='both', num_objects=num_objects, renderers=[renderer])
        plot.add_tools(tool)
        plot.toolbar.active_multi = tool
        div = Div(text='False')
        def cb(attr, old, new):
            if cds_data_almost_equal(new, expected):
                div.text = 'True'
        source.on_change('data', cb)
        code = RECORD("matches", "div.text")
        plot.add_tools(CustomAction(callback=CustomJS(args=dict(div=div), code=code)))
        doc.add_root(column(plot, div))
    return modify_doc, plot


@pytest.mark.selenium
class Test_BoxEditTool:
    def test_selected_by_default(self, single_plot_page: SinglePlotPage) -> None:
        plot = _make_plot('both')

        page = single_plot_page(plot)

        button = page.get_toolbar_button('box-edit')
        assert 'active' in button.get_attribute('class')

        assert page.has_no_console_errors()

    def test_can_be_deselected_and_selected(self, single_plot_page: SinglePlotPage) -> None:
        plot = _make_plot('both')

        page = single_plot_page(plot)

        # Check is active
        button = page.get_toolbar_button('box-edit')
        assert 'active' in button.get_attribute('class')

        # Click and check is not active
        button = page.get_toolbar_button('box-edit')
        button.click()
        assert 'active' not in button.get_attribute('class')

        # Click again and check is active
        button = page.get_toolbar_button('box-edit')
        button.click()
        assert 'active' in button.get_attribute('class')

        assert page.has_no_console_errors()

    def test_double_click_triggers_draw(self, single_plot_page: SinglePlotPage) -> None:
        plot = _make_plot('both')

        page = single_plot_page(plot)

        # ensure double clicking added a box
        page.double_click_canvas_at_position(plot, 100, 100)
        time.sleep(0.5)
        page.double_click_canvas_at_position(plot, 200, 200)
        time.sleep(0.5)
        page.click_custom_action()

        expected = {"x": [1, 2, 1.2162162162162162],
                    "y": [1, 1, 1.875],
                    "width": [0.5, 0.5, 0.8108108108108109],
                    "height": [0.5, 0.5, 0.75]}
        assert cds_data_almost_equal(page.results, expected)

        assert page.has_no_console_errors()

    def test_shift_drag_triggers_draw(self, single_plot_page: SinglePlotPage) -> None:
        plot = _make_plot('both')

        page = single_plot_page(plot)

        # ensure double clicking added a box
        page.drag_canvas_at_position(plot, 100, 100, 50, 50, mod="\ue008")
        time.sleep(0.5)
        page.click_custom_action()
        expected = {"x": [1, 2, 1.0135135135135136],
                    "y": [1, 1, 2.0625],
                    "width": [0.5, 0.5, 0.4054054054054054],
                    "height": [0.5, 0.5, 0.3750000000000002]}
        assert cds_data_almost_equal(page.results, expected)

        assert page.has_no_console_errors()

    def test_drag_moves_box(self, single_plot_page: SinglePlotPage) -> None:
        plot = _make_plot('both')

        page = single_plot_page(plot)

        # ensure double clicking added a box
        page.double_click_canvas_at_position(plot, 100, 100)
        time.sleep(0.5)
        page.double_click_canvas_at_position(plot, 200, 200)
        time.sleep(0.5)
        page.drag_canvas_at_position(plot, 150, 150, 50, 50)
        time.sleep(0.5)
        page.click_custom_action()

        expected = {"x": [1, 2, 1.6216216216216217],
                    "y": [1, 1, 1.5000000000000002],
                    "width": [0.5, 0.5, 0.8108108108108109],
                    "height": [0.5, 0.5, 0.75]}
        assert cds_data_almost_equal(page.results, expected)

        assert page.has_no_console_errors()

    def test_backspace_deletes_drawn_box(self, single_plot_page: SinglePlotPage) -> None:
        plot = _make_plot('both', num_objects=2)

        page = single_plot_page(plot)

        # ensure backspace deletes box
        page.double_click_canvas_at_position(plot, 100, 100)
        time.sleep(0.5)
        page.double_click_canvas_at_position(plot, 200, 200)
        time.sleep(0.5)
        page.click_canvas_at_position(plot, 150, 150)
        time.sleep(0.5)
        page.send_keys("\ue003")  # Backspace
        time.sleep(0.5)

        page.click_custom_action()

        expected = {"x": [2], "y": [1], "width": [0.5], "height": [0.5]}
        assert cds_data_almost_equal(page.results, expected)

        assert page.has_no_console_errors()

    def test_num_objects_limits_drawn_boxes(self, single_plot_page: SinglePlotPage) -> None:
        plot = _make_plot('both', num_objects=2)

        page = single_plot_page(plot)

        # ensure double clicking added a box
        page.drag_canvas_at_position(plot, 100, 100, 50, 50, mod="\ue008")
        time.sleep(0.5)
        page.click_custom_action()

        expected = {"x": [2, 1.0135135135135136],
                    "y": [1, 2.0625],
                    "width": [0.5, 0.4054054054054054],
                    "height": [0.5, 0.3750000000000002]}
        assert cds_data_almost_equal(page.results, expected)

        assert page.has_no_console_errors()

    @flaky(max_runs=10)
    def test_box_draw_syncs_to_server(self, bokeh_server_page: BokehServerPage) -> None:
        expected = {"x": [1, 2, 1.2162162162162162],
                    "y": [1, 1, 1.875],
                    "width": [0.5, 0.5, 0.8108108108108109],
                    "height": [0.5, 0.5, 0.75]}

        modify_doc, plot = _make_server_plot(expected)
        page = bokeh_server_page(modify_doc)

        # ensure double clicking added a box
        page.double_click_canvas_at_position(plot, 100, 100)
        time.sleep(0.5)
        page.double_click_canvas_at_position(plot, 200, 200)
        time.sleep(0.5)

        page.click_custom_action()
        assert page.results == {"matches": "True"}

    @flaky(max_runs=10)
    def test_box_drag_syncs_to_server(self, bokeh_server_page: BokehServerPage) -> None:
        expected = {"x": [1, 2, 1.6216216216216217],
                    "y": [1, 1, 1.5000000000000002],
                    "width": [0.5, 0.5, 0.8108108108108109],
                    "height": [0.5, 0.5, 0.75]}

        modify_doc, plot = _make_server_plot(expected)
        page = bokeh_server_page(modify_doc)

        # ensure drag moves box
        page.double_click_canvas_at_position(plot, 100, 100)
        time.sleep(0.5)
        page.double_click_canvas_at_position(plot, 200, 200)
        time.sleep(0.5)
        page.drag_canvas_at_position(plot, 150, 150, 50, 50)
        time.sleep(0.5)
        page.click_custom_action()

        page.click_custom_action()
        assert page.results == {"matches": "True"}

    @flaky(max_runs=10)
    def test_box_delete_syncs_to_server(self, bokeh_server_page: BokehServerPage) -> None:
        expected = {"x": [2], "y": [1],
                    "width": [0.5], "height": [0.5]}

        modify_doc, plot = _make_server_plot(expected, num_objects=2)
        page = bokeh_server_page(modify_doc)

        # ensure backspace deletes box
        page.double_click_canvas_at_position(plot, 100, 100)
        time.sleep(0.5)
        page.double_click_canvas_at_position(plot, 200, 200)
        time.sleep(0.5)
        page.click_canvas_at_position(plot, 150, 150)
        time.sleep(0.5)
        page.send_keys("\ue003")  # Backspace
        time.sleep(0.5)

        page.click_custom_action()
        assert page.results == {"matches": "True"}
