#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

EPSILON = 1e-6
NONE = -99

TET, HEX, PRI, PYR = 1, 0, 2, 3

TETVNUM = [[0, 1, 2, -1], [0, 1, 3, -1], [1, 2, 3, -1], [0, 2, 3, -1]]
PRIVNUM = [[0, 1, 2, 3], [0, 1, 4, -1], [1, 2, 5, 4], [3, 2, 5, -1], [0, 3, 5, 4]]
PYRVNUM = [[0, 1, 2, 3], [0, 1, 4, -1], [1, 2, 4, -1], [3, 2, 4, -1], [0, 3, 4, -1]]
HEXVNUM = [[0, 1, 2, 3], [0, 1, 5, 4], [1, 2, 6, 5], [3, 2, 6, 7], [0, 3, 7, 4], [4, 5, 6, 7]]


@dataclass
class Vertex:
    x: float
    y: float
    z: float
    elmts_vertisin: set = field(default_factory=set)


@dataclass
class Element:
    etype: int
    vert_ids: List[int]
    conn_element: List[int]
    conn_face: List[int]

    def nverts(self) -> int:
        return len(self.vert_ids)

    def face_ids(self, fid: int) -> Tuple[int, int, int, int]:
        if self.etype == HEX:
            ids = HEXVNUM[fid]
        elif self.etype == TET:
            ids = TETVNUM[fid]
        elif self.etype == PRI:
            ids = PRIVNUM[fid]
        else:
            ids = PYRVNUM[fid]
        vals = [self.vert_ids[i] for i in ids if i >= 0]
        while len(vals) < 4:
            vals.append(NONE)
        return tuple(vals)

    def find_match_face(self, v0: int, v1: int, v2: int, v3: int) -> int:
        fn = 6 if self.etype == HEX else (4 if self.etype == TET else 5)
        for fid in range(fn):
            f = self.face_ids(fid)
            ss = {f[0], f[1], f[2]} if f[3] < 0 else {f[0], f[1], f[2], f[3]}
            tt = {v0, v1, v2} if v3 < 0 else {v0, v1, v2, v3}
            if ss == tt:
                return fid
        return NONE


@dataclass
class Boundary:
    name: str
    curved: int = 0
    curve_type: str = "a"
    btype: str = "W"
    lines: List[str] = field(default_factory=list)
    inline_params: str = "0. 0. 0.\n"
    bfaces: List[Tuple[int, int, int, int]] = field(default_factory=list)


@dataclass
class Mesh:
    vertices: List[Vertex] = field(default_factory=list)
    elements: List[Element] = field(default_factory=list)
    groups: List[int] = field(default_factory=list)
    boundaries: List[Boundary] = field(default_factory=list)

    def determinant(self, v0: int, v1: int, v2: int, v3: int) -> float:
        a = self.vertices[v1]; b = self.vertices[v2]; c = self.vertices[v3]; o = self.vertices[v0]
        ax, ay, az = a.x - o.x, a.y - o.y, a.z - o.z
        bx, by, bz = b.x - o.x, b.y - o.y, b.z - o.z
        cx, cy, cz = c.x - o.x, c.y - o.y, c.z - o.z
        dx, dy, dz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
        return cx * dx + cy * dy + cz * dz

    def orient_elements(self) -> None:
        for e in self.elements:
            vv = e.vert_ids
            if e.etype == HEX:
                if self.determinant(vv[0], vv[1], vv[3], vv[4]) < 0:
                    e.vert_ids = [vv[4], vv[5], vv[6], vv[7], vv[0], vv[1], vv[2], vv[3]]
            elif e.etype == TET:
                s = sorted(vv, reverse=True)
                v0, v1, v2, v3 = s[0], s[1], s[2], s[3]
                if self.determinant(v3, v2, v1, v0) < 0:
                    e.vert_ids = [v2, v3, v1, v0]
                else:
                    e.vert_ids = [v3, v2, v1, v0]

    def build_vertex_to_elements(self) -> None:
        for v in self.vertices:
            v.elmts_vertisin.clear()
        for ei, e in enumerate(self.elements):
            for vid in e.vert_ids:
                self.vertices[vid].elmts_vertisin.add(ei)

    def find_match_element_face(self, eid_: int, v0: int, v1: int, v2: int, v3: int) -> Tuple[int, int]:
        e = NONE
        for eid in sorted(self.vertices[v0].elmts_vertisin):
            if eid == eid_:
                continue
            cnt = 1
            if eid in self.vertices[v1].elmts_vertisin:
                cnt += 1
            if eid in self.vertices[v2].elmts_vertisin:
                cnt += 1
            if v3 >= 0 and eid in self.vertices[v3].elmts_vertisin:
                cnt += 1
            if (v3 >= 0 and cnt == 4) or (v3 < 0 and cnt == 3):
                e = eid
        if e == NONE:
            return NONE, NONE
        return e, self.elements[e].find_match_face(v0, v1, v2, v3)

    def connect(self) -> None:
        self.build_vertex_to_elements()
        for eid, e in enumerate(self.elements):
            nf = len(e.conn_element)
            for fid in range(nf):
                v0, v1, v2, v3 = e.face_ids(fid)
                ee, ff = self.find_match_element_face(eid, v0, v1, v2, v3)
                e.conn_element[fid] = ee
                e.conn_face[fid] = ff

    def set_boundary_conditions(self) -> None:
        for bid, bc in enumerate(self.boundaries):
            for v0, v1, v2, v3 in bc.bfaces:
                ee, ff = self.find_match_element_face(NONE, v0, v1, v2, v3)
                self.elements[ee].conn_element[ff] = -(bid + 1)
                self.elements[ee].conn_face[ff] = -(bid + 1)


def _find(lines: List[str], key: str, start: int = 0) -> int:
    for i in range(start, len(lines)):
        if key in lines[i]:
            return i
    return -1


def parse_grd(path: Path, scale=(1.0, 1.0, 1.0)) -> Mesh:
    lines = path.read_text().splitlines()
    mesh = Mesh()

    i = _find(lines, "Boundary Table")
    nbc = int(lines[i + 1].split()[0])
    for k in range(nbc):
        mesh.boundaries.append(Boundary(lines[i + 2 + k].rstrip("\n") + "\n"))

    i = _find(lines, "Nodes")
    npt = int(lines[i + 1].split()[0])
    for k in range(npt):
        x, y, z = map(float, lines[i + 2 + k].split()[:3])
        mesh.vertices.append(Vertex(scale[0] * x, scale[1] * y, scale[2] * z))

    i = _find(lines, "Elements") + 1
    while i < len(lines) and "Variables" not in lines[i]:
        t = lines[i].split()
        if len(t) >= 11:
            ntyp = int(t[0]); part_id = int(t[2]); ids = [int(x) - 1 for x in t[3:11]]
            if ntyp == 1:
                e = Element(TET, ids[:4], [NONE] * 4, [NONE] * 4)
            elif ntyp == 2:
                e = Element(HEX, [ids[0], ids[1], ids[3], ids[2], ids[4], ids[5], ids[7], ids[6]], [NONE] * 6, [NONE] * 6)
            elif ntyp == 3:
                e = Element(PRI, [ids[0], ids[3], ids[5], ids[1], ids[2], ids[4]], [NONE] * 5, [NONE] * 5)
            else:
                e = Element(PYR, ids[:5], [NONE] * 5, [NONE] * 5)
            mesh.elements.append(e)
            mesh.groups.append(part_id)
        i += 1

    i = _find(lines, "Boundary Faces")
    nbf = int(lines[i + 1].split()[0])
    for k in range(nbf):
        t = lines[i + 2 + k].split()
        bc_type, vnum = int(t[0]), int(t[1])
        vids = [int(x) - 1 for x in t[2:6]]
        if vnum == 3:
            vids[3] = NONE
        mesh.boundaries[bc_type - 1].bfaces.append(tuple(vids))

    return mesh


def parse_info(path: Path, boundaries: List[Boundary]) -> None:
    lines = path.read_text().splitlines(keepends=True)
    for bc in boundaries:
        idx = _find(lines, bc.name.strip())
        inl = int(lines[idx + 1].split()[0])
        bc.curved = 1 if inl == 1 else 0
        bc.curve_type = lines[idx + 2][0]
        bc.btype = lines[idx + 3][0]
        nlines = int(lines[idx + 4].split()[0])
        bc.lines = [lines[idx + 5 + j] for j in range(max(0, nlines))]
        look = idx + 5 + max(0, nlines)
        if look < len(lines) and "INLINE" in lines[look]:
            bc.inline_params = lines[look + 1]
        else:
            bc.inline_params = "0. 0. 0.\n"
