import time
import serial
from serial.tools.list_ports import comports

def make_checksum(source: bytes, fixed_value: int = 0xA001) -> str:
    '''Makes crc-16 modbus checksums for communication

    This is for internal use. In normal operation, this shouldn't need to be
    accessed

    Args:
        source: ASCII encoded byte string to checksum
        fixed_value: preset fixed value used in checksum calculation
    '''
    crc = 0xffff
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


class SumitomoF70:
    '''Sumitomo (SHI) F70 Helium Compressor Serial Communication Utils

    Args:
        com_port: The port of the helium compressor
        connection: **FOR DEBUGGING** Pass a pre-made serial connection here

    Raises:
        ValueError: if no com port or connection is passed
        ConnectionError: If no device can be found on the given com port
    '''

    def __init__(self, com_port: str, connection=None, **kwargs):
        self.com_port = com_port

        if connection is None and com_port is None:
            raise ValueError('Either port or serial connection must be passed')

        if connection is not None:
            self.connection = connection
            return

        if com_port is not None:
            if com_port in [ port.device for port in comports() ]:
                self.connection = serial.Serial(com_port, **kwargs)
                self.connection.reset_output_buffer()
                self.connection.reset_input_buffer()
            else:
                raise ConnectionError('No device matching {} found'.format(com_port))

    def __enter__(self):
        return self

    def __exit__(self, _type, value, traceback):
        if self.connection.is_open:
            self.connection.close()

    def send_command(self, command:str) -> None:
        '''Writes command to F70 (it doesn't read)'''
        checksum = make_checksum(bytes(command, 'ascii'))
        command += checksum

        self.connection.write(command.encode('ascii') + b'\r')

    def send_query(self, query:str) -> str:
        '''Writes a query to F70 and reads response

        Returns:
            A string of the raw response from the F70
        '''
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

    def read_all_temperatures(self) -> tuple[int]:
        '''Reads all temperature values (in degrees C)

        Returns:
            tuple of values (T1, T2, T3, T4)
        '''
        response = self.send_query('$TEA')
        response = response.split(',')[1:5]
        return tuple([int(temp) for temp in response])

    def read_temperature(self, n) -> float:
        '''Read temperature from a specific sensor (in degrees C)

        Args:
            n: The index of the temperature sensor to read

        Returns:
            float of reading
        '''
        response = self.send_query('$TE' + str(n))
        reading = response.split(',')[1]
        return float(reading)

    def read_all_pressures(self) -> tuple[int]:
        '''Read pressure values from all sensors (in PSIG)

        Returns:
            tuple (P1, P2)
        '''
        response = self.send_query('$PRA')
        response = response.split(',')[1:3]
        return tuple([int(pres) for pres in response])

    def read_pressure(self, n) -> int:
        '''Read pressure value from a specific sensor (in PSIG)
        
        Args:
            n: The index of the pressure sensor to read

        Returns:
            Pressure at the sensor (int)
        '''
        response = self.send_query('$PR' + str(n))
        response = response.split(',')[1]
        return int(response)

    def read_status_bits(self) -> tuple[int, dict]:
        '''Read status bits and alarm states (See user manual)

        Returns:
            A tuple containing (raw status bits, dict of status)

            The dict of status pulls out the information in the status bits

            {'configuration': int,
             'solenoid': bool,
             'pressure_alarm': bool,
             'oil_level_alarm': bool,
             'water_flow_alarm': bool,
             'water_temperature_alarm': bool,
             'helium_temperature_alarm': bool,
             'phase_sequence_alarm': bool,
             'motor_temperature_alarm': bool,
             'system': bool,
             'state': str,
             'state_number': int}

             All of the boolean dict values correspond to the value of their 
             bit

             'state' parameter is the witten state of the machine 
             (one of 'local off', 'local on', 'remote off', etc)
        '''
        response = self.send_query('$STA')
        response = response.split(',')[1]
        bits = int(response, 16)

        status = {
                'configuration': 2 if (bits & 0x8000) else 1,
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

        return bits, status

    def read_id(self) -> dict:
        '''Returns the version and elapsed operating hours in a dictionary
        
        Returns:
            A dict with the version and operating hours

            {'version': str,
             'operating_hours': float}
        '''
        response = self.send_query('$ID1')
        response = response.split(',')[1:3]
        return {'version':response[0], 'operating_hours':float(response[1])}

    def set_on(self) -> None:
        '''Turns on the compressor and the cold head'''
        self.send_command('$ON1')

    def set_off(self) -> None:
        '''Turns off compressor and/or cold head if one or both are on'''
        self.send_command('$OFF')

    def reset(self) -> None:
        '''Clears fault status from status response'''
        self.send_command('$RS1')

    def set_cold_head_run(self) -> None:
        '''Turns on the cold head if the compressor is off

        It will disable the cold head after 30 minutes if no other command is 
        recieved.
        '''
        self.send_command('$CHR')

    def set_cold_head_pause(self) -> None:
        '''Turns off only the cold head'''
        self.send_command('$CHP')

    def set_cold_head_unpause(self) -> None:
        '''Turns on the cold head when the compressor is on'''
        self.send_command('$POF')
