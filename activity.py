# Copyright 2014 Gonzalo Odird, SugarLabs
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import logging
import json

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf

from gettext import gettext as _

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics import style


class ComunicatorMakerActivity(activity.Activity):

    def __init__(self, handle):
        """Set up the HelloWorld activity."""
        activity.Activity.__init__(self, handle)

        # Change the following number to change max participants
        self.max_participants = 1

        toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

        self._boards = []

        background = Gtk.EventBox()
        background.modify_bg(Gtk.StateType.NORMAL,
                             style.Color('#FFFFFF').get_gdk_color())
        self.set_canvas(background)

        # canvas
        hbox = Gtk.HBox()
        background.add(hbox)

        # treeview with pictograms
        self._create_picto_treeview()
        scrolled = Gtk.ScrolledWindow()
        scrolled.props.hscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        scrolled.props.vscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        scrolled.set_size_request(Gdk.Screen.width() / 4, -1)
        scrolled.add_with_viewport(self._picto_tree_view)
        hbox.pack_start(scrolled, False, False, 0)

        self._board_edit_panel = BoardEditPanel()
        hbox.pack_start(self._board_edit_panel, True, True, 0)

        self._load_pictograms()

        self.show_all()

    def _create_picto_treeview(self):
        self._picto_tree_view = Gtk.TreeView()
        self._picto_tree_view.props.headers_visible = False
        self._picto_tree_view.connect('row-activated',
                                      self.__picto_tree_row_activated_cb)

        cell = Gtk.CellRendererText()
        self._column = Gtk.TreeViewColumn()
        self._column.pack_start(cell, True)
        self._column.add_attribute(cell, 'text', 0)
        self._picto_tree_view.append_column(self._column)
        self._picto_tree_view.set_search_column(0)

    def _load_pictograms(self):
        self._picto_tree_view.set_model(Gtk.TreeStore(str, str))
        self._picto_model = self._picto_tree_view.get_model()
        self._add_dir_to_model('./pictograms', self._filter_function)

    def _add_dir_to_model(self, dir_path, filter_function, parent=None):
        logging.error('dir %s', dir_path)
        for f in os.listdir(dir_path):
            full_path = os.path.join(dir_path, f)
            if os.path.isdir(full_path):
                new_iter = self._picto_model.append(parent, [f, full_path])
                self._add_dir_to_model(full_path, filter_function, new_iter)
            else:
                if filter_function(full_path):
                    self._picto_model.append(parent, [f, full_path])

    def _filter_function(self, path):
        return True

    def __picto_tree_row_activated_cb(self, treeview, path, col):
        model = treeview.get_model()
        image_path = model[path][1]
        if os.path.isfile(image_path):
            self._board_edit_panel.add_image(image_path)
        else:
            if treeview.row_expanded(path):
                treeview.collapse_row(path)
            else:
                treeview.expand_to_path(path)

    def write_file(self, file_name):
        # test reading the data from the board
        logging.error(self._board_edit_panel.get_data())
        self._boards.append(self._board_edit_panel.get_data())
        with open(file_name, 'w') as json_file:
            json.dump(self._boards, json_file)

    def read_file(self, file_name):
        with open(file_name) as json_file:
            self._boards = json.load(json_file)
        logging.error('READ_FILE boards = %s', self._boards)
        # display the first board
        if len(self._boards) > 0:
            board = self._boards[0]
            self._board_edit_panel.set_name(board['name'])
            for option in board['options']:
                self._board_edit_panel.add_image(option['image_file_name'],
                                                 option['title'])


class BoardEditPanel(Gtk.EventBox):

    def __init__(self):
        Gtk.EventBox.__init__(self)
        vbox = Gtk.VBox()
        self.add(vbox)
        title_label = Gtk.Label(_('Board name'))
        title_label.set_valign(Gtk.Align.START)
        title_label.set_halign(Gtk.Align.START)
        title_label.props.margin = 10

        hbox = Gtk.HBox()
        hbox.pack_start(title_label, False, False, 10)
        self._title_entry = Gtk.Entry()
        hbox.pack_start(self._title_entry, True, True, 10)

        vbox.pack_start(hbox, False, False, 0)
        grid = Gtk.Grid()
        vbox.pack_start(grid, True, True, 0)
        self._editors = []
        for row in range(2):
            for column in range(3):
                picto_editor = PictoEditPanel()
                picto_editor.set_hexpand(True)
                picto_editor.set_vexpand(True)
                picto_editor.connect('button-press-event',
                                     self._editor_selected_cb)
                self._editors.append(picto_editor)
                grid.attach(picto_editor, column, row, 1, 1)

        self._selected = 0

    def _editor_selected_cb(self, editor, data=None):
        last_editor = self._editors[self._selected]
        last_editor.modify_bg(Gtk.StateType.NORMAL,
                              style.Color('#FFFFFF').get_gdk_color())

        self._selected = self._editors.index(editor)
        editor.modify_bg(Gtk.StateType.NORMAL,
                         style.Color('#FF0000').get_gdk_color())

        logging.error('_last_selected is %d', self._selected)

    def add_image(self, image_file_name, label=None):
        editor = self._editors[self._selected]
        editor.set_image(image_file_name)
        if label is not None:
            editor.set_label(label)

    def set_name(self, board_title):
        self._title_entry.set_text(board_title)

    def get_data(self):
        data = {}
        data['name'] = self._title_entry.get_text()
        options = []
        data['options'] = options
        for editor in self._editors:
            if editor.get_image_file_name() is not None:
                option = {'image_file_name': editor.get_image_file_name(),
                          'title': editor.get_label()}
                options.append(option)
        return data


class PictoEditPanel(Gtk.EventBox):

    def __init__(self):
        Gtk.EventBox.__init__(self)
        vbox = Gtk.VBox()
        self.add(vbox)
        self.image = Gtk.Image()
        vbox.add(self.image)
        self.entry = Gtk.Entry()
        self.entry.props.margin = 20
        vbox.add(self.entry)
        self.set_image('./pictograms/no.png')
        self.set_label('')
        # set as None to clean the default no.png
        self._image_file_name = None

    def set_image(self, image_file_name):
        self._image_file_name = image_file_name
        image_size = Gdk.Screen.height() / 4
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
            image_file_name, image_size, image_size)
        self.image.set_from_pixbuf(pixbuf)
        if self.get_label() == '':
            image_name = image_file_name[image_file_name.rfind('/') + 1:]
            image_name = image_name[:image_name.find('.')]
            self.set_label(image_name.upper())

    def get_image_file_name(self):
        return self._image_file_name

    def set_label(self, label):
        self.entry.set_text(label)

    def get_label(self):
        return self.entry.get_text()
