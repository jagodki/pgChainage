import db
import time
from PyQt4.QtGui import QcomboBox, QProgressBar
from qgis.core import QgsVectorLayer, QgsDataSourceURI, QgsMapLayerRegistry

class PgcController:
	
	def __init__(self, gui):
		self.db = None
		self.gui = gui
	
	def start_db_connection(self, host, port, database, user, password):
		self.db = Db(host, port, user, password, database)
		self.db.start_connection(self.gui)
		self.db.close_connection()
	
	def populate_schema_combo_box(self, combo_box):
		self.db.start_connection(self.gui)
		combo_items[] = self.db.get_all_schemata()
		for combo_item in combo_items:
			combo_box.add_item(combo_item)
		self.db.close_connection()
	
	def populate_table_combo_box(self, combo_box, schema):
		self.db.start_connection(self.gui)
		combo_items[] = self.db.get_all_tables(schema)
		for combo_item in combo_items:
			combo_box.add_item(combo_item)
		self.db.close_connection()
	
	def start_chainage(schema, table, id_column, geom_column, equidistance, crs, pb, create_new_layer):
		#establishing a database connection
		self.db.start_connection(self.gui)
		
		#get the start time
		start_time = time.time()
		
		#define the names of the new schema and table
		chainage_schema = "chainage"
		chainage_table = table + "_chainage"
		
		#create the new schema and table
		self.db.create_target_schema_and_table(chainage_schema, chainage_table, schema, table, id_column, crs)
		
		#get IDs of all records in the source table and init the progressbar
		list_of_ids = self.db.get_all_ids(id_column, schema, table)
		pb.setMaximum(len(list_of_ids))
		pb.setValue(0)
		
		#now iterate over the IDs and create a chainage for every linestring
		for id in list_of_ids:
			self.db.chainage_line(schema, table, id_column, geom_column, chainage_schema, chainage_table, equidistance, crs)
			pb.setValue(pb.getValue() + 1)
		
		#close database connection
		self.db.close_connection()
		
		#load the new table into QGIS
		if create_new_layer is True:
			uri = QgsDataSourceURI()
			uri.setConnection(self.db.host, self.db.port, self.db.database, self.db.user, self.db.password)
			uri.setDataSource(chainage_schema, chainage_table, "geom")
			layer = QgsVectorLayer(uri.uri(False), chainage_table, "postgres")
			QgsMapLayerRegistry.instance().addMapLayer(layer)
		