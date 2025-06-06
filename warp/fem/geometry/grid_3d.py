# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Optional

import warp as wp
from warp.fem.cache import cached_arg_value, dynamic_func
from warp.fem.types import NULL_ELEMENT_INDEX, OUTSIDE, Coords, ElementIndex, Sample, make_free_sample

from .closest_point import project_on_box_at_origin
from .element import Cube, Square
from .geometry import Geometry


@wp.struct
class Grid3DCellArg:
    res: wp.vec3i
    cell_size: wp.vec3
    origin: wp.vec3


class Grid3D(Geometry):
    """Three-dimensional regular grid geometry"""

    dimension = 3

    def __init__(self, res: wp.vec3i, bounds_lo: Optional[wp.vec3] = None, bounds_hi: Optional[wp.vec3] = None):
        """Constructs a dense 3D grid

        Args:
            res: Resolution of the grid along each dimension
            bounds_lo: Position of the lower bound of the axis-aligned grid
            bounds_hi: Position of the upper bound of the axis-aligned grid
        """

        if bounds_lo is None:
            bounds_lo = wp.vec3(0.0)

        if bounds_hi is None:
            bounds_hi = wp.vec3(1.0)

        self.bounds_lo = bounds_lo
        self.bounds_hi = bounds_hi

        self._res = res

    @property
    def extents(self) -> wp.vec3:
        # Avoid using native sub due to higher over of calling builtins from Python
        return wp.vec3(
            self.bounds_hi[0] - self.bounds_lo[0],
            self.bounds_hi[1] - self.bounds_lo[1],
            self.bounds_hi[2] - self.bounds_lo[2],
        )

    @property
    def cell_size(self) -> wp.vec3:
        ex = self.extents
        return wp.vec3(
            ex[0] / self.res[0],
            ex[1] / self.res[1],
            ex[2] / self.res[2],
        )

    def cell_count(self):
        return self.res[0] * self.res[1] * self.res[2]

    def vertex_count(self):
        return (self.res[0] + 1) * (self.res[1] + 1) * (self.res[2] + 1)

    def side_count(self):
        return (
            (self.res[0] + 1) * (self.res[1]) * (self.res[2])
            + (self.res[0]) * (self.res[1] + 1) * (self.res[2])
            + (self.res[0]) * (self.res[1]) * (self.res[2] + 1)
        )

    def edge_count(self):
        return (
            (self.res[0] + 1) * (self.res[1] + 1) * (self.res[2])
            + (self.res[0]) * (self.res[1] + 1) * (self.res[2] + 1)
            + (self.res[0] + 1) * (self.res[1]) * (self.res[2] + 1)
        )

    def boundary_side_count(self):
        return 2 * (self.res[1]) * (self.res[2]) + (self.res[0]) * 2 * (self.res[2]) + (self.res[0]) * (self.res[1]) * 2

    def reference_cell(self) -> Cube:
        return Cube()

    def reference_side(self) -> Square:
        return Square()

    @property
    def res(self):
        return self._res

    @property
    def origin(self):
        return self.bounds_lo

    @property
    def strides(self):
        return wp.vec3i(self.res[1] * self.res[2], self.res[2], 1)

    # Utility device functions

    CellArg = Grid3DCellArg
    Cell = wp.vec3i

    @wp.func
    def _to_3d_index(strides: wp.vec2i, index: int):
        x = index // strides[0]
        y = (index - strides[0] * x) // strides[1]
        z = index - strides[0] * x - strides[1] * y
        return wp.vec3i(x, y, z)

    @wp.func
    def _from_3d_index(strides: wp.vec2i, index: wp.vec3i):
        return strides[0] * index[0] + strides[1] * index[1] + index[2]

    @wp.func
    def cell_index(res: wp.vec3i, cell: Cell):
        strides = wp.vec2i(res[1] * res[2], res[2])
        return Grid3D._from_3d_index(strides, cell)

    @wp.func
    def get_cell(res: wp.vec3i, cell_index: ElementIndex):
        strides = wp.vec2i(res[1] * res[2], res[2])
        return Grid3D._to_3d_index(strides, cell_index)

    @wp.struct
    class Side:
        axis: int  # normal
        origin: wp.vec3i  # index of vertex at corner (0,0,0)

    @wp.struct
    class SideArg:
        cell_count: int
        axis_offsets: wp.vec3i
        cell_arg: Grid3DCellArg

    SideIndexArg = SideArg

    @wp.func
    def _world_to_local(axis: int, vec: Any):
        return type(vec)(
            vec[axis],
            vec[(axis + 1) % 3],
            vec[(axis + 2) % 3],
        )

    @wp.func
    def _local_to_world(axis: int, vec: Any):
        return type(vec)(
            vec[(2 * axis) % 3],
            vec[(2 * axis + 1) % 3],
            vec[(2 * axis + 2) % 3],
        )

    @wp.func
    def _local_to_world_axis(axis: int, loc_index: Any):
        return (axis + loc_index) % 3

    @wp.func
    def side_index(arg: SideArg, side: Side):
        alt_axis = Grid3D._local_to_world_axis(side.axis, 0)
        if side.origin[0] == arg.cell_arg.res[alt_axis]:
            # Upper-boundary side
            longitude = side.origin[1]
            latitude = side.origin[2]

            latitude_res = arg.cell_arg.res[Grid3D._local_to_world_axis(side.axis, 2)]
            lat_long = latitude_res * longitude + latitude

            return 3 * arg.cell_count + arg.axis_offsets[side.axis] + lat_long

        cell_index = Grid3D.cell_index(arg.cell_arg.res, Grid3D._local_to_world(side.axis, side.origin))
        return side.axis * arg.cell_count + cell_index

    @wp.func
    def get_side(arg: SideArg, side_index: ElementIndex):
        res = arg.cell_arg.res

        if side_index < 3 * arg.cell_count:
            axis = side_index // arg.cell_count
            cell_index = side_index - axis * arg.cell_count
            origin_loc = Grid3D._world_to_local(axis, Grid3D.get_cell(res, cell_index))
            return Grid3D.Side(axis, origin_loc)

        axis_offsets = arg.axis_offsets
        axis_side_index = side_index - 3 * arg.cell_count
        if axis_side_index < axis_offsets[1]:
            axis = 0
        elif axis_side_index < axis_offsets[2]:
            axis = 1
        else:
            axis = 2

        altitude = res[Grid3D._local_to_world_axis(axis, 0)]

        lat_long = axis_side_index - axis_offsets[axis]
        latitude_res = res[Grid3D._local_to_world_axis(axis, 2)]

        longitude = lat_long // latitude_res
        latitude = lat_long - longitude * latitude_res

        origin_loc = wp.vec3i(altitude, longitude, latitude)

        return Grid3D.Side(axis, origin_loc)

    # Geometry device interface

    @cached_arg_value
    def cell_arg_value(self, device) -> CellArg:
        args = self.CellArg()
        self.fill_cell_arg(args, device)
        return args

    def fill_cell_arg(self, args: CellArg, device):
        args.res = self.res
        args.origin = self.bounds_lo
        args.cell_size = self.cell_size

    @wp.func
    def cell_position(args: CellArg, s: Sample):
        cell = Grid3D.get_cell(args.res, s.element_index)
        return (
            wp.vec3(
                (float(cell[0]) + s.element_coords[0]) * args.cell_size[0],
                (float(cell[1]) + s.element_coords[1]) * args.cell_size[1],
                (float(cell[2]) + s.element_coords[2]) * args.cell_size[2],
            )
            + args.origin
        )

    @wp.func
    def cell_deformation_gradient(args: CellArg, s: Sample):
        return wp.diag(args.cell_size)

    @wp.func
    def cell_inverse_deformation_gradient(args: CellArg, s: Sample):
        return wp.diag(wp.cw_div(wp.vec3(1.0), args.cell_size))

    @wp.func
    def cell_coordinates(args: Grid3DCellArg, cell_index: int, pos: wp.vec3):
        uvw = wp.cw_div(pos - args.origin, args.cell_size)
        ijk = Grid3D.get_cell(args.res, cell_index)
        return uvw - wp.vec3(ijk)

    @wp.func
    def cell_closest_point(args: Grid3DCellArg, cell_index: int, pos: wp.vec3):
        ijk_world = wp.cw_mul(wp.vec3(Grid3D.get_cell(args.res, cell_index)), args.cell_size) + args.origin
        dist_sq, coords = project_on_box_at_origin(pos - ijk_world, args.cell_size)
        return coords, dist_sq

    def supports_cell_lookup(self, device):
        return True

    def make_filtered_cell_lookup(self, filter_func: wp.Function = None):
        suffix = f"{self.name}{filter_func.key if filter_func is not None else ''}"

        @dynamic_func(suffix=suffix)
        def cell_lookup(args: self.CellArg, pos: wp.vec3, max_dist: float, filter_data: Any, filter_target: Any):
            cell_size = args.cell_size
            res = args.res

            # Start at closest point on grid
            loc_pos = wp.cw_div(pos - args.origin, cell_size)
            x = wp.clamp(loc_pos[0], 0.0, float(res[0]))
            y = wp.clamp(loc_pos[1], 0.0, float(res[1]))
            z = wp.clamp(loc_pos[2], 0.0, float(res[2]))

            x_cell = wp.min(wp.floor(x), float(res[0]) - 1.0)
            y_cell = wp.min(wp.floor(y), float(res[1]) - 1.0)
            z_cell = wp.min(wp.floor(z), float(res[2]) - 1.0)

            coords = Coords(x - x_cell, y - y_cell, z - z_cell)
            cell_index = Grid3D.cell_index(res, Grid3D.Cell(int(x_cell), int(y_cell), int(z_cell)))

            if wp.static(filter_func is None):
                return make_free_sample(cell_index, coords)
            else:
                if filter_func(filter_data, cell_index) == filter_target:
                    return make_free_sample(cell_index, coords)

                offset = float(0.5)
                min_cell_size = wp.min(cell_size)
                max_offset = wp.ceil(max_dist / min_cell_size)
                scales = wp.cw_div(wp.vec3(min_cell_size), cell_size)

                closest_cell = NULL_ELEMENT_INDEX
                closest_coords = Coords()

                # Iterate over increasingly larger neighborhoods
                while closest_cell == NULL_ELEMENT_INDEX:
                    i_min = wp.max(0, int(wp.floor(x - offset * scales[0])))
                    i_max = wp.min(res[0], int(wp.floor(x + offset * scales[0])) + 1)
                    j_min = wp.max(0, int(wp.floor(y - offset * scales[1])))
                    j_max = wp.min(res[1], int(wp.floor(y + offset * scales[1])) + 1)
                    k_min = wp.max(0, int(wp.floor(z - offset * scales[2])))
                    k_max = wp.min(res[2], int(wp.floor(z + offset * scales[2])) + 1)

                    closest_dist = min_cell_size * min_cell_size * float(offset * offset)

                    for i in range(i_min, i_max):
                        for j in range(j_min, j_max):
                            for k in range(k_min, k_max):
                                ijk = Grid3D.Cell(i, j, k)
                                cell_index = Grid3D.cell_index(res, ijk)
                                if filter_func(filter_data, cell_index) == filter_target:
                                    rel_pos = wp.cw_mul(loc_pos - wp.vec3(ijk), cell_size)
                                    dist, coords = project_on_box_at_origin(rel_pos, cell_size)

                                    if dist <= closest_dist:
                                        closest_dist = dist
                                        closest_coords = coords
                                        closest_cell = cell_index

                    if offset >= max_offset:
                        break
                    offset = wp.min(3.0 * offset, max_offset)

                return make_free_sample(closest_cell, closest_coords)

        return cell_lookup

    @wp.func
    def cell_measure(args: CellArg, s: Sample):
        return args.cell_size[0] * args.cell_size[1] * args.cell_size[2]

    @wp.func
    def cell_normal(args: CellArg, s: Sample):
        return wp.vec3(0.0)

    @cached_arg_value
    def side_arg_value(self, device) -> SideArg:
        args = self.SideArg()
        self.fill_side_arg(args, device)
        return args

    def fill_side_arg(self, args: SideArg, device):
        axis_dims = wp.vec3i(
            self.res[1] * self.res[2],
            self.res[2] * self.res[0],
            self.res[0] * self.res[1],
        )
        args.axis_offsets = wp.vec3i(
            0,
            axis_dims[0],
            axis_dims[0] + axis_dims[1],
        )
        args.cell_count = self.cell_count()
        args.cell_arg = self.cell_arg_value(device)

    def side_index_arg_value(self, device) -> SideIndexArg:
        return self.side_arg_value(device)

    def fill_side_index_arg(self, args: SideIndexArg, device):
        self.fill_side_arg(args, device)

    @wp.func
    def boundary_side_index(args: SideArg, boundary_side_index: int):
        """Boundary side to side index"""

        axis_side_index = boundary_side_index // 2
        border = boundary_side_index - 2 * axis_side_index

        if axis_side_index < args.axis_offsets[1]:
            axis = 0
        elif axis_side_index < args.axis_offsets[2]:
            axis = 1
        else:
            axis = 2

        lat_long = axis_side_index - args.axis_offsets[axis]
        latitude_res = args.cell_arg.res[Grid3D._local_to_world_axis(axis, 2)]

        longitude = lat_long // latitude_res
        latitude = lat_long - longitude * latitude_res

        altitude = border * args.cell_arg.res[axis]

        side = Grid3D.Side(axis, wp.vec3i(altitude, longitude, latitude))
        return Grid3D.side_index(args, side)

    @wp.func
    def side_position(args: SideArg, s: Sample):
        side = Grid3D.get_side(args, s.element_index)

        coord0 = wp.where(side.origin[0] == 0, 1.0 - s.element_coords[0], s.element_coords[0])

        local_pos = wp.vec3(
            float(side.origin[0]),
            float(side.origin[1]) + coord0,
            float(side.origin[2]) + s.element_coords[1],
        )

        pos = args.cell_arg.origin + wp.cw_mul(Grid3D._local_to_world(side.axis, local_pos), args.cell_arg.cell_size)

        return pos

    @wp.func
    def side_deformation_gradient(args: SideArg, s: Sample):
        side = Grid3D.get_side(args, s.element_index)

        sign = wp.where(side.origin[0] == 0, -1.0, 1.0)

        return wp.matrix_from_cols(
            wp.cw_mul(Grid3D._local_to_world(side.axis, wp.vec3(0.0, sign, 0.0)), args.cell_arg.cell_size),
            wp.cw_mul(Grid3D._local_to_world(side.axis, wp.vec3(0.0, 0.0, 1.0)), args.cell_arg.cell_size),
        )

    @wp.func
    def side_inner_inverse_deformation_gradient(args: SideArg, s: Sample):
        return Grid3D.cell_inverse_deformation_gradient(args.cell_arg, s)

    @wp.func
    def side_outer_inverse_deformation_gradient(args: SideArg, s: Sample):
        return Grid3D.cell_inverse_deformation_gradient(args.cell_arg, s)

    @wp.func
    def side_measure(args: SideArg, s: Sample):
        side = Grid3D.get_side(args, s.element_index)
        long_axis = Grid3D._local_to_world_axis(side.axis, 1)
        lat_axis = Grid3D._local_to_world_axis(side.axis, 2)
        return args.cell_arg.cell_size[long_axis] * args.cell_arg.cell_size[lat_axis]

    @wp.func
    def side_measure_ratio(args: SideArg, s: Sample):
        side = Grid3D.get_side(args, s.element_index)
        alt_axis = Grid3D._local_to_world_axis(side.axis, 0)
        return 1.0 / args.cell_arg.cell_size[alt_axis]

    @wp.func
    def side_normal(args: SideArg, s: Sample):
        side = Grid3D.get_side(args, s.element_index)

        sign = wp.where(side.origin[0] == 0, -1.0, 1.0)

        local_n = wp.vec3(sign, 0.0, 0.0)
        return Grid3D._local_to_world(side.axis, local_n)

    @wp.func
    def side_inner_cell_index(arg: SideArg, side_index: ElementIndex):
        side = Grid3D.get_side(arg, side_index)

        inner_alt = wp.where(side.origin[0] == 0, 0, side.origin[0] - 1)

        inner_origin = wp.vec3i(inner_alt, side.origin[1], side.origin[2])

        cell = Grid3D._local_to_world(side.axis, inner_origin)
        return Grid3D.cell_index(arg.cell_arg.res, cell)

    @wp.func
    def side_outer_cell_index(arg: SideArg, side_index: ElementIndex):
        side = Grid3D.get_side(arg, side_index)

        alt_axis = Grid3D._local_to_world_axis(side.axis, 0)

        outer_alt = wp.where(
            side.origin[0] == arg.cell_arg.res[alt_axis], arg.cell_arg.res[alt_axis] - 1, side.origin[0]
        )

        outer_origin = wp.vec3i(outer_alt, side.origin[1], side.origin[2])

        cell = Grid3D._local_to_world(side.axis, outer_origin)
        return Grid3D.cell_index(arg.cell_arg.res, cell)

    @wp.func
    def side_inner_cell_coords(args: SideArg, side_index: ElementIndex, side_coords: Coords):
        side = Grid3D.get_side(args, side_index)

        inner_alt = wp.where(side.origin[0] == 0, 0.0, 1.0)

        side_coord0 = wp.where(side.origin[0] == 0, 1.0 - side_coords[0], side_coords[0])

        return Grid3D._local_to_world(side.axis, wp.vec3(inner_alt, side_coord0, side_coords[1]))

    @wp.func
    def side_outer_cell_coords(args: SideArg, side_index: ElementIndex, side_coords: Coords):
        side = Grid3D.get_side(args, side_index)

        alt_axis = Grid3D._local_to_world_axis(side.axis, 0)
        outer_alt = wp.where(side.origin[0] == args.cell_arg.res[alt_axis], 1.0, 0.0)

        side_coord0 = wp.where(side.origin[0] == 0, 1.0 - side_coords[0], side_coords[0])

        return Grid3D._local_to_world(side.axis, wp.vec3(outer_alt, side_coord0, side_coords[1]))

    @wp.func
    def side_from_cell_coords(
        args: SideArg,
        side_index: ElementIndex,
        element_index: ElementIndex,
        element_coords: Coords,
    ):
        side = Grid3D.get_side(args, side_index)
        cell = Grid3D.get_cell(args.cell_arg.res, element_index)

        if float(side.origin[0] - cell[side.axis]) == element_coords[side.axis]:
            long_axis = Grid3D._local_to_world_axis(side.axis, 1)
            lat_axis = Grid3D._local_to_world_axis(side.axis, 2)
            long_coord = element_coords[long_axis]
            long_coord = wp.where(side.origin[0] == 0, 1.0 - long_coord, long_coord)
            return Coords(long_coord, element_coords[lat_axis], 0.0)

        return Coords(OUTSIDE)

    @wp.func
    def side_to_cell_arg(side_arg: SideArg):
        return side_arg.cell_arg

    @wp.func
    def side_coordinates(args: SideArg, side_index: int, pos: wp.vec3):
        cell_arg = args.cell_arg
        side = Grid3D.get_side(args, side_index)

        pos_loc = Grid3D._world_to_local(side.axis, wp.cw_div(pos - cell_arg.origin, cell_arg.cell_size)) - wp.vec3(
            side.origin
        )

        coord0 = wp.where(side.origin[0] == 0, 1.0 - pos_loc[1], pos_loc[1])
        return Coords(coord0, pos_loc[2], 0.0)

    @wp.func
    def side_closest_point(args: SideArg, side_index: int, pos: wp.vec3):
        coord = Grid3D.side_coordinates(args, side_index, pos)

        cell_arg = args.cell_arg
        side = Grid3D.get_side(args, side_index)

        loc_cell_size = Grid3D._world_to_local(side.axis, cell_arg.cell_size)
        long_lat_sizes = wp.vec2(loc_cell_size[1], loc_cell_size[2])
        dist, proj_coord = project_on_box_at_origin(wp.vec2(coord[0], coord[1]), long_lat_sizes)
        return proj_coord, dist
