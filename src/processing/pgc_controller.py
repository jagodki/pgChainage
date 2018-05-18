from . import db
from PyQt5.QtWidgets import QComboBox, QProgressBar, QApplication
#from qgis.core import QgsVectorLayer, QgsDataSourceURI, QgsMapLayerRegistry
from qgis import *

class PgcController:
    
    def __init__(self, gui):
        self.database = None
        self.gui = gui
    
    def start_db_connection(self, host, port, database, user, password):
        self.database = db.Db(host, port, user, password, database)
        self.database.start_connection(self.gui)
        self.database.close_connection()
    
    def populate_schema_combo_box(self, combo_box):
        self.database.start_connection(self.gui)
        combo_items = self.database.get_all_schemata()
        for combo_item in combo_items:
            combo_box.addItem(combo_item)
        self.database.close_connection()
    
    def populate_table_combo_box(self, combo_box, schema):
        self.database.start_connection(self.gui)
        combo_items = self.database.get_all_tables(schema)
        for combo_item in combo_items:
            combo_box.addItem(combo_item)
        self.database.close_connection()
    
    def start_chainage(self,
                       schema,
                       table,
                       id_column,
                       geom_column,
                       equidistance,
                       crs,
                       pb,
                       create_new_layer,
                       chainage,
                       substring,
                       end_geometries):
        #establishing a database connection
        self.database.start_connection(self.gui)
        
        #define the names of the new schema and table
        pgchainage_schema = "pgchainage"
        chainage_table = ""
        substring_table = ""
        if chainage:
          chainage_table = table + "_chainage"
        if substring:
            substring_table = table + "_substring"
        
        #create the new schema and table
        self.database.create_target_schema_and_table(pgchainage_schema, chainage_table, substring_table, schema, table, id_column, crs)

        #get IDs of all records in the source table and init the progressbar
        list_of_ids = self.database.get_all_ids(id_column, schema, table)

        if chainage and substring:
            pb.setMaximum(len(list_of_ids) * 2)
        elif chainage or substring:
            pb.setMaximum(len(list_of_ids))
            pb.setValue(0)
            QApplication.processEvents()
        
        #now iterate over the IDs and create a chainage and/or substring for every linestring
        if chainage:
            for id in list_of_ids:
                self.database.chainage_line(schema, table, id_column, id, geom_column, pgchainage_schema, chainage_table, equidistance, crs, end_geometries)
                pb.setValue(pb.value() + 1)
                QApplication.processEvents()
        if substring:
            for id in list_of_ids:
                self.database.substring_line(schema, table, id_column, id, geom_column, pgchainage_schema, substring_table, equidistance, crs, end_geometries)
                pb.setValue(pb.value() + 1)
                QApplication.processEvents()
        
        #close database connection
        self.database.close_connection()
        
        #load the new table(s) into QGIS
        if create_new_layer is True:
            uri = QgsDataSourceURI()
            uri.setConnection(self.database.host, self.database.port, self.database.database, self.database.user, self.database.password)
        if chainage:
            uri.setDataSource(pgchainage_schema, chainage_table, "geom")
            chainage_layer = QgsVectorLayer(uri.uri(False), chainage_table, "postgres")
            QgsMapLayerRegistry.instance().addMapLayer(chainage_layer)
        if substring:
            uri.setDataSource(pgchainage_schema, substring_table, "geom")
            substring_layer = QgsVectorLayer(uri.uri(False), substring_table, "postgres")
            QgsMapLayerRegistry.instance().addMapLayer(substring_layer)
