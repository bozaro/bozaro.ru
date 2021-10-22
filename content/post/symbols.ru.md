---
date: 2015-06-23
title: Получение идентификатора файла для Symbol-сервера
slug: symbol-server
tags:
 - pdb
 - python
categories:
 - Libraries
menu: main
---
У Microsoft для создания груды файлов с отпладочной информацией есть утилита [symstore.exe](https://msdn.microsoft.com/en-us/library/windows/desktop/ms681417%28v=vs.85%29.aspx).

Эта утилита по сути копирует файлы из одного места в другое, при этом достаточно хитрым образом формирует путь к новому файлу.

Недавно со мной поделились алгоритмом формирования этого загадочного пути.
<!--more-->
```
#!/usr/bin/env python

import os
import sys
import mmap
import struct
import datetime

class DebugInfo(object):

    def __init__(self, fname):
        """
        08h   DWord   Time/Date Stamp
        50h   DWord   Image Size
        """
        pe_geader_sigbnature = '\x50\x45\x00\x00'
        rsds_signature = '\x52\x53\x44\x53'

        fd = None
        try:
            fd = open(fname, 'rb')
            fileno = fd.fileno()
            data = mmap.mmap(fileno, 0, access=mmap.ACCESS_READ)
        finally:
            if fd:
                fd.close()
        pe_header_offset = data.find(pe_geader_sigbnature)
        if pe_header_offset == -1:
            raise ValueError("Could not locate PE signature")
        (_, timestamp, _, image_size) = struct.unpack('<8sL68sL', str(data[pe_header_offset:pe_header_offset + 84]))
        self.timestamp = datetime.datetime.fromtimestamp(timestamp)
        self.name = os.path.basename(fname)
        self.code_id = "%X%x" % (timestamp, image_size)

        self.debug_id = None
        rsds_offset = data.find(rsds_signature)
        if rsds_offset != -1:
            (_, pdb_guid, age) = struct.unpack('<L16sL', str(data[rsds_offset:rsds_offset + 24]))
            guid = struct.unpack('<LHH' + ('c' * 8), pdb_guid)
            self.debug_id = "%08X%04X%04X%02X%02X%02X%02X%02X%02X%02X%02X%d" % \
                            tuple(list(guid[:3]) + map(ord, guid[3:]) + [age])

        if self.debug_id:
            name = os.path.splitext(self.name)[0]
            self.symstorage_path = os.sep.join([name + '.pdb', self.debug_id, name + '.sym'])
        else:
            self.symstorage_path = None

    def __str__(self):
        return self.code_id

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    info = DebugInfo(sys.argv[1])
    print ("code_id: %s" % info.code_id)
    print ("debug_id: %s" % info.debug_id)
```
