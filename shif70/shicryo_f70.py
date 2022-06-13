import time
import serial
from serial.tools.list_ports import comports
import numpy as np

class F70Exception(Exception):
    pass

def make_checksum(source: bytes, fixed_value: hex = 0xA001) -> str:
    '''Makes crc-16 modbus checksums for communication'''
    crc = np.uint16(0xffff)
    for _char in source:
        crc ^= _char
        for _ in range(8):
            if crc & 0x0001:
                crc = crc >> 1
                crc ^= fixed_value
            else:
                crc = crc >> 1
    crc_str = hex(crc).upper()[2:]
    crc_str = '0000'[len(crc_str):] + crc_str
    return crc_str


class SHICryoF70:
    def __init__(self, com_port, connection=None, **kwargs):
        self.com_port = com_port
        self.connection = connection

        if connection is None and com_port is None:
            raise TypeError('Either port or serial connection must be passed')

        if com_port is not None:
            for port in comports():
                if com_port == port.device:
                    self.connection = serial.Serial(port.device, **kwargs)
                    self.connection.reset_output_buffer()
                    self.connection.reset_input_buffer()
                    break
            else:
                raise F70Exception(f'No device matching {com_port} found')

    def __enter__(self):
        return self

    def __exit__(self, _type, value, traceback):
        if self.connection.is_open:
            self.connection.close()

    def send_command(self, command:str):
        checksum = make_checksum(bytes(command, 'ascii'))
        command += checksum

        self.connection.write(command.encode('ascii') + b'\r')

    def send_query(self, query:str):
        self.send_command(query)

        response = ''
        while True:
            if self.connection.in_waiting > 0:
                response += self.connection.read(\
                                self.connection.in_waiting).decode('ascii')
                if response[-1] == '\r':
                    break
            time.sleep(0.01)
        return response[:-5].strip()

    def read_all_temperatures(self):
        '''Returns the temperatures values (T1, T2, T3, T4) in degrees C'''
        response = self.send_query('$TEA')
        response = response.split(',')[1:5]
        return tuple([int(temp) for temp in response])

    def read_temperature(self, n):
        '''Returns selected temperature in degrees C'''
        response = self.send_query('$TE' + str(n))
        reading = response.split(',')[1]
        return float(reading)

    def read_all_pressures(self):
        '''Returns pressure values for (P1, P2) in PSIG'''
        response = self.send_query('$PRA')
        response = response.split(',')[1:3]
        return tuple([int(pres) for pres in response])

    def read_pressure(self, n):
        '''Returns pressure values for Pn in PSIG'''
        response = self.send_query('$PR' + str(n))
        response = response.split(',')[1]
        return int(response)

    def read_status_bits(self):
        '''
        Returns status bit and dictionary containing possible alarm states
            (See user manual)
        '''
        response = self.send_query('$STA')
        response = response.split(',')[1]
        bits = int(response, 16)

        status = {
                'status_bits':bits,
                'configuration': 2 if bits & 0x8000 else 1,
                'solenoid':bool(bits & 0x100),
                'pressure_alarm':bool(bits & 0x80),
                'oil_level_alarm':bool(bits & 0x40),
                'water_flow_alarm':bool(bits & 0x20),
                'water_temperature_alarm':bool(bits & 0x10),
                'helium_temperature_alarm':bool(bits & 8),
                'phase_sequence_alarm':bool(bits & 4),
                'motor_temperature_alarm':bool(bits & 2),
                'system':bool(bits & 1)
        }

        state_number = (bits & 0x0E00) >> 9
        state_lookup = ['local off', 'local on', 'remote off', 'remote on',
            'cold head run', 'cold head pause', 'fault off', 'oil fault off']
        status['state'] = state_lookup[state_number]
        status['state_number'] = state_number

        return status

    def read_id(self):
        '''Returns the version and elapsed operating hours in a dictionary'''
        response = self.send_query('$ID1')
        response = response.split(',')[1:3]
        return {'version':response[0], 'operating_hours':float(response[1])}

    def set_on(self):
        '''Turns on the compressor and the cold head'''
        self.send_command('$ON1')

    def set_off(self):
        '''Turns off compressor and/or cold head if one or both are on'''
        self.send_command('$OFF')

    def reset(self):
        '''Clears fault status from status response'''
        self.send_command('$RS1')

    def set_cold_head_run(self):
        '''
        Turns on the cold head if the compressor is off
            It will disable the cold head after 30 minutes if no other command
            is recieved.
        '''
        self.send_command('$CHR')

    def set_cold_head_pause(self):
        '''Turns off only the cold head'''
        self.send_command('$CHP')

    def set_cold_head_unpause(self):
        '''Turns on the cold head when the compressor is on'''
        self.send_command('$POF')
