import pygltflib
from pygltflib import *

import DracoPy

import vtk
from vtk.util import numpy_support

import numpy as np

import collections


#
#
# MAP VTK DATATYPE TO GLTF COMPONENT TYPE
#
#
vtkDataType_to_gltfComponentType = {

  vtk.VTK_CHAR: pygltflib.BYTE,
  vtk.VTK_UNSIGNED_CHAR: pygltflib.UNSIGNED_BYTE,
  vtk.VTK_SHORT: pygltflib.SHORT,
  vtk.VTK_UNSIGNED_SHORT: pygltflib.UNSIGNED_SHORT,
  vtk.VTK_INT: pygltflib.UNSIGNED_INT,
  vtk.VTK_UNSIGNED_INT: pygltflib.UNSIGNED_INT,
  vtk.VTK_FLOAT: pygltflib.FLOAT

}

#
#
# MAP VTK NUMBEROFCOMPONENTS TO GLTF TYPE
#
#
vtkNumberOfComponents_to_gltfType = {
  
  1: pygltflib.SCALAR,
  2: pygltflib.VEC2,
  3: pygltflib.VEC3,
  4: pygltflib.VEC4
  # TODO MAT2, MAT3, MAT4

}



def convert(input, output=None):

  r = vtk.vtkXMLPolyDataReader()
  r.SetFileName(input)
  r.Update()
  polydata = r.GetOutput()

  points = numpy_support.vtk_to_numpy(polydata.GetPoints().GetData())
  lines = numpy_support.vtk_to_numpy(polydata.GetLines().GetData())
  number_of_streamlines = polydata.GetLines().GetNumberOfCells()

  #
  # scalars are per point
  #
  pointdata = polydata.GetPointData()
  number_of_scalars = pointdata.GetNumberOfArrays()
  scalars = []#np.zeros((points.shape[0], number_of_scalars))
  scalar_types = []
  scalar_names = []

  for i in range(number_of_scalars):
      arr_name = pointdata.GetArrayName(i)
      scalar_names.append(str(arr_name))
      arr = pointdata.GetArray(i)

      number_of_components = arr.GetNumberOfComponents()
      data_type = arr.GetDataType()

      scalar_types.append((data_type, number_of_components))

      print('Loading per vertex data', arr_name)
      # scalars[:, i] = numpy_support.vtk_to_numpy(arr)
      scalars.append(numpy_support.vtk_to_numpy(arr))


  #
  # convert to streamlines
  #
  ordered_indices = []
  ordered_scalars = []
  i = 0
  current_fiber_id = 0
  line_length = lines[i]
  line_index = 0

  while (line_index<number_of_streamlines):

      current_line = lines[i+1+line_index:i+1+line_length+line_index]
      current_indices = []

      # print('line',line_index)
      for k in range(len(current_line)-1):

          indexA = current_line[k]
          indexB = current_line[k+1]
      
          # print(indexA, indexB)
          current_indices.append(indexA)
          current_indices.append(indexB)
      
      ordered_indices += current_indices

      i += line_length
      line_index += 1
      if line_index < number_of_streamlines:
          line_length = lines[i+line_index]

  #
  # now, create fiber cluster data structure
  #
  fibercluster = {

    'number_of_streamlines': number_of_streamlines,
    'per_vertex_data': collections.OrderedDict(),
    'indices': ordered_indices

  }

  fibercluster['per_vertex_data']['POSITION'] = {
    'componentType': vtkDataType_to_gltfComponentType[polydata.GetPoints().GetDataType()],
    'type': vtkNumberOfComponents_to_gltfType[polydata.GetPoints().GetData().GetNumberOfComponents()],
    'data': points#ordered_vertices
  }

  for i,s in enumerate(scalar_names):

    vtkdatatype = scalar_types[i][0]
    vtknumberofcomponents = scalar_types[i][1]

    thisdata = scalars[i]#[]

    fibercluster['per_vertex_data'][s] = {
      'componentType': vtkDataType_to_gltfComponentType[vtkdatatype],
      'type': vtkNumberOfComponents_to_gltfType[vtknumberofcomponents],
      'data': thisdata
    }

  return fibercluster


def fibercluster2gltf(fibercluster, draco=False):

  gltf = GLTF2()
  scene = Scene()
  scene.nodes.append(0)
  gltf.scene = 0
  gltf.scenes.append(scene)

  # we need a bunch of buffers for all the attributes
  buffers = collections.OrderedDict()
  for attributename in fibercluster['per_vertex_data'].keys():
    buffers[attributename] = Buffer()

  # and of course a bunch of chunkers per attribute
  chunkers = collections.OrderedDict()
  for attributename in fibercluster['per_vertex_data'].keys():
    chunkers[attributename] = b""

  # and a bunch of bufferviews
  bufferviews = []
  # and a bunch of accessors
  accessors = []

  node = Node() # one fiber cluster has a node
  mesh = Mesh() # .. and a mesh
  node.mesh = 0

  custom_attributes = {}
  custom_attribute_index = 0
  for attributename in fibercluster['per_vertex_data'].keys():
    if attributename != 'POSITION':
      # this is custom
      attributename = '_'+attributename
    custom_attributes[attributename] = custom_attribute_index
    custom_attribute_index += 1

  primitive = Primitive()
  for attributeindex,attributename in enumerate(custom_attributes.keys()):
    # we need to update the indices increasingly
    # print('before', s, custom_attributes[attributename])
    custom_attributes[attributename] = attributeindex
    # print('after', custom_attributes[attributename])

  primitive.attributes = Attributes(**custom_attributes)
  primitive.mode = 1


  for attributeindex,attributename in enumerate(fibercluster['per_vertex_data'].keys()):

    # print('Parsing', attributename)

    componentType = fibercluster['per_vertex_data'][attributename]['componentType']
    aType = fibercluster['per_vertex_data'][attributename]['type']
    data = fibercluster['per_vertex_data'][attributename]['data']

    if componentType == pygltflib.FLOAT:
      asciiType = 'f'
    else:
      asciiType = 'f'
      print('Type not supported!')

    if draco:

      for index, values in enumerate(data):

        
        if not type(values) is np.ndarray:
          values = [values]

        if index == 0:
          # first loop run
          bounds = (list(values), list(values))
        else:
          for i,v in enumerate(values):       
            bounds[0][i] = min(float(bounds[0][i]), float(v))
            bounds[1][i] = max(float(bounds[1][i]), float(v))

      # compress the chunks
      position = False
      if (attributename == 'POSITION'):
        position = True

      chunk = DracoPy.encode_point_cloud_to_buffer(data.ravel(), position=position, sequential=True, 
        quantization_bits=14, create_metadata=True)

    else:

      #
      # create bytestream for buffer
      #
      chunk = b""
      bounds = (None, None) # min,max
      for index, values in enumerate(data):

        
        if not type(values) is np.ndarray:
          values = [values]

        if chunk == b"":
          # first loop run
          bounds = (list(values), list(values))
        else:
          for i,v in enumerate(values):       
            bounds[0][i] = min(float(bounds[0][i]), float(v))
            bounds[1][i] = max(float(bounds[1][i]), float(v))

        pack = "<" + (asciiType*len(values))

        subChunk = struct.pack(pack, *values)
        chunk += subChunk


    # each attribute has a bufferview for each streamline
    # and an accessor
    bufferview = BufferView()
    bufferview.target = ARRAY_BUFFER
    # print(buffers.keys())
    bufferview.buffer = attributeindex
    bufferview.byteOffset = 0#len(chunkers[attributename])##byteOffset 
    bufferview.byteLength = len(chunk) 
    bufferviews.append(bufferview)

    # print(len(chunkers[attributename]))

    chunkers[attributename] += chunk

    # byteOffset += len(chunk)


    accessor = Accessor()
    # print(accessor)
    accessor.bufferView = len(bufferviews)-1
    accessor.byteOffset = 0#byteOffset
    accessor.componentType = componentType
    accessor.count = len(data)
    accessor.type = aType
    accessor.min = list(bounds[0])
    accessor.max = list(bounds[1])
    accessors.append(accessor)

  # now indices
  indices = fibercluster['indices']

  if draco:

    for index, values in enumerate(indices):

      values = [values]

      if chunk == b"":
        # first loop run
        bounds = (list(values), list(values))
      else:
        for i,v in enumerate(values):       
          bounds[0][i] = min(int(bounds[0][i]), int(v))
          bounds[1][i] = max(int(bounds[1][i]), int(v))

    chunk = DracoPy.encode_point_cloud_to_buffer(indices, position=False, sequential=True, 
        quantization_bits=14, create_metadata=True)

  else:

    #
    # create bytestream for index buffer
    #
    chunk = b""
    bounds = (None, None) # min,max
    for index, values in enumerate(indices):

      values = [values]

      if chunk == b"":
        # first loop run
        bounds = (list(values), list(values))
      else:
        for i,v in enumerate(values):       
          bounds[0][i] = min(int(bounds[0][i]), int(v))
          bounds[1][i] = max(int(bounds[1][i]), int(v))

      pack = "<" + ('H'*len(values))

      subChunk = struct.pack(pack, *values)
      chunk += subChunk


  bufferview = BufferView()
  bufferview.target = ELEMENT_ARRAY_BUFFER
  bufferview.buffer = attributeindex+1 # this is last buffer
  bufferview.byteOffset = 0
  bufferview.byteLength = len(chunk)

  # print(len(chunk), len(indices))

  primitive.indices = len(accessors) # again, last one!

  accessor = Accessor()
  # print(accessor)
  accessor.bufferView = len(bufferviews) # the last buffer view
  accessor.byteOffset = 0#byteOffset
  accessor.componentType = UNSIGNED_SHORT
  accessor.count = len(indices)
  accessor.type = SCALAR
  accessor.min = list(bounds[0])
  accessor.max = list(bounds[1])


  # add this streamline to the mesh
  mesh.primitives.append(primitive)

  # now add the mesh to the scene
  gltf.meshes.append(mesh)
  gltf.nodes.append(node)

  # add the bufferviews and the accessors
  gltf.bufferViews += bufferviews + [bufferview]
  gltf.accessors += accessors + [accessor]

  #
  # store all buffer data base64-encoded
  #
  for attributename in fibercluster['per_vertex_data'].keys():

    buffer = buffers[attributename]
    chunker = chunkers[attributename]

    buffer.uri = pygltflib.DATA_URI_HEADER
    buffer.uri += str(base64.b64encode(chunker), "utf-8")
    buffer.byteLength = len(chunker)

    gltf.buffers.append(buffer)


  # and now for the indices
  indexbuffer = Buffer()
  indexbuffer.uri = pygltflib.DATA_URI_HEADER
  indexbuffer.uri += str(base64.b64encode(chunk), "utf-8")
  indexbuffer.byteLength = len(chunk)
  gltf.buffers.append(indexbuffer)

  return gltf




  for s in range(fibercluster['number_of_streamlines']):
    # print(s)
    # print('-'*8)
    primitive = Primitive()

    for attributeindex,attributename in enumerate(custom_attributes.keys()):
      # we need to update the indices increasingly
      # print('before', s, custom_attributes[attributename])
      custom_attributes[attributename] = (s*len(custom_attributes.keys())+attributeindex)
      # print('after', custom_attributes[attributename])

    primitive.attributes = Attributes(**custom_attributes)
    primitive.mode = 1 # LINES

    byteOffset = 0

    for attributeindex,attributename in enumerate(fibercluster['per_vertex_data'].keys()):

      # print('Parsing', attributename)

      componentType = fibercluster['per_vertex_data'][attributename]['componentType']
      aType = fibercluster['per_vertex_data'][attributename]['type']
      data_per_streamline = fibercluster['per_vertex_data'][attributename]['data'][s]

      if componentType == pygltflib.FLOAT:
        asciiType = 'f'
      else:
        asciiType = 'f'
        print('Type not supported!')

      #
      # create bytestream for buffer
      #
      chunk = b""
      bounds = (None, None) # min,max
      for index, values in enumerate(data_per_streamline):

        
        if not type(values) is np.ndarray:
          values = [values]

        if chunk == b"":
          # first loop run
          bounds = (list(values), list(values))
        else:
          for i,v in enumerate(values):       
            bounds[0][i] = min(float(bounds[0][i]), float(v))
            bounds[1][i] = max(float(bounds[1][i]), float(v))


        pack = "<" + (asciiType*len(values))

        subChunk = struct.pack(pack, *values)
        chunk += subChunk

      
      # print('added', attributename, chunkers[attributename])
      # print (len(data_per_streamline))

      # each attribute has a bufferview for each streamline
      # and an accessor
      bufferview = BufferView()
      bufferview.target = ARRAY_BUFFER
      # print(buffers.keys())
      bufferview.buffer = attributeindex
      bufferview.byteOffset = len(chunkers[attributename])##byteOffset 
      bufferview.byteLength = len(chunk) 
      bufferviews.append(bufferview)

      # print(len(chunkers[attributename]))

      chunkers[attributename] += chunk

      byteOffset += len(chunk)


      accessor = Accessor()
      # print(accessor)
      accessor.bufferView = len(bufferviews)-1
      accessor.byteOffset = 0#byteOffset
      accessor.componentType = componentType
      accessor.count = len(data_per_streamline)
      accessor.type = aType
      accessor.min = list(bounds[0])
      accessor.max = list(bounds[1])
      accessors.append(accessor)

    # add this streamline to the mesh
    mesh.primitives.append(primitive)

  # now add the mesh to the scene
  gltf.meshes.append(mesh)
  gltf.nodes.append(node)

  # add the bufferviews and the accessors
  gltf.bufferViews += bufferviews
  gltf.accessors += accessors

  #
  # store all buffer data base64-encoded
  #
  for attributename in fibercluster['per_vertex_data'].keys():

    buffer = buffers[attributename]
    chunker = chunkers[attributename]

    buffer.uri = pygltflib.DATA_URI_HEADER
    buffer.uri += str(base64.b64encode(chunker), "utf-8")
    buffer.byteLength = len(chunker)

    gltf.buffers.append(buffer)

  return gltf