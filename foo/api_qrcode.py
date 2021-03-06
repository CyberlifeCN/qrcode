#!/usr/bin/env python
# _*_ coding: utf-8_*_
#
# Copyright 2016-2017 7x24hs.com
# thomas@7x24hs.com
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import tornado.web
import logging
import time
import sys
import os
import json as JSON # 启用别名，不会跟方法里的局部变量混淆

from comm import *
from global_const import *
from base_handler import *

from tornado.escape import json_encode, json_decode
from tornado.httpclient import *
from tornado.httputil import url_concat

from tornado_swagger import swagger
from qrcode import *


@swagger.model()
class QrcodeReq:
    def __init__(self, url, size=5):
        self.url = url
        self.size = size


# /qrcode/api/qrcode
class ApiQrcodeXHR(tornado.web.RequestHandler):
    @swagger.operation(nickname='post')
    def post(self):
        """
            @description: 生成二维码

            @param body:
            @type body: C{QrcodeReq}
            @in body: body
            @required body: True

            @rtype: L{Resp}
            @raise 400: Invalid Input
            @raise 500: Internal Server Error
        """
        logging.info("POST %r", self.request.uri)
        logging.debug("body %r", self.request.body)

        _url = None
        _size = 5
        try:
            data = json_decode(self.request.body)
            _url = data['url']
            if data.has_key("size"):
                _size = data['size']
        except:
            logging.warn("Bad Request[400]: generate qrcode req_body=[%r]", self.request.body)

            self.set_status(200) # Bad Request
            self.write(JSON.dumps({"errCode":400,"errMsg":"Bad Request"}))
            self.finish()
            return

        qr = QRCode(
            # version值为1~40的整数,控制二维码的大小,(最小值是1,是个12*12的矩阵)
            # 如果想让程序自动确定,将值设置为 None 并使用 fit 参数即可
            version=_size,
            # error_correction: 控制二维码的错误纠正功能,可取值下列4个常量
            #   ERROR_CORRECT_L: 大约7%或更少的错误能被纠正
            #   ERROR_CORRECT_M(默认): 大约15%或更少的错误能被纠正
            #   ERROR_CORRECT_Q: 大约25%或更少的错误能被纠正
            #   ERROR_CORRECT_H: 大约30%或更少的错误能被纠正
            error_correction=ERROR_CORRECT_L,
            # 控制二维码中每个小格子包含的像素数
            box_size=10,
            # 控制边框(二维码与图片边界的距离)包含的格子数(默认为4,是相关标准规定的最小值)
            border=4,
        )
        qr.add_data(_url)
        qr.make() # Generate the QRCode itself
        # im contains a PIL.Image.Image object
        img = qr.make_image()

        _id = generate_uuid_str()
        timestamp = current_timestamp()
        _datehour = timestamp_to_datehour(timestamp)
        path = cur_file_dir()
        logging.debug("got path %r", path)
        if not os.path.exists(path + "/static/qrcode/" + _datehour):
            os.makedirs(path + "/static/qrcode/" + _datehour)

        # To save it
        img.save(path + "/static/qrcode/" + _datehour + "/" + _id + '.png')     # Save file

        img_url = self.request.protocol + "://" + self.request.host
        img_url = img_url + '/static/qrcode/' + _datehour + "/" + _id + '.png'
        logging.info("Success[200]: generate qrcode from=[%r] img_url=[%r]", _url, img_url)
        self.set_status(200) # Success
        self.write(JSON.dumps({"errCode":200,"errMsg":"Success","rs":img_url}))
        self.finish()
