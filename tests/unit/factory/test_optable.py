__author__ = "Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
import os
from nose.plugins.attrib import attr

from jnpr.junos import Device
from jnpr.junos.op.phyport import PhyPortStatsTable
from jnpr.junos.op.ethport import EthPortTable

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession

from mock import patch


@attr('unit')
class TestFactoryOpTable(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.ppt = PhyPortStatsTable(self.dev)

    @patch('jnpr.junos.Device.execute')
    def test_optable_get(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get()
        self.assertEqual(len(self.ppt), 2)

    @patch('jnpr.junos.Device.execute')
    def test_optable_get_key(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get('ge-0/0/0')
        self.assertEqual(self.ppt.GET_KEY, 'interface_name')

    def test_optable_local(self):
        fname = 'local-get-interface-information.xml'
        self.ppt._path = os.path.join(os.path.dirname(__file__),
                                      'rpc-reply', fname)
        self.ppt.get()
        self.assertEqual(len(self.ppt), 2)

    @patch('jnpr.junos.Device.execute')
    def test_optable_view_get(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get()
        v = self.ppt['ge-0/0/0']
        self.assertEqual(v['rx_packets'], 1207)

    @patch('jnpr.junos.Device.execute')
    def test_optable_view_get_astype_bool(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        et = EthPortTable(self.dev)
        et.get()
        v = et['ge-0/0/0']
        self.assertEqual(v['present'], True)

    @patch('jnpr.junos.Device.execute')
    def test_optable_view_get_astype_bool_regex(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.op.bfd import BfdSessionTable
        bfd = BfdSessionTable(self.dev)
        bfd.get()
        v = bfd['10.92.20.4']
        self.assertEqual(v['no_absorb'], True)

    @patch('jnpr.junos.Device.execute')
    def test_optable_view_get_unknown_field(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get()

        def bad(key):
            v = self.ppt['ge-0/0/0']
            return v[key]

        self.assertRaises(ValueError, bad, 'bunk')

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(foo, self.dev._conn.
                              _device_handler.transform_reply())\
            ._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            return self._read_file(args[0].tag + '.xml')
