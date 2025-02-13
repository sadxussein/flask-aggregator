"""Attempt to make full-scale view (MVC pattern)."""

from abc import ABC, abstractmethod

# 'Composite' pattern implementation attempt.

class UIMeta:
    """Define name, id and class tags of the item."""
    def __init__(
        self,
        id_: str=None,
        class_: str=None,
        name: str=None
    ):
        self.__id = id_ or ''
        self.__class = class_ or ''
        self.__name = name or ''

    def render(self):
        """Print without tags, so result string can be embedded into html."""
        result = ' '.join([
            f'class="{self.__class}" ' if self.__class else '',
            f'id="{self.__id}" ' if self.__id else '',
            f'name="{self.__name}" ' if self.__name else ''
        ])
        return result

class FlaskUIComponent(ABC):
    """Base class for widget elements like buttons, drop-down fields, etc."""
    @abstractmethod
    def render(self):
        """Return HTML representation of the UI element."""

class LinkWrapper(FlaskUIComponent):
    """Simple 'a' tag wrapper for single element.
    
    If constructor is empty it does nothing.
    """
    def __init__(self, element: FlaskUIComponent, href: str=None):
        self.__href = href
        self.__el = element

    def render(self):
        return (
            f'<a href="{self.__href}">{self.__el}</a>' 
            if self.__href else self.__el
        )

class LinkButton(FlaskUIComponent):
    """Simple button with link attached."""
    def __init__(
        self,
        label: str,
        href: str,
        id_: str=None,
        name: str=None,
        class_: str="btn-primary"
    ):
        self.__ui_meta = UIMeta(id_, class_, name)
        self.__label = label
        self.__href = href

    def render(self):
        return (
            f'<a href="{self.__href}"><button {self.__ui_meta.render()}>'
            f'{self.__label}</button></a>'
        )

class TextField(FlaskUIComponent):
    """Simple text field UI element."""
    def __init__(
        self,
        id_: str,
        name: str,
        label: str,
        class_: str="text-field-primary",
        value: str=''
    ):
        self.__id = id_
        self.__name = name
        self.__label = label
        self.__class = class_
        self.__value = value

    def render(self):
        return (
            f'<label for="{self.__name}">{self.__label}:</label>'
            f'<input type="text" class="{self.__class}" '
            f'id="{self.__id}" name="{self.__name}" value="{self.__value}">'
        )

    def set_value(self, value: str):
        """Set text field value."""
        self.__value = value

class DropDownField(FlaskUIComponent):
    """Simple drop-down field UI element."""
    def __init__(
        self,
        id_: str,
        name: str,
        label: str,
        items: dict[str, str],
        cur_option: str='',
        class_: str="dropdown-primary"
    ):
        self.__id = id_
        self.__name = name
        self.__label = label
        self.__class = class_
        self.__items = items
        self.__value = cur_option

    def set_value(self, cur_option: str):
        """Set dropdown field value."""
        self.__value = cur_option

    def render(self):
        items_html = ''.join(
            (
                f'<option value="{k}"'
                f'{"selected" if self.__value == v else ""}>{v}</option>'
            ) for k, v in self.__items.items()
        )
        return (
            f'<label for="{self.__id}">{self.__label}</label>'
            f'<select id="{self.__id}" name={self.__name} '
            f'class="{self.__class}">{items_html}</select>'
        )

class CheckBox(FlaskUIComponent):
    """Simple single check box."""
    def __init__(
        self,
        id_: str,
        name: str,
        label: str,
        class_: str="chkbox-primary",
        checked: bool=False
    ):
        self.__id = id_
        self.__name = name
        self.__label = label
        self.__class = class_
        self.__checked = "checked" if checked else ""

    def set_value(self, checked: bool):
        """Set checkbox state."""
        self.__checked = "checked" if checked else ""

    def render(self):
        return (
            f'<label><input type="checkbox" name="{self.__name}" '
            f'class="{self.__class}" id="{self.__id}" {self.__checked}>'
            f'{self.__label}</label>'
        )


class SubmitButton(FlaskUIComponent):
    """Simple submit button."""
    def __init__(self, name: str, class_: str="submit-primary"):
        self.__name = name
        self.__class = class_

    def render(self):
        return (
            f'<button type="submit" class="{self.__class}">'
            f'{self.__name}</button>'
        )

class Table(FlaskUIComponent):
    """Table container."""
    def __init__(
        self,
        id_: str,
        name: str,
        class_: str="table-primary",
        components: FlaskUIComponent=None
    ):
        self.__id = id_
        self.__name = name
        self.__class = class_
        self.__components = components or []

    def add_component(self, c: FlaskUIComponent):
        """Add component to container."""
        self.__components.append(c)

    def render(self):
        items_html = ''.join(c.render() for c in self.__components)
        return (
            f'<table id="{self.__id}" class="{self.__class}" '
            f'name="{self.__name}">{items_html}</table>'
        )

class TableRow(FlaskUIComponent):
    """Row table element."""
    def __init__(
        self,
        components: FlaskUIComponent=None
    ):
        self.__components = components or []

    def add_component(self, c: FlaskUIComponent):
        """Add cells to table row."""
        self.__components.append(c)

    def render(self):
        items_html = ''.join(c.render() for c in self.__components)
        return f'<tr>{items_html}</tr>'

class TableCell(FlaskUIComponent):
    """Cell table element."""
    def __init__(
        self,
        value: any,
        id_: str=None,
        name: str=None,
        class_: str="table-cell-primary",
        is_header: bool=False,
        link: str=''
    ):
        self.__ui_meta = UIMeta(id_, class_, name)
        self.__is_header = is_header
        # If link is empty, wrapper returns simple value.
        self.__link_wrap = LinkWrapper(value, link)

    def render(self):
        if self.__is_header:
            return (
                f'<th {self.__ui_meta.render()}>{self.__link_wrap.render()}'
                '</th>'
            )
        return f'<td>{self.__link_wrap.render()}</td>'


class UIContainer(FlaskUIComponent):
    """Container for UI components."""
    def __init__(
        self,
        id_: str=None,
        name: str=None,
        tag: str="div",
        components: FlaskUIComponent=None,
        class_: str="container"
    ):
        self.__ui_meta = UIMeta(id_, class_, name)
        self.__tag = tag
        self.__components = components or []

    def add_component(self, c: FlaskUIComponent):
        """Add component to container."""
        self.__components.append(c)

    def render(self):
        inner_html = ''.join(c.render() for c in self.__components)
        return (
            f'<{self.__tag} {self.__ui_meta.render()}> {inner_html}'
            f'</{self.__tag}>'
        )
