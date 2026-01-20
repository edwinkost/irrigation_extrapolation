
import netCDF4 as nc
import numpy as np
import pcraster as pcr

import virtualOS as vos

class WriteNC():
    
    def __init__(self, cloneMapFile, nc_attributes, nc_format):
        		
        # cloneMap
        # - the cloneMap must be at 5 arc min resolution
        cloneMap = pcr.readmap(cloneMapFile)
        cloneMap = pcr.boolean(1.0)
        
        # latitudes and longitudes
        self.latitudes  = np.unique(pcr.pcr2numpy(pcr.ycoordinate(cloneMap), vos.MV))[::-1]
        self.longitudes = np.unique(pcr.pcr2numpy(pcr.xcoordinate(cloneMap), vos.MV))

        # netCDF format and attributes:
        self.format = nc_format
        self.attributeDictionary = nc_attributes

    def createNetCDF(self, ncFileName, varName,varUnit):

        rootgrp= nc.Dataset(ncFileName, 'w', format = self.format)

        #-create dimensions - time is unlimited, others are fixed
        rootgrp.createDimension('time', None)
        rootgrp.createDimension('lat', len(self.latitudes))
        rootgrp.createDimension('lon', len(self.longitudes))

        date_time= rootgrp.createVariable('time', 'f4', ('time',))
        date_time.standard_name = 'time'
        date_time.long_name = 'Days since 1901-01-01'

        date_time.units = 'Days since 1901-01-01' 
        date_time.calendar = 'standard'

        lat= rootgrp.createVariable('lat','f4',('lat',))
        lat.long_name = 'latitude'
        lat.units = 'degrees_north'
        lat.standard_name = 'latitude'

        lon= rootgrp.createVariable('lon','f4',('lon',))
        lon.standard_name = 'longitude'
        lon.long_name = 'longitude'
        lon.units = 'degrees_east'

        lat[:]= self.latitudes
        lon[:]= self.longitudes

        shortVarName = varName
        var= rootgrp.createVariable(shortVarName,'f4', ('time','lat','lon',), fill_value = vos.MV, zlib = True)
        var.standard_name = shortVarName
        var.long_name = shortVarName
        var.units = varUnit

        attributeDictionary = self.attributeDictionary
        for k, v in attributeDictionary.items():
          setattr(rootgrp,k,v)

        rootgrp.sync()
        rootgrp.close()

    def writePCR2NetCDF(self,ncFileName,varName,varField,timeStamp,posCnt):

        #-write data to netCDF
        rootgrp= nc.Dataset(ncFileName,'a')    

        shortVarName = varName        

        date_time = rootgrp.variables['time']
        date_time[posCnt] = nc.date2num(timeStamp, date_time.units, date_time.calendar)

        rootgrp.variables[shortVarName][posCnt,:,:] = (varField)

        rootgrp.sync()
        rootgrp.close()
