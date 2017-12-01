from escpos import *
from html.parser import HTMLParser

Printer = printer.File("/dev/usb/lp1")

class TagParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if(tag == "br"):
            Printer.text("\n")
        if(tag == "cut"):
            Printer.cut()
        if(tag == "text"):
            align = "left"
            font = "a"
            text_type = 'normal'
            width = 1
            height = 1
            density = 9
            invert = False
            smooth=False
            flip=False

            for attr in attrs:
                if(attr[0] == "align"):
                    print("Alineacion: ", attr[1])
                    align = attr[1]

                if(attr[0] == "font"):
                    print("Fuente: ", attr[1])
                    font = attr[1]

                if(attr[0] == "type"):
                    print("Tipo de texto: ", attr[1])
                    text_type = attr[1]

                if(attr[0] == "underline"):
                    print("Subrayado: ", attr[1])
                    underline = attr[1]

                if(attr[0] == "width"):
                    print("Anchura: ", attr[1])
                    try:
                        data = int(attr[1])
                    except:
                        data = 1
                    width = data

                if(attr[0] == "height"):
                    print("Altura: ", attr[1])
                    try:
                        data = int(attr[1])
                    except:
                        data = 1
                    height = data

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

            Printer.set(align=align, font=font, text_type=text_type, width=width, height=height, density=density, invert=invert, smooth=smooth, flip=flip)

    def handle_endtag(self, tag):
        #print("End tag  :", tag)
        if(tag == "text"):
            Printer.text("\n")

    def handle_data(self, text):
        text = text.replace("\n", "")
        text = text.replace("ñ", "n")
        text = text.replace("á", "a")
        text = text.replace("é", "e")
        text = text.replace("í", "i")
        text = text.replace("ó", "o")
        text = text.replace("ú", "u")
        text = text.replace("ü", "u")
        if(len(text) > 0):
            print("Imprimir: ", text)
            Printer.text(text)

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