from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent/'raw/pages'
for stem in ('drawing','guide'):
    paths=sorted(H.glob(stem+'-*.png'))
    if not paths:raise ValueError('missing renders')
    for batch in range(0,len(paths),12):
        image=Image.new('RGB',(1600,1200),'white');draw=ImageDraw.Draw(image)
        for i,p in enumerate(paths[batch:batch+12]):
            thumb=Image.open(p);thumb.thumbnail((390,350))
            x=(i%4)*400;y=(i//4)*400
            image.paste(thumb,(x,y+25));draw.text((x+10,y+5),p.name,fill='black')
        image.save(H/(stem+'_contact_'+str(batch//12)+'.png'))
print('CONTACT_SHEETS_READY')
