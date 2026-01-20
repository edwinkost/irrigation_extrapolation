
import pcraster as pcr
import virtualOS as vos

# clone map at 30sec resolution
clone_map = "/projects/0/dfguu/users/edwin/data/pcrglobwb_input_arise/develop/europe_30sec/cloneMaps/clonemaps_europe_countries/rhinemeuse/rhinemeuse_30sec.map"
pcr.setclone(clone_map)

# use directly the bounding box as the 'basin' map (area of interest) 
basin_map = pcr.spatial(pcr.nominal(1.0))

# percentange increse change
basin_annual_percent_change = 2.0
basin_maximum_percent_change = 40.

# cell area
cell_area_in_m2_file = "/projects/0/dfguu/users/edwin/data/pcrglobwb_input_arise/develop/global_30sec/routing/cell_area/cdo_grid_area_30sec_map_correct_lat.nc"
# - cell area in hectar
cell_area  = (1./(100.*100.)) * vos.netcdf2PCRobjCloneWithoutTime(ncFile  = cell_area_in_m2_file,\
                                                                  varName = "automatic", cloneMapFileName = clone_map, LatitudeLongitude = True, specificFillValue = None, absolutePath = None)

# original future irrigation area (based on PCR-GLOBWB aqueduct input files)
# ~ original_future_irrigation_area_file = "/home/jsteyaert1/rhine_30sec/ssp5_2015_2100/irrigated_area_30sec_hectar_meier_g_aei_ssp5_2015_2100_v20250310.nc"
original_future_irrigation_area_file = "/scratch-shared/edwin/irrigation_downscaling/rhine_30sec/ssp5_2015_2100/irrigated_area_30sec_hectar_meier_g_aei_ssp5_2015_2100_v20250310.nc"

# baseline irrigation area (hectar)
baseline_year = 2015
baseline_irrigation_area_file = original_future_irrigation_area_file
baseline_irrigation_area = vos.netcdf2PCRobjClone(ncFile = baseline_irrigation_area_file,\
                                                  varName = "automatic", dateInput = str(baseline_year)+"-01-01", useDoy = None, cloneMapFileName  = clone_map, LatitudeLongitude = True, specificFillValue = None)

# basin scale maximum irrigation area (hectar) 
basin_maximum_irr_area = pcr.areatotal(baseline_irrigation_area, basin_map) * (1. + basin_maximum_percent_change/100.)

for year in range(2016, 2100, 1):
    
    # calculate all (or most) of the following steps in hectare
    
    # get the previous year of irrigated area (hectare)
    if year == 2016:
        previous_year_irr_area = baseline_irrigation_area
    else:
        previous_year_irr_area = final_current_year_irr_area

    # get basin scale irrigation area (hectare) for this year
    basin_previous_year_irr_area = pcr.areatotal(previous_year_irr_area, basin_map)
    basin_irr_area = basin_previous_year_irr_area * (1. + basin_annual_percent_change/100.)
    # - limited by basin scale maximum irrigation area
    basin_irr_area = pcr.min(basin_maximum_irr_area, basin_irr_area) 

    # get basin scale irrigation area change/increase (hectare) 
    basin_irr_area_increase   = pcr.max(0.0, basin_irr_area - basin_previous_year_irr_area)
    # - in percentage
    basin_increase_in_percent = (basin_irr_area_increase / basin_previous_year_irr_area) * 100.
    
    # get the pixel scale estimate of increase based on the original future irrigation area (based on PCR-GLOBWB aqueduct input files)
    prev_year_estimate     = vos.netcdf2PCRobjClone(ncFile = original_future_irrigation_area_file,\
                                                    varName = "automatic", dateInput = str(year-1)+"-01-01", useDoy = None, cloneMapFileName = clone_map, LatitudeLongitude = True, specificFillValue = None) 
    current_year_estimate  = vos.netcdf2PCRobjClone(ncFile = original_future_irrigation_area_file,\
                                                    varName = "automatic", dateInput = str(year)+"-01-01", useDoy = None, cloneMapFileName = clone_map, LatitudeLongitude = True, specificFillValue = None)
    # - pixel scale estimate of increase (hectar), ignore any decrease
    delta_increase_estimate = pcr.max(0.0, current_year_estimate - prev_year_estimate)

    # set the minimum increase of every pixel according basin_increase_in_percent
    delta_increase = pcr.max(delta_increase_estimate, (basin_increase_in_percent/100.) * previous_year_irr_area) 
    # - correct/distribute the increase (hectare) in order to get the expected basin_irr_area_increase  
    basin_delta_increase = pcr.areatotal(delta_increase, basin_map)
    delta_increase = (delta_increase / basin_delta_increase) * (basin_increase_in_percent/100.) * basin_previous_year_irr_area

    # estimate the current irrigation area (hectare)
    estimate_current_year_irr_area =  previous_year_irr_area + delta_increase
    
    # constrained by cell area
    surplus_area, valid = pcr.cellvalue(pcr.mapmaximum(estimate_current_year_irr_area - cell_area), 1)
    print(float(surplus_area))
    while surplus_area > 0:

        # - limit the increase based on the cell area
        delta_increase = pcr.min(delta_increase, cell_area - previous_year_irr_area)
        
        basin_delta_increase = pcr.areatotal(delta_increase, basin_map)
        delta_increase = (delta_increase / basin_delta_increase) * (basin_increase_in_percent/100.) * basin_previous_year_irr_area
        
        estimate_current_year_irr_area = previous_year_irr_area + delta_increase
        surplus_area, valid = pcr.cellvalue(pcr.mapmaximum(estimate_current_year_irr_area - cell_area), 1)
        
        print(float(surplus_area))
    
    final_current_year_irr_area = estimate_current_year_irr_area
    
    # check 
    basin_final_current_year_irr_area = pcr.areatotal(final_current_year_irr_area, basin_map)
    check_basin_increase_in_percent, valid = pcr.cellvalue(pcr.mapmaximum((basin_final_current_year_irr_area - basin_previous_year_irr_area) / basin_previous_year_irr_area) * 100., 1)
    
    print(float(check_basin_increase_in_percent))
