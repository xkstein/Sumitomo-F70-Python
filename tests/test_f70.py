from sumitomo_f70 import SumitomoF70
import unittest

class FakeConnection:
    def __init__(self):
        self.response = ''
        self.query = ''
    
    def set_response(self, msg):
        self.response = msg

    @property
    def in_waiting(self):
        return len(self.response)

    def read(self, n):
        return bytes(self.response, 'ascii')

    def write(self, msg):
        self.query = msg
    
    def reset_output_buffer(self):
        pass

    def rest_input_buffer(self):
        pass

class TestF70(unittest.TestCase):
    def setUp(self):
        self.fake_connection = FakeConnection()
        self.fake_connection.set_response('')
        self.compressor = SumitomoF70(com_port=None, connection=self.fake_connection)

    def test_read_all_temperatures(self):
        self.fake_connection.set_response('$TEA,086,040,031,000,3798\r')
        response = self.compressor.read_all_temperatures()
        self.assertEqual(response, (86, 40, 31, 0))
        self.assertEqual(self.fake_connection.query, b'$TEAA4B9\r')

    def test_read_temperature(self):
        self.fake_connection.set_response('$TE1,086,ADBC\r')
        response = self.compressor.read_temperature(1)
        self.assertEqual(response, 86)
        self.assertEqual(self.fake_connection.query, b'$TE140B8\r')

    def test_read_all_pressures(self):
        self.fake_connection.set_response('$PRA,079,000,0CEC\r')
        response = self.compressor.read_all_pressures()
        self.assertEqual(response, (79, 0))
        self.assertEqual(self.fake_connection.query, b'$PRA95F7\r')

    def test_read_pressure(self):
        self.fake_connection.set_response('$PR1,079,2EBD\r')
        response = self.compressor.read_pressure(1)
        self.assertEqual(response, 79)
        self.assertEqual(self.fake_connection.query, b'$PR171F6\r')

    def test_read_status_bit(self):
        self.fake_connection.set_response('$STA,0301,2ED1\r')
        _, response= self.compressor.read_status_bits()
        self.assertEqual(self.fake_connection.query, b'$STA3504\r')
        self.assertEqual(response['solenoid'], True)
        self.assertEqual(response['pressure_alarm'], False)
        self.assertEqual(response['oil_level_alarm'], False)
        self.assertEqual(response['water_flow_alarm'], False)
        self.assertEqual(response['water_temperature_alarm'], False)
        self.assertEqual(response['helium_temperature_alarm'], False)
        self.assertEqual(response['phase_sequence_alarm'], False)
        self.assertEqual(response['motor_temperature_alarm'], False)
        self.assertEqual(response['system'], True)
        self.assertEqual(response['state'], 'local on')

    def test_read_id(self):
        self.fake_connection.set_response('$ID1,1.6,005842.1,1E26\r')
        response = self.compressor.read_id()
        self.assertEqual(response, {'version':'1.6', 'operating_hours':5842.1})
        self.assertEqual(self.fake_connection.query, b'$ID1D629\r')

    def test_set_on(self):
        self.compressor.set_on()
        self.assertEqual(self.fake_connection.query, b'$ON177CF\r')

    def test_set_off(self):
        self.compressor.set_off()
        self.assertEqual(self.fake_connection.query, b'$OFF9188\r')

    def test_reset(self):
        self.compressor.reset()
        self.assertEqual(self.fake_connection.query, b'$RS12156\r')
        
    def test_cold_head_run(self):
        self.compressor.set_cold_head_run()
        self.assertEqual(self.fake_connection.query, b'$CHRFD4C\r')

    def test_cold_head_pause(self):
        self.compressor.set_cold_head_pause()
        self.assertEqual(self.fake_connection.query, b'$CHP3CCD\r')

    def test_cold_head_unpause(self):
        self.compressor.set_cold_head_unpause()
        self.assertEqual(self.fake_connection.query, b'$POF07BF\r')
