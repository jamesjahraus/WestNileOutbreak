"""GIS 305 - Lab 1, West Nile Outbreak.

Alphabetical list of ArcPy functions:
https://pro.arcgis.com/en/pro-app/arcpy/functions/alphabetical-list-of-arcpy-functions.htm
"""

import arcpy
import os
import sys
import time
import logging

logger = logging.getLogger(__name__)


def setup_logging(level='INFO'):
    r"""Configures the logger Level.
    Arguments:
        level: CRITICAL -> ERROR -> WARNING -> INFO -> DEBUG.
    Side effect:
        The minimum logging level is set.
    """
    ll = logging.getLevelName(level)
    logger = logging.getLogger()
    logger.handlers.clear()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(name)-12s %(levelname)-8s"
        "{'file': %(filename)s 'function': %(funcName)s 'line': %(lineno)s}\n"
        "message: %(message)s\n")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(ll)


def pwd():
    wd = sys.path[0]
    logger.info('wd: {0}'.format(wd))
    return wd


def ls_fc():
    featureclasses = arcpy.ListFeatureClasses()
    logger.info('featureclasses: {0}'.format(featureclasses))
    return featureclasses


def output_name(input_name, suffix):
    output_name = '{0}{1}'.format(input_name, suffix)
    logger.info('output_name: {0}'.format(output_name))
    return output_name


def set_path(wd, data_path):
    path_name = os.path.join(wd, data_path)
    logger.info('path_name: {0}'.format(path_name))
    return path_name


def import_spatial_reference(dataset):
    spatial_reference = arcpy.Describe(dataset).SpatialReference
    logger.info('spatial_reference: {0}'.format(spatial_reference.name))
    return spatial_reference


def setup_env(workspace_path, spatial_ref_dataset):
    # Set workspace path.
    arcpy.env.workspace = workspace_path
    logger.info('workspace(s): {}'.format(arcpy.env.workspace))

    # Set output overwrite option.
    arcpy.env.overwriteOutput = True
    logger.info('overwriteOutput: {}'.format(arcpy.env.overwriteOutput))

    # Set the output spatial reference.
    arcpy.env.outputCoordinateSystem = import_spatial_reference(
        spatial_ref_dataset)
    logger.info('outputCoordinateSystem: {}'.format(
        arcpy.env.outputCoordinateSystem.name))


def check_status(result):
    r"""Function summary.
    Description sentence(s).
    Understanding message types and severity:
    https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/message-types-and-severity.htm
    Arguments:
        arg 1: Description sentence.
        arg 2: Description sentence.
    Returns:
        Description sentence.
    Raises:
        Description sentence.
    """
    status_code = dict([(0, 'New'), (1, 'Submitted'), (2, 'Waiting'),
                        (3, 'Executing'), (4, 'Succeeded'), (5, 'Failed'),
                        (6, 'Timed Out'), (7, 'Canceling'), (8, 'Canceled'),
                        (9, 'Deleting'), (10, 'Deleted')])

    logger.info('current job status: {0}-{1}'.format(
        result.status, status_code[result.status]))
    # Wait until the tool completes
    while result.status < 4:
        logger.info('current job status (in while loop): {0}-{1}'.format(
            result.status, status_code[result.status]))
        time.sleep(0.2)
    messages = result.getMessages()
    logger.info('job messages: {0}'.format(messages))
    return messages


def get_map(aprx, map_name):
    for mp in aprx.listMaps():
        if map_name == mp.name:
            logger.info('Map called {0} found'.format(mp.name))
            return mp
    raise ValueError('Map called {0} does not exist in current aprx {1}'.format(map_name, aprx.filePath))


def buffer(aprx_mp, input_fc, output_fc, lyr_name, buf_distance):
    r"""Run ArcGIS Pro tool Buffer.
    https://pro.arcgis.com/en/pro-app/latest/tool-reference/analysis/buffer.htm

    Arguments:
        aprx_mp: mp object from aprx.listMaps()
        input_fc: Required feature class to buffer.
        output_fc: Output buffered feature class.
        lyr_name: name of layer for the map
        buf_distance: Distance to buffer the feature class.
    Returns:
        arcpy tool result object
    Raises:
        N/A
    """
    for lyr in aprx_mp.listLayers():
        logger.debug(lyr.name)
        if lyr.name == lyr_name:
            logger.info('layer {0} already exists, deleting {0} ...'.format(lyr_name))
            aprx_mp.removeLayer(lyr)
            break
    for lyr in aprx_mp.listLayers():
        print(lyr.name)
    buf = arcpy.Buffer_analysis(input_fc, output_fc, buf_distance, "FULL",
                                "ROUND", "ALL")
    check_status(buf)
    logger.debug(type(aprx_mp))
    logger.debug(output_fc)
    lyr = arcpy.MakeFeatureLayer_management(output_fc, lyr_name)
    logger.debug(type(lyr))
    logger.debug(type(lyr[0]))
    aprx_mp.addLayer(lyr[0], 'TOP')


def intersect(aprx_mp, fc_list, output_fc, lyr_name):
    r"""Run ArcGIS Pro tool Intersect.
    https://pro.arcgis.com/en/pro-app/latest/tool-reference/analysis/intersect.htm

    Arguments:
        fc_list: List of feature classes to run Intersect Analysis on.
        output_fc: Output intersect feature class.
    Returns:
        arcpy tool result object
    Raises:
        N/A
    """
    for lyr in aprx_mp.listLayers():
        logger.debug(lyr.name)
        if lyr.name == lyr_name:
            logger.info('layer {0} already exists, deleting {0} ...'.format(lyr_name))
            aprx_mp.removeLayer(lyr)
            break
    for lyr in aprx_mp.listLayers():
        print(lyr.name)
    inter = arcpy.Intersect_analysis(fc_list, output_fc, "ALL")
    check_status(inter)
    lyr = arcpy.MakeFeatureLayer_management(output_fc, lyr_name)
    aprx_mp.addLayer(lyr[0], 'TOP')


def run_model(spatial_ref_dataset, ll='INFO'):
    r"""Environment setup and orchestration.
    Assumes that this module is in the ArcGIS Pro project directory.
    pwd() will capture the path of the ArcGIS Pro project directory.

    Uses ArcGIS Pro tools Intersect and Buffer.
    https://pro.arcgis.com/en/pro-app/latest/tool-reference/analysis/buffer.htm
    https://pro.arcgis.com/en/pro-app/latest/tool-reference/analysis/intersect.htm

    Arguments:
        spatial_ref_dataset: Sets the output spatial reference to match input dataset (assumes it exist).
        ll: Sets the log level: CRITICAL -> ERROR -> WARNING -> INFO -> DEBUG.
        intersect_fc_name: Name of the output feature class for Intersect Analysis.
    """
    setup_logging(ll)
    # Assumes that this module is in the ArcGIS Pro project directory.
    # pwd() should be the
    wd = pwd()
    input_db = set_path(wd, 'WestNileOutbreak.gdb')
    output_db = set_path(wd, 'WestNileOutbreak_Outputs.gdb')
    logger.info('output db: {0}'.format(output_db))
    setup_env(input_db, spatial_ref_dataset)
    aprx = arcpy.mp.ArcGISProject(r'{0}\{1}'.format(wd, 'WestNileOutbreak.aprx'))
    logger.info('aprx path: {0}'.format(aprx.filePath))
    mp = get_map(aprx, 'Map')
    logger.debug(type(mp))

    # # Buffer Analysis
    buf_fc_list = ['Mosquito_Larval_Sites', 'Wetlands_Regulatory', 'Lakes_and_Reservoirs', 'OSMP_Properties']
    for fc in buf_fc_list:
        print(fc)
        print(r'Input buffer distance for {0} (i.e. 2500 Feet):'.format(fc))
        buf_distance = input()
        logger.debug(type(buf_distance))
        input_fc_name = fc
        buf_fc_name = '{0}_buf'.format(fc)
        buf_fc = r'{0}\{1}'.format(output_db, buf_fc_name)
        buffer(mp, input_fc_name, buf_fc, buf_fc_name, buf_distance)
        for lyr in mp.listLayers():
            print(lyr.name)
        aprx.save()

    # Intersect Analysis
    # for loop is used to create intersect_fc_list for intersect function (including paths to output_db)
    intersect_fc_list = []
    for fn in buf_fc_list:
        intersect_fn = r'{0}\{1}_buf'.format(output_db, fn)
        intersect_fc_list.append(intersect_fn)
    print(r'Input fc name for Intersect Analysis (i.e. IntersectAnalysis):')
    intersect_fc_name = input()
    inter = r'{0}\{1}'.format(output_db, intersect_fc_name)
    intersect(mp, intersect_fc_list, inter, intersect_fc_name)
    for lyr in mp.listLayers():
        print(lyr.name)
    aprx.save()

    # Query by Location
    join_output_name = 'IntersectAnalysis_Join_BoulderAddresses'
    jofc = r'{0}\{1}'.format(output_db, join_output_name)
    sp = arcpy.SpatialJoin_analysis('Boulder_Addresses', inter, jofc, join_type="KEEP_COMMON", match_option="WITHIN")
    check_status(sp)

    # Record Count
    record_count = arcpy.GetCount_management(jofc)
    print('Boulder Addresses at-risk =  {0}'.format(record_count[0]))


if __name__ == '__main__':
    run_model('Boulder_Addresses')
