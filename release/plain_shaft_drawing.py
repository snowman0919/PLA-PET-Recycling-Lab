"""Dimensioned outlines for the three plain guide/dancer shafts only."""
import math
PLAIN_SHAFT_IDS = {'SP-TG-01', 'SP-AX-01', 'SP-AX-02'}


def views(part, shape):
    if part['part_id'] not in PLAIN_SHAFT_IDS:
        raise ValueError('plain-shaft renderer used for another part')
    b=shape.BoundBox; diameter=b.XLength; length=b.ZLength
    if not all(math.isfinite(v) and v>0 for v in (diameter,length)):
        raise ValueError('invalid shaft dimensions')
    if abs(diameter-8)>1e-6 or abs(b.YLength-diameter)>1e-6:
        raise ValueError('unexpected shaft cross-section')
    if len(shape.Solids)!=1 or len(shape.Faces)!=3 or abs(shape.Volume-math.pi*diameter**2*length/4)>1e-3:
        raise ValueError('non-plain shaft requires a dedicated feature drawing')
    tolerance='0.50 (ISO 2768-m)' if part['part_id']=='SP-TG-01' else '0.10'
    x0,x1,cy=430.,1000.,230.
    height=diameter/length*(x1-x0); top=cy-height/2; bottom=cy+height/2
    return f'''<defs><marker id="shaft-arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse"><path d="M8,0 L0,4 L8,8" fill="none" stroke="#111"/></marker></defs>
<g fill="none" stroke="#111" stroke-width="1.2">
<circle cx="180" cy="230" r="55"/>
<rect x="{x0}" y="{top}" width="{x1-x0}" height="{height}"/>
<path d="M110,230 H250 M180,160 V300 M410,230 H1020" stroke-dasharray="10,4,2,4"/>
<path d="M{x0},{bottom+8} V375 M{x1},{bottom+8} V375"/>
<path d="M{x0},360 H{x1}" marker-start="url(#shaft-arrow)" marker-end="url(#shaft-arrow)"/>
<path d="M110,175 H180 M110,285 H180"/>
<path d="M120,175 V285" marker-start="url(#shaft-arrow)" marker-end="url(#shaft-arrow)"/>
</g>'''+f'''<g fill="#111" font-size="16"><text x="112" y="130">END VIEW</text><text x="620" y="130">SIDE VIEW / SILHOUETTE</text>
<text x="125" y="323">D8 h6</text><text x="85" y="347">7.991 - 8.000 mm</text>
<text x="{(x0+x1)/2}" y="345" text-anchor="middle">L {length:g} +/-{tolerance} mm</text></g>'''
