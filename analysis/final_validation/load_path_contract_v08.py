"""Explicit, right-handed machine-coordinate load resultants, no pressure/force inference from current."""
import math

def station_loads(st,shaft,torque,share,direction,slack,cut_index,centre_distance_mm=90.,root_radius_mm=18.,pitch_mm=9.525):
    if shaft not in ('153','105') or direction not in (-1,1): raise ValueError('shaft/direction')
    if not all(math.isfinite(float(v)) for v in (torque,share,slack,centre_distance_mm,root_radius_mm,pitch_mm)):raise ValueError('nonfinite')
    if not (0<=share<=1 and torque>=0 and slack>=0 and root_radius_mm>0 and centre_distance_mm>0):raise ValueError('bounds')
    large=pitch_mm/(2*math.sin(math.pi/30))/1000
    small=pitch_mm/(2*math.sin(math.pi/12))/1000
    beta=math.asin((large-small)/(centre_distance_mm/1000))
    phase=torque*share;ft=phase/.024;fr=ft*math.tan(math.radians(20))
    rows=[]
    def add(y,fx,fz,t,label):rows.append({'y_mm':y,'fx_n':fx,'fz_n':fz,'torque_nm':t,'source':label})
    if shaft=='153':
        delta=torque/large
        add(st['chain_sprocket_y_mm'],direction*delta*math.sin(beta),(delta+2*slack)*math.cos(beta),direction*torque,'chain exact open-span tangents toward motor +Z')
        add(st['gear_y_mm'],fr,-direction*ft,-direction*phase,'master phase gear: outward separation +X, resisting torque')
        local=torque-phase;cut_t=-direction*local
    else:
        add(st['gear_y_mm'],-fr,direction*ft,-direction*phase,'slave phase gear: reaction opposite master, counterrotating input')
        local=phase;cut_t=direction*local
    add(st['cutter_y_mm'][cut_index],0,-direction*local/(root_radius_mm/1000),cut_t,'inner-side hook tangent; additional wedge normal unqualified')
    if abs(sum(r['torque_nm'] for r in rows))>1e-8:raise ValueError('unbalanced torque')
    return rows

def support_reactions(loads,a,b):
    if not math.isfinite(a+b) or a>=b:raise ValueError('support order')
    components=[]
    for key in ('fx_n','fz_n'):
        rb=-sum(r[key]*(r['y_mm']-a)/(b-a) for r in loads)
        ra=-sum(r[key] for r in loads)-rb
        components.append((ra,rb))
    return {'front_fx_n':components[0][0],'front_fz_n':components[1][0],'rear_fx_n':components[0][1],'rear_fz_n':components[1][1], 'max_bearing_n':max(math.hypot(components[0][i],components[1][i]) for i in (0,1))}
