from html.parser import HTMLParser
from jinja2 import is_undefined
import zpl
import logging

class LabelParser(HTMLParser):
    def __init__(self, width, height):
        super().__init__()
        self.width = width
        self.height = height

        self.set_default()

    def set_default(self):
        self.type = None
        self.pos_x = 0
        self.pos_y = 0
        self.char_height = 10
        self.char_width = 10
        self.align = 'L'
        self.font = '0'
        self.barcode_type = 'C'

    def parse(self, stream, *args, **kwargs):
        self.label = zpl.Label(self.height, self.width)
        self.feed(stream)
        
        return self.label.dumpZPL()

    def handle_starttag(self, tag, attrs):
        print(tag, attrs)

        self.type = tag
        
        for attr in attrs:
            if(attr[0] == "x"):
                self.pos_x = float(attr[1])
            if(attr[0] == "y"):
                self.pos_y = float(attr[1])
            if(attr[0] == "height"):
                self.char_height = float(attr[1])
            if(attr[0] == "width"):
                self.char_width = float(attr[1])
            if(attr[0] == "align"):
                if(attr[1] == "center"):
                    self.align = "C"
                if(attr[1] == "left"):
                    self.align = "L"
                if(attr[1] == "right"):
                    self.align = "R"
            if(attr[0] == "type"):
                if(attr[1] == "a"):
                    self.font = '0'
                if(attr[1] == "b"):
                    self.font = '1'

    def handle_endtag(self, tag):
        self.set_default()
        
        pass

    def handle_data(self, text):
        self.label.origin(self.pos_x, self.pos_y)

        if(self.type == "text"):
            self.label.write_text(text, char_height=self.char_height, char_width=self.char_width, line_width=self.width, justification=self.align, font=self.font)

        if(self.type == "barcode"):
            # self.label.barcode(height=int(self.char_height), barcode_type=self.barcode_type, print_interpretation_line='N', print_interpretation_line_above='Y', check_digit='N', mode='N', magnification=2)
            self.label.field_orientation('N', '0')
            self.label.barcode(self.barcode_type, text, height=int(self.char_height), print_interpretation_line='N', print_interpretation_line_above='Y')

        self.label.endorigin()

    def handle_comment(self, data):
        pass

    def handle_entityref(self, name):
        pass

    def handle_charref(self, name):
        pass

    def handle_decl(self, data):
        pass

class TagParser(HTMLParser):
    def parse(self, printer, stream, chars, *args, **kwargs):
        self.printer = printer
        self.chars = int(chars)
        self.feed(stream)
        self.tab = False
        
        # self._parse(stream, False, None, *args, **kwargs)
        # return self.tree.getDocument()

    def handle_starttag(self, tag, attrs):
        print(tag, attrs)

        if(tag == "qr"):
            text = ""
            ec = 0
            size = 10
            model = 2
            native = True
            center = False
            impl = None
            image_arguments = None

            for attr in attrs:
                if(attr[0] == "text"):
                    text = attr[1]
                if(attr[0] == "size"):
                    size = int(attr[1])
                if(attr[0] == "ec"):
                    ec = int(attr[1])
                if(attr[0] == "model"):
                    model = int(attr[1])
                if(attr[0] == "native"):
                    if(attr[1] == "true"):
                        native = True
                        center = False
                    else:
                        native = False
                if(attr[0] == "center"):
                    if(attr[1] == "true"):
                        if native:
                            center = False
                        else:
                            center = True
                    else:
                        center = False
                        
            self.printer.qr(text, ec=ec, size=size, model=model, native=native, center=center, impl=impl, image_arguments=image_arguments)
        
        if(tag == "br"):
            self.printer.text("\n")
        if(tag == "cut"):
            self.printer.cut()
        if(tag == "line"):
            self.printer.set(align="center")
            self.printer.text(( "-" * self.chars ) + "\n")
        if(tag == "text"):
            self.tab = False

            align = "left"
            font = "a"
            is_bold = False
            is_underline = False
            normal_textsize = True
            double_height = False
            double_width = False
            custom_size = False
            width = 1
            height = 1
            density = 8
            invert = False
            smooth=False
            flip=False

            for attr in attrs:
                if(attr[0] == "align"):
                    print("Alineacion: ", attr[1])
                    if not(attr[1] == 'tab'):
                        align = attr[1]
                    else:
                        align = 'right'
                        self.tab = True

                if(attr[0] == "font"):
                    print("Fuente: ", attr[1])
                    font = attr[1]

                if(attr[0] == "type"):
                    print("Tipo de texto: ", attr[1])
                    if(attr[1] == "bold"):
                        is_bold = True

                if(attr[0] == "underline"):
                    print("Subrayado: ", attr[1])
                    if(attr[1] == "true"):
                        is_underline = True
                    else:
                        is_underline = False

                if(attr[0] == "width"):
                    print("Anchura: ", attr[1])
                    try:
                        data = int(attr[1])
                    except:
                        data = 1
                    width = data
                    custom_size = True

                if(attr[0] == "height"):
                    print("Altura: ", attr[1])
                    try:
                        data = int(attr[1])
                    except:
                        data = 1
                    height = data
                    custom_size = True

                if(attr[0] == "density"):
                    print("Densidad: ", attr[1])
                    try:
                        data = int(attr[1])
                    except:
                        data = 9
                    density = data

                if(attr[0] == "invert"):
                    print("Invertido: ", attr[1])
                    if(attr[1] == "true"):
                        data = True
                    else:
                        data = False
                    invert = data

                if(attr[0] == "smooth"):
                    print("Suevizado: ", attr[1])
                    if(attr[1] == "true"):
                        data = True
                    else:
                        data = False
                    smooth = data

                if(attr[0] == "flip"):
                    print("Volteado: ", attr[1])
                    if(attr[1] == "true"):
                        data = True
                    else:
                        data = False
                    flip = data

            self.printer.set(align=align, font=font, bold=is_bold, underline=is_underline, normal_textsize=normal_textsize, double_height=double_height, double_width=double_width, custom_size=custom_size, width=width, height=height, density=density, invert=invert, smooth=smooth, flip=flip)

    def handle_endtag(self, tag):
        #print("End tag  :", tag)
        if(tag == "text"):
            self.printer.text("\n")

    def handle_data(self, text):
        text = text.replace("\n", "")
        text = text.replace("ñ", "n")
        text = text.replace("á", "a")
        text = text.replace("é", "e")
        text = text.replace("í", "i")
        text = text.replace("ó", "o")
        text = text.replace("ú", "u")
        text = text.replace("ü", "u")
        text = text.replace("º", "o")
        text = text.replace("ª", "a")
        text = text.replace("Ñ", "N")
        text = text.replace("Á", "A")
        text = text.replace("É", "E")
        text = text.replace("Í", "I")
        text = text.replace("Ó", "O")
        text = text.replace("Ú", "U")
        text = text.replace("¢", "c")

        if(len(text) > 0):
            if(self.tab):
                colums = text.split('|')
                # print(colums)

                chars = 0
                for col in colums:
                    chars += len(col)

                try:
                    space = (self.chars - chars)//(len(colums)-1)
                except:
                    space = 1

                text = text.replace('|', ' '*space)

            print("Imprimir: ", text)
            self.printer.text(text)


    def handle_comment(self, data):
        #print("Comment  :", data)
        pass

    def handle_entityref(self, name):
        c = chr(name2codepoint[name])
        #print("Named ent:", c)

    def handle_charref(self, name):
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        #print("Num ent  :", c)
        pass

    def handle_decl(self, data):
        #print("Decl     :", data)
        pass
