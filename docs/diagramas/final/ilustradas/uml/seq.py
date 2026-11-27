from svglib import *
X={'P':42,'I':185,'S':300,'T':415,'O':530,'E':645,'J':760,'DB':862}
NOMES={'I':["Interface"],'S':["Servidor e","serviço"],'T':["Tema e","busca BNCC"],'O':["Orquestrador","da geração"],'E':["Especialistas","(Gemini)"],'J':["IA Juiz","(Groq)"],'DB':["SQLite"]}
msgs=[]  # (tipo, de, para, texto)
def m(a,b,t,r=False): msgs.append(('m',a,b,t,r))
def frag(kind,label,start=True): msgs.append(('f',kind,label,start))
m('P','I',"Informar contexto"); m('I','S',"POST /consultas"); m('S','T',["Extrair tema e","buscar habilidades"])
m('T','S',["Candidatas","e fonte"],True); m('S','DB',"Registrar consulta"); m('S','I',"Tema e candidatas",True)
m('P','I',"Confirmar habilidade"); m('I','S',"POST /confirmar"); m('S','DB',"Gravar confirmação")
m('P','I',"Gerar plano"); m('I','S',"POST /gerar"); m('S','DB',"Criar pedido"); m('S','O',"Gerar plano")
frag('loop','loop',True); m('O','E',["Próxima etapa com as","saídas anteriores"]); m('E','O',"Saída em JSON",True); m('O','O',"Validar a saída"); frag('loop','',False)
m('O','O',["Integrar 11 seções","e validar contrato"]); m('O','S',"Plano válido (rascunho)",True)
m('S','J',"Avaliar plano (rubrica de 6 critérios)"); m('J','S',"Parecer e decisão da política",True)
frag('opt','opt',True); m('S','O',["Gerar de novo com a versão","anterior e as críticas"]); m('O','S',"Nova versão",True); m('S','J',"Avaliar a nova versão"); m('J','S',"Novo parecer",True); frag('opt','',False)
m('S','DB',"Gravar versões, pareceres e versão entregue"); m('S','I',"Plano e parecer",True)
m('P','I',"Aprovar plano"); m('I','S',"POST /aprovar"); m('S','DB','Estado "aprovado"'); m('P','I',"Baixar PDF")
# altura
y=96; pos=[]
for it in msgs:
    if it[0]=='f': y+= 40 if it[3] else 12; pos.append(y); continue
    n=2 if isinstance(it[3],list) else 1
    y+= 14+17*n+ (16 if it[1]==it[2] else 0); pos.append(y)
H=y+40; s=S(900,H)
def head(k,y):
    x=X[k]
    if k=='P':
        s.add(f'<circle cx="{x}" cy="{y+12}" r="9" fill="#fff" stroke="{INK}" stroke-width="1.5"/><path d="M{x},{y+21} v18 M{x-13},{y+27} h26 M{x},{y+39} l-10,14 M{x},{y+39} l10,14" stroke="{INK}" stroke-width="1.5" fill="none"/>')
        s.text(x,y+66,"Professor",size=14,weight=600)
    else:
        w=102 if k!='DB' else 70
        s.rect(x-w/2,y,w,48,rx=3,fill="#f8fafc",stroke=INK); s.text(x,y+24,NOMES[k],size=14,weight=600)
for k in X: head(k,10)
for k,x in X.items(): s.line([(x,80 if k=='P' else 58),(x,H-20)],head=None,dash="5 4",color="#94a3b8",sw=1.1)
fr=[]
for it,yy in zip(msgs,pos):
    if it[0]=='f':
        if it[3]: fr.append((it[1],yy-12))
        else:
            kind,y0=fr.pop(); x0,x1=(X['O']-60,X['E']+70) if kind=='loop' else (X['S']-50,X['J']+60)
            s.rect(x0,y0,x1-x0,yy-y0,fill="none",stroke="#475569",sw=1.2)
            lab='loop' if kind=='loop' else 'opt'; g='[6 chamadas encadeadas]' if kind=='loop' else '[parecer não favorável, até 1 vez]'
            s.add(f'<path d="M{x0},{y0} h44 v12 l-8,8 h-36 z" fill="#fff" stroke="#475569" stroke-width="1.2"/>')
            s.text(x0+6,y0+10,lab,size=13,anchor="start",weight=600)
            s.text(x0+52,y0+11,g,size=13,anchor="start",fill="#334155",style="italic")
        continue
    _,a,b,t,r=it; xa,xb=X[a],X[b]
    lines=t if isinstance(t,list) else [t]
    if a==b:
        s.line([(xa,yy-12),(xa+34,yy-12),(xa+34,yy+4),(xa+2,yy+4)],head="filled")
        s.text(xa+42,yy-4,lines,size=14,anchor="start",halo=True); continue
    s.line([(xa,yy),(xb,yy)],dash="6 4" if r else None,head="open" if r else "filled",sw=1.3)
    cx=(xa+xb)/2; s.text(cx,yy-5-len(lines)*17.08/2,lines,size=14,halo=True)
open("sequencia-uml.svg","w").write(s.svg()); print(H)
