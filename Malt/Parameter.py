# Copyright (c) 2020 BlenderNPR and contributors. MIT license. 

class PipelineGraph(object):
    
    def __init__(self, language, file_extension, functions, structs, graph_IO):
        self.language = language
        self.file_extension = file_extension
        self.functions = functions
        self.structs = structs
        self.graph_IO = graph_IO
    
    def generate_source(self, parameters):
        return ''

class GLSLPipelineGraph(PipelineGraph):

    def __init__(self, file_extension, source, root_path, graph_io_map, default_global_scope):
        from . GL.Shader import GLSL_Reflection
        functions = GLSL_Reflection.reflect_functions(source, root_path)
        structs = GLSL_Reflection.reflect_structs(source, root_path)
        graph_io = {}
        for name in graph_io_map.keys():
            graph_io[name] = functions[name]        
        for name in [*functions.keys()]:
            if name.startswith('_') or name.isupper() or name == 'main':
                functions.pop(name)
        for name in [*structs.keys()]:
            if name.startswith('_'):
                structs.pop(name)
        super().__init__('GLSL', file_extension, functions, structs, graph_io)
        self.graph_io_map = graph_io_map
        self.default_global_scope = default_global_scope
    
    def generate_source(self, parameters):
        import textwrap
        code = ''
        for graph_function, (define, declaration) in self.graph_io_map.items():
            if graph_function in parameters.keys() and define:
                code += '#define {}\n'.format(define)
        code += '\n\n' + self.default_global_scope + '\n\n' + parameters['GLOBAL'] + '\n\n'
        for graph_function, (define, declaration) in self.graph_io_map.items():
            if graph_function in parameters.keys():
                code += '{}\n{{\n{}\n}}'.format(declaration, textwrap.indent(parameters[graph_function],'\t'))
        return code

class PythonPipelineGraph(PipelineGraph):
    
    def __init__(self, function_nodes, graph_io_nodes):
        functions = {}
        for node in function_nodes:
            functions[node['name']] = node
        graph_io = {}
        for node in graph_io_nodes:
            graph_io[node['name']] = node
        super().__init__('Python', '-render_layer.py', functions, {}, graph_io)
    
    def generate_source(self, parameters):
        src = ''
        src += parameters['GLOBAL']
        src += '\n\n'
        for io in self.graph_IO.keys():
            if io in parameters.keys():
                src += parameters[io]
        return src


class PipelineParameters(object):

    def __init__(self, scene={}, world={}, camera={}, object={}, material={}, mesh={}, light={}):
        self.scene = scene
        self.world = world
        self.camera = camera
        self.object = object
        self.material = material
        self.mesh = mesh
        self.light = light

class Type(object):
    BOOL=0
    INT=1
    FLOAT=2
    STRING=3
    #???=4
    #ENUM=5 #TODO
    TEXTURE=6
    GRADIENT=7
    MATERIAL=8
    #RENDER_TARGET=9 #TODO
    OTHER=10

    @classmethod
    def to_string(cls, type):
        return ['Bool', 'Int', 'Float', 'String', '???', 'Enum', 'Texture', 'Gradient', 'Material', 'RenderTarget', 'Other'][type]
    
    @classmethod
    def from_string(cls, type):
        return ['Bool', 'Int', 'Float', 'String', '???', 'Enum', 'Texture', 'Gradient', 'Material', 'RenderTarget', 'Other'].index(type)

class Parameter(object):
    def __init__(self, default_value, type, size=1, filter=None):
        self.default_value = default_value
        self.type = type
        self.size = size
        self.filter = filter
    
    def type_string(self):
        if self.type == Type.OTHER:
            return self.default_value
        else:
            return Type.to_string(self.type)

    @classmethod
    def from_uniform(cls, uniform):
        type, size = gl_type_to_malt_type(uniform.type)
        value = uniform.value
        if size > 1:
            value = tuple(value)
        else:
            value = value[0]
        #TODO: uniform length ??? (Arrays)
        return Parameter(value, type, size)
    
    @classmethod
    def from_glsl_type(cls, glsl_type):
        type, size = glsl_type_to_malt_type(glsl_type)
        value = None
        if type is Type.INT:
            value = tuple([1] * size)
        if type is Type.FLOAT:
            value = tuple([1.0] * size)
        if type is Type.BOOL:
            value = tuple([False] * size)
        if value and len(value) == 1:
            value = value[0]
        return Parameter(value, type, size)

class MaterialParameter(Parameter):
    def __init__(self, default_path, extension, filter=None):
        super().__init__(default_path, Type.MATERIAL, 1, filter)
        self.extension = extension

def gl_type_to_malt_type(gl_type):
    from Malt.GL import GL
    types = {
        'FLOAT' : Type.FLOAT,
        'DOUBLE' : Type.FLOAT,
        'INT' : Type.INT,
        'BOOL' : Type.BOOL,
        'SAMPLER_1D' : Type.GRADIENT,
        'SAMPLER' : Type.TEXTURE,
    }
    sizes = {
        'VEC2' : 2,
        'VEC3' : 3,
        'VEC4' : 4,
        'MAT2' : 4,
        'MAT3' : 9,
        'MAT4' : 16,
    }
    gl_name = GL.GL_ENUMS[gl_type]

    for type_name, type in types.items():
        if type_name in gl_name:
            for size_name, size in sizes.items():
                if size_name in gl_name:
                    return (type, size)
            return (type, 1)
    
    raise Exception(gl_name, ' Uniform type not supported')

def glsl_type_to_malt_type(glsl_type):
    types = {
        'float' : Type.FLOAT,
        'vec' : Type.FLOAT,
        'mat' : Type.FLOAT,
        'double' : Type.FLOAT,
        'd' : Type.FLOAT,
        'int' : Type.INT,
        'i' : Type.INT,
        'uint' : Type.INT,
        'u' : Type.INT,
        'bool' : Type.BOOL,
        'b' : Type.BOOL,
        'sampler1D' : Type.GRADIENT,
        'sampler2D' : Type.TEXTURE,
    }
    sizes = {
        'vec2' : 2,
        'vec3' : 3,
        'vec4' : 4,
        'mat2' : 4,
        'mat3' : 9,
        'mat4' : 16,
    }
    for type_name, type in types.items():
        if glsl_type.startswith(type_name):
            for size_name, size in sizes.items():
                if size_name in glsl_type:
                    return (type, size)
            return (type, 1)
    
    return None
  