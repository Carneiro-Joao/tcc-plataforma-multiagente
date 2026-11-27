from svglib import *
H=1352; s=S(900,H)
LANE=300
# swimlanes
s.rect(2,2,896,H-4,fill="none",stroke="#475569",sw=1.4)
s.line([(LANE,2),(LANE,H-2)],head=None,color="#475569",sw=1.2)
s.line([(2,36),(898,36)],head=None,color="#475569",sw=1.2)
s.text(LANE/2,19,"Professor",size=16,weight=600); s.text((LANE+900)/2,19,"AulaIA",size=16,weight=600)
def act(x,y,lines,w=220,h=44):
    s.rect(x-w/2,y-h/2,w,h,rx=16,fill="#fff",stroke=INK,sw=1.5); s.text(x,y,lines,size=15)
def dec(x,y,r=20,label=None,side="right"):
    s.add(f'<polygon points="{x},{y-r} {x+r},{y} {x},{y+r} {x-r},{y}" fill="#fff" stroke="{INK}" stroke-width="1.5"/>')
    if label:
        if side=="right": s.text(x+r+6,y-r+2,label,size=13,anchor="start",fill=MUTED,style="italic")
        else: s.text(x-r-6,y-r+2,label,size=13,anchor="end",fill=MUTED,style="italic")
def ini(x,y): s.add(f'<circle cx="{x}" cy="{y}" r="10" fill="{INK}"/>')
def fim(x,y): s.add(f'<circle cx="{x}" cy="{y}" r="12" fill="#fff" stroke="{INK}" stroke-width="1.5"/><circle cx="{x}" cy="{y}" r="7" fill="{INK}"/>')
def g(x,y,t,anchor="start"): s.text(x,y,t,size=13,anchor=anchor,fill="#334155")
A=lambda pts: s.line(pts,head="open",sw=1.4)
P=150; M=500; R=740
ini(P,62); A([(P,72),(P,90)]); dec(P,102,12)
A([(P,114),(P,128)]); act(P,150,"Informar o contexto da aula",w=250)
A([(275,150),(478,150)]); dec(M,150,label="contexto válido?")
A([(M,130),(M,102),(162,102)]); g(M-8,118,"[não]",anchor="end")
A([(M,170),(M,203)]); g(M+8,188,"[sim]")
act(M,225,["Extrair o tema e","buscar habilidades"],w=230,h=52)
A([(385,225),(P,225),(P,270)]); act(P,298,["Escolher e confirmar","a habilidade"],w=230,h=56)
A([(265,298),(M,298),(M,358)]); dec(M,370,12)
A([(M,382),(M,402)]); act(M,437,["Gerar o plano: 5 agentes em","6 chamadas, com verificação","a cada etapa"],w=250,h=70)
A([(M,472),(M,498)]); dec(M,520,label="geração concluída?",side="left")
A([(M+20,520),(R-100,520)]); g(M+28,510,"[não]"); act(R,520,"Registrar a falha e avisar",w=210)
A([(R,542),(R,566)]); fim(R,578)
A([(M,540),(M,588)]); g(M+8,560,"[sim]"); dec(M,600,12)
A([(M,612),(M,636)]); act(M,658,"IA Juiz avalia o plano",w=250)
A([(M,680),(M,708)]); dec(M,730,label="parecer?")
# favorável / indisponível -> left to M3
A([(M-20,730),(380,730),(380,1010),(488,1010)]); s.text(387,756,["[favorável ou","sem parecer]"],size=13,anchor="start",fill="#334155")
A([(M,750),(M,808)]); g(M+8,775,"[não favorável]")
dec(M,830); s.text(M+28,800,"há ciclo?",size=13,anchor="start",fill=MUTED,style="italic")
A([(M+20,830),(R-115,830)]); g(M+28,846,"[sim]")
act(R,830,["Regenerar o plano com","as críticas da IA Juiz"],w=230,h=56)
A([(R,858),(R,893)]); dec(R,915,label="nova versão gerada?",side="left")
A([(R+20,915),(870,915),(870,600),(512,600)]); g(R+26,905,"[sim]")
A([(R,935),(R,1010),(512,1010)]); g(R+8,965,"[não]")
A([(M,850),(M,998)]); g(M+8,875,"[não]")
dec(M,1010,12)
A([(M,1022),(M,1046)]); act(M,1068,"Entregar o plano",w=200)
# note
nx,ny,nw,nh=640,1040,250,96
s.add(f'<path d="M{nx},{ny} h{nw-14} l14,14 v{nh-14} h-{nw} z" fill="#fffbeb" stroke="#92400e" stroke-width="1.1"/>')
s.text(nx+10,ny+nh/2,["Versão entregue (RN12): a com","parecer favorável; sem parecer,","se a avaliação falhar; ou a com","menos falhas graves, com aviso"],size=12.5,anchor="start",fill="#78350f")
s.line([(600,1068),(nx,1068)],head=None,sw=1,color="#92400e") ; 
A([(400,1068),(P,1068),(P,1110)]); act(P,1132,["Revisar o plano","e o parecer"],w=220,h=52)
A([(P,1158),(P,1186)]); dec(P,1206,label="aprova?",side="left")
A([(P,1226),(P,1250)]); g(P+8,1240,"[sim]"); act(P,1272,"Aprovar e baixar o PDF",w=230)
A([(P,1294),(P,1316)]); fim(P,1328)
A([(P-115,1272),(28,1272),(28,1300)]) if False else None
A([(P+20,1206),(M-125,1206)]); g(P+60,1196,"[não]")
act(M,1206,["Gerar novamente: novo","pedido, do zero"],w=250,h=52)
A([(M+125,1206),(890,1206),(890,370),(512,370)])
open("atividades_uml.svg","w").write(s.svg())
