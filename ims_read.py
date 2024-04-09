from tifffile import imwrite
import numpy as np
import h5py


class ims_read:
    def __init__(self,  filename):
        self.f = h5py.File(filename, 'r')
        self.info = {}
        self.n_surf = sum(name.startswith('MegaSurfaces') for name in self.f['Scene8/Content'])
        if self.n_surf > 0:
            self.surfs= {}
        self.n_pts = sum(name.startswith('Points') for name in self.f['Scene/Content'])
        if self.n_pts > 0:
            self.pts= {}
        self.data = {}
        
    def get_dataset_info(self):
        
        infopath = self.f['DataSetInfo']['Image'].attrs

        x_px = self.read_nums(infopath['X'], type='int')
        y_px = self.read_nums(infopath['Y'], type='int')
        z_px = self.read_nums(infopath['Z'], type='int')

        x_um = self.read_nums(infopath['ExtMax0'], type='float') - self.read_nums(infopath['ExtMin0'], type='float')
        y_um = self.read_nums(infopath['ExtMax1'], type='float') - self.read_nums(infopath['ExtMin1'], type='float')
        z_um = self.read_nums(infopath['ExtMax2'], type='float') - self.read_nums(infopath['ExtMin2'], type='float')

        unit = self.read_nums(infopath['Unit'])
        
        n_ch = sum(name.startswith('Channel ') for name in self.f['DataSetInfo'])
        
        self.info = {
            "x_px": x_px,
            "y_px": y_px,
            "z_px": z_px,
            "x_um": x_um,
            "y_um": y_um,
            "z_um": z_um,
            "x_res": x_um/x_px,
            "y_res": y_um/y_px,
            "z_res": z_um/z_px,
            "unit": unit,
            "n_ch": n_ch,
            "channels": {},
        }
        
        for ch in range(n_ch):
            self.info['channels'].update({ch: {
                "Name": self.read_nums(self.f['DataSetInfo']['Channel '+str(ch)].attrs['Name']),
                "Color": self.read_nums(self.f['DataSetInfo']['Channel '+str(ch)].attrs['Color']),
            }
                                         })    
        
    def get_surf_info(self, surf_int):
        assert surf_int < self.n_surf, "surf_int should be between 0 and "+str(self.n_surf-1)
        
        surf_creation = self.f['Scene8']['Content']['MegaSurfaces'+str(surf_int)]['CreationParameters'][0].decode('UTF-8')
        ch_idx_start = surf_creation.find('ChannelIndex=')
        ch_idx_start = surf_creation.find('"', ch_idx_start)+1
        ch_idx_end = surf_creation.find('"', ch_idx_start)

        ch_idx = surf_creation[ch_idx_start:ch_idx_end]
        
        surf_key = self.f['Scene8']['Content']['MegaSurfaces'+str(surf_int)]['SurfaceModelInfo']
        surf_info = {
            "x" : surf_key['CenterOfMassX'],
            "y" : surf_key['CenterOfMassY'],
            "z" : surf_key['CenterOfMassZ'],
            "dx" : surf_key['EllipsoidAxisLengthX'],
            "dy" : surf_key['EllipsoidAxisLengthY'],
            "dz" : surf_key['EllipsoidAxisLengthZ'],
            "ch" : int(ch_idx),   
        }
        self.surfs.update({surf_int: surf_info})
        
    def get_pt_info(self, pt_int):
        assert pt_int < self.n_pts, "pt_int should be between 0 and "+str(self.n_pts-1)
        
        points_key = f'Scene/Content/Points{pt_int}'
            
        pt_info = {
            "XYZR" : self.f[f'{points_key}/CoordsXYZR'][()],
            "RadiusYZ": self.f[f'{points_key}/RadiusYZ'][()],
        }
        
        self.pts.update({pt_int: pt_info})
        
    def save_image_data(self, save_name, ext):
        assert len(self.info)>0, "need to run get_surf_info before save_image_data"
        
        base_key = 'DataSet/ResolutionLevel 0/TimePoint 0'
        
        im_data = np.zeros((self.info['n_ch'], 
                            self.info['z_px'], 
                            self.info['y_px'],
                            self.info['x_px']), dtype=self.f[base_key+'/Channel 0/Data'].dtype)
        
        for channel_idx in range(self.info['n_ch']):
            data_key = base_key+'/Channel '+str(channel_idx)+'/Data'
            data = self.f[data_key]
            
            tmp_shape = data.shape
            out_shape = (self.info['z_px'], self.info['y_px'], self.info['x_px'])

            if tmp_shape[0] > out_shape[0]:
                data = data[np.sum(np.sum(data, axis=2), axis=1)>0]
            if tmp_shape[1] > out_shape[1]:
                data = data[:,np.sum(np.sum(data, axis=2), axis=0)>0, :]    
            if tmp_shape[2] > out_shape[2]:
                data = data[:,:,np.sum(np.sum(data, axis=1), axis=0)>0]
            #im_data[channel_idx,:,:,:] = data
            save_path = save_name + "_ch"+ str(channel_idx)+ext
            if save_path.endswith(".tif"):    
                imwrite(save_path, data)
                
    def get_channel(self, channel_idx):
        assert len(self.info)>0, "need to run get_surf_info before get_image_data"
        assert channel_idx<self.info['n_ch'], "channel identifier must be less than "+str(self.info['n_ch'])
        
        base_key = 'DataSet/ResolutionLevel 0/TimePoint 0'
        im_data = np.zeros((self.info['z_px'], 
                            self.info['y_px'],
                            self.info['x_px']), dtype=self.f[base_key+'/Channel 0/Data'].dtype)
        
        data_key = base_key+'/Channel '+str(channel_idx)+'/Data'
        data = self.f[data_key]
        
        tmp_shape = data.shape
        out_shape = (self.info['z_px'], self.info['y_px'], self.info['x_px'])

        if tmp_shape[0] > out_shape[0]:
            data = data[np.sum(np.sum(data, axis=2), axis=1)>0]
        if tmp_shape[1] > out_shape[1]:
            data = data[:,np.sum(np.sum(data, axis=2), axis=0)>0, :]    
        if tmp_shape[2] > out_shape[2]:
            data = data[:,:,np.sum(np.sum(data, axis=1), axis=0)>0]

        self.data[channel_idx] = data
                
    def plot_surf_project(self, image_chan, surf_n, crop_area=None):
        import matplotlib.pyplot as plt
        base_key = 'DataSet/ResolutionLevel 0/TimePoint 0'
        data_key = base_key+'/Channel '+str(image_chan)+'/Data'
        data = self.f[data_key]

        tmp_shape = data.shape
        out_shape = (self.info['z_px'], self.info['y_px'], self.info['x_px'])

        if tmp_shape[0] > out_shape[0]:
            data = data[np.sum(np.sum(data, axis=2), axis=1)>0]
        if tmp_shape[1] > out_shape[1]:
            data = data[:,np.sum(np.sum(data, axis=2), axis=0)>0, :]
        if tmp_shape[2] > out_shape[2]:
            data = data[:,:,np.sum(np.sum(data, axis=1), axis=0)>0]

        plt.imshow(np.max(data, axis=0))

        plt.plot(self.surfs[surf_n]["x"]/self.info["x_res"], self.surfs[surf_n]["y"]/self.info["y_res"],".r")
        if crop_area is not None:
            plt.xlim(crop_area[0], crop_area[1])
            plt.ylim(crop_area[2], crop_area[3])
        #for i inprint(len(self.surfs[surf_n]["x"]))
    
    def read_nums(self, utf8array, type=None):
        n = ''.join([st.decode("utf-8") for st in utf8array])
        if type == 'float':
            n = float(n)
        elif type == 'int':
            n = int(n)
        return n


