"""Support for simplified access to data on nodes of type omni.warp.OgnParticleVolume

Particle volume sampler
"""

import omni.graph.core as og
import sys
import traceback
class OgnParticleVolumeDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.warp.OgnParticleVolume

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.execIn
            inputs.max_points
            inputs.sdf_max
            inputs.sdf_min
            inputs.shape
            inputs.spacing
            inputs.spacing_jitter
            inputs.velocity
        Outputs:
            outputs.particles

    Predefined Tokens:
        tokens.points
        tokens.worldMatrix
        tokens.primPath
        tokens.faceVertexCounts
        tokens.faceVertexIndices
    """
    # This is an internal object that provides per-class storage of a per-node data dictionary
    PER_NODE_DATA = {}
    # This is an internal object that describes unchanging attributes in a generic way
    # The values in this list are in no particular order, as a per-attribute tuple
    #     Name, Type, ExtendedTypeIndex, UiName, Description, Metadata, Is_Required, DefaultValue
    # You should not need to access any of this data directly, use the defined database interfaces
    INTERFACE = og.Database._get_interface([
        ('inputs:execIn', 'int', 0, None, '', {og.MetadataKeys.DEFAULT: '0'}, True, 0),
        ('inputs:max_points', 'int', 0, None, '', {og.MetadataKeys.DEFAULT: '262144'}, True, 262144),
        ('inputs:sdf_max', 'float', 0, None, '', {og.MetadataKeys.DEFAULT: '0.0'}, True, 0.0),
        ('inputs:sdf_min', 'float', 0, None, '', {og.MetadataKeys.DEFAULT: '-10000.0'}, True, -10000.0),
        ('inputs:shape', 'bundle', 0, None, 'Volume primitive', {}, True, None),
        ('inputs:spacing', 'float', 0, None, '', {og.MetadataKeys.DEFAULT: '10.0'}, True, 10.0),
        ('inputs:spacing_jitter', 'float', 0, None, '', {og.MetadataKeys.DEFAULT: '0.0'}, True, 0.0),
        ('inputs:velocity', 'vector3f', 0, None, '', {og.MetadataKeys.DEFAULT: '[0.0, 0.0, 0.0]'}, True, [0.0, 0.0, 0.0]),
        ('outputs:particles', 'bundle', 0, None, 'Particles bundle: points, velocities', {}, True, None),
    ])
    class tokens:
        points = "points"
        worldMatrix = "worldMatrix"
        primPath = "primPath"
        faceVertexCounts = "faceVertexCounts"
        faceVertexIndices = "faceVertexIndices"
    @classmethod
    def _populate_role_data(cls):
        """Populate a role structure with the non-default roles on this node type"""
        role_data = super()._populate_role_data()
        role_data.inputs.velocity = og.Database.ROLE_VECTOR
        return role_data
    class ValuesForInputs(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, context_helper: og.ContextHelper, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            super().__init__(context_helper, node, attributes, dynamic_attributes)
            self.__bundles = og.BundleContainer(context_helper.context, node, attributes, [], read_only=True)

        @property
        def execIn(self):
            return self._context_helper.get(self._attributes.execIn)

        @execIn.setter
        def execIn(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.execIn)
            self._context_helper.set_attr_value(value, self._attributes.execIn)

        @property
        def max_points(self):
            return self._context_helper.get(self._attributes.max_points)

        @max_points.setter
        def max_points(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.max_points)
            self._context_helper.set_attr_value(value, self._attributes.max_points)

        @property
        def sdf_max(self):
            return self._context_helper.get(self._attributes.sdf_max)

        @sdf_max.setter
        def sdf_max(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.sdf_max)
            self._context_helper.set_attr_value(value, self._attributes.sdf_max)

        @property
        def sdf_min(self):
            return self._context_helper.get(self._attributes.sdf_min)

        @sdf_min.setter
        def sdf_min(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.sdf_min)
            self._context_helper.set_attr_value(value, self._attributes.sdf_min)

        @property
        def shape(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute inputs.shape"""
            return self.__bundles.shape

        @property
        def spacing(self):
            return self._context_helper.get(self._attributes.spacing)

        @spacing.setter
        def spacing(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.spacing)
            self._context_helper.set_attr_value(value, self._attributes.spacing)

        @property
        def spacing_jitter(self):
            return self._context_helper.get(self._attributes.spacing_jitter)

        @spacing_jitter.setter
        def spacing_jitter(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.spacing_jitter)
            self._context_helper.set_attr_value(value, self._attributes.spacing_jitter)

        @property
        def velocity(self):
            return self._context_helper.get(self._attributes.velocity)

        @velocity.setter
        def velocity(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.velocity)
            self._context_helper.set_attr_value(value, self._attributes.velocity)
    class ValuesForOutputs(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to output attributes"""
        def __init__(self, context_helper: og.ContextHelper, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            super().__init__(context_helper, node, attributes, dynamic_attributes)
            self.__bundles = og.BundleContainer(context_helper.context, node, attributes, [], read_only=False)

        @property
        def particles(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute outputs.particles"""
            return self.__bundles.particles

        @particles.setter
        def particles(self, bundle: og.BundleContents):
            """Overwrite the bundle attribute outputs.particles with a new bundle"""
            if not isinstance(bundle, og.BundleContents):
                carb.log_error("Only bundle attributes can be assigned to another bundle attribute")
            self.__bundles.particles.bundle = bundle
    class ValuesForState(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to state attributes"""
        def __init__(self, context_helper: og.ContextHelper, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            super().__init__(context_helper, node, attributes, dynamic_attributes)
    def __init__(self, context_helper, node):
        super().__init__(node, context_helper)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT)
        self.inputs = OgnParticleVolumeDatabase.ValuesForInputs(context_helper, node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = OgnParticleVolumeDatabase.ValuesForOutputs(context_helper, node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = OgnParticleVolumeDatabase.ValuesForState(context_helper, node, self.attributes.state, dynamic_attributes)

    @property
    def context(self) -> og.GraphContext:
        return self.context_helper.context
    class abi:
        """Class defining the ABI interface for the node type"""
        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(OgnParticleVolumeDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):
                return get_node_type_function()
            return 'omni.warp.OgnParticleVolume'
        @staticmethod
        def compute(context_helper, node):
            db = OgnParticleVolumeDatabase(context_helper, node)
            try:
                db.inputs._setting_locked = True
                compute_function = getattr(OgnParticleVolumeDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:
                    return compute_function(context_helper, node)
                return OgnParticleVolumeDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
            return False
        @staticmethod
        def initialize(context_helper, node):
            OgnParticleVolumeDatabase._initialize_per_node_data(node)

            # Set any default values the attributes have specified
            db = OgnParticleVolumeDatabase(context_helper, node)
            db.inputs.execIn = 0
            db.inputs.max_points = 262144
            db.inputs.sdf_max = 0.0
            db.inputs.sdf_min = -10000.0
            db.inputs.spacing = 10.0
            db.inputs.spacing_jitter = 0.0
            db.inputs.velocity = [0.0, 0.0, 0.0]
            initialize_function = getattr(OgnParticleVolumeDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):
                initialize_function(context_helper, node)
        @staticmethod
        def release(node):
            release_function = getattr(OgnParticleVolumeDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):
                release_function(node)
            OgnParticleVolumeDatabase._release_per_node_data(node)
        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(OgnParticleVolumeDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):
                return update_node_version_function(context, node, old_version, new_version)
            return False
        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(OgnParticleVolumeDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(og.MetadataKeys.EXTENSION, "omni.warp")
                node_type.set_metadata(og.MetadataKeys.TOKENS, "[\"points\", \"worldMatrix\", \"primPath\", \"faceVertexCounts\", \"faceVertexIndices\"]")
                node_type.set_metadata(og.MetadataKeys.DESCRIPTION, "Particle volume sampler")
                node_type.set_metadata(og.MetadataKeys.LANGUAGE, "Python")
                OgnParticleVolumeDatabase.INTERFACE.add_to_node_type(node_type)
                node_type.set_has_state(True)
        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(OgnParticleVolumeDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):
                on_connection_type_resolve_function(node)
    NODE_TYPE_CLASS = None
    GENERATOR_VERSION = (1, 1, 2)
    TARGET_VERSION = (2, 2, 0)
    @staticmethod
    def register(node_type_class):
        OgnParticleVolumeDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(OgnParticleVolumeDatabase.abi, 1)
    @staticmethod
    def deregister():
        og.deregister_node_type("omni.warp.OgnParticleVolume")