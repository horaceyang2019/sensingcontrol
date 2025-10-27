# -*- coding: utf-8 -*-

#http://www.raspberrypi-spy.co.uk/2013/10/analogue-sensors-on-the-raspberry-pi-using-an-mcp3008/
#http://magicjackting.pixnet.net/blog/post/164725144
#http://embeddedmicro.weebly.com/spi.html
#http://raspberrypi-aa.github.io/session3/spi.html
#===============================================================================
# MCP 3008 Pin          Pi GPIO Pin #    Pi Pin Name
# ==============        ===============  =============
#  16  VDD                 1              3.3 V
#  15  VREF                1              3.3 V
#  14  AGND                6              GND
#  13  CLK                23                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    GPIO11 SPI0_SCLK
#  12  DOUT               21              GPIO09 SPI0_MISO
#  11  DIN                19              GPIO10 SPI0_MOSI
#  10  CS                 24              GPIO08 CE0
#   9  DGND                6              GND
#===============================================================================
# LM35 Pin        MCP3008 Pin
# ==========      =============
#  Vs              16 VDD
#  Vout             1 CH0
#  GND              9 DGND
#===============================================================================
import spidev
import time

class ADConverter(object):
    
    def __init__(self, port, device):
        self.spi = spidev.SpiDev()    # create spi object
        self.spi.open(port, device)           # open spi port 0, device (CS) 1         
        
    def readADC(self, ch):
        # read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
        if ((ch > 7) or (ch < 0)):
            return -1
    
    # send 3 bytes to ADC0 "00000001 10000000 00000000"
        adc = self.spi.xfer2([1, (8 + ch) << 4, 0]) 
        adcout = ((adc[1] & 3) << 8) + adc[2]  # 10 bits data
        return adcout

    # Convert data to voltage level
    def convertVolts(self, data, deci):
        volts = (data * 3.3) / float(1023) #supply voltage 3.3 voltage by 10 bits
        volts = round(volts, deci)
        return volts

    def convertTemp(self, data, deci):
        temp = data * 100
        temp = round(temp,deci)
        return temp

#------------------------------------------------------------------------------------------------        
if __name__ == '__main__':
    
    temp_ch = 0
    adc =  ADConverter(bus = 0,device = 0);  # 

    while True:
        value = adc.readADC(temp_ch)
        volts = adc.convertVolts(value, 4)
        temperature = adc.convertTemp(volts, 2)
        print ("%4d/1023 => %5.3f V => %4.1f ¢XC" % (value, volts, temperature))
        time.sleep(1)