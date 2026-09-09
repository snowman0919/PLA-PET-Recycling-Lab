"""Sheet guards with explicit mounting; no hardware approval is implied."""
import FreeCAD as App
import Part

def finish_guards(items):
    by_name={row['name']:row for row in items}
    for label,xc,zc,y0,length,ro,ri,flange_y,mount_y in (
            ('SH',153,676.167,186,57,27,25,186,180),
            ('EX',320,382,413,58,25,24,469,471)):
        direction=App.Vector(0,1,0)
        shell=Part.makeCylinder(ro,length,App.Vector(xc,y0,zc),direction)
        shell=shell.cut(Part.makeCylinder(ri,length,App.Vector(xc,y0,zc),direction))
        flange=Part.makeCylinder(38,2,App.Vector(xc,flange_y,zc),direction)
        flange=flange.cut(Part.makeCylinder(ri,2,App.Vector(xc,flange_y,zc),direction))
        cover=shell.fuse(flange)
        mount=by_name['GGM_'+label+'_Mount']
        for dx in (-29,29) if label=='SH' else (-18,18):
            for dz in (-18,18) if label=='SH' else (-29,29):
                cover=cover.cut(Part.makeCylinder(1.7,2,App.Vector(xc+dx,flange_y,zc+dz),direction))
                mount['shape']=mount['shape'].cut(Part.makeCylinder(1.25,6,App.Vector(xc+dx,mount_y,zc+dz),direction))
        cover=cover.cut(Part.makeBox(90,length+4,1,App.Vector(xc-45,y0-1,zc-.5)))
        row=by_name['GGM_'+label+'_CouplingGuard']
        row['shape']=cover.removeSplitter()
        row['material']='split metal cover: 2 formed halves, OD76x2 front flange, fourM3 mounts, 1mm seam'
    guard=by_name['GGM_ChainGuard']; plate=by_name['GGM_SH_BearingPlate273']
    for x in (100,186):
        tab=Part.makeBox(20,10,2,App.Vector(x,241,640))
        tab=tab.fuse(Part.makeBox(20,2,20,App.Vector(x,241,642)))
        tab=tab.cut(Part.makeCylinder(1.7,2,App.Vector(x+10,241,654),App.Vector(0,1,0)))
        guard['shape']=guard['shape'].fuse(tab).removeSplitter()
        plate['shape']=plate['shape'].cut(Part.makeCylinder(1.25,10,App.Vector(x+10,243,654),App.Vector(0,1,0)))
    guard['material']='1mm folded steel plus2x20x20 mounting tabs; twoM3 to front bearing plate; interlock required'
