from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def sin_espacios(parrafo):
    parrafo.paragraph_format.space_before = Pt(0)
    parrafo.paragraph_format.space_after = Pt(0)

def agregar_linea_divisora(parrafo):
    p = parrafo._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')

    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')   # tipo de línea
    bottom.set(qn('w:sz'), '12')        # grosor (8-24 recomendado)
    bottom.set(qn('w:space'), '2')      # separación
    bottom.set(qn('w:color'), '000000') # color

    pBdr.append(bottom)
    pPr.append(pBdr)
