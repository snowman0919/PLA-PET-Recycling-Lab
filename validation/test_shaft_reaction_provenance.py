"""입력 토크를 solver 반력으로 재사용하지 않는다."""
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis/final_validation'))
from run_calculix_v08 import printed_reactions

with tempfile.TemporaryDirectory() as folder:
    dat = Path(folder)/'model.dat'
    dat.write_text('forces (fx,fy,fz) for set REACTION\n1 0 0 10\n2 0 0 -10\ntotal force\n')
    result = printed_reactions(dat,{1:(0,0,0),2:(.1,0,0)})
    assert result['force_n']==[0,0,0]
    assert result['moment_about_origin_nm']==[0,1,0]
    assert result['torsional_reaction_qualified'] is False
    dat.write_text('no results')
    try:
        printed_reactions(dat,{})
    except ValueError:
        pass
    else:
        raise AssertionError('missing reactions accepted')
print('SHAFT_REACTION_PROVENANCE_PASS')
