import math
F="Inter, 'DejaVu Sans', sans-serif"
INK="#1f2937"; MUTED="#64748b"
class S:
    def __init__(s,w,h): s.w,s.h,s.o=w,h,[]
    def add(s,x): s.o.append(x)
    def text(s,x,y,lines,size=16,anchor="middle",weight=400,fill=INK,style="normal",halo=False):
        if isinstance(lines,str): lines=[lines]
        lh=size*1.22; y0=y-(len(lines)-1)*lh/2
        for i,l in enumerate(lines):
            w=weight; st=style; sz=size
            if isinstance(l,tuple): l,opt=l; w=opt.get('w',w); st=opt.get('st',st); sz=opt.get('sz',sz)
            hl=' stroke="#fff" stroke-width="5" paint-order="stroke" stroke-linejoin="round"' if halo else ''
            l=l.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            s.add(f'<text x="{x}" y="{y0+i*lh+sz*0.35:.1f}" font-family="{F}" font-size="{sz}" font-weight="{w}" font-style="{st}" text-anchor="{anchor}" fill="{fill}"{hl}>{l}</text>')
    def rect(s,x,y,w,h,rx=0,fill="#fff",stroke=INK,sw=1.4,dash=None):
        d=f' stroke-dasharray="{dash}"' if dash else ''
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')
    def line(s,pts,dash=None,head="open",sw=1.3,color=INK):
        d=f' stroke-dasharray="{dash}"' if dash else ''
        p=" ".join(f"{a},{b}" for a,b in pts)
        s.add(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{sw}"{d}/>')
        if head:
            (x1,y1),(x2,y2)=pts[-2],pts[-1]; a=math.atan2(y2-y1,x2-x1); L=11; W=0.42
            p1=(x2-L*math.cos(a-W),y2-L*math.sin(a-W)); p2=(x2-L*math.cos(a+W),y2-L*math.sin(a+W))
            if head=="open": s.add(f'<polyline points="{p1[0]:.1f},{p1[1]:.1f} {x2},{y2} {p2[0]:.1f},{p2[1]:.1f}" fill="none" stroke="{color}" stroke-width="{sw}"/>')
            else: s.add(f'<polygon points="{p1[0]:.1f},{p1[1]:.1f} {x2},{y2} {p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/>')
    def svg(s):
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{s.w}" height="{s.h}" viewBox="0 0 {s.w} {s.h}"><rect width="100%" height="100%" fill="#fff"/>'+"".join(s.o)+'</svg>'
