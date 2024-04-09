# ims_reader
reads image data, spot locations, and surface locations from imaris files

## Usage:
##### initialize object
filename = 'file.ims'
x = ims_read(filename)

##### read in image info from the ims file (dimensions, number of channels, pixel size, ...) 
x.get_dataset_info()

##### read surface area for all surfaces (or certain surfaces of interest):
for i in range(x.n_surf):
  x.get_surf_info(i) 

##### read spot area for all spots objects (or certain spot objects of interest):
for i in range(x.n_pts):
  x.get_pt_info(i)   

##### save out image data:
x.save_image_data('filename', '.tif') # Each channel will be saved as filename_ch[0, 1, ...].tif

##### take note of which image channel was used to generate a surface:
surf_n = 1
image_chan = x.surfs[surf_n]["ch"] 

##### pull image data from a specific channel 
x.get_channel(image_chan) #(will be stored in x.data[n])

##### plot surface centers:
x.plot_surf_project(image_chan, surf_n, crop_area=None) # plot surface centers over a projection of an image channel, eg:
x.plot_surf_project(image_chan, surf_n, crop_area=[750,1000,600,900])

![image](https://github.com/caylamiller/ims_reader/assets/26422897/27555890-1321-4681-a716-fd99bb69a323)

## Notes on functionality:
Here, we are mostly reading in the surface centroids since we are interested in small objects, so this will not read out whole surface information (full surface shape)
