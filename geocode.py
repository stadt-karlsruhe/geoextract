#!/usr/bin/env python
# encoding: utf-8

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io


class AddressLocator(object):

    def __init__(self, db):
        self.db = db

    def locate(self, road, number):
        with self.db.cursor() as cursor:
            sql = '''
                SELECT `latitude`, `longitude`
                FROM `anwesen`
                WHERE `strasse`=%s AND `hausnr`=%s
                '''
            cursor.execute(sql, (road, number))
            result = cursor.fetchone()
            if not result:
                return
            lat, lon = result
            if lat == 0 and lon == 0:
                return None
            if lat < lon:
                # One some entries, the coordinates are mixed up
                lat, lon = lon, lat
            return lat, lon

