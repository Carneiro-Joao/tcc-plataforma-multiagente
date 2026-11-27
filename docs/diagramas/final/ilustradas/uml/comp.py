from svglib import *
s=S(900,900)
def icon(x,y):
    s.rect(x,y,14,18,fill="#fff",sw=1.1); s.rect(x-4,y+3,8,4,fill="#fff",sw=1.1); s.rect(x-4,y+11,8,4,fill="#fff",sw=1.1)
def comp(x,y,w,h,name,st="«component»",fill="#fff",stroke=INK):
    s.rect(x,y,w,h,rx=2,fill=fill,stroke=stroke); icon(x+w-22,y+6)
    lines=[(st,{'sz':12.5,'w':400})]+[(n,{'w':500}) for n in (name if isinstance(name,list) else [name])]
    s.text(x+w/2-6,y+h/2,lines,size=16)
def frame(x,y,w,h,label,dash="6 4",stroke=MUTED,rx=8,bold=False):
    s.rect(x,y,w,h,rx=rx,fill="none",stroke=stroke,sw=1.2,dash=dash)
    s.text(x+10,y+16,label,size=13.5,anchor="start",fill="#334155",weight=600 if bold else 500)
D="5 4"
# subsystem frame
s.rect(10,92,880,688,rx=10,fill="none",stroke="#475569",sw=1.5); s.text(22,112,"«subsystem» Backend do AulaIA (Python)",size=14,anchor="start",weight=600,fill="#334155")
comp(360,8,200,62,["Interface web","(React + Vite)"])
comp(360,128,200,56,"Servidor HTTP"); comp(360,215,200,56,"Serviço de aplicação")
# lollipop
s.line([(460,128),(460,118)],head=None); s.add('<circle cx="460" cy="110" r="8" fill="#fff" stroke="#1f2937" stroke-width="1.4"/>')
s.text(476,110,"HTTP/JSON",size=13,anchor="start")
s.line([(460,70),(460,101)],dash=D)
# SQLite cylinder
x,y,w,h=150,205,150,72
s.add(f'<path d="M{x},{y+10} v{h-20} a{w/2},10 0 0 0 {w},0 v-{h-20}" fill="#fff" stroke="#1f2937" stroke-width="1.4"/><ellipse cx="{x+w/2}" cy="{y+10}" rx="{w/2}" ry="10" fill="#fff" stroke="#1f2937" stroke-width="1.4"/>')
s.text(x+w/2,y+42,[("«database»",{'sz':12.5}),("SQLite",{'w':500})],size=16)
s.line([(360,243),(300,243)],dash=D)
s.line([(360,166),(330,166)],head=None) if False else None
s.line([(460,184),(460,215)],dash=D)
# Consulta curricular
frame(20,300,195,380,"Consulta curricular")
comp(32,335,172,56,["Extração de tema"]); comp(32,420,172,56,["Busca curricular"])
# artifact note
x,y,w,h=45,520,148,74
s.add(f'<path d="M{x},{y} h{w-14} l14,14 v{h-14} h-{w} z" fill="#fff" stroke="#1f2937" stroke-width="1.4"/><path d="M{x+w-14},{y} v14 h14" fill="none" stroke="#1f2937" stroke-width="1.2"/>')
s.text(x+w/2,y+h/2,[("«artifact»",{'sz':12.5}),("Catálogo BNCC",{'w':500}),("8º ano (JSON)",{'sz':14})],size=16)
s.line([(118,476),(118,520)],dash=D)
s.line([(380,271),(380,288),(117,288),(117,300)],dash=D)
# Geração
frame(230,300,445,465,"Geração do plano")
comp(245,330,180,56,"Revisão informada"); comp(450,330,205,64,["Orquestrador","da geração"])
s.line([(425,358),(450,358)],dash=D)
s.line([(400,271),(400,330)],dash=D)
s.line([(520,271),(520,330)],dash=D)
# agentes
x,y,w,h=245,420,230,245
s.rect(x,y,w,h,rx=2,fill="#f0fdfa",stroke="#0f766e"); icon(x+w-22,y+6)
s.text(x+w/2-8,y+30,[("«component»",{'sz':12.5}),("Agentes especialistas",{'w':600}),("6 chamadas, nesta ordem:",{'sz':13.5,'fill':MUTED})],size=16)
for i,a in enumerate(["Objetivos","Avaliação (preliminar)","Metodologia e Recursos","Sequência Didática","Avaliação (final)","Adaptação"]):
    s.text(x+16,y+92+i*25,f"{i+1}. {a}",size=15,anchor="start")
s.line([(470,394),(470,407),(360,407),(360,420)],dash=D)
comp(495,420,160,62,["Verificação","de acentuação"]); comp(495,505,160,56,"Integrador"); comp(495,590,160,56,"Validador")
s.line([(575,394),(575,420)],dash=D)
s.line([(655,372),(666,372),(666,533),(655,533)],dash=D)
s.line([(666,533),(666,618),(655,618)],dash=D)
s.line([(575,561),(575,590)],dash=D)
comp(255,695,210,56,"Adaptador Gemini")
s.line([(360,665),(360,695)],dash=D)
# Avaliação
frame(690,300,190,300,"Avaliação do plano")
comp(702,330,160,56,"IA Juiz"); comp(702,415,160,62,["Política","de decisão"]); comp(702,505,160,56,"Adaptador Groq")
s.line([(560,243),(845,243),(845,330)],dash=D)
s.line([(782,386),(782,415)],dash=D)
s.line([(862,358),(874,358),(874,533),(862,533)],dash=D)
# externos
def ext(x,y,w,h,lines):
    s.rect(x,y,w,h,rx=2,fill="#f8fafc",stroke="#475569",dash="4 3")
    s.text(x+w/2,y+h/2,[("«sistema externo»",{'sz':12.5})]+[(l,{'w':500}) if i==0 else (l,{'sz':13.5}) for i,l in enumerate(lines)],size=16)
ext(240,805,240,72,["API do Gemini","gemini-3.5-flash-lite"]); ext(690,805,190,72,["API da Groq","gpt-oss-120b"])
s.line([(360,751),(360,805)],dash=D); s.text(372,792,"HTTPS",size=12.5,anchor="start",fill=MUTED)
s.line([(782,561),(782,805)],dash=D); s.text(794,792,"HTTPS",size=12.5,anchor="start",fill=MUTED)
open("componentes-uml.svg","w").write(s.svg())
