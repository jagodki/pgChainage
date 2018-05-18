import psycopg2, sys, traceback
from qgis.gui import QgsMessageBar
from qgis.core import QgsMessageLog

class Db:
    
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cur = None
    
    def start_connection(self, gui):
        try:
            #define connection string
            conn_string = "host=" + self.host + " port=" + self.port + " dbname=" + self.database + " user=" + self.user + " password=" + self.password
            
            #create connection
            self.conn = psycopg2.connect(conn_string)
            self.conn.autocommit = True
            self.cur = self.conn.cursor()
            
            #display information to the user
            #gui.messageBar().pushMessage("Info", "Connection to database can be established.", level=Qgis.Info, duration = 5)
        except:
            gui.messageBar().pushMessage("Error", "Establishing a connection to the database with the given parameters failed.", level=Qgis.CRITICAL)
            QgsMessageLog.logMessage(traceback.format_exc(), level=Qgis.Critical)
    
    def close_connection(self):
        self.conn.close()
    
    def get_all_schemata(self):
        get_all_schemata_sql = "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name ASC;"
        self.cur.execute(get_all_schemata_sql)
        rows = self.cur.fetchall()
        all_schemata = self.get_query_result_of_first_column(rows)
        return all_schemata
    
    def get_all_tables(self, schema):
        get_all_tables_of_schema_sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = '" + schema + "' ORDER BY table_name ASC;"
        self.cur.execute(get_all_tables_of_schema_sql)
        rows = self.cur.fetchall()
        allTables = self.get_query_result_of_first_column(rows)
        return allTables
    
    def get_all_ids(self, id_column, schema, table):
        get_all_ids_sql = "SELECT " + id_column + " FROM " + schema + "." + table + ";"
        self.cur.execute(get_all_ids_sql)
        rows = self.cur.fetchall()
        all_ids = self.get_query_result_of_first_column(rows)
        return all_ids
    
    def get_query_result_of_first_column(self, rows):
        result_list = []
        for row in rows:
            result_list.append(row[0])
        return result_list
    
    def chainage_line(self, source_schema, source_table, id_column, id, geom_column, target_schema, target_table, equidistance, crs, end_point=False):
        chainage_sql = ("DO $chainage$\n" +
                        "DECLARE\n" +
                        "current_fractional double precision := 0.0;\n" +
                        "current_number_of_point integer := 1;\n" +
                        "i record;\n" +
                        "BEGIN\n" +
                        "FOR i IN SELECT " + id_column + " as id_column, st_transform(" + geom_column + ", " + crs + ") as geom, st_length(st_transform(" + geom_column + ", " + crs + ")) as line_length FROM " + source_schema + "." + source_table + " WHERE " + id_column + " = " + str(id) + " LOOP\n" +
                        "current_fractional := 0.0;\n" +
                        "WHILE current_fractional <= (1.0)::double precision LOOP\n" +
                        "INSERT INTO " + target_schema + "." + target_table + "(old_edge_id, geom, number_on_line)\n" +
                        "VALUES(i.id_column, ST_LineInterpolatePoint(i.geom, current_fractional), current_number_of_point);\n" +
                        "current_fractional := current_fractional + (" + str(equidistance) + " / i.line_length);\n" +
                        "current_number_of_point := current_number_of_point + 1;\n" +
                        "END LOOP;\n" +
                        "IF " + str(end_point) + " THEN\n" +
                        "INSERT INTO " + target_schema + "." + target_table + "(old_edge_id, geom, number_on_line)\n" +
                        "VALUES(i.id_column, ST_EndPoint(i.geom), current_number_of_point);\n" +
                        "END IF;\n" +
                        "END LOOP;\n" +
                        "END $chainage$")
        #print(chainage_sql)
        self.cur.execute(chainage_sql)
    
    def substring_line(self, source_schema, source_table, id_column, id, geom_column, target_schema, target_table, equidistance, crs, end_edge=False):
        chainage_sql = ("DO $split$\n" +
                        "DECLARE\n" +
                        "current_fractional double precision := 0.0;\n" +
                        "next_fractional double precision := 0.0;\n" +
                        "current_number_of_substring integer := 1;\n" +
                        "i record;\n" +
                        "BEGIN\n" +
                        "FOR i IN SELECT " + id_column + " as id_column, st_transform(" + geom_column + ", " + crs + ") as geom, st_length(st_transform(" + geom_column + ", " + crs + ")) as line_length FROM " + source_schema + "." + source_table + " WHERE " + id_column + " = " + str(id) + " LOOP\n" +
                        "current_fractional := 0.0;\n" +
                        "next_fractional := current_fractional + (" + str(equidistance) + " / i.line_length);\n" +
                        "WHILE next_fractional <= (1.0)::double precision LOOP\n" +
                        "INSERT INTO " + target_schema + "." + target_table + "(old_edge_id, geom, number_on_line)\n" +
                        "VALUES(i.id_column, ST_LineSubstring(i.geom, current_fractional, next_fractional), current_number_of_substring);\n" +
                        "current_fractional := next_fractional;\n" +
                        "next_fractional := current_fractional + (" + str(equidistance) + " / i.line_length);\n" +
                                    "current_number_of_substring := current_number_of_substring + 1;\n" +
                                    "END LOOP;\n" +
                        "IF " + str(end_edge) + " THEN\n" +
                        "INSERT INTO " + target_schema + "." + target_table + "(old_edge_id, geom, number_on_line)\n" +
                        "VALUES(i.id_column, ST_LineSubstring(i.geom, current_fractional, 1.0), current_number_of_substring);\n" +
                        "END IF;\n" +
                        "END LOOP;\n" +
                        "END $split$")
        #print(chainage_sql)
        self.cur.execute(chainage_sql)
    
    def create_target_schema_and_table(self, target_schema, target_point_table, target_line_table, source_schema, source_table, source_id_column, crs):
        #first create the new schema
        create_schema_sql = "CREATE SCHEMA IF NOT EXISTS " + target_schema + ";"
        self.cur.execute(create_schema_sql)
        
        #get the column type of the old id column
        get_column_type_sql = "SELECT data_type FROM information_schema.columns WHERE table_schema = '" +  source_schema + "' AND table_name = '" + source_table + "' AND column_name = '" + source_id_column + "';"
        self.cur.execute(get_column_type_sql)
        rows = self.cur.fetchall()
        data_type = rows[0][0]
        
        #now create new table(s)
        if target_point_table != "":
          create_table_sql = "CREATE TABLE IF NOT EXISTS " + target_schema + "." + target_point_table + "(id serial PRIMARY KEY, old_edge_id " + data_type + ", number_on_line integer);"
          self.cur.execute(create_table_sql)
        if target_line_table != "":
          create_table_sql = "CREATE TABLE IF NOT EXISTS " + target_schema + "." + target_line_table + "(id serial PRIMARY KEY, old_edge_id " + data_type + ", number_on_line integer);"
          self.cur.execute(create_table_sql)
        
            #add a geometry column to table(s)
        if target_point_table != "":
          add_geometry_column_sql = "SELECT addGeometryColumn('" + target_schema + "', '" + target_point_table + "', 'geom', " + crs + ", 'POINT', 2);"
          self.cur.execute(add_geometry_column_sql)
        if target_line_table != "":
          add_geometry_column_sql = "SELECT addGeometryColumn('" + target_schema + "', '" + target_line_table + "', 'geom', " + crs + ", 'LINESTRING', 2);"
          self.cur.execute(add_geometry_column_sql)
