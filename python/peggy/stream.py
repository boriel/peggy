#!/usr/bin/env python
# -*- coding: utf-8 -*-

BUFFSIZE = 1024

class Stream(object):
    ''' Uses a file like an array
    '''
    def __init__(self, filename):
        self.f = open(filename, 'rb')
        self.pos = 0
        self.f.seek(0, os.SEEK_END);
        self.length = self.f.tell()
        self.f.seek(0, os.SEEK_SET);
        self.buff = self.f.read(BUFFSIZE)

    def __len__(self):
        return self.length

    def __getitem__(self, s):
        if not isinstance(s, slice):
            s = slice(s, s + 1, 1)

        i, j, k = s.indices(self.length)
        if i < self.pos or i >= self.pos + BUFFSIZE:
            self.pos = i
            self.f.seek(i, os.SEEK_SET)
            self.buff = self.f.read(BUFFSIZE)

        return self.buff[i - self.pos:j - self.pos:k]

