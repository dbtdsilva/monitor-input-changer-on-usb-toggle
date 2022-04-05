#!/usr/bin/env python3

"""
Show and adjust display parameters on a Dell U2713HM monitor

Requirements:
- mentioned monitor (27' should also work) with DDC/CI setting on
- Windows Vista+ (dxva2.dll)
- Python 3


Copyright (C) 2015  Diego Fernández Gosende <dfgosende@gmail.com>
Copyright (C) 2016  https://gist.github.com/Canule
Copyright (C) 2016  https://github.com/mchubby for Dell monitor

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along 
with this program.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.
"""


version = '0.1.0'


import ctypes
import ctypes.wintypes as wintypes


"""Capabilities string
prot(monitor)
type(lcd)
model(U2713HM)
cmds(01 02 03 07 0C E3 F3)
vcp(02 04 05 06 08 10 12 14(01 04 05 06 08 09 0B 0C) 16 18 1A 52
    60(01 03 04 0F) AC AE B2 B6 C6 C8 C9 D6(01 04 05) DC(00 02 03 05 )
    F0(00 01) DF FD E0 E1 E2(00 01 02 04 06 0B 0C 0D 0F 10 11 13 14) F1 F2)
mccs_ver(2.1)
mswhql(1))
"""

# Reference: VESA Monitor Control Command Set (MCCS)
# Standard PDF available after free registration
# at: http://www.vesa.org/vesa-standards/free-standards/

vcp_codes = {
    # ignore for scripting
    'New Control Value': 0x02, 
    
    # pass a non-zero value
    'Restore Factory Defaults': 0x04, 
    
    # pass a non-zero value
    'Restore Factory Luminance/ Contrast Defaults': 0x05, 
    
    # pass a non-zero value
    'Restore Factory Geometry Defaults': 0x06, 
    
    # pass a non-zero value, resets also luminance
    'Restore Factory Color Defaults': 0x08, 
    
    # 0-100, called 'brightness' on the OSD
    'Luminance': 0x10, 
    
    # 0-100
    'Contrast': 0x12, 
    
    # 0x01: sRGB
    # 0x04: 5000k
    # 0x05: 6500k
    # 0x06: 7500k
    # 0x08: 9300k
    # 0x09: 10000k
    # 0x0B: 5700k
    # 0x0C: user (Custom Color)
    'Select Color Preset': 0x14, 
    
    # 0-100, it also changes the preset to 'user'
    'Video Gain (Drive): Red': 0x16, 
    
    # 0-100, it also changes the preset to 'user'
    'Video Gain (Drive): Green': 0x18, 
    
    # 0-100, it also changes the preset to 'user'
    'Video Gain (Drive): Blue': 0x1A, 
    
    # ignore for scripting
    'Active Control': 0x52, 
    
    # 0x01: VGA, 0x03: DVI, 0x04: HDMI, 0x0F: DisplayPort
    'Input Source': 0x60, 
    
    # 0-100 (unexposed command)
    'Video Black Level: Red': 0x16, 
    
    # 0-100 (unexposed command)
    'Video Black Level: Green': 0x18, 
    
    # 0-100 (unexposed command)
    'Video Black Level: Blue': 0x1A, 
    
    # read-only, Hz
    'Horizontal Frequency': 0xAC, 
    
    # read-only, 0.01 Hz
    'Vertical Frequency': 0xAE, 
    
    # read-only, 0x01 -> Red / Green / Blue vertical stripe
    'Flat Panel Sub-Pixel Layout': 0xB2, 
    
    # read-only, 0x03 -> LCD (active matrix)
    'Display Technology Type': 0xB6, 
    
    # read-only, 0x6f, some id
    'Application Enable Key': 0xC6, 
    
    # read-only, 0x5605 -> Mstar Semiconductor
    'Display Controller Type': 0xC8, 
    
    # read-only, 0x0101
    'Display Firmware Level': 0xC9, 
    
    # 01 or 02 (unexposed command)
    'OSD': 0xCA, 
    
    # 0x01: power on, 0x04: standby (screenoff + blinking led), 0x05: power off
    'Power Mode': 0xD6, 
    
    # presets (manufacturer-defined):
    # no Text preset?
    # 00: Standard
    # 02: Mixed (Multimedia)
    # 03: Movie
    # 05: Games
    'Display Application': 0xDC, 
    
    # read-only, 0x0201 -> MCCS v2.1
    'VCP Version': 0xDF, 
    
    # Codes 0xE0 to 0xFF are manufacturer-specific
    
    # ignore for scripting, 00 or 01 (Energy Smart?)
    'Dell-E0': 0xE0, 
    
    # ignore for scripting
    # power control
    # 01: off
    # 00: on
    'Dell-E1': 0xE1, 
    
    # ignore for scripting, 00 01 02 04 06 0B 0C 0D 0F 10 11 13 14
    'Dell-E2': 0xE2, 
    
    # ignore for scripting, 00 or 01 (magicbright?)
    'Dell-F0': 0xF0, 
    
    # ignore for scripting, read
    'Dell-F1': 0xF1, 
    
    # ignore for scripting, read-only, (Energy Smart?)
    'Dell-F2': 0xF2, 
    
    # ignore for scripting
    'Dell-FD': 0xFD, 
}

# Reference: https://msdn.microsoft.com/en-us/library/dd692982(v=vs.85).aspx

_PHYSICAL_MONITOR_DESCRIPTION_SIZE = 128

_MONITORENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, 
                                      wintypes.HMONITOR, 
                                      wintypes.HDC, 
                                      ctypes.POINTER(wintypes.RECT), 
                                      wintypes.LPARAM)

class _PHYSICAL_MONITOR(ctypes.Structure):
    _fields_ = [('hPhysicalMonitor', wintypes.HANDLE), 
                ('szPhysicalMonitorDescription', 
                           wintypes.WCHAR * _PHYSICAL_MONITOR_DESCRIPTION_SIZE)]


def get_displays():
    """Get a list of the available displays"""
    def MonitorEnumProc_callback(hmonitor, hdc, lprect, lparam):
            monitors.append(hmonitor)
            return True
    monitors = []
    displays = []
    # get display monitors
    if not ctypes.windll.user32.EnumDisplayMonitors(None, None, 
                              _MONITORENUMPROC(MonitorEnumProc_callback), None):
            raise ctypes.WinError()
    # get physical monitors for each display monitor
    for monitor in monitors:
        monitor_number = wintypes.DWORD()
        if not ctypes.windll.dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(
                                         monitor, ctypes.byref(monitor_number)):
            raise ctypes.WinError()
        physical_monitor_array = (_PHYSICAL_MONITOR * monitor_number.value)()
        if not ctypes.windll.dxva2.GetPhysicalMonitorsFromHMONITOR(
                               monitor, monitor_number, physical_monitor_array):
            raise WinError()
        for physical_monitor in physical_monitor_array:
            displays.append(Display(physical_monitor.hPhysicalMonitor))
    return displays


class Display():
    
    def __init__(self, handle):
        self._handle = handle
        self._capabilities = None
    
    @property
    def capabilities(self):
        if self._capabilities is None:
            self._get_capabilities()
        return self._capabilities
    
    @property
    def capabilities_raw(self):
        if self._capabilities_raw is None:
            self._get_capabilities()
        return self._capabilities_raw
    
    def _get_capabilities(self):
        # this is slow
        length = wintypes.DWORD()
        if not ctypes.windll.dxva2.GetCapabilitiesStringLength(
                                            self._handle, ctypes.byref(length)):
            raise ctypes.WinError()
        capabilities_string = (ctypes.c_char * length.value)()
        if not ctypes.windll.dxva2.CapabilitiesRequestAndCapabilitiesReply(
                                     self._handle, capabilities_string, length):
            raise ctypes.WinError()
        self._capabilities_raw = capabilities_string.value.decode('ascii')
        self._capabilities = self.parse_capabilities_string(
                                                         self._capabilities_raw)
    
    @classmethod
    def parse_capabilities_string(cls, capabilities_string):
        level = 0
        capabilities = {}
        open_p = {}
        close_p = {0: 0}
        id = {}
        for i, chr in enumerate(capabilities_string):
            if chr == '(':
                if i == 0:
                    close_p[0] = 1
                    continue
                open_p[level] = i
                if level == 0:
                    id[0] = capabilities_string[close_p[0] + 1:i]
                level += 1
            elif chr == ')':
                level -= 1
                close_p[level] = i
                if level == 0:
                    values = capabilities_string[open_p[0] + 1:i]
                    if id[0] == 'cmds':
                        values = values.split()
                    elif id[0] == 'vcp':
                        values = cls._parse_vcp_list(values)
                    capabilities[id[0]] = values
        return capabilities
    
    @staticmethod
    def _parse_vcp_list(vcp_list):
        vcp_dict = {}
        open_p = 0
        for i, chr in enumerate(vcp_list):
            if chr == '(':
                open_p = i
                code = vcp_list[i-2:i]
            elif chr == ')':
                vcp_dict[code] = vcp_list[open_p + 1:i].split()
            elif chr.isspace() and vcp_list[i-1] != ')':
                vcp_dict[vcp_list[i-2:i]] = None
        return vcp_dict
    
    def _get_vcf_feature_and_vcf_feature_reply(self, code):
        """Get current and maximun values for continuous VCP codes"""
        current_value = wintypes.DWORD()
        maximum_value = wintypes.DWORD()
        if not ctypes.windll.dxva2.GetVCPFeatureAndVCPFeatureReply(
                                       self._handle, wintypes.BYTE(code), None, 
                                       ctypes.byref(current_value), 
                                       ctypes.byref(maximum_value)):
            raise ctypes.WinError()
        return current_value.value, maximum_value.value

    def _set_vcp_feature(self, code, value):
        """Set 'code' to 'value'"""
        if not ctypes.windll.dxva2.SetVCPFeature(self._handle, 
                                    wintypes.BYTE(code), wintypes.DWORD(value)):
            raise ctypes.WinError()
    
    @property
    def model(self):
        return self.capabilities['model']
    
    _display_technology_types = {
        0x01: 'CRT (shadow mask)', 
        0x02: 'CRT (aperture grill)', 
        0x03: 'LCD (active matrix)', 
        0x04: 'LCoS', 
        0x05: 'Plasma', 
        0x06: 'OLED', 
        0x07: 'EL', 
        0x08: 'Dynamic MEM e.g. DLP', 
        0x09: 'Static MEM e.g. iMOD', }
    
    @property
    def display_technology_type(self):
        return self._display_technology_types.get(
                        self._get_vcf_feature_and_vcf_feature_reply(
                                       vcp_codes['Display Technology Type'])[0])
    
    _flat_panel_sub_pixel_layouts = {
        0x00: 'Sub-pixel layout is not defined', 
        0x01: 'Red / Green / Blue vertical stripe', 
        0x02: 'Red / Green / Blue horizontal stripe', 
        0x03: 'Blue / Green / Red vertical stripe', 
        0x04: 'Blue/ Green / Red horizontal stripe', 
        0x05: 'Quad-pixel, a 2 x 2 sub-pixel structure with red at top left, '
              'blue at bottom right and green at top right and bottom left', 
        0x06: 'Quad-pixel, a 2 x 2 sub-pixel structure with red at bottom '
              'left, blue at top right and green at top left and bottom right', 
        0x07: 'Delta (triad)', 
        0x08: 'Mosaic with interleaved sub-pixels of different colors', }
    
    @property
    def flat_panel_sub_pixel_layout(self):
        return self._flat_panel_sub_pixel_layouts.get(
                        self._get_vcf_feature_and_vcf_feature_reply(
                                   vcp_codes['Flat Panel Sub-Pixel Layout'])[0])
    
    _display_controller_type_lsb = {
        0x01: 'Conexant', 
        0x02: 'Genesis Microchip', 
        0x03: 'Macronix', 
        0x04: 'MRT (Media Reality Technologies)', 
        0x05: 'Mstar Semiconductor', 
        0x06: 'Myson', 
        0x07: 'Philips', 
        0x08: 'PixelWorks', 
        0x09: 'RealTek Semiconductor', 
        0x0A: 'Sage', 
        0x0B: 'Silicon Image', 
        0x0C: 'SmartASIC', 
        0x0D: 'STMicroelectronics', 
        0x0E: 'Topro', 
        0x0F: 'Trumpion', 
        0x10: 'Welltrend', 
        0x11: 'Samsung', 
        0x12: 'Novatek Microelectronics', 
        0x13: 'STK', 
        0xFF: 'Manufacturer designed controller', }
    
    @property
    def display_controller_type(self):
        value = self._get_vcf_feature_and_vcf_feature_reply(
                                        vcp_codes['Display Controller Type'])[0]
        return self._display_controller_type_lsb.get(value & 0xff)
                                                      
    
    @property
    def display_firmware_level(self):
        value = self._get_vcf_feature_and_vcf_feature_reply(
                                         vcp_codes['Display Firmware Level'])[0]
        return '{}.{}'.format(value >> 8, value & 0x1f)
    
    @property
    def application_enable_key(self):
        return self._get_vcf_feature_and_vcf_feature_reply(
                                         vcp_codes['Application Enable Key'])[0]
    
    @property
    def vcp_version(self):
        value = self._get_vcf_feature_and_vcf_feature_reply(
                                                    vcp_codes['VCP Version'])[0]
        return '{}.{}'.format(value >> 8, value & 0xff)
    
    @property
    def vertical_frequency(self):
        return self._get_vcf_feature_and_vcf_feature_reply(
                                       vcp_codes['Vertical Frequency'])[0] / 100
    
    @property
    def horizontal_frequency(self):
        value = self._get_vcf_feature_and_vcf_feature_reply(
                                           vcp_codes['Horizontal Frequency'])[0]
        if value < 50000: # MSB is missing, should be 0 or 1
            value |= 0x10000
        return value / 1000
    
    @property
    def brightness(self):
        return self._get_vcf_feature_and_vcf_feature_reply(
                                                      vcp_codes['Luminance'])[0]
    
    @brightness.setter
    def brightness(self, value):
        current, max = self._get_vcf_feature_and_vcf_feature_reply(
                                                         vcp_codes['Luminance'])
        if value == current:
            return
        if value > max:
            value = max
        elif value < 0:
            value = 0
        self._set_vcp_feature(vcp_codes['Luminance'], value)
    
    @property
    def max_brightness(self):
        return self._get_vcf_feature_and_vcf_feature_reply(
                                                      vcp_codes['Luminance'])[1]
     
    @property
    def contrast(self):
        return self._get_vcf_feature_and_vcf_feature_reply(
                                                       vcp_codes['Contrast'])[0]
    
    @contrast.setter
    def contrast(self, value):
        current, max = self._get_vcf_feature_and_vcf_feature_reply(
                                                          vcp_codes['Contrast'])
        if value == current:
            return
        if value > max:
            value = max
        elif value < 0:
            value = 0
        self._set_vcp_feature(vcp_codes['Contrast'], value)
    
    @property
    def max_contrast(self):
        return self._get_vcf_feature_and_vcf_feature_reply(
                                                       vcp_codes['Contrast'])[1]
     
    @property
    def color_temperature(self):
        value = self._get_vcf_feature_and_vcf_feature_reply(
                                      vcp_codes['Color Temperature Request'])[0]
        increment = self._get_vcf_feature_and_vcf_feature_reply(
                                    vcp_codes['Color Temperature Increment'])[0]
        return 3000 + increment * value
    
    @color_temperature.setter
    def color_temperature(self, value):
        current, max = self._get_vcf_feature_and_vcf_feature_reply(
                                         vcp_codes['Color Temperature Request'])
        increment = self._get_vcf_feature_and_vcf_feature_reply(
                                    vcp_codes['Color Temperature Increment'])[0]
        value = (value - 3000) // increment
        if value == current:
            return
        if value > max:
            value = max
        elif value < 0:
            value = 0
        self._set_vcp_feature(vcp_codes['Color Temperature Request'], value)
    
    @property
    def max_color_temperature(self):
        value = self._get_vcf_feature_and_vcf_feature_reply(
                                      vcp_codes['Color Temperature Request'])[1]
        increment = self._get_vcf_feature_and_vcf_feature_reply(
                                    vcp_codes['Color Temperature Increment'])[0]
        return 3000 + increment * value
     
    _color_presets = {0x01: 'srgb', 0x04: '5000k', 0x05: '6500k',
                      0x06: '7500k', 0x08: '9300k', 0x09: '10000k',
                      0x0B: '5700k', 0x0C: 'user' }
    _color_presets_i = {'srgb': 0x01, '5000k': 0x04, '6500k': 0x05,
                        '7500k': 0x06, '9300k': 0x08, '10000k': 0x09,
                        '5700k': 0x0B, 'user': 0x0C}
    
    @property
    def color_preset(self):
        value = self._get_vcf_feature_and_vcf_feature_reply(
                                            vcp_codes['Select Color Preset'])[0]
        return self._color_presets[value]
    
    @color_preset.setter
    def color_preset(self, value):
        value = self._color_presets_i[value]
        if value == self._get_vcf_feature_and_vcf_feature_reply(
                                           vcp_codes['Select Color Preset'])[0]:
            return
        self._set_vcp_feature(vcp_codes['Select Color Preset'], value)
     
    @property
    def rgb(self):
        return [self._get_vcf_feature_and_vcf_feature_reply(
                    vcp_codes['Video Gain (Drive): {}'.format(color)])[0] 
                for color in ['Red', 'Green', 'Blue']]
    
    @rgb.setter
    def rgb(self, values):
        color = ['Red', 'Green', 'Blue']
        template = 'Video Gain (Drive): {}'
        for i, value in enumerate(values):
            vcp_name = template.format(color[i])
            current, max = self._get_vcf_feature_and_vcf_feature_reply(
                                                            vcp_codes[vcp_name])
            if value in (-1, current):
                continue
            if value > max:
                value = max
            elif value < 0:
                value = 0
            self._set_vcp_feature(vcp_codes[vcp_name], value)
    
    @property
    def max_rgb(self):
        return [self._get_vcf_feature_and_vcf_feature_reply(
                    vcp_codes['Video Gain (Drive): {}'.format(color)])[1] 
                for color in ['Red', 'Green', 'Blue']]
    
    _input_sources = {0x01: 'vga', 0x03: 'dvi', 0x04: 'hdmi', 0x0F: 'dp'}
    _input_sources_i = {'vga': 0x01, 'dvi': 0x03, 'hdmi': 0x04, 'dp': 0x0F}
    
    @property
    def input_source(self):
        value = self._get_vcf_feature_and_vcf_feature_reply(
                                                   vcp_codes['Input Source'])[0]
        return self._input_sources[value]
    
    @input_source.setter
    def input_source(self, value):
        value = self._input_sources_i[value]
        if value == self._get_vcf_feature_and_vcf_feature_reply(
                                                  vcp_codes['Input Source'])[0]:
            return
        self._set_vcp_feature(vcp_codes['Input Source'], value)
    
    _display_applications = {0x00: 'std', 0x02: 'mix', 0x03: 'mov', 0x05: 'gam'}
    _display_applications_i = {'std': 0x00, 'mix': 0x02, 'mov': 0x03, 'gam': 0x05}
    
    @property
    def display_application(self):
        value = self._get_vcf_feature_and_vcf_feature_reply(
                                                   vcp_codes['Display Application'])[0]
        return self._display_applications[value]
    
    @display_application.setter
    def display_application(self, value):
        value = self._display_applications_i[value]
        if value == self._get_vcf_feature_and_vcf_feature_reply(
                                                  vcp_codes['Display Application'])[0]:
            return
        self._set_vcp_feature(vcp_codes['Display Application'], value)
    
    _power_mode = {0x01: 'on', 0x05: 'off'}
    _power_mode_i = {'on': 0x01, 'off': 0x05}
    
    @property
    def power_mode(self):
        value = self._get_vcf_feature_and_vcf_feature_reply(
                                                     vcp_codes['Power Mode'])[0]
        return self._power_mode[value]
    
    @power_mode.setter
    def power_mode(self, value):
        value = self._power_mode_i[value]
        if value == self._get_vcf_feature_and_vcf_feature_reply(
                                                    vcp_codes['Power Mode'])[0]:
            return
        self._set_vcp_feature(vcp_codes['Power Mode'], value)
    
    _restore_options = {
                   'all': 'Restore Factory Defaults', 
                   'luminance': 'Restore Factory Luminance/ Contrast Defaults', 
                   'color': 'Restore Factory Color Defaults'}
    
    def restore(self, option):
        """Restore factory defaults ('all' / 'luminance' / 'colors')"""
        self._set_vcp_feature(vcp_codes[self._restore_options[option]], 1)
    
    def close(self):
        if not ctypes.windll.dxva2.DestroyPhysicalMonitor(self._handle):
            raise ctypes.WinError()
    
    def __del__(self):
        self.close()


if __name__ == '__main__':
    
    import sys
    import os
    import argparse
    import textwrap
    
    
    # Custom Action for argparse
    # The accepted number of arguments can be specified with '_nargs' (list)
    # 'nargs' must be '*'
    # Added also 'default_str' and 'const_str', formatted with 'default' and 
    # 'const' respectively, that can be used on the 'help' string
    class VariableNArgsAction(argparse.Action):
        
        def __init__(self, option_strings, dest, **kwargs):
            self._nargs = kwargs.pop('_nargs', None)
            self.const_str = kwargs.pop('const_str', None)
            self.default_str = kwargs.pop('default_str', None)
            argparse.Action.__init__(self, option_strings, dest, **kwargs)
            if self.const_str is not None:
                self.const_str = self.const_str.format(*self.const)
            if self.default_str is not None:
                self.default_str = self.default_str.format(*self.default)
        
        def __call__(self, parser, namespace, values, option_string=None):
            if len(values) not in self._nargs:
                parser.error('argument {}: invalid number of arguments'
                             .format('/'.join(self.option_strings)))
            if not values and self.const is not None:
                values = self.const
            setattr(namespace, self.dest, values)
    
    
    # For VariableNArgsAction, use 'metavar' as the displayed args string
    # XXX: not part of the public API
    class RawDescriptionHelpFormatter2(argparse.RawDescriptionHelpFormatter):
        
        def _format_args(self, action, *args, **kwargs):
            if action.metavar is not None and isinstance(action, 
                                                         VariableNArgsAction):
                return action.metavar
            return argparse.RawDescriptionHelpFormatter._format_args(
                self, action, *args, **kwargs)
    
    
    # Parse command line
    name = os.path.basename(__file__)
    description, license1, license2 = __doc__.rpartition('\nCopyright')
    license = license1 + license2
    parser = argparse.ArgumentParser(prog=name, description=description, 
        epilog=license, formatter_class=RawDescriptionHelpFormatter2, 
        add_help=False)
    parser_o = parser.add_argument_group('optional arguments', 
             'if not argument is passed, all available display info is printed')
    parser_o.add_argument('-h', '--help', action='help', 
                          help='show this help message and exit')
    parser_o.add_argument('-V', '--version', action='version', 
                          version='{} v{}\n{}'.format(name, version, license))
    parser_o.add_argument('-b', '--brightness', nargs='?', type=int, 
                          const=-1, metavar='NEW_BRIGHTNESS', 
                          help='retrieve or set brightness (0-100)')
    parser_o.add_argument('-c', '--contrast', type=int, nargs='?',
                          const=-1, metavar='NEW_CONTRAST', 
                          help='retrieve or set contrast (0-100)')
    parser_o.add_argument('-cp', '--color_preset', type = str.lower, nargs='?', 
                          choices=sorted(Display._color_presets_i.keys()), 
                          const=-1, help='retrieve or set the color preset')
    parser_o.add_argument('-u', '--rgb', nargs='*', action=VariableNArgsAction, 
                          _nargs=(0, 3), type=int, const=-1, 
                          metavar='[NEW_RED NEW_GREEN NEW_BLUE]', 
                          help='retrieve or set red, green and blue gains '
                          '(0-100)')
    parser_o.add_argument('-i', '--input_source', type = str.lower, nargs='?', 
                          choices=sorted(Display._input_sources_i.keys()), 
                          const=-1, help='retrieve or set the input source')
    parser_o.add_argument('-p', '--power_mode', type = str.lower, nargs='?', 
                          choices=sorted(Display._power_mode_i.keys()), 
                          const=-1, help='retrieve or set the power mode')
    parser_o.add_argument('-app', '--display_application', type = str.lower, nargs='?', 
                          choices=sorted(Display._display_applications_i.keys()), 
                          const=-1, help='retrieve or set the display application')
    parser_o.add_argument('-r', '--restore', type = str.lower, 
                          choices=sorted(Display._restore_options.keys()), 
                          help='restore factory defaults')
    
    settings = vars(parser.parse_args())
    
    # Set / show display parameters
    for display in get_displays():
        model = display.capabilities['model']
        if model in ('U2713HM'):
            if len(sys.argv) == 1:
                print(textwrap.dedent('''\
            model: {model}
            display technology type: {display.display_technology_type}
            flat panel sub-pixel layout: {display.flat_panel_sub_pixel_layout}
            display controller type: {display.display_controller_type}
            display firmware level: v{display.display_firmware_level}
            application enable key: {display.application_enable_key}
            vcp version: v{display.vcp_version}
            vertical frequency: {display.vertical_frequency} Hz
            horizontal frequency: {display.horizontal_frequency} kHz
            
            brightness: {display.brightness}
            contrast {display.contrast}
            color preset: {display.color_preset}
            rgb gains: {display.rgb}
            input source: {display.input_source}
            power mode: {display.power_mode}
            '''.format(model=model, display=display)))
                sys.exit()
            restore = settings.pop('restore')
            if restore:
                display.restore(restore)
            for key, value in settings.items():
                if value is not None:
                    if value == -1:
                        print(getattr(display, key))
                    else:
                        setattr(display, key, value)
        else:
            print('model not supported:', model, file=sys.stderr)