#!/usr/bin/env python
# encoding: utf-8

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


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
            return cursor.fetchone()

