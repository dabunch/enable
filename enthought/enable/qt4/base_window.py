#------------------------------------------------------------------------------
# Copyright (c) 2008, Riverbank Computing Limited
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license.
#
# Author: Riverbank Computing Limited
# Description: <Enthought enable package component>
#
# In an e-mail to enthought-dev on 2008.09.12 at 2:49 AM CDT, Phil Thompson said:
# The advantage is that all of the PyQt code in ETS can now be re-licensed to
# use the BSD - and I hereby give my permission for that to be done. It's
# been on my list of things to do.
#------------------------------------------------------------------------------

# Qt imports.
from enthought.qt.api import QtCore, QtGui, QtOpenGL

# Enthought library imports.
from enthought.enable.abstract_window import AbstractWindow
from enthought.enable.events import KeyEvent, MouseEvent
from enthought.traits.api import Instance

# Local imports.
from constants import BUTTON_NAME_MAP, KEY_MAP, POINTER_MAP

class _QtWindowMixin(object):
    def __init__(self, enable_window):
        self._enable_window = enable_window

        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        self.last_mouse_pos = (pos.x(), pos.y())

        self.setAutoFillBackground(True)
        self.setFocusPolicy(QtCore.Qt.WheelFocus)
        self.setMouseTracking(True)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Expanding)
    
    def closeEvent(self, event):
        self._enable_window.cleanup()
        self._enable_window = None
        return super(_QtWindowMixin, self).closeEvent(event)

    def paintEvent(self, event):
        self._enable_window._paint(event)

    def resizeEvent(self, event):
        dx = self.width()
        dy = self.height()
        component = self._enable_window.component
        
        self._enable_window.resized = (dx, dy)

        if hasattr(component, "fit_window") and component.fit_window:
            component.outer_position = [0, 0]
            component.outer_bounds = [dx, dy]
        elif hasattr(component, "resizable"):
            if "h" in component.resizable:
                component.outer_x = 0
                component.outer_width = dx
            if "v" in component.resizable:
                component.outer_y = 0
                component.outer_height = dy

    def keyReleaseEvent(self, event):
        focus_owner = self._enable_window.focus_owner

        if focus_owner is None:
            focus_owner = self._enable_window.component

            if focus_owner is None:
                event.ignore()
                return

        # Convert the keypress to a standard enable key if possible, otherwise
        # to text.
        key = KEY_MAP.get(event.key())

        if key is None:
            key = unicode(event.text())

            if not key:
                return

        # Use the last-seen mouse position as the coordinates of this event.
        x, y = self.last_mouse_pos

        modifiers = event.modifiers()

        enable_event = KeyEvent(character=key, x=x,
                y=self._enable_window._flip_y(y),
                alt_down=bool(modifiers & QtCore.Qt.AltModifier),
                shift_down=bool(modifiers & QtCore.Qt.ShiftModifier),
                control_down=bool(modifiers & QtCore.Qt.ControlModifier),
                event=event,
                window=self._enable_window)

        focus_owner.dispatch(enable_event, "key_pressed")
    
    #------------------------------------------------------------------------
    # Qt Mouse event handlers
    #------------------------------------------------------------------------

    def enterEvent(self, event):
        self._enable_window._handle_mouse_event("mouse_enter", event)

    def leaveEvent(self, event):
        self._enable_window._handle_mouse_event("mouse_leave", event)

    def mouseDoubleClickEvent(self, event):
        name = BUTTON_NAME_MAP[event.button()]
        self._enable_window._handle_mouse_event(name + "_dclick", event)

    def mouseMoveEvent(self, event):
        self._enable_window._handle_mouse_event("mouse_move", event)

    def mousePressEvent(self, event):
        name = BUTTON_NAME_MAP[event.button()]
        self._enable_window._handle_mouse_event(name + "_down", event)

    def mouseReleaseEvent(self, event):
        name = BUTTON_NAME_MAP[event.button()]
        self._enable_window._handle_mouse_event(name + "_up", event)

    def wheelEvent(self, event):
        self._enable_window._handle_mouse_event("mouse_wheel", event)

    #------------------------------------------------------------------------
    # Qt Drag and drop event handlers
    #------------------------------------------------------------------------

    def dragEnterEvent(self, event):
        pass

    def dragLeaveEvent(self, event):
        pass

    def dragMoveEvent(self, event):
        pass

    def dropEvent(self, event):
        pass


class _QtWindow(QtGui.QWidget, _QtWindowMixin):
    """ The Qt widget that implements the enable control. """
    def __init__(self, enable_window):
        QtGui.QWidget.__init__(self)
        _QtWindowMixin.__init__(self, enable_window)


class _QtGLWindow(QtOpenGL.QGLWidget, _QtWindowMixin):
    def __init__(self, enable_window):
        QtOpenGL.QGLWidget.__init__(self)
        _QtWindowMixin.__init__(self, enable_window)

    def paintEvent(self, event):
        QtOpenGL.QGLWidget.paintEvent(self, event)
        _QtWindowMixin.paintEvent(self, event)

    def resizeEvent(self, event):
        QtOpenGL.QGLWidget.resizeEvent(self, event)
        _QtWindowMixin.resizeEvent(self, event)


class _Window(AbstractWindow):

    control = Instance(_QtWindowMixin)

    def __init__(self, parent, wid=-1, pos=None, size=None, **traits):
        AbstractWindow.__init__(self, **traits)

        self._mouse_captured = False

        self.control = self._create_control(self)

        if pos is not None:
            self.control.move(*pos)

        if size is not None:
            self.control.resize(*size)

    #------------------------------------------------------------------------
    # Implementations of abstract methods in AbstractWindow
    #------------------------------------------------------------------------
    
    def set_drag_result(self, result):
        # FIXME
        raise NotImplementedError

    def _capture_mouse ( self ):
        "Capture all future mouse events"
        # Nothing needed with Qt.
        pass

    def _release_mouse ( self ):
        "Release the mouse capture"
        # Nothing needed with Qt.
        pass

    def _create_mouse_event(self, event):
        # If the event (if there is one) doesn't contain the mouse position,
        # modifiers and buttons then get sensible defaults.
        try:
            x = event.x()
            y = event.y()
            modifiers = event.modifiers()
            buttons = event.buttons()
        except AttributeError:
            pos = self.control.mapFromGlobal(QtGui.QCursor.pos())
            x = pos.x()
            y = pos.y()
            modifiers = 0
            buttons = 0

        self.control.last_mouse_pos = (x, y)

        # A bit crap, because AbstractWindow was written with wx in mind, and
        # we treat wheel events like mouse events.
        if isinstance(event, QtGui.QWheelEvent):
            delta = event.delta()
            degrees_per_step = 15.0
            mouse_wheel = delta / float(8 * degrees_per_step)
        else:
            mouse_wheel = 0

        return MouseEvent(x=x, y=self._flip_y(y), mouse_wheel=mouse_wheel,
                alt_down=bool(modifiers & QtCore.Qt.AltModifier),
                shift_down=bool(modifiers & QtCore.Qt.ShiftModifier),
                control_down=bool(modifiers & QtCore.Qt.ControlModifier),
                left_down=bool(buttons & QtCore.Qt.LeftButton),
                middle_down=bool(buttons & QtCore.Qt.MidButton),
                right_down=bool(buttons & QtCore.Qt.RightButton),
                window=self)

    def _redraw(self, coordinates=None):
        if self.control:
            if coordinates is None:
                self.control.update()
            else:
                self.control.update(*coordinates)

    def _get_control_size(self):
        if self.control:
            return (self.control.width(), self.control.height())

        return None

    def _create_gc(self, size, pix_format="bgra32"):
        raise NotImplementedError 

    def _window_paint(self, event):
        raise NotImplementedError

    def set_pointer(self, pointer):
        self.control.setCursor(POINTER_MAP[pointer])

    def _set_timer_interval(self, component, interval):
        # FIXME
        raise NotImplementedError

    def set_tooltip(self, tooltip):
        self.control.setToolTip(tooltip)

    def _set_focus(self):
        self.control.setFocus()

    #------------------------------------------------------------------------
    # Private methods
    #------------------------------------------------------------------------

    def _flip_y(self, y):
        "Converts between a Kiva and a Qt y coordinate"
        return int(self._size[1] - y - 1)


class BaseGLWindow(_Window):
    # The toolkit control
    control = Instance(_QtGLWindow)
    
    def _create_control(self, enable_window):
        """ Create the toolkit control.
        """
        return _QtGLWindow(enable_window)


class BaseWindow(_Window):
    # The toolkit control
    control = Instance(_QtWindow)
    
    def _create_control(self, enable_window):
        """ Create the toolkit control.
        """
        return _QtWindow(enable_window)
