# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pgChainage
                                 A QGIS plugin
 plugin for chainage linestrings of a table in PostgreSQL
                              -------------------
        begin                : 2018-01-10
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Christoph Jung
        email                : jagodki.cj@gmail.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from pgchainage_dialog import pgChainageDialog
import os.path
from qgis.gui import QgsMessageBar
from qgis.core import QgsMessageLog
# import own mdoules
from src.pgc_controller import PgcController


class pgChainage:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'pgChainage_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = pgChainageDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&pgChainage')
        self.controller = PgcController(self.iface)
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'pgChainage')
        self.toolbar.setObjectName(u'pgChainage')
        #connect signals and slots
        self.dlg.pushButton_connect_to_database.clicked.connect(self.connect_to_database)
        self.dlg.comboBox_schema.currentIndexChanged.connect(self.select_tables)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('pgChainage', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.
        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str
        :param text: Text that should be shown in menu items for this action.
        :type text: str
        :param callback: Function to be called when the action is triggered.
        :type callback: function
        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool
        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool
        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool
        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str
        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget
        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.
        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        #self.dlg = pgChainageDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToDatabaseMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/pgChainage/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'pgChainage'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(
                self.tr(u'&pgChainage'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
			try:
				#read the user input
				host = self.dlg.lineEdit_host.text()
				port = self.dlg.lineEdit_port.text()
				database = self.dlg.lineEdit_database.text()
				user = self.dlg.lineEdit_user.text()
				password = self.dlg.lineEdit_password.text()
				schema = self.dlg.comboBox_schema.currentText()
				table = self.dlg.comboBox_table.currentText()
				equidistance = self.dlg.lineEdit_equidistance.text()
				crs = self.dlg.lineEdit_crs.text()
				
				#start processing
				self.controller.start_chainage(schema, table, id_column, geom_column, equidistance, crs, self.dlg.progessBar, self.dlg.chechBox_create_new_layer.isChecked())
				self.iface.messageBar().pushMessage("Info", "Chainage finished ^o^", level=QgsMessageBar.INFO, duration=5)
			except:
				e = sys.exc_info()[0]
				self.iface.messageBar().pushMessage("Error", "A problem occured. Look into QGIS-log for further information.", level=QgsMessageBar.CRITICAL)
				QgsMessageLog.logMessage(traceback.print_exc(), level=QgsMessageLog.CRITICAL)
    
    def connect_to_database(self):
        try:
            self.controller.start_db_connection(self.dlg.lineEdit_host.text(), self.dlg.lineEdit_port.text(), self.dlg.lineEdit_database.text(), self.dlg.lineEdit_user.text(), self.dlg.lineEdit_password.text())
            self.controller.populate_schema_combo_box(self.dlg.comboBox_schema)
            self.comboBox_table.clear()
        except:
            e = sys.exc_info()[0]
            self.iface.messageBar().pushMessage("Error", "Not able to query the schemata from the database. Look into QGIS-log for further information.", level=QgsMessageBar.CRITICAL)
            QgsMessageLog.logMessage(traceback.print_exc(), level=QgsMessageLog.CRITICAL)
            QgsMessageLog.logMessage(traceback.print_exc(), level=QgsMessageLog.CRITICAL)
    
    def select_tables(self):
        try:
            self.controller.populate_table_combo_box(self.dlg.comboBox_table, self.dlg.comboBox_schema.currentText())
        except:
            e = sys.exc_info()[0]
            self.iface.messageBar().pushMessage("Error", "Not able to query the tables of the schema. Look into QGIS-log for further information.", level=QgsMessageBar.CRITICAL)
            QgsMessageLog.logMessage(traceback.print_exc(), level=QgsMessageLog.CRITICAL)

