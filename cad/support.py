import cadquery as cq
# ----------------------------
# Parameters
# ----------------------------

box_length = 100
box_width = 150
box_height = 40
box_wall = 3

lid_thickness_center = 4
lid_thickness_edge = 2
lid_clearance = 0.1
lid_plug_depth = lid_thickness_center - lid_thickness_edge
lid_post_clearance = 0.1
lid_plug_ring_width = 6

box_screw_post_diameter = 7
box_screw_post_hole_diameter = 1.9
box_screw_post_hole_depth = 6
box_screw_post_inset = 5
box_screw_post_height = box_height - lid_plug_depth - lid_post_clearance
lid_screw_hole_diameter = 2.4
lid_screw_head_recess_diameter = 4.2
lid_screw_head_recess_depth = 1

post_base_fillet_radius = 1.5

nano_post_corner_offset = 1
nano_width = 18
nano_length = 44
nano_board_thickness = 1.6
nano_post_hole_depth = 4
nano_post_hole_diameter = 2
nano_post_diameter = 7
nano_post_height = 10 + box_wall
nano_post_fillet_radius = 1.5

usb_hole_width = 15
usb_hole_height = 10

side_hole_diameter = 11.5


conn_hole_width = 19.5
conn_hole_height = 7.5

conn_ledge_depth = 10
conn_ledge_thickness = 3
conn_ledge_wall_thickness = 7
conn_ledge_extra_width = conn_ledge_wall_thickness
conn_ledge_wall_hole_diameter = 1.9
conn_ledge_wall_hole_depth = 5

conn_strap_thickness = 5
conn_strap_hole_diameter = 2.5
conn_registration_bump_diameter = 2.4

conn_registration_bump_height = 1.5
conn_registration_bump_spacing = 6
conn_registration_bump_chamfer = 0.5

conn_positions = [
    (-20, 15),
    ( 20, 15),
]


# ----------------------------
# Helper geometry
# ----------------------------

def screw_post_points():
    x = box_width / 2 - box_wall - box_screw_post_inset
    y = box_length / 2 - box_wall - box_screw_post_inset

    return [
        (-x, -y),
        ( x, -y),
        (-x,  y),
        ( x,  y),
    ]

def chamfered_post(
    diameter,
    height,
    base_chamfer=0,
    top_chamfer=0,
    base_z=0,
    hole_diameter=None,
    hole_depth=None,
):
    """
    Vertical cylindrical post from base_z to height.
    Positive base_chamfer flares outward at the base; positive top_chamfer
    tapers inward at the working/top end. Optional hole is drilled from top.
    """
    radius = diameter / 2
    solids = []
    z = base_z

    if base_chamfer > 0:
        solids.append(cq.Solid.makeCone(
            radius + base_chamfer,
            radius,
            base_chamfer,
            pnt=(0, 0, z),
            dir=(0, 0, 1),
        ))
        z += base_chamfer

    straight_height = height - z - top_chamfer
    if straight_height > 0:
        solids.append(cq.Solid.makeCylinder(
            radius,
            straight_height,
            pnt=(0, 0, z),
            dir=(0, 0, 1),
        ))
        z += straight_height

    if top_chamfer > 0:
        tip_radius = max(radius - top_chamfer, 0.1)
        solids.append(cq.Solid.makeCone(
            radius,
            tip_radius,
            top_chamfer,
            pnt=(0, 0, z),
            dir=(0, 0, 1),
        ))

    post = cq.Workplane("XY").newObject(solids).combine()

    if hole_diameter is not None and hole_depth is not None:
        post = (
            post.faces(">Z")
            .workplane()
            .hole(hole_diameter, hole_depth)
        )

    return post


def cyl_post(diameter, height, hole_diameter, hole_depth, fillet_radius=1.5, base_z=box_wall):
    return chamfered_post(
        diameter,
        height,
        base_chamfer=fillet_radius,
        base_z=base_z,
        hole_diameter=hole_diameter,
        hole_depth=hole_depth,
    )

def post_array(points, diameter, height, hole_diameter, hole_depth, fillet_radius):
    posts = cq.Workplane("XY")

    for x, y in points:
        posts = posts.union(
            cyl_post(
                diameter,
                height,
                hole_diameter,
                hole_depth,
                fillet_radius,
            ).translate((x, y, 0))
        )

    return posts

# ----------------------------
# Nano support posts
# ----------------------------

def nano_post_body():
    return cyl_post(
        nano_post_diameter,
        nano_post_height,
        nano_post_hole_diameter,
        nano_post_hole_depth,
        nano_post_fillet_radius,
    )


def nano_board_corner_cutout():
    return (
        cq.Workplane("XY")
        .box(
            4,
            4,
            nano_board_thickness,
            centered=(False, False, False),
        )
        .translate((
            nano_post_corner_offset,
            nano_post_corner_offset,
            nano_post_height - 1,
        ))
    )


def nano_post():
    return nano_post_body().cut(nano_board_corner_cutout())


def nano_supports():
    dx = nano_width + 2 * nano_post_corner_offset
    dy = nano_length + 2 * nano_post_corner_offset

    placements = [
        (-dx / 2, -dy / 2,   0),
        (-dx / 2,  dy / 2, -90),
        ( dx / 2, -dy / 2,  90),
        ( dx / 2,  dy / 2, 180),
    ]

    supports = cq.Workplane("XY")

    for x, y, angle in placements:
        p = (
            nano_post()
            .rotate((0, 0, 0), (0, 0, 1), angle)
            .translate((x, y, 0))
        )
        supports = supports.union(p)

    return supports

# ----------------------------
# Enclosure
# ----------------------------

def enclosure_shell():
    outer = (
        cq.Workplane("XY")
        .box(box_width, box_length, box_height)
        .translate((0, 0, box_height / 2))
    )
    inner = (
        cq.Workplane("XY")
        .box(
            box_width - 2 * box_wall,
            box_length - 2 * box_wall,
            box_height,
        )
        .translate((0, 0, box_wall + box_height / 2))
    )

    return outer.cut(inner)


def enclosure_screw_posts():
    return post_array(
        screw_post_points(),
        box_screw_post_diameter,
        box_screw_post_height,
        box_screw_post_hole_diameter,
        box_screw_post_hole_depth,
        post_base_fillet_radius,
    )

def usb_cutout():
    cutout_overcut = 2
    return (
        cq.Workplane("XY")
        .box(
            usb_hole_width,
            box_wall + 2 * cutout_overcut,
            usb_hole_height,
        )
        .translate((
            box_width / 2 - box_width / 3,
            box_length / 2 - box_wall / 2,
            nano_post_height + 1,
        ))
    )


def side_hole_cutout():
    cutout_overcut = 2
    x = -box_width / 2 + box_width / 3

    return (
        cq.Workplane("XY")
        .circle(side_hole_diameter / 2)
        .extrude(box_wall + 2 * cutout_overcut)
        .rotate((0, 0, 0), (1, 0, 0), -90)
        .translate((
            x,
            -box_length / 2 - cutout_overcut,
            box_height / 2,
        ))
    )

def registration_bumps(up=True):
    bump = chamfered_post(
        conn_registration_bump_diameter,
        conn_registration_bump_height,
        base_chamfer=conn_registration_bump_chamfer,
        top_chamfer=conn_registration_bump_chamfer,
    )

    if not up:
        bump = bump.rotate((0, 0, 0), (1, 0, 0), 180)

    bumps = cq.Workplane("XY")
    for y_offset in (-conn_registration_bump_spacing / 2, conn_registration_bump_spacing / 2):
        bumps = bumps.union(bump.translate((0, y_offset, 0)))

    return bumps


def add_conn_cutout(body, offset_y, offset_z):
    cutout_overcut = 2
    cutter = (
        cq.Workplane("XY")
        .box(
            box_wall + 2 * cutout_overcut,
            conn_hole_width,
            conn_hole_height,
        )
        .translate((
            -box_width / 2 + box_wall / 2,
            offset_y,
            offset_z,
        ))
    )

    ledge_width = conn_hole_width + 2 * conn_ledge_extra_width
    ledge_x = -box_width / 2 + box_wall + conn_ledge_depth / 2

    ledge = (
        cq.Workplane("XY")
        .box(
            conn_ledge_depth,
            ledge_width,
            conn_ledge_thickness,
        )
        .translate((
            ledge_x,
            offset_y,
            offset_z
                - conn_hole_height / 2
                - conn_ledge_thickness / 2,
        ))
    )

    wall_gap = conn_hole_width
    side_wall_y_offset = wall_gap / 2 + conn_ledge_wall_thickness / 2
    side_walls = cq.Workplane("XY")
    wall_top_z = offset_z + conn_hole_height / 2
    wall_bottom_z = box_wall
    wall_height = wall_top_z - wall_bottom_z
    wall_center_z = wall_bottom_z + wall_height / 2

    for y_offset in (-side_wall_y_offset, side_wall_y_offset):
        side_walls = side_walls.union(
            cq.Workplane("XY")
            .box(
                conn_ledge_depth,
                conn_ledge_wall_thickness,
                wall_height,
            )
            .translate((
                ledge_x,
                offset_y + y_offset,
                wall_center_z,
            ))
        )

    wall_holes = (
        cq.Workplane("XY")
        .pushPoints([
            (ledge_x, offset_y - side_wall_y_offset),
            (ledge_x, offset_y + side_wall_y_offset),
        ])
        .circle(conn_ledge_wall_hole_diameter / 2)
        .extrude(conn_ledge_wall_hole_depth)
        .translate((0, 0, wall_top_z - conn_ledge_wall_hole_depth))
    )

    ledge_bumps = registration_bumps(up=True).translate((
        ledge_x,
        offset_y,
        offset_z - conn_hole_height / 2,
    ))

    return body.cut(cutter).union(ledge).union(ledge_bumps).union(side_walls).cut(wall_holes)

def enclosure():
    body = enclosure_shell()
    body = body.union(enclosure_screw_posts())

    body = body.union(
        nano_supports().translate((
            box_width / 2 - box_width / 3,
            0,
            0,
        ))
    )

    body = body.cut(usb_cutout())
    body = body.cut(side_hole_cutout())

    for offset_y, offset_z in conn_positions:
        body = add_conn_cutout(body, offset_y, offset_z)

    return body

# ----------------------------
# Connector straps
# ----------------------------

def conn_wall_y_offset():
    return conn_hole_width / 2 + conn_ledge_wall_thickness / 2


def connector_strap():
    strap_length = conn_hole_width + 2 * conn_ledge_wall_thickness
    hole_y = conn_wall_y_offset()

    strap = (
        cq.Workplane("XY")
        .box(
            conn_ledge_depth,
            strap_length,
            conn_strap_thickness,
            centered=(True, True, False),
        )
        .faces(">Z")
        .workplane()
        .pushPoints([(0, -hole_y), (0, hole_y)])
        .hole(conn_strap_hole_diameter)
    )

    bumps = registration_bumps(up=False)

    return strap.union(bumps)


def connector_straps():
    straps = cq.Workplane("XY")
    strap_spacing = conn_hole_width + 2 * conn_ledge_wall_thickness + 10
    strap_x = -box_width / 2 - conn_ledge_depth / 2 - 20
    first_strap_y = -strap_spacing * (len(conn_positions) - 1) / 2

    for index, _ in enumerate(conn_positions):
        straps = straps.union(
            connector_strap().translate((
                strap_x,
                first_strap_y + index * strap_spacing,
                conn_registration_bump_height,
            ))
        )

    return straps

# ----------------------------
# Lid
# ----------------------------

def enclosure_lid():
    plug_width = box_width - 2 * (box_wall + lid_clearance)
    plug_length = box_length - 2 * (box_wall + lid_clearance)

    flange = (
        cq.Workplane("XY")
        .box(box_width, box_length, lid_thickness_edge)
        .translate((0, 0, lid_plug_depth + lid_thickness_edge / 2))
    )

    plug_inner_width = plug_width - 2 * lid_plug_ring_width
    plug_inner_length = plug_length - 2 * lid_plug_ring_width

    plug_outer = (
        cq.Workplane("XY")
        .box(plug_width, plug_length, lid_plug_depth)
        .translate((0, 0, lid_plug_depth / 2))
    )

    plug_inner = (
        cq.Workplane("XY")
        .box(plug_inner_width, plug_inner_length, lid_plug_depth + 2)
        .translate((0, 0, lid_plug_depth / 2))
    )

    plug = plug_outer.cut(plug_inner)

    lid = flange.union(plug)

    lid = (
        lid.faces(">Z")
        .workplane()
        .pushPoints(screw_post_points())
        .hole(lid_screw_hole_diameter)
        .faces(">Z")
        .workplane()
        .pushPoints(screw_post_points())
        .hole(lid_screw_head_recess_diameter, lid_screw_head_recess_depth)
    )

    return lid

# ----------------------------
# Build objects
# ----------------------------

box = enclosure()
lid = enclosure_lid().translate((box_width + 20, 0, 0))
straps = connector_straps()

box.export("./box.step")
lid.export("box-lid.step")
straps.export("connector-straps.step")

assy = cq.Assembly()
assy.add(box, name="box")
assy.add(lid, name="lid")
assy.add(straps, name="connector_straps")

try:
    show_object(box, name="box")
    show_object(lid, name="lid")
    show_object(straps, name="connector_straps")
except:
    pass


