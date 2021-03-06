# TRAKO

**Trako compresses DTI streamlines from .vtp to smaller .tko files!**

## Installation as PyPI package (recommended, preferably in a virtualenv)

`pip install trako`

## Usage
```
./trakofy -i DATA/example.vtp -o /tmp/test.tko
./untrakofy -i /tmp/test.tko -o /tmp/restored.vtp
./tkompare -a DATA/example.vtp -b /tmp/restored.vtp
```

Diffusion Tensor Imaging (DTI) allows to estimate the brain's white matter tracts. Fiber tracking methods then produce clusters of streamlines that are 3D fiber bundles. Each fiber in these bundles is a line with X,Y,Z coordinates (floats) but researchers may attach many different scalars to each coordinate (per-vertex). Each scalar can be of arbitrary dimension, size, and data type. Researchers may also attach many different property values to individual streamlines (per-fiber). Adding scalars and properties can result in large streamline files.

Trako is a new file format that stores streamlines and associated per-vertex and per-fiber data as glTF containers with compression. We use the Draco algorithm to compress X,Y,Z coordinates, scalars, and properties.

<table>
  <tr>
    <td><img src="https://github.com/haehn/TRAKO/blob/master/IPY/newplot(3).png?raw=true"></td>
    <td><img src="https://github.com/haehn/TRAKO/blob/master/IPY/newplot(4).png?raw=true"></td>
  </tr>
</table>

We compared Trako and common streamline file formats (VTK, TrackVis) on data of two subjects  with 800 fiber clusters each. The data includes multiple per-fiber and per-vertex scalar values. Trako yields an average compression ratio of 3.2 and reduces the data size from 2974 Megabytes to 941 Megabytes.

<table>
  <tr>
    <td><img src="https://github.com/haehn/TRAKO/blob/master/IPY/newplot(6).png?raw=true"></td>
    <td><img src="https://github.com/haehn/TRAKO/blob/master/IPY/newplot(5).png?raw=true"></td>
  </tr>
</table>

We also used Trako to compress a single whole brain tractography dataset with 153,537 streamlines. Trako reduces the data size from 543 Megabytes to 267 Megabytes (compression factor 2.02).

<table>
  <tr>
    <td><img src="https://github.com/haehn/TRAKO/blob/master/IPY/newplot(2).png?raw=true"></td>
    <td><img src="https://github.com/haehn/TRAKO/blob/master/IPY/newplot(1).png?raw=true"></td>
  </tr>
</table>

With default parameters, Trako uses lossy compression for position data and per-vertex/per-fiber scalar values with a mean relative loss of less than 0.0001 (besides RGB values as EmbeddingColor). We show the relative information loss for two subjects with 800 fiber clusters each on the left, and the relative information loss for a single whole brain tractography dataset on the right.

## Developer installation (comes with test data)

Please follow these steps with Miniconda or Anaconda installed:

```
# create environment
conda create --name TRAKO python=3.6
conda activate TRAKO

# get TRAKO
git clone git@github.com:haehn/TRAKO.git
cd TRAKO

python setup.py install
```
