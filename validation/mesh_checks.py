#!/usr/bin/env python3
"""Check exported printable STL meshes for watertight two-manifold topology."""

from __future__ import annotations

import json
import math
import struct
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def triangles(path):
    data=path.read_bytes()
    if len(data)>=84:
        count=struct.unpack_from("<I",data,80)[0]
        if 84+50*count==len(data):
            for i in range(count):
                values=struct.unpack_from("<12fH",data,84+50*i)
                yield (values[3:6],values[6:9],values[9:12])
            return
    vertices=[]
    for line in data.decode("ascii",errors="ignore").splitlines():
        fields=line.strip().split()
        if fields[:1]==["vertex"]: vertices.append(tuple(map(float,fields[1:4])))
        if len(vertices)==3:
            yield tuple(vertices); vertices=[]


def key(v): return tuple(round(x,5) for x in v)


def audit(path):
    tris=list(triangles(path)); edges=Counter(); adjacency=defaultdict(set); zero=0
    for index,tri in enumerate(tris):
        a,b,c=tri
        cross=((b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]),(b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]),(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
        if math.sqrt(sum(x*x for x in cross))/2 <= 1e-10: zero+=1
        for u,v in ((a,b),(b,c),(c,a)):
            e=tuple(sorted((key(u),key(v)))); edges[e]+=1; adjacency[e].add(index)
    nonmanifold=sum(1 for n in edges.values() if n!=2)
    graph=defaultdict(set)
    for faces in adjacency.values():
        if len(faces)==2:
            p,q=tuple(faces); graph[p].add(q); graph[q].add(p)
    seen=set(); components=0
    for start in range(len(tris)):
        if start in seen: continue
        components+=1; queue=deque([start]); seen.add(start)
        while queue:
            for nxt in graph[queue.popleft()]:
                if nxt not in seen: seen.add(nxt); queue.append(nxt)
    ok=bool(tris) and zero==0 and nonmanifold==0 and components==1
    return {"file":str(path.relative_to(ROOT)),"triangles":len(tris),"zero_area_triangles":zero,"nonmanifold_edges":nonmanifold,"connected_components":components,"status":"PASS" if ok else "FAIL"}


def main():
    rows=[audit(p) for p in sorted((ROOT/"exports/print").glob("PPR-C*/PPR-C*.stl"))]
    coupon=audit(ROOT/"exports/print/coupons/PPR-TC01/PPR-TC01.stl")
    result={"revision":"coupled-digital-validation-v0.5","mesh_count":len(rows),"meshes":rows,"tolerance_coupon":coupon,"status":"PASS" if len(rows)==12 and all(r["status"]=="PASS" for r in rows) and coupon["status"]=="PASS" else "FAIL"}
    out=ROOT/"validation/results"; out.mkdir(parents=True,exist_ok=True)
    (out/"mesh_manifold.json").write_text(json.dumps(result,indent=2)+"\n")
    if result["status"]!="PASS": raise SystemExit("MESH_WATERTIGHT_MANIFOLD_FAIL")
    print("MESH_WATERTIGHT_MANIFOLD_OK meshes=12 coupon=1")


if __name__=="__main__": main()
