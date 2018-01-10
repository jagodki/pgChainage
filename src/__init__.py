# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pgChainage
                                 A QGIS plugin
 plugin for chainage linestrings of a table in PostgreSQL
                             -------------------
        begin                : 2018-01-10
        copyright            : (C) 2018 by Christoph Jung
        email                : jagodki.cj@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load pgChainage class from file pgChainage.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .pgchainage import pgChainage
    return pgChainage(iface)
