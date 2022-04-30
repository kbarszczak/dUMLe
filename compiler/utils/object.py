from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from compiler.dUMLeParser import dUMLeParser


class Note:
    def __init__(self, ctx: dUMLeParser.NoteContext):
        self.object_name = ctx.NAME().getText()
        self.note_code = "note left\n"
        for line in ctx.TEXT():
            self.note_code += (line.getText()[1:-1] + "\n")
        self.note_code += "end note\n"

    def generate(self):
        return self.note_code


class Object(ABC):
    @abstractmethod
    def __init__(self):
        self.name = ""
        self.note = None
        self.theme = None  # todo: implement theme

    @abstractmethod
    def _generate(self) -> str:
        pass

    def generate_all(self) -> str:
        result = ""
        result += self._generate()

        # implement theme here

        if self.note:
            result += self.note.generate()
        return result

    def add_note(self, note: Note) -> None:
        if self.note is not None:
            raise Exception(f"Note is already attached to the object \"{self.name}\"")
        self.note = note


class Theme(Object):
    def __init__(self, ctx: dUMLeParser.ThemeContext):
        self.values = []
        self.name = str(ctx.NAME()[0])

        for i in range(len(ctx.PARAM_TYPE())):
            self.values.append((ctx.PARAM_TYPE()[i].getText(),ctx.TEXT()[i].getText().replace('"', '')))

    def _generate(self) -> str:
        res = ""
        for i in range(len(self.values)):
            res += 'skinparam ' + str(self.values[i][0]) + ' ' + str(self.values[i][1]) + '\n'
        return res


class UseCase(Object):
    def __init__(self, ctx: dUMLeParser.Use_caseContext):
        self.content = []
        self.themeName = ""

        if ctx.name()[0]:
            self.themeName = str(ctx.name()[0])

        self.name = str(ctx.NAME()[0])

        for line in ctx.TEXT():
            self.content.append(line)

    def _generate(self):
        res = 'usecase ('
        for i in range(len(self.content)):
            res += str(self.content[i])
        res += ')\n'
        return res


class Block(Object):
    def __init__(self, ctx: dUMLeParser.BlockContext):
        self.themeName = ""
        self.label = ""

        if ctx.name():
            self.themeName = str(ctx.name()[0])
       
        self.name = str(ctx.NAME()[0])

        if ctx.TEXT():
            self.label = str(ctx.TEXT()).replace('"', '')

    def _generate(self):
        res = "block :" + str(self.name) + ":"
        if self.label != "":
            res += ' as ' + self.label
        return res


@dataclass
class Connection:
    source_object_name: str
    destination_object_name: str
    arrow: str
    label: str

    def __init__(self, ctx: dUMLeParser.ConnectionContext):
        self.source_object_name = ctx.name(0).getText()
        self.destination_object_name = ctx.name(1).getText()
        connection_type = ctx.CONNECTION_TYPE().getText()
        self.label = ctx.TEXT()[1:-1]
        if ctx.ARROW():
            self.arrow = str(ctx.ARROW())
        else:
            arrows = {"aggregate": "o--",
                      "inherit": "<|--",
                      "implement": "<|..",
                      "associate": "<--",
                      "depend": "<..",
                      "compose": "*--"}
            self.arrow = arrows[connection_type]

    def generate(self) -> str:
        result = self.source_object_name + " " + self.arrow + " " + self.destination_object_name
        if self.label:
            result += " : " + self.label
        result += "\n"
        return result


class Class(Object):
    def __init__(self, ctx: dUMLeParser.Class_declarationContext):
        self.theme = ""
        self.class_lines = ctx.class_declaration_line()
        self.connections = {}
        if ctx.name():
            self.theme = str(ctx.name()[0])
        self.name = str(ctx.NAME()[0])

    def _generate(self) -> str:
        result = "class " + self.name + " {\n"
        for class_declaration_line in self.class_lines:
            if class_declaration_line.MODIFIER():
                access_type = {"private": "-", "public": "+", "protected": "#"}
                result += (access_type[str(class_declaration_line.MODIFIER())])
            result += str(class_declaration_line.TEXT())[1:-1] + "\n"

        result += "}\n"
        return result

    def add_connection(self, ctx: dUMLeParser.ConnectionContext) -> None:
        if self.name != ctx.name(0).getText():
            raise Exception(f"Source class name is invalid. Expected: {self.name} Got: {ctx.name(0).getText()}")
        connection = Connection(ctx)
        self.connections[connection.destination_object_name] = connection

    def generate_connections(self, class_names: List[str]) -> str:
        result = ""
        for class_name in class_names:
            if class_name not in self.connections:
                continue
            for connection in self.connections[class_name]:
                result += connection.generate()
        return result


class Actor(Object):
    def __init__(self, ctx: dUMLeParser.ActorContext):
        self.themeName = ""
        self.name = ""
        self.label = ""

        if ctx.name():
            # todo: theme is used in object
            self.themeName = str(ctx.name()[0])
        self.name = str(ctx.NAME()[0])

        if ctx.TEXT():
            self.label = str(ctx.TEXT()).replace('"', '')

    def _generate(self):
        res = "actor :" + str(self.name) + ":"
        if self.label != "":
            res += ' as ' + self.label
        return res


class Package(Object):
    def __init__(self, ctx: dUMLeParser.Package_declarationContext):
        self.name = str(ctx.NAME()[0])
        self.themeName = ""
        self.names = []
        self.objects = []

    def _generate(self):
        return ""
