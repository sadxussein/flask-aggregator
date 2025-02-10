"""Attempt to make full-scale view (MVC pattern)."""

from abc import ABC, abstractmethod

# 'Composite' pattern implementation attempt.

class FlaskUIComponent(ABC):
    """Base class for widget elements like buttons, drop-down fields, etc."""
    @abstractmethod
    def render(self):
        """Return HTML representation of the UI element."""

class TextField(FlaskUIComponent):
    """Simple text field UI element."""
    def __init__(
        self,
        id_: str,
        name: str,
        label: str,
        class_: str="btn-primary",
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
        class_: str="dropdown-primary"
    ):
        self.__id = id_
        self.__name = name
        self.__label = label
        self.__class = class_
        self.__items = items

    def render(self):
        items_html = ''.join(
            f'<option value="{k}">{v}</option>'
            for k, v in self.__items.items()
        )
        return (
            f'<label for="{self.__id}">{self.__label}</label>'
            f'<select id="{self.__id}" name={self.__name} '
            f'class="{self.__class}">{items_html}</ul>'
        )

class CheckBox(FlaskUIComponent):
    """Simple single check box."""
    def __init__(
        self,
        id_: str,
        name: str,
        label: str,
        class_: str="btn-primary",
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

class UIContainer(FlaskUIComponent):
    """Container for UI components."""
    def __init__(
        self,
        id_: str,
        name: str,
        tag: str="div",
        components: FlaskUIComponent=None,
        class_: str="container"
    ):
        self.__id = id_
        self.__name = name
        self.__tag = tag
        self.__class = class_
        self.__components = components or []

    def add_component(self, c: FlaskUIComponent):
        """Add component to container."""
        self.__components.append(c)

    def render(self):
        inner_html = ''.join(c.render() for c in self.__components)
        return (
            f'<{self.__tag} class="{self.__class}" id="{self.__id}" '
            f'name="{self.__name}"> {inner_html}'
            f'</<{self.__tag}>'
        )
