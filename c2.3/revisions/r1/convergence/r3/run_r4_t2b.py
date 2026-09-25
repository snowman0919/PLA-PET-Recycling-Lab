"""R4-T2b: chain suspended via end posts (FixedJoint), NO pin,
gravity + preload force, guide walls at crown level (span covers
the chain) blocking X drift. Sustained contact via gravity+preload.
Per reviewer approval: diagnostic fixture ONLY; no PPR design change;
no thresholds changed. Per-physics-step contact stream via
subscribe_contact_report_events. Signed shaft load and boundary work
per R2/R3 (no R*sum|F|).
"""
import os, json, sys
os.environ['OMNI_KIT_ACCEPT_EULA'] = 'YES'
DT = float(sys.argv[1]) if len(sys.argv) > 1 else 0.01
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/r4t2b_out.json'
NSTEPS = int(round(2.4 / DT))
F_PRESS_N = 2.0  # N, constant preload (reviewer: contact-hold only)

def mark(s):
    with open('/tmp/r4t2b_marks.txt', 'a') as fh:
        fh.write(s + '\n')

from isaacsim import SimulationApp
sim = SimulationApp({'headless': True})
mark('app')
acc = {'tauA': 0.0, 'tauB': 0.0, 'W': 0.0, 'n': 0}
try:
    import numpy as np, math
    import omni.timeline, omni.physx as px
    from pxr import PhysicsSchemaTools, UsdGeom, UsdPhysics, \
        PhysxSchema, Sdf, Gf
    from isaacsim.core.simulation_manager import SimulationManager
    import isaacsim.core.experimental.utils.stage as stage_utils
    from isaacsim.core.experimental.objects import GroundPlane
    from isaacsim.core.experimental.prims import RigidPrim
    stage_utils.create_new_stage()
    stage_utils.define_prim('/World', 'Xform')
    stage_utils.define_prim('/World/PhysicsScene', 'PhysicsScene')
    stage_utils.define_prim('/World/DIAGNOSTIC_FIXTURE', 'Xform')
    GroundPlane('/World/DIAGNOSTIC_FIXTURE/Ground')
    mark('stage')
    SHAFT_X, SHAFT_R, SHAFT_Z = 0.0, 0.04, 0.30
    sp = '/World/DIAGNOSTIC_FIXTURE/S1/ShaftA'
    stage_utils.define_prim(sp, 'Xform')
    cyl = stage_utils.define_prim(sp + '/Cyl', 'Cylinder')
    UsdGeom.Cylinder(cyl).GetRadiusAttr().Set(SHAFT_R)
    UsdGeom.Cylinder(cyl).GetHeightAttr().Set(0.12)
    UsdPhysics.CollisionAPI.Apply(cyl)
    rb = UsdPhysics.RigidBodyAPI.Apply(
        stage_utils.get_current_stage().GetPrimAtPath(Sdf.Path(sp)))
    rb.GetKinematicEnabledAttr().Set(True)
    bprim = stage_utils.get_current_stage().GetPrimAtPath(Sdf.Path(sp))
    cra = PhysxSchema.PhysxContactReportAPI.Apply(bprim)
    cra.CreateThresholdAttr().Set(0.0)
    shaft = RigidPrim([sp],
                      positions=np.array([[SHAFT_X, 0, SHAFT_Z]],
                                         dtype=np.float32),
                      orientations=np.array([[1, 0, 0, 0]],
                                            dtype=np.float32),
                      reset_xform_op_properties=True)
    mark('shaft')
    BOX = 0.04
    MASS = 0.25
    spec_y = [-BOX, 0.0, BOX]
    z_rest = SHAFT_Z + SHAFT_R + BOX / 2 - 0.005
    paths = []
    for i in range(3):
        fp = '/World/DIAGNOSTIC_FIXTURE/Spec/S%03d' % i
        xp = stage_utils.define_prim(fp, 'Xform')
        bx = stage_utils.define_prim(fp + '/B', 'Cube')
        UsdGeom.Cube(bx).GetSizeAttr().Set(BOX)
        UsdPhysics.RigidBodyAPI.Apply(xp)
        UsdPhysics.MassAPI.Apply(xp).GetMassAttr().Set(MASS)
        UsdPhysics.CollisionAPI.Apply(bx)
        bp2 = stage_utils.get_current_stage().GetPrimAtPath(
            Sdf.Path(fp))
        cra2 = PhysxSchema.PhysxContactReportAPI.Apply(bp2)
        cra2.CreateThresholdAttr().Set(0.0)
        paths.append(fp)
    bodies = RigidPrim(
        paths,
        positions=np.array([[SHAFT_X, spec_y[i], z_rest]
                            for i in range(3)], dtype=np.float32),
        orientations=np.tile(np.array([[1, 0, 0, 0]], dtype=np.float32),
                             (3, 1)),
        reset_xform_op_properties=True)
    mark('chain')
    stage_utils.define_prim('/World/DIAGNOSTIC_FIXTURE/Walls', 'Xform')
    for wi, wx in enumerate((-(BOX / 2 + 0.06), (BOX / 2 + 0.06))):
        wp = '/World/DIAGNOSTIC_FIXTURE/Walls/W%02d' % wi
        stage_utils.define_prim(wp, 'Xform')
        wbx = stage_utils.define_prim(wp + '/B', 'Cube')
        UsdGeom.Cube(wbx).GetSizeAttr().Set(0.02)
        arb2 = UsdPhysics.RigidBodyAPI.Apply(
            stage_utils.get_current_stage().GetPrimAtPath(
                Sdf.Path(wp)))
        arb2.GetKinematicEnabledAttr().Set(True)
        wall = RigidPrim([wp],
                         positions=np.array(
                             [[wx, 0.0, SHAFT_Z + 0.05]],
                             dtype=np.float32),
                         orientations=np.array([[1, 0, 0, 0]],
                                               dtype=np.float32),
                         reset_xform_op_properties=True)
    mark('walls')
    stage_utils.define_prim('/World/DIAGNOSTIC_FIXTURE/Anchor', 'Xform')
    for i, ay in ((0, spec_y[0]), (2, spec_y[2])):
        ap = '/World/DIAGNOSTIC_FIXTURE/Anchor/P%02d' % i
        stage_utils.define_prim(ap, 'Xform')
        arb = UsdPhysics.RigidBodyAPI.Apply(
            stage_utils.get_current_stage().GetPrimAtPath(
                Sdf.Path(ap)))
        arb.GetKinematicEnabledAttr().Set(True)
        anchor = RigidPrim([ap],
                           positions=np.array(
                               [[SHAFT_X, ay, z_rest + BOX]],
                               dtype=np.float32),
                           orientations=np.array([[1, 0, 0, 0]],
                                                 dtype=np.float32),
                           reset_xform_op_properties=True)
        jp = stage_utils.get_current_stage().DefinePrim(
            '/World/DIAGNOSTIC_FIXTURE/Anchor/JA%02d' % i,
            'PhysicsFixedJoint')
        jp.GetRelationship('physics:body0').SetTargets([ap])
        jp.GetRelationship('physics:body1').SetTargets([paths[i]])
        fj = UsdPhysics.FixedJoint(jp)
        fj.CreateLocalPos0Attr().Set(Gf.Vec3f(0.0, 0.0, -BOX / 2))
        fj.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, BOX / 2))
        fj.CreateLocalRot0Attr().Set(Gf.Quatf(1.0))
        fj.CreateLocalRot1Attr().Set(Gf.Quatf(1.0))
    mark('anchors')
    for i in range(2):
        jp = stage_utils.get_current_stage().DefinePrim(
            '/World/DIAGNOSTIC_FIXTURE/Spec/J%02d' % (i + 1),
            'PhysicsFixedJoint')
        jp.GetRelationship('physics:body0').SetTargets([paths[i]])
        jp.GetRelationship('physics:body1').SetTargets(
            [paths[i + 1]])
        fj = UsdPhysics.FixedJoint(jp)
        fj.CreateLocalPos0Attr().Set(Gf.Vec3f(0.0, BOX / 2, 0.0))
        fj.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, -BOX / 2, 0.0))
        fj.CreateLocalRot0Attr().Set(Gf.Quatf(1.0))
        fj.CreateLocalRot1Attr().Set(Gf.Quatf(1.0))
    mark('chain-joints')
    px_iface = px.get_physx_simulation_interface()
    sp_str = sp
    omega = 40.0 * 2.0 * math.pi / 60.0

    def on_contact(hdr, data):
        try:
            for i in range(len(hdr)):
                h = hdr[i]
                a0 = str(PhysicsSchemaTools.intToSdfPath(h.actor0))
                a1 = str(PhysicsSchemaTools.intToSdfPath(h.actor1))
                if 'Shaft' not in a0 and 'Shaft' not in a1:
                    continue
                origin = np.array([SHAFT_X, 0, SHAFT_Z])
                axis = np.array([0.0, 1.0, 0.0])
                acc['n'] += 1
                for j in range(h.contact_data_offset,
                               h.contact_data_offset
                               + h.num_contact_data):
                    d = data[j]
                    im = np.array([d.impulse.x, d.impulse.y,
                                   d.impulse.z])
                    pos = np.array([d.position.x, d.position.y,
                                    d.position.z])
                    tau = float(np.dot(np.cross(pos - origin, im),
                                       axis))
                    r_vec = np.array([pos[0] - origin[0], 0.0,
                                      pos[2] - origin[2]])
                    v_b = np.cross(axis, omega * r_vec)
                    dW = float(np.dot(im, v_b))
                    if a0 == sp_str or a1 == sp_str:
                        acc['tauA'] += tau
                    else:
                        acc['tauB'] += tau
                    acc['W'] += dW
        except Exception as _e:
            with open('/tmp/r4cb_err.txt', 'a') as _fh:
                _fh.write(str(_e) + '\n')
    px_iface.subscribe_contact_report_events(on_contact)
    SimulationManager.set_physics_sim_device('cpu')
    SimulationManager.set_physics_dt(DT)
    tl = omni.timeline.get_timeline_interface()
    tl.play()
    sim.update()
    mark('armed')
    theta = 0.0
    F_pre = np.zeros((3, 3), dtype=np.float32)
    F_pre[:, 2] = -F_PRESS_N
    z_traj = []
    for _ in range(NSTEPS):
        theta += omega * DT
        ha = 0.5 * theta
        shaft.set_world_poses(
            orientations=np.array(
                [[math.cos(ha), 0, math.sin(ha), 0]], dtype=np.float32))
        bodies.apply_forces(F_pre)
        SimulationManager.step(steps=1)
        pp0, _ = bodies.get_world_poses()
        z_traj.append(float(np.asarray(pp0.numpy())[1][2]))
    mark('loop-done')
    pp, _ = bodies.get_world_poses()
    P = np.asarray(pp.numpy())
    with open(OUT, 'w') as fh:
        json.dump({'n_shaft_rows': acc['n'],
                   'tauA': acc['tauA'], 'tauB': acc['tauB'],
                   'W_total': acc['W'],
                   'spec_final': P.tolist(),
                   'z_traj': z_traj}, fh, indent=2)
finally:
    try:
        sim.close(exit_code=0)
    except Exception:
        pass
